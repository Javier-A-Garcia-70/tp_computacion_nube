import asyncio
import io
import json
import re
import os
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional
import httpx
import anthropic as anthropic_sdk
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_voyageai import VoyageAIEmbeddings
from langchain_postgres import PGVector
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from config import CloudConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AskRequest(BaseModel):
    question: str
    modo: str = "auto"       # "auto", "factual", "cuento"
    nombre: Optional[str] = None

class StoryRequest(BaseModel):
    prompt: str
    nombre: Optional[str] = None
    formato: str = "pdf"   # "chat" devuelve JSON | "pdf" devuelve archivo PDF

KEYWORDS_CUENTO = {"escribe", "crea", "inventa", "cuento", "historia", "relato", "genera", "imagina", "narra", "redacta", "compone"}

def _detect_modo(question: str) -> str:
    words = set(question.lower().split())
    if words & KEYWORDS_CUENTO:
        return "cuento"
    return "factual"

def _build_prompt(modo: str, nombre: Optional[str]) -> PromptTemplate:
    nombre_linea = (
        f"El interlocutor se llama {nombre}. Dirígete a él por ese nombre."
        if nombre
        else "No conoces el nombre del interlocutor. NO lo llames Watson ni asumas ningún nombre. Si querés dirigirte a él, usá 'usted' o 'mi estimado visitante'."
    )

    if modo == "cuento":
        template = (
            "Sos Sherlock Holmes, el detective de Baker Street 221B. "
            "Escribí una historia en primera persona con tu estilo victoriano, deductivo y preciso. "
            "Usá los documentos como fuente de personajes, lugares y casos reales de tu historia. "
            f"{nombre_linea} "
            "IMPORTANTE: La historia debe tener hasta 3 partes o capítulos, en funcion de la complejidad del caso. "
            "Cada parte debe tener un título. "
            "La historia DEBE tener un final conclusivo y satisfactorio en la tercera parte como mucho. "
            "NO dejes la historia abierta ni cortada. El misterio debe resolverse completamente.\n\n"
            "Documentos de referencia:\n{context}\n\n"
            "Solicitud: {question}\n\n"
            "Historia:"
        )
    else:
        template = (
            "Sos Sherlock Holmes, el detective de Baker Street 221B. "
            "Respondé en primera persona con tu estilo deductivo, preciso y ocasionalmente arrogante. "
            f"{nombre_linea} "
            "Basá tu respuesta en los documentos. Sé conciso y directo.\n\n"
            "Documentos de referencia:\n{context}\n\n"
            "Pregunta: {question}\n\n"
            "Respuesta:"
        )

    return PromptTemplate(template=template, input_variables=["context", "question"])


class MultiCloudQAService:
    def __init__(self, config: CloudConfig):
        self.config = config
        self.current_provider = None
        self.current_embedding_provider = None
        self._retriever = None

    def get_embeddings(self):
        embeddings = VoyageAIEmbeddings(
            voyage_api_key=self.config.voyage_api_key,
            model=self.config.voyage_model
        )
        self.current_embedding_provider = 'voyage'
        logger.info("✅ Voyage AI embeddings configurados")
        return embeddings

    def get_llm(self, temperature: float = 0.1, max_tokens: int = 1024):
        self.current_provider = 'anthropic'
        return ChatAnthropic(
            api_key=self.config.anthropic_api_key,
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            temperature=temperature
        )

    def initialize_qa_chain(self):
        try:
            embeddings = self.get_embeddings()
            db = PGVector(
                embeddings=embeddings,
                collection_name="lorechat_holmes",
                connection=self.config.database_url,
            )
            self._retriever = db.as_retriever(search_kwargs={"k": 10})
            # Forzar que current_provider quede seteado
            self.get_llm()
            logger.info("✅ Claude (Anthropic) configurado")
            logger.info(f"🚀 Sistema listo — Embeddings: {self.current_embedding_provider.upper()} | LLM: {self.current_provider.upper()}")
        except Exception as e:
            logger.error(f"Error inicializando sistema: {e}")
            raise

    def build_chain(self, modo: str, nombre: Optional[str]) -> RetrievalQA:
        temperature = 0.85 if modo == "cuento" else 0.1
        max_tokens = 8000 if modo == "cuento" else 1024
        prompt = _build_prompt(modo, nombre)
        return RetrievalQA.from_chain_type(
            llm=self.get_llm(temperature=temperature, max_tokens=max_tokens),
            chain_type="stuff",
            retriever=self._retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )


# Configuración global
config = CloudConfig()
qa_service = MultiCloudQAService(config)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        qa_service.initialize_qa_chain()
        app.state.qa_service = qa_service
        logger.info("✅ API lista")
    except Exception as e:
        logger.error(f"❌ Error al iniciar: {e}")
        raise
    yield
    logger.info("🔄 Cerrando API")

app = FastAPI(
    title="LoreChat Holmes",
    description="RAG sobre el corpus de Sherlock Holmes",
    lifespan=lifespan
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://ia-responde-mvp.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "llm_provider": qa_service.current_provider,
        "embedding_provider": qa_service.current_embedding_provider,
        "voyage_model": config.voyage_model
    }

@app.post("/ask")
async def ask(request: AskRequest):
    logger.info(f"Pregunta recibida: {request.question}")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")

    modo_efectivo = request.modo if request.modo != "auto" else _detect_modo(request.question)
    logger.info(f"Modo: {modo_efectivo} | Nombre: {request.nombre or '(desconocido)'}")

    try:
        t0 = time.time()

        logger.info(f"⏳ [1] Construyendo chain (modo={modo_efectivo}, max_tokens={'4000' if modo_efectivo == 'cuento' else '1024'})...")
        chain = app.state.qa_service.build_chain(modo_efectivo, request.nombre)
        t_chain = time.time()
        logger.info(f"✅ [1] Chain lista en {t_chain - t0:.2f}s")

        logger.info(f"⏳ [2] Recuperando docs de pgvector (k=10)...")
        retriever = app.state.qa_service._retriever
        loop = asyncio.get_event_loop()
        docs_retrieved = await loop.run_in_executor(
            None, lambda: retriever.invoke(request.question)
        )
        t_retrieval = time.time()
        logger.info(f"✅ [2] {len(docs_retrieved)} docs recuperados en {t_retrieval - t_chain:.2f}s")

        # Estimar tamaño de contexto enviado al LLM
        context_chars = sum(len(d.page_content) for d in docs_retrieved)
        question_chars = len(request.question)
        logger.info(f"📏 Contexto: {context_chars} chars docs + {question_chars} chars pregunta ≈ {(context_chars + question_chars) // 4} tokens estimados")

        logger.info(f"⏳ [3] Llamando al LLM (Claude)...")
        result = chain.invoke({"query": request.question})
        t_llm = time.time()
        answer = result["result"]
        logger.info(f"✅ [3] LLM respondió en {t_llm - t_retrieval:.2f}s | respuesta: {len(answer)} chars ≈ {len(answer) // 4} tokens")

        docs_sorted = result.get("source_documents", [])

        # Post-procesar con spaCy solo en modo factual
        if modo_efectivo != "cuento":
            logger.info(f"⏳ [4] Post-procesando con spaCy...")
            import spacy
            try:
                nlp = spacy.load("es_core_news_sm")
                doc = nlp(answer)
                sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
                paragraphs = []
                for i in range(0, len(sentences), 4):
                    paragraphs.append(" ".join(sentences[i:i+4]))
                answer = "\n\n".join(paragraphs)
                t_spacy = time.time()
                logger.info(f"✅ [4] spaCy en {t_spacy - t_llm:.2f}s")
            except Exception as e:
                logger.error(f"spaCy error: {e}")

        seen_chunks = set()
        sources = []
        for doc in docs_sorted:
            chunk_id = doc.metadata.get("chunk_id")
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                sources.append({
                    "source": doc.metadata.get("source"),
                    "chunk_id": chunk_id,
                    "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })

        t_total = time.time()
        logger.info(f"🏁 TOTAL: {t_total - t0:.2f}s | chain={t_chain-t0:.2f}s | retrieval={t_retrieval-t_chain:.2f}s | llm={t_llm-t_retrieval:.2f}s")
        return {
            "answer": answer,
            "sources": sources,
            "modo": modo_efectivo,
            "llm_provider": qa_service.current_provider,
            "embedding_provider": qa_service.current_embedding_provider
        }
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ─── /generate-story helpers ──────────────────────────────────────────────────

async def _generate_story_meta(story_text: str, api_key: str) -> dict:
    """Una sola llamada a Claude: sinopsis + 4 prompts de imagen."""
    client = anthropic_sdk.AsyncAnthropic(api_key=api_key)
    excerpt = story_text[:4000]
    msg = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": (
                f"Basándote en este cuento de Sherlock Holmes:\n\n{excerpt}\n\n"
                "Generá en JSON puro sin markdown:\n"
                '{"synopsis": "sinopsis atractiva para contratapa, 120 palabras, sin spoilers del final", '
                '"image_prompts": {'
                '"cover": "dramatic Victorian illustration for book cover, Sherlock Holmes and a child, detailed, atmospheric, pencil sketch style",'
                '"internal_1": "Victorian London scene from the story, detailed pencil illustration",'
                '"internal_2": "key mystery scene from the story, Victorian pencil illustration",'
                '"back": "Baker Street 221B exterior, foggy Victorian London, atmospheric pencil illustration"'
                '}}'
            )
        }]
    )
    raw = re.sub(r"```json\s*|\s*```", "", msg.content[0].text).strip()
    return json.loads(raw)


async def _generate_image_leonardo(prompt: str, api_key: str) -> bytes:
    """Submite job a Leonardo AI y espera el resultado (polling)."""
    if not api_key:
        raise ValueError("LEONARDO_API_KEY no configurada")

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://cloud.leonardo.ai/api/rest/v1/generations",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "prompt": prompt,
                "modelId": "b24e16ff-06e3-43eb-8d33-4416c2d75876",
                "width": 768,
                "height": 768,
                "num_images": 1,
            }
        )
        resp.raise_for_status()
        generation_id = resp.json()["sdGenerationJob"]["generationId"]

        for _ in range(30):
            await asyncio.sleep(3)
            poll = await client.get(
                f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            data = poll.json().get("generations_by_pk", {})
            if data.get("status") == "COMPLETE":
                image_url = data["generated_images"][0]["url"]
                img_resp = await client.get(image_url)
                return img_resp.content

    raise TimeoutError(f"Leonardo AI timeout: {prompt[:50]}")


def _build_pdf(story_text: str, synopsis: str, title: str, nombre: Optional[str],
               cover_img, internal_1_img, internal_2_img, back_img) -> bytes:
    """Arma el PDF con ReportLab."""
    buffer = io.BytesIO()
    page_w = A4[0] - 5 * cm

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2.5*cm, rightMargin=2.5*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_st   = ParagraphStyle('T', parent=styles['Title'],  fontSize=22, alignment=1, spaceAfter=14)
    sub_st     = ParagraphStyle('S', parent=styles['Normal'], fontSize=12, alignment=1, spaceAfter=8)
    body_st    = ParagraphStyle('B', parent=styles['Normal'], fontSize=11, leading=17, spaceAfter=8)
    synopsis_st= ParagraphStyle('Y', parent=styles['Normal'], fontSize=10, leading=14, alignment=4)

    def make_img(img_bytes, w, h):
        if not img_bytes:
            return None
        try:
            return RLImage(io.BytesIO(img_bytes), width=w, height=h)
        except Exception:
            return None

    flow = []

    # === TAPA ===
    flow.append(Spacer(1, 1.5*cm))
    img = make_img(cover_img, page_w, 13*cm)
    if img:
        flow.append(img)
        flow.append(Spacer(1, 0.5*cm))
    flow.append(Paragraph(title[:80], title_st))
    flow.append(Paragraph("Un caso de Sherlock Holmes", sub_st))
    if nombre:
        flow.append(Paragraph(f"Protagonista: {nombre}", sub_st))
    flow.append(PageBreak())

    # === TEXTO CON ILUSTRACIONES ===
    paras = [p.strip() for p in story_text.split('\n\n') if p.strip()]
    third = max(1, len(paras) // 3)

    for i, para in enumerate(paras):
        flow.append(Paragraph(para, body_st))

        if i == third - 1:
            img = make_img(internal_1_img, 10*cm, 8*cm)
            if img:
                flow += [Spacer(1, 0.3*cm), img, Spacer(1, 0.3*cm)]

        if i == 2 * third - 1:
            img = make_img(internal_2_img, 10*cm, 8*cm)
            if img:
                flow += [Spacer(1, 0.3*cm), img, Spacer(1, 0.3*cm)]

    flow.append(PageBreak())

    # === CONTRATAPA ===
    img = make_img(back_img, page_w, 8*cm)
    if img:
        flow.append(img)
        flow.append(Spacer(1, 0.5*cm))
    flow.append(HRFlowable(width="100%", thickness=1, color=colors.darkgrey))
    flow.append(Spacer(1, 0.3*cm))
    flow.append(Paragraph("Sinopsis", sub_st))
    flow.append(Paragraph(synopsis, synopsis_st))

    doc.build(flow)
    return buffer.getvalue()


# ─── Endpoint /generate-story ─────────────────────────────────────────────────

@app.post("/generate-story")
async def generate_story(request: StoryRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="El prompt no puede estar vacío")

    t0 = time.time()
    loop = asyncio.get_event_loop()

    # 1. Generar texto del cuento (RetrievalQA es sync → executor)
    logger.info(f"⏳ [1] Generando texto del cuento...")
    chain = app.state.qa_service.build_chain("cuento", request.nombre)
    story_result = await loop.run_in_executor(
        None, lambda: chain.invoke({"query": request.prompt})
    )
    story_text = story_result["result"]
    t1 = time.time()
    logger.info(f"✅ [1] Cuento: {len(story_text)} chars ≈ {len(story_text)//4} tokens | {t1-t0:.1f}s")

    # Modo chat: devolver JSON sin PDF
    if request.formato == "chat":
        logger.info("📨 Formato chat — devolviendo JSON")
        return {
            "story": story_text,
            "modo": "cuento",
            "llm_provider": qa_service.current_provider,
        }

    # 2 & 3. Sinopsis e imágenes — solo si Leonardo está configurado
    t2 = t1
    synopsis = ""
    images = [None, None, None, None]
    if config.leonardo_api_key:
        logger.info(f"⏳ [2] Generando sinopsis y prompts de imagen (Claude)...")
        meta = await _generate_story_meta(story_text, config.anthropic_api_key)
        t2 = time.time()
        logger.info(f"✅ [2] Meta generada en {t2-t1:.1f}s")

        logger.info(f"⏳ [3] Generando imágenes con Leonardo AI...")
        prompts_img = [
            meta["image_prompts"]["cover"],
            meta["image_prompts"]["internal_1"],
            meta["image_prompts"]["internal_2"],
            meta["image_prompts"]["back"],
        ]
        images_raw = await asyncio.gather(
            *[_generate_image_leonardo(p, config.leonardo_api_key) for p in prompts_img],
            return_exceptions=True
        )
        images = [b if isinstance(b, bytes) else None for b in images_raw]
        ok_count = sum(1 for i in images if i)
        logger.info(f"✅ [3] Imágenes: {ok_count}/4 generadas en {time.time()-t2:.1f}s")
        synopsis = meta["synopsis"]
    else:
        logger.info("⏭️  [2/3] Sin LEONARDO_API_KEY — saltando sinopsis e imágenes")
        t3 = t2

    # 4. Armar PDF
    logger.info(f"⏳ [4] Armando PDF con ReportLab...")
    pdf_bytes = await loop.run_in_executor(
        None,
        lambda: _build_pdf(
            story_text=story_text,
            synopsis=synopsis,
            title=request.prompt,
            nombre=request.nombre,
            cover_img=images[0],
            internal_1_img=images[1],
            internal_2_img=images[2],
            back_img=images[3],
        )
    )
    t4 = time.time()
    logger.info(f"✅ [4] PDF: {len(pdf_bytes)//1024}KB en {t4-t3:.1f}s")
    logger.info(f"🏁 TOTAL generate-story: {t4-t0:.1f}s | texto={t1-t0:.1f}s | meta={t2-t1:.1f}s | imgs={t3-t2:.1f}s | pdf={t4-t3:.1f}s")

    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_slug = (request.nombre or 'cuento').lower().replace(' ', '_')
    filename = f"holmes_{nombre_slug}_{ts}.pdf"

    cuentos_dir = os.path.join(os.path.dirname(__file__), "cuentos")
    os.makedirs(cuentos_dir, exist_ok=True)
    saved_path = os.path.join(cuentos_dir, filename)
    with open(saved_path, "wb") as f:
        f.write(pdf_bytes)
    logger.info(f"💾 PDF guardado en cuentos/{filename}")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

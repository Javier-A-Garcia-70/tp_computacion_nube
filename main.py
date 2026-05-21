import asyncio
import io
import json
import re
import os
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
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

try:
    import spacy
    _nlp = spacy.load("es_core_news_sm")
    logger.info("✅ spaCy cargado")
except Exception as _spacy_err:
    _nlp = None
    logger.warning(f"spaCy no disponible: {_spacy_err}")

class HistoryMessage(BaseModel):
    role: str   # "user" | "holmes"
    content: str

class AskRequest(BaseModel):
    question: str
    modo: str = "auto"       # "auto", "factual", "cuento"
    nombre: Optional[str] = None
    history: List[HistoryMessage] = []

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
    allow_origins=config.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
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

        chain = app.state.qa_service.build_chain(modo_efectivo, request.nombre)

        query = request.question
        if request.history:
            window = request.history[-6:]
            history_text = "Conversación previa:\n"
            for msg in window:
                role = "Usuario" if msg.role == "user" else "Holmes"
                history_text += f"{role}: {msg.content}\n"
            query = history_text + "\nPregunta actual: " + request.question

        result = chain.invoke({"query": query})
        t_llm = time.time()
        answer = result["result"]
        docs_sorted = result.get("source_documents", [])

        logger.info(f"✅ LLM: {t_llm - t0:.2f}s | {len(docs_sorted)} chunks recuperados")

        # Post-procesar con spaCy solo en modo factual
        if modo_efectivo != "cuento" and _nlp is not None:
            try:
                spacy_doc = _nlp(answer)
                sentences = [sent.text.strip() for sent in spacy_doc.sents if sent.text.strip()]
                logger.info(f"[spaCy] Oraciones detectadas: {sentences}")
                paragraphs = []
                for i in range(0, len(sentences), 4):
                    paragraphs.append(" ".join(sentences[i:i+4]))
                logger.info(f"[spaCy] Párrafos generados: {paragraphs}")
                answer = "\n\n".join(paragraphs)
                logger.info(f"[spaCy] Respuesta final (con \\n\\n): {repr(answer)}")
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
        logger.info(f"🏁 TOTAL: {t_total - t0:.2f}s")
        for src in sources:
            logger.info(f"• {src['source']} (chunk {src['chunk_id']})\n  ↳ {src['preview']}")
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

def _extract_title(story_text: str) -> str:
    """Extrae el título del cuento desde el texto generado por Claude."""
    for line in story_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Markdown h1: # Título
        if line.startswith('# '):
            return line[2:].strip()
        # Markdown h2: ## Título
        if line.startswith('## '):
            return line[3:].strip()
        # Negrita sola en línea: **Título**
        m = re.match(r'^\*\*(.+?)\*\*$', line)
        if m:
            return m.group(1).strip()
        # Primera línea no vacía como fallback
        return line[:80]
    return "Un caso de Sherlock Holmes"

async def _generate_story_meta(story_text: str, api_key: str) -> dict:
    """Una sola llamada a Claude: sinopsis + 3 prompts de imagen contextuales en inglés."""
    client = anthropic_sdk.AsyncAnthropic(api_key=api_key)
    title = _extract_title(story_text)
    excerpt = story_text[:6000]

    msg = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1800,
        messages=[{
            "role": "user",
            "content": (
                f'You are illustrating a Sherlock Holmes story titled: "{title}"\n\n'
                f"Story content:\n{excerpt}\n\n"
                "Generate a JSON object (no markdown, no code blocks) with exactly these keys:\n"
                "1. \"synopsis\": 100-120 word Spanish back-cover summary. Intriguing but NO spoilers of the ending.\n"
                "2. \"cover_prompt\": English prompt for a FULL-PAGE book cover illustration. "
                "Style: Victorian steel engraving, Gustave Doré lithograph, intricate crosshatching, monochrome ink, "
                "19th century book illustration. Describe a dramatic scene SPECIFIC to this story's central mystery. "
                "Include Sherlock Holmes. No color, no modern elements, no text.\n"
                "3. \"chapter1_prompt\": English prompt for a LANDSCAPE illustration at the end of Chapter 1. "
                "Same Victorian engraving style. Describe a SPECIFIC scene from the FIRST chapter of this story.\n"
                "4. \"chapter2_prompt\": English prompt for a LANDSCAPE illustration at the end of Chapter 2. "
                "Same Victorian engraving style. Describe a SPECIFIC scene from the SECOND chapter of this story.\n\n"
                'Return only valid JSON: {"synopsis": "...", "cover_prompt": "...", "chapter1_prompt": "...", "chapter2_prompt": "..."}'
            )
        }]
    )
    raw = re.sub(r"```json\s*|\s*```", "", msg.content[0].text).strip()
    return json.loads(raw)


async def _generate_image_leonardo(
    prompt: str, api_key: str,
    width: int = 768, height: int = 768
) -> bytes:
    """Submite job a Leonardo AI (Phoenix 1.0) y espera el resultado (polling)."""
    if not api_key:
        raise ValueError("LEONARDO_API_KEY no configurada")

    # Flux Schnell — más rápido y barato, "Unlimited" en la plataforma
    MODEL_ID = "1dd50843-d653-4516-a8e3-f0238ee453ff"
    NEGATIVE = (
        "color, colorful, modern, digital art, photography, photo, "
        "anime, cartoon, 3D render, watercolor, oil painting, blurry, "
        "low quality, deformed"
    )

    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            "https://cloud.leonardo.ai/api/rest/v1/generations",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "prompt": prompt,
                "negative_prompt": NEGATIVE,
                "modelId": MODEL_ID,
                "width": width,
                "height": height,
                "num_images": 1,
            }
        )
        resp.raise_for_status()
        generation_id = resp.json()["sdGenerationJob"]["generationId"]

        for _ in range(40):   # hasta ~2 min
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
               cover_img, chapter1_img, chapter2_img) -> bytes:
    """Arma el PDF con ReportLab."""
    buffer = io.BytesIO()
    page_w = A4[0] - 5 * cm
    BROWN       = colors.HexColor('#3a2810')
    BROWN_MID   = colors.HexColor('#5a4a2a')
    BROWN_LIGHT = colors.HexColor('#8a7a5a')

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2.5*cm, rightMargin=2.5*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_st    = ParagraphStyle('T',  parent=styles['Title'],  fontSize=24, alignment=1,
                                 spaceAfter=8,  textColor=BROWN,       fontName='Times-Bold')
    subtitle_st = ParagraphStyle('S',  parent=styles['Normal'], fontSize=12, alignment=1,
                                 spaceAfter=6,  textColor=BROWN_MID,   fontName='Times-Italic')
    chapter_st  = ParagraphStyle('CH', parent=styles['Normal'], fontSize=14, alignment=1,
                                 spaceBefore=18, spaceAfter=12, textColor=BROWN, fontName='Times-Bold')
    body_st     = ParagraphStyle('B',  parent=styles['Normal'], fontSize=11, leading=17,
                                 spaceAfter=8,  fontName='Times-Roman')
    synopsis_st = ParagraphStyle('Y',  parent=styles['Normal'], fontSize=10, leading=15,
                                 alignment=4,   textColor=BROWN,       fontName='Times-Roman')
    back_hdr_st = ParagraphStyle('BH', parent=styles['Normal'], fontSize=15, alignment=1,
                                 spaceAfter=10, textColor=BROWN,       fontName='Times-BoldItalic')
    footer_st   = ParagraphStyle('F',  parent=styles['Normal'], fontSize=9,  alignment=1,
                                 textColor=BROWN_LIGHT, fontName='Times-Italic')

    chapter_re = re.compile(
        r'^(#{1,3}\s+|\*\*(parte|cap[íi]tulo|chapter|part)\b.*?\*\*'
        r'|(parte|cap[íi]tulo|chapter|part)\s+[ivxIVX\d]+)',
        re.IGNORECASE
    )

    def make_img(img_bytes, w, h):
        if not img_bytes:
            return None
        try:
            return RLImage(io.BytesIO(img_bytes), width=w, height=h)
        except Exception:
            return None

    # Detectar fines de capítulo para colocar ilustraciones
    paras = [p.strip() for p in story_text.split('\n\n') if p.strip()]
    chapter_starts = [i for i, p in enumerate(paras) if chapter_re.match(p) and i > 0]

    if len(chapter_starts) >= 2:
        ch1_end = chapter_starts[1] - 1
        ch2_end = chapter_starts[2] - 1 if len(chapter_starts) >= 3 else len(paras) - 1
    elif len(chapter_starts) == 1:
        ch1_end = chapter_starts[0] - 1
        ch2_end = len(paras) - 1
    else:
        # Sin encabezados detectados — fallback a 1/3 y 2/3
        third = max(1, len(paras) // 3)
        ch1_end = third - 1
        ch2_end = 2 * third - 1

    flow = []

    # === TAPA ===
    img = make_img(cover_img, page_w, 16*cm)
    if img:
        flow.append(Spacer(1, 0.3*cm))
        flow.append(img)
        flow.append(Spacer(1, 0.5*cm))
        flow.append(HRFlowable(width="70%", thickness=2, color=BROWN_MID))
        flow.append(Spacer(1, 0.4*cm))
    else:
        flow.append(Spacer(1, 4*cm))
    flow.append(Paragraph(title[:80], title_st))
    flow.append(Paragraph("Un caso de Sherlock Holmes", subtitle_st))
    if nombre:
        flow.append(Paragraph(f"con {nombre}", subtitle_st))
    flow.append(HRFlowable(width="40%", thickness=1, color=BROWN_LIGHT))
    flow.append(PageBreak())

    # === TEXTO CON ILUSTRACIONES ===
    for i, para in enumerate(paras):
        if chapter_re.match(para):
            clean = re.sub(r'^#{1,3}\s+|\*\*', '', para).strip()
            flow.append(Paragraph(clean, chapter_st))
        else:
            flow.append(Paragraph(para, body_st))

        if i == ch1_end:
            img = make_img(chapter1_img, 13*cm, 7*cm)
            if img:
                flow += [Spacer(1, 0.6*cm), img, Spacer(1, 0.6*cm)]

        if i == ch2_end and ch2_end != ch1_end:
            img = make_img(chapter2_img, 13*cm, 7*cm)
            if img:
                flow += [Spacer(1, 0.6*cm), img, Spacer(1, 0.6*cm)]

    flow.append(PageBreak())

    # === CONTRATAPA ===
    flow.append(Spacer(1, 2.5*cm))
    flow.append(HRFlowable(width="55%", thickness=2.5, color=BROWN_MID))
    flow.append(Spacer(1, 0.6*cm))
    flow.append(Paragraph("Sinopsis", back_hdr_st))
    flow.append(Spacer(1, 0.4*cm))
    flow.append(HRFlowable(width="55%", thickness=1, color=BROWN_LIGHT))
    flow.append(Spacer(1, 0.6*cm))
    if synopsis:
        flow.append(Paragraph(synopsis, synopsis_st))
    flow.append(Spacer(1, 1.5*cm))
    flow.append(HRFlowable(width="35%", thickness=1, color=BROWN_LIGHT))
    flow.append(Spacer(1, 0.4*cm))
    flow.append(Paragraph("Sherlock Holmes  ·  Baker Street 221B  ·  Londres", footer_st))

    doc.build(flow)
    return buffer.getvalue()


# ─── Endpoint /generate-story ─────────────────────────────────────────────────

@app.post("/generate-story")
async def generate_story(request: StoryRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="El prompt no puede estar vacío")

    t0 = time.time()
    loop = asyncio.get_running_loop()

    # 1. Generar texto del cuento (RetrievalQA es sync → executor)
    logger.info(f"⏳ [1] Generando texto del cuento...")
    chain = app.state.qa_service.build_chain("cuento", request.nombre)
    story_result = await loop.run_in_executor(
        None, lambda: chain.invoke({"query": request.prompt})
    )
    story_text = story_result["result"]
    story_docs = story_result.get("source_documents", [])
    t1 = time.time()
    logger.info(f"✅ [1] Cuento: {len(story_text)} chars ≈ {len(story_text)//4} tokens | {t1-t0:.1f}s | {len(story_docs)} chunks recuperados")
    logger.info(f"── Cuento generado: '{story_text[:300].replace(chr(10), ' ')}...'")
    for doc in story_docs:
        src = doc.metadata.get("source", "?")
        cid = doc.metadata.get("chunk_id", "?")
        preview = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
        logger.info(f"• {src} (chunk {cid})\n  ↳ {preview}")

    # Modo chat: devolver JSON sin PDF
    if request.formato == "chat":
        logger.info("📨 Formato chat — devolviendo JSON")
        seen = set()
        sources = []
        for doc in story_docs:
            cid = doc.metadata.get("chunk_id")
            if cid not in seen:
                seen.add(cid)
                sources.append({
                    "source": doc.metadata.get("source"),
                    "chunk_id": cid,
                    "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
        return {
            "story": story_text,
            "sources": sources,
            "modo": "cuento",
            "llm_provider": qa_service.current_provider,
        }

    # 2 & 3. Sinopsis e imágenes — solo si Leonardo está configurado
    story_title = _extract_title(story_text)
    logger.info(f"📖 Título detectado: '{story_title}'")
    t2 = t1
    synopsis = ""
    cover_img, ch1_img, ch2_img = None, None, None
    if config.leonardo_api_key:
        logger.info(f"⏳ [2] Generando sinopsis y prompts de imagen (Claude)...")
        meta = await _generate_story_meta(story_text, config.anthropic_api_key)
        t2 = time.time()
        logger.info(f"✅ [2] Meta generada en {t2-t1:.1f}s")
        logger.info(f"   cover: {meta.get('cover_prompt','')[:80]}")
        logger.info(f"   ch1:   {meta.get('chapter1_prompt','')[:80]}")
        logger.info(f"   ch2:   {meta.get('chapter2_prompt','')[:80]}")

        logger.info(f"⏳ [3] Generando 3 imágenes con Leonardo Phoenix...")
        images_raw = await asyncio.gather(
            _generate_image_leonardo(meta["cover_prompt"],    config.leonardo_api_key, width=768,  height=1024),
            _generate_image_leonardo(meta["chapter1_prompt"], config.leonardo_api_key, width=896,  height=512),
            _generate_image_leonardo(meta["chapter2_prompt"], config.leonardo_api_key, width=896,  height=512),
            return_exceptions=True
        )
        cover_img = images_raw[0] if isinstance(images_raw[0], bytes) else None
        ch1_img   = images_raw[1] if isinstance(images_raw[1], bytes) else None
        ch2_img   = images_raw[2] if isinstance(images_raw[2], bytes) else None
        t3 = time.time()
        ok_count = sum(1 for x in [cover_img, ch1_img, ch2_img] if x)
        logger.info(f"✅ [3] Imágenes: {ok_count}/3 generadas en {t3-t2:.1f}s")
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
            title=story_title,
            nombre=request.nombre,
            cover_img=cover_img,
            chapter1_img=ch1_img,
            chapter2_img=ch2_img,
        )
    )
    t4 = time.time()
    logger.info(f"✅ [4] PDF: {len(pdf_bytes)//1024}KB en {t4-t3:.1f}s")
    logger.info(f"🏁 TOTAL generate-story: {t4-t0:.1f}s | texto={t1-t0:.1f}s | meta={t2-t1:.1f}s | imgs={t3-t2:.1f}s | pdf={t4-t3:.1f}s")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    title_slug = re.sub(r'[^a-z0-9]+', '_', story_title[:50].lower().strip()).strip('_')
    filename = f"holmes_{title_slug}_{ts}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

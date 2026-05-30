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
import sqlalchemy
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
try:
    from langchain.chains import RetrievalQA
except ModuleNotFoundError:
    from langchain_classic.chains import RetrievalQA

try:
    from langchain.prompts import PromptTemplate
except ModuleNotFoundError:
    from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_voyageai import VoyageAIEmbeddings
from langchain_postgres import PGVector
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, HRFlowable, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader
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
    story_text: Optional[str] = None  # si viene, saltea la generación del cuento

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
                "2. \"cover_prompt\": English prompt for a FULL-PAGE vintage book cover illustration. "
                "Style: rich Victorian fine-art painting with jewel-tone colors — deep crimson, burnished gold, "
                "dark forest green, midnight navy, aged ivory. Painterly brushwork like a 19th-century illustrated "
                "book frontispiece or Pre-Raphaelite oil painting. Dramatic scene SPECIFIC to this story's central "
                "mystery. Include Sherlock Holmes prominently. Ornate, atmospheric, no text, no modern elements.\n"
                "3. \"chapter1_prompt\": English prompt for a LANDSCAPE illustration at the end of Chapter 1. "
                "Style: Victorian pen-and-ink engraving with warm sepia and amber ink tones, intricate crosshatching, "
                "19th century book illustration. Describe a SPECIFIC scene from the FIRST chapter of this story.\n"
                "4. \"chapter2_prompt\": English prompt for a LANDSCAPE illustration at the end of Chapter 2. "
                "Same Victorian engraving style with sepia tones. Describe a SPECIFIC scene from the SECOND chapter.\n\n"
                'Return only valid JSON: {"synopsis": "...", "cover_prompt": "...", "chapter1_prompt": "...", "chapter2_prompt": "..."}'
            )
        }]
    )
    raw = re.sub(r"```json\s*|\s*```", "", msg.content[0].text).strip()
    return json.loads(raw)


async def _generate_image_leonardo(
    prompt: str, api_key: str,
    width: int = 768, height: int = 768,
    negative_prompt: Optional[str] = None,
) -> bytes:
    """Submite job a Leonardo AI (Flux Schnell) y espera el resultado (polling)."""
    if not api_key:
        raise ValueError("LEONARDO_API_KEY no configurada")

    MODEL_ID = "1dd50843-d653-4516-a8e3-f0238ee453ff"
    if negative_prompt is None:
        negative_prompt = (
            "photo, photography, modern, digital art, anime, cartoon, "
            "3D render, blurry, low quality, deformed, watermark, text"
        )

    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            "https://cloud.leonardo.ai/api/rest/v1/generations",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
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
    """Arma el PDF: portada cuero/oro + cuerpo con ilustraciones + contratapa."""
    import fitz  # PyMuPDF — para merge

    A4_W, A4_H = A4

    # ── Paleta vintage ───────────────────────────────────────────────────────
    C_BG      = HexColor('#1e1208')   # cuero oscuro
    C_GOLD    = HexColor('#c9a84c')   # oro
    C_GOLD_LT = HexColor('#edd98e')   # crema dorada
    C_CREAM   = HexColor('#f0e6c8')   # crema texto
    C_BROWN   = HexColor('#3a2810')
    C_BROWN_M = HexColor('#5a4a2a')
    C_BROWN_L = HexColor('#8a7a5a')

    chapter_re = re.compile(
        r'^(#{1,3}\s+|\*\*(parte|cap[íi]tulo|chapter|part)\b.*?\*\*'
        r'|(parte|cap[íi]tulo|chapter|part)\s+[ivxIVX\d]+)',
        re.IGNORECASE
    )

    # ── Helper: marco vintage en canvas ──────────────────────────────────────
    def draw_vintage_bg(c, w, h):
        c.setFillColor(C_BG)
        c.rect(0, 0, w, h, fill=1, stroke=0)
        m1, m2 = 0.85*cm, 1.3*cm
        c.setStrokeColor(C_GOLD)
        c.setLineWidth(2.5)
        c.rect(m1, m1, w - 2*m1, h - 2*m1, fill=0, stroke=1)
        c.setLineWidth(0.8)
        c.rect(m2, m2, w - 2*m2, h - 2*m2, fill=0, stroke=1)
        sq = 0.27*cm
        c.setFillColor(C_GOLD)
        for cx, cy in [(m2, m2), (w - m2, m2), (m2, h - m2), (w - m2, h - m2)]:
            c.saveState()
            c.translate(cx, cy)
            c.rotate(45)
            c.rect(-sq/2, -sq/2, sq, sq, fill=1, stroke=0)
            c.restoreState()

    # ── Helper: wrap simple de texto ─────────────────────────────────────────
    def wrap_text(text, font, size, max_w, c):
        words = text.split()
        lines, current = [], ""
        for word in words:
            test = (current + " " + word).strip()
            if c.stringWidth(test, font, size) <= max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    # ── PORTADA ──────────────────────────────────────────────────────────────
    cover_buf = io.BytesIO()
    c = rl_canvas.Canvas(cover_buf, pagesize=A4)
    draw_vintage_bg(c, A4_W, A4_H)

    pad = 1.7*cm
    inner_w = A4_W - 2*pad
    cx = A4_W / 2

    # Título (ajusta tamaño según largo)
    title_text = title[:70]
    fsize = 28 if len(title_text) <= 32 else 22 if len(title_text) <= 50 else 17
    t_lines = wrap_text(title_text, "Times-Bold", fsize, inner_w - 0.4*cm, c)

    ty = A4_H - 3.0*cm
    c.setFillColor(C_GOLD_LT)
    lh = fsize * 1.35
    for line in t_lines[:3]:
        c.setFont("Times-Bold", fsize)
        c.drawCentredString(cx, ty, line)
        ty -= lh

    # Línea separadora
    ty -= 0.2*cm
    c.setStrokeColor(C_GOLD)
    c.setLineWidth(1.5)
    c.line(pad + 0.5*cm, ty, A4_W - pad - 0.5*cm, ty)
    ty -= 0.65*cm

    # Subtítulos
    c.setFillColor(C_GOLD)
    c.setFont("Times-Italic", 13)
    c.drawCentredString(cx, ty, "Un caso de Sherlock Holmes")
    ty -= 0.55*cm
    if nombre:
        c.setFont("Times-Italic", 11)
        c.drawCentredString(cx, ty, f"con {nombre}")
        ty -= 0.45*cm

    # Imagen de portada centrada en el área restante
    footer_h = 2.2*cm
    img_area_top = ty - 0.5*cm
    img_area_h = img_area_top - footer_h
    img_area_w = A4_W - 2*pad - 0.4*cm

    if cover_img:
        try:
            ir = ImageReader(io.BytesIO(cover_img))
            iw, ih = ir.getSize()
            scale = min(img_area_w / iw, img_area_h / ih)
            dw, dh = iw * scale, ih * scale
            c.drawImage(ir, (A4_W - dw) / 2, footer_h + (img_area_h - dh) / 2,
                        width=dw, height=dh, mask='auto')
        except Exception:
            pass
    else:
        # Ornamentos decorativos cuando no hay imagen
        oy = footer_h + img_area_h / 2
        c.setStrokeColor(C_GOLD)
        c.setLineWidth(0.7)
        for x_off in [-2.5*cm, -1.2*cm, 0, 1.2*cm, 2.5*cm]:
            c.line(cx + x_off, footer_h + 0.8*cm, cx + x_off, img_area_top - 0.8*cm)
        c.setFillColor(C_GOLD)
        c.setFont("Times-Italic", 36)
        c.drawCentredString(cx, oy - 0.5*cm, "✦")

    c.setFillColor(C_GOLD)
    c.setFont("Times-Italic", 9)
    c.drawCentredString(cx, 1.6*cm, "Baker Street 221B  ·  Londres")
    c.showPage()
    c.save()
    cover_buf.seek(0)

    # ── CUERPO ───────────────────────────────────────────────────────────────
    body_buf = io.BytesIO()
    page_w = A4_W - 5*cm

    doc = SimpleDocTemplate(body_buf, pagesize=A4,
                            leftMargin=2.5*cm, rightMargin=2.5*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    chapter_st = ParagraphStyle('CH', parent=styles['Normal'], fontSize=14, alignment=1,
                                spaceBefore=18, spaceAfter=12, textColor=C_BROWN, fontName='Times-Bold')
    body_st    = ParagraphStyle('B',  parent=styles['Normal'], fontSize=11, leading=17,
                                spaceAfter=8, fontName='Times-Roman')

    def make_img(img_bytes, w, h):
        if not img_bytes:
            return None
        try:
            return RLImage(io.BytesIO(img_bytes), width=w, height=h)
        except Exception:
            return None

    paras = [p.strip() for p in story_text.split('\n\n') if p.strip()]
    chapter_starts = [i for i, p in enumerate(paras) if chapter_re.match(p) and i > 0]

    if len(chapter_starts) >= 2:
        ch1_end = chapter_starts[1] - 1
        ch2_end = chapter_starts[2] - 1 if len(chapter_starts) >= 3 else len(paras) - 1
    elif len(chapter_starts) == 1:
        ch1_end = chapter_starts[0] - 1
        ch2_end = len(paras) - 1
    else:
        third = max(1, len(paras) // 3)
        ch1_end = third - 1
        ch2_end = 2 * third - 1

    # Imágenes de capítulo: ancho completo, ratio 16:9
    ch_w = page_w
    ch_h = ch_w * 9 / 16

    flow = []
    for i, para in enumerate(paras):
        if chapter_re.match(para):
            clean = re.sub(r'^#{1,3}\s+|\*\*', '', para).strip()
            flow.append(Paragraph(clean, chapter_st))
        else:
            flow.append(Paragraph(para, body_st))

        if i == ch1_end:
            img = make_img(chapter1_img, ch_w, ch_h)
            if img:
                flow += [Spacer(1, 0.8*cm), img, Spacer(1, 0.8*cm)]

        if i == ch2_end and ch2_end != ch1_end:
            img = make_img(chapter2_img, ch_w, ch_h)
            if img:
                flow += [Spacer(1, 0.8*cm), img, Spacer(1, 0.8*cm)]

    doc.build(flow)
    body_buf.seek(0)

    # ── CONTRATAPA ───────────────────────────────────────────────────────────
    back_buf = io.BytesIO()
    c2 = rl_canvas.Canvas(back_buf, pagesize=A4)
    draw_vintage_bg(c2, A4_W, A4_H)

    # Header "Sinopsis"
    c2.setFillColor(C_GOLD_LT)
    c2.setFont("Times-BoldItalic", 22)
    c2.drawCentredString(cx, A4_H - 3.5*cm, "Sinopsis")
    c2.setStrokeColor(C_GOLD)
    c2.setLineWidth(1.2)
    c2.line(pad + 1.5*cm, A4_H - 4.1*cm, A4_W - pad - 1.5*cm, A4_H - 4.1*cm)

    # Texto de sinopsis con Frame + Paragraph (justificado)
    synopsis_style = ParagraphStyle(
        'SY', fontSize=11, leading=18, alignment=4,
        textColor=C_CREAM, fontName='Times-Roman', spaceAfter=8,
    )
    frame_x = pad + 0.4*cm
    frame_w = A4_W - 2*pad - 0.8*cm
    frame_y = 2.8*cm
    frame_h = A4_H - 4.8*cm - frame_y
    syn_frame = Frame(frame_x, frame_y, frame_w, frame_h, showBoundary=0)
    syn_content = [Paragraph(synopsis, synopsis_style)] if synopsis else []
    syn_frame.addFromList(syn_content, c2)

    c2.setStrokeColor(C_GOLD)
    c2.setLineWidth(0.8)
    c2.line(pad + 1.5*cm, 2.6*cm, A4_W - pad - 1.5*cm, 2.6*cm)
    c2.setFillColor(C_GOLD)
    c2.setFont("Times-Italic", 9)
    c2.drawCentredString(cx, 1.6*cm, "Sherlock Holmes  ·  Baker Street 221B  ·  Londres")
    c2.showPage()
    c2.save()
    back_buf.seek(0)

    # ── MERGE ────────────────────────────────────────────────────────────────
    merged = fitz.open()
    for buf in [cover_buf, body_buf, back_buf]:
        part = fitz.open(stream=buf.read(), filetype="pdf")
        merged.insert_pdf(part)
    out = io.BytesIO()
    merged.save(out)
    return out.getvalue()


# ─── Endpoint /generate-story ─────────────────────────────────────────────────

@app.post("/generate-story")
async def generate_story(request: StoryRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="El prompt no puede estar vacío")

    t0 = time.time()
    loop = asyncio.get_running_loop()

    # 1. Generar texto del cuento — o usar el texto ya generado en el chat
    if request.story_text and request.story_text.strip():
        story_text = request.story_text.strip()
        story_docs = []
        t1 = time.time()
        logger.info(f"⏳ [1] Usando story_text del request ({len(story_text)} chars) — saltea generación")
    else:
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
            _generate_image_leonardo(
                meta["cover_prompt"], config.leonardo_api_key, width=768, height=1024,
                negative_prompt=(
                    "modern, digital art, anime, cartoon, 3D render, blurry, low quality, "
                    "deformed, text, watermark, grayscale, black and white, monochrome"
                ),
            ),
            _generate_image_leonardo(meta["chapter1_prompt"], config.leonardo_api_key, width=896, height=512),
            _generate_image_leonardo(meta["chapter2_prompt"], config.leonardo_api_key, width=896, height=512),
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


# ─── Rincón del Profe ─────────────────────────────────────────────────────────

class RinconRequest(BaseModel):
    texto_id: str = "holmes"

class ActividadesRequest(BaseModel):
    texto_id: str = "holmes"
    nivel: str = "primaria"   # "primaria" | "secundaria"

class ResumenRequest(BaseModel):
    texto_id: str = "holmes"
    nivel: str = "aula"       # "aula" | "casa"


async def _rincon_call(prompt: str, config: CloudConfig, max_tokens: int = 2000) -> str:
    """Llama a Claude directamente (sin RAG) con un prompt ya armado."""
    client = anthropic_sdk.AsyncAnthropic(api_key=config.anthropic_api_key)
    msg = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text


def _retrieve_context(qa_service: MultiCloudQAService, query: str, texto_id: str = None, k: int = 15) -> str:
    db = qa_service._retriever.vectorstore
    filter_kwargs = {"filter": {"source": texto_id}} if texto_id and texto_id != "todos" else {}
    docs = db.similarity_search(query, k=k, **filter_kwargs)
    return "\n\n".join(d.page_content for d in docs)


@app.get("/textos")
async def get_textos():
    import psycopg2
    try:
        # psycopg2 no entiende el prefijo +psycopg de SQLAlchemy
        db_url = config.database_url.replace("postgresql+psycopg://", "postgresql://")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT name FROM langchain_pg_collection")
        collections = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT COUNT(*) FROM langchain_pg_embedding")
        total = cur.fetchone()[0]
        cur.execute(
            "SELECT DISTINCT cmetadata->>'source' as source "
            "FROM langchain_pg_embedding "
            "WHERE collection_id = ("
            "  SELECT uuid FROM langchain_pg_collection WHERE name = 'lorechat_holmes'"
            ") ORDER BY source"
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        sources = [r[0] for r in rows if r[0]]
        return {
            "_debug": {"url": config.database_url, "collections": collections, "total_embeddings": total},
            "textos": [{"id": s, "label": s.replace(" - Arthur Conan Doyle.pdf", "").strip()} for s in sources]
        }
    except Exception as e:
        return {"_debug_error": str(e), "url": config.database_url, "textos": []}


@app.post("/rincon-profe/resumen")
async def rincon_resumen(request: ResumenRequest):
    loop = asyncio.get_running_loop()
    context = await loop.run_in_executor(
        None,
        lambda: _retrieve_context(app.state.qa_service, "personajes trama argumento cuento historia", texto_id=request.texto_id, k=15)
    )

    if request.nivel == "aula":
        prompt = (
            "Sos un asistente pedagógico especializado en literatura. "
            "Analizá el siguiente corpus literario y generá un análisis estructurado para docentes. "
            "Respondé ÚNICAMENTE con un JSON válido (sin markdown, sin bloques de código) con exactamente estas claves:\n"
            '{"tipo_texto": "string", '
            '"epoca_contexto": "string", '
            '"temas_centrales": ["string"], '
            '"personajes": [{"nombre": "string", "descripcion": "string"}], '
            '"recursos_literarios": ["string"], '
            '"valores": ["string"], '
            '"ejes_debate": ["string"], '
            '"nivel_sugerido": "string"}\n\n'
            f"Corpus:\n{context}"
        )
    else:  # casa
        prompt = (
            "Sos un asistente que ayuda a padres a acompañar la lectura de sus hijos. "
            "Analizá el siguiente corpus literario y generá un resumen accesible. "
            "Respondé ÚNICAMENTE con un JSON válido (sin markdown, sin bloques de código) con exactamente estas claves:\n"
            '{"resumen": "string (máximo 150 palabras, lenguaje simple, qué pasa en el cuento)", '
            '"preguntas": ["string", "string", "string"], '
            '"datos_curiosos": ["string", "string"]}\n\n'
            f"Corpus:\n{context}"
        )

    raw = await _rincon_call(prompt, config, max_tokens=2000)
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
    return json.loads(raw)


@app.post("/rincon-profe/actividades")
async def rincon_actividades(request: ActividadesRequest):
    loop = asyncio.get_running_loop()
    context = await loop.run_in_executor(
        None,
        lambda: _retrieve_context(app.state.qa_service, "trama personajes conflicto resolución", texto_id=request.texto_id, k=15)
    )

    nivel_label = "primaria (alumnos de 6 a 12 años)" if request.nivel == "primaria" else "secundaria (alumnos de 13 a 18 años)"
    prompt = (
        f"Sos un diseñador de actividades pedagógicas para nivel {nivel_label}. "
        "Basándote en el siguiente corpus literario, generá exactamente 4 actividades: "
        "2 grupales y 2 individuales de escritura. "
        "Respondé ÚNICAMENTE con un JSON válido (sin markdown, sin bloques de código) con esta estructura:\n"
        '{"grupales": ['
        '{"nombre": "string", "consigna": "string", "tiempo_estimado": "string"}, '
        '{"nombre": "string", "consigna": "string", "tiempo_estimado": "string"}], '
        '"individuales": ['
        '{"nombre": "string", "consigna": "string", "tiempo_estimado": "string"}, '
        '{"nombre": "string", "consigna": "string", "tiempo_estimado": "string"}]}\n\n'
        f"Corpus:\n{context}"
    )

    raw = await _rincon_call(prompt, config, max_tokens=2000)
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
    return json.loads(raw)


@app.post("/rincon-profe/valores")
async def rincon_valores(request: RinconRequest):
    loop = asyncio.get_running_loop()
    context = await loop.run_in_executor(
        None,
        lambda: _retrieve_context(app.state.qa_service, "valores morales temas sociales conflicto personajes", texto_id=request.texto_id, k=15)
    )

    prompt = (
        "Sos un analista literario especializado en educación. "
        "Analizá el siguiente corpus y detectá los valores y temas transversales presentes. "
        "Respondé ÚNICAMENTE con un JSON válido (sin markdown, sin bloques de código) con esta estructura:\n"
        '{"valores": [{"valor": "string", "contexto": "string (dónde/cómo aparece en el texto)"}], '
        '"temas_transversales": [{"tema": "string", "descripcion": "string"}]}\n\n'
        f"Corpus:\n{context}"
    )

    raw = await _rincon_call(prompt, config, max_tokens=1500)
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
    return json.loads(raw)


@app.post("/rincon-profe/personajes")
async def rincon_personajes(request: RinconRequest):
    loop = asyncio.get_running_loop()
    context = await loop.run_in_executor(
        None,
        lambda: _retrieve_context(app.state.qa_service, "personajes descripción física personalidad protagonista", texto_id=request.texto_id, k=15)
    )

    prompt = (
        "Sos un analista literario. "
        "Analizá el siguiente corpus e identificá todos los personajes principales. "
        "Para cada uno generá una ficha completa. "
        "Respondé ÚNICAMENTE con un JSON válido (sin markdown, sin bloques de código) con esta estructura:\n"
        '{"personajes": [{'
        '"nombre": "string", '
        '"caracteristicas_fisicas": "string", '
        '"caracteristicas_psicologicas": "string", '
        '"rol_en_historia": "string", '
        '"frase_o_momento_representativo": "string"'
        '}]}\n\n'
        f"Corpus:\n{context}"
    )

    raw = await _rincon_call(prompt, config, max_tokens=4096)
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Si el JSON viene truncado, intentar cerrarlo
        patched = raw
        if not patched.endswith("}"):
            patched = patched.rstrip(",. \n") + '"}]}'
        try:
            return json.loads(patched)
        except json.JSONDecodeError:
            return {"personajes": [], "_error": "Respuesta truncada del modelo"}


# ─── Para Casa ────────────────────────────────────────────────────────────────

class ParaCasaRequest(BaseModel):
    texto_id: str = "todos"


@app.post("/para-casa/de-que-trata")
async def casa_de_que_trata(request: ParaCasaRequest):
    loop = asyncio.get_running_loop()
    context = await loop.run_in_executor(
        None,
        lambda: _retrieve_context(app.state.qa_service, "trama argumento historia personajes conflicto", texto_id=request.texto_id, k=12)
    )

    prompt = (
        "Sos un asistente que ayuda a padres a entender los libros que leen sus hijos. "
        "Explicá el siguiente texto de forma clara y simple, sin tecnicismos. "
        "Respondé ÚNICAMENTE con un JSON válido (sin markdown, sin bloques de código) con esta estructura:\n"
        '{"titulo_informal": "string (nombre coloquial del libro, ej: El sabueso de los Baskerville)", '
        '"de_que_trata": "string (3 a 5 oraciones simples explicando de qué va el libro)", '
        '"personajes_principales": [{"nombre": "string", "quien_es": "string (1 oración simple)"}], '
        '"como_termina": "string (resolución general sin spoilers excesivos, 2 oraciones)"}\n\n'
        f"Corpus:\n{context}"
    )

    raw = await _rincon_call(prompt, config, max_tokens=1500)
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
    return json.loads(raw)


@app.post("/para-casa/preguntas-charla")
async def casa_preguntas_charla(request: ParaCasaRequest):
    loop = asyncio.get_running_loop()
    context = await loop.run_in_executor(
        None,
        lambda: _retrieve_context(app.state.qa_service, "trama conflicto valores decisiones personajes", texto_id=request.texto_id, k=10)
    )

    prompt = (
        "Sos un asistente que ayuda a padres a conectar con sus hijos a través de la lectura. "
        "Generá preguntas simples y naturales para que un padre le haga a su hijo durante la cena o antes de dormir. "
        "Las preguntas deben invitar a conversar, no a evaluar. "
        "Respondé ÚNICAMENTE con un JSON válido (sin markdown, sin bloques de código) con esta estructura:\n"
        '{"preguntas": ['
        '{"pregunta": "string", "por_que_sirve": "string (en 1 oración, para qué sirve hacerla)"}'
        ']}\n'
        "Generá exactamente 4 preguntas.\n\n"
        f"Corpus:\n{context}"
    )

    raw = await _rincon_call(prompt, config, max_tokens=1200)
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
    return json.loads(raw)


@app.post("/para-casa/glosario")
async def casa_glosario(request: ParaCasaRequest):
    loop = asyncio.get_running_loop()
    context = await loop.run_in_executor(
        None,
        lambda: _retrieve_context(app.state.qa_service, "vocabulario términos difíciles descripción lenguaje", texto_id=request.texto_id, k=12)
    )

    prompt = (
        "Sos un asistente educativo. "
        "Analizá el siguiente corpus literario e identificá las palabras o frases que pueden ser difíciles para un chico. "
        "Para cada una, dá una definición muy simple y un ejemplo de uso en contexto del libro. "
        "Respondé ÚNICAMENTE con un JSON válido (sin markdown, sin bloques de código) con esta estructura:\n"
        '{"palabras": ['
        '{"palabra": "string", "definicion_simple": "string", "en_el_libro": "string (cómo aparece o se usa en el texto)"}'
        ']}\n'
        "Incluí entre 6 y 10 palabras.\n\n"
        f"Corpus:\n{context}"
    )

    raw = await _rincon_call(prompt, config, max_tokens=1500)
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
    return json.loads(raw)


@app.post("/para-casa/datos-curiosos")
async def casa_datos_curiosos(request: ParaCasaRequest):
    loop = asyncio.get_running_loop()
    context = await loop.run_in_executor(
        None,
        lambda: _retrieve_context(app.state.qa_service, "autor época histórica contexto datos curiosidades", texto_id=request.texto_id, k=10)
    )

    prompt = (
        "Sos un asistente que hace la lectura más entretenida para las familias. "
        "Basándote en el siguiente corpus, generá datos curiosos sobre el autor, la época o el libro "
        "que un padre pueda contarle a su hijo para hacer la lectura más interesante. "
        "Respondé ÚNICAMENTE con un JSON válido (sin markdown, sin bloques de código) con esta estructura:\n"
        '{"datos": ['
        '{"titulo": "string (título corto del dato)", "dato": "string (el dato en 2-3 oraciones simples y entretenidas)"}'
        ']}\n'
        "Generá exactamente 4 datos curiosos.\n\n"
        f"Corpus:\n{context}"
    )

    raw = await _rincon_call(prompt, config, max_tokens=1200)
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
    return json.loads(raw)

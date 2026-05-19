import os
import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_voyageai import VoyageAIEmbeddings
from langchain_postgres import PGVector
from config import CloudConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AskRequest(BaseModel):
    question: str
    modo: str = "auto"       # "auto", "factual", "cuento"
    nombre: Optional[str] = None

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
            "La historia debe ser larga, detallada y envolvente.\n\n"
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
        max_tokens = 10000 if modo == "cuento" else 1024
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

    import time
    try:
        chain = app.state.qa_service.build_chain(modo_efectivo, request.nombre)

        t0 = time.time()
        result = chain.invoke({"query": request.question})
        t1 = time.time()

        docs_sorted = result.get("source_documents", [])
        answer = result["result"]

        # Post-procesar con spaCy solo en modo factual (cuento ya viene bien formateado)
        if modo_efectivo != "cuento":
            import spacy
            try:
                nlp = spacy.load("es_core_news_sm")
                doc = nlp(answer)
                sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
                paragraphs = []
                for i in range(0, len(sentences), 4):
                    paragraphs.append(" ".join(sentences[i:i+4]))
                answer = "\n\n".join(paragraphs)
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

        t2 = time.time()
        logger.info(f"⏱️ LLM: {t1-t0:.2f}s | Total: {t2-t0:.2f}s")
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

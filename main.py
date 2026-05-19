import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.chains import RetrievalQA
from langchain_anthropic import ChatAnthropic
from langchain_voyageai import VoyageAIEmbeddings
from langchain_postgres import PGVector
from config import CloudConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AskRequest(BaseModel):
    question: str

class MultiCloudQAService:
    """Servicio QA con LLM cloud + embeddings locales"""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.current_provider = None
        self.current_embedding_provider = None
        self.qa_chain = None
        
    def get_embeddings(self):
        embeddings = VoyageAIEmbeddings(
            voyage_api_key=self.config.voyage_api_key,
            model=self.config.voyage_model
        )
        self.current_embedding_provider = 'voyage'
        logger.info("✅ Voyage AI embeddings configurados")
        return embeddings
    
    def get_llm(self):
        llm = ChatAnthropic(
            api_key=self.config.anthropic_api_key,
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            temperature=0.1
        )
        self.current_provider = 'anthropic'
        logger.info("✅ Claude (Anthropic) configurado")
        return llm
    
    def initialize_qa_chain(self):
        """Inicializa cadena QA"""
        try:
            embeddings = self.get_embeddings()
            
            db = PGVector(
                embeddings=embeddings,
                collection_name="lorechat_holmes",
                connection=self.config.database_url,
            )
            retriever = db.as_retriever(search_kwargs={"k": 10})
            
            llm = self.get_llm()
            
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )
            
            logger.info(f"🚀 Sistema listo:")
            logger.info(f"   📊 Embeddings: {self.current_embedding_provider.upper()}")
            logger.info(f"   🤖 LLM: {self.current_provider.upper()}")
            return self.qa_chain
            
        except Exception as e:
            logger.error(f"Error inicializando sistema: {e}")
            raise

# Configuración global
config = CloudConfig()
qa_service = MultiCloudQAService(config)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        qa_service.initialize_qa_chain()
        app.state.qa_service = qa_service
        logger.info("✅ API lista")
    except Exception as e:
        logger.error(f"❌ Error al iniciar: {e}")
        raise
    yield
    # Shutdown
    logger.info("🔄 Cerrando API")

app = FastAPI(
    title="RAG Local Multi-Cloud",
    description="AWS/Azure LLM + Embeddings Locales",
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
    """Estado del sistema"""
    return {
        "status": "healthy",
        "llm_provider": qa_service.current_provider,
        "embedding_provider": qa_service.current_embedding_provider,
        "voyage_model": config.voyage_model
    }

@app.post("/ask")
async def ask(request: AskRequest):
    """Hacer pregunta a los documentos"""
    logger.info(f"Pregunta recibida: {request.question}")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")

    import time
    try:
        t0 = time.time()
        result = app.state.qa_service.qa_chain({"query": request.question})
        t1 = time.time()
        docs_sorted = result.get("source_documents", [])
        answer = result["result"]
        t2 = time.time()
        # Post-procesar: separar en párrafos reales usando spaCy (cada 3 oraciones)
        import spacy
        try:
            nlp = spacy.load("es_core_news_sm")
            doc = nlp(answer)
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
            logger.info(f"[spaCy] Oraciones detectadas: {sentences}")
            # Agrupar en párrafos de al menos 4 oraciones cada uno
            paragraphs = []
            min_sent_per_paragraph = 4
            for i in range(0, len(sentences), min_sent_per_paragraph):
                paragraphs.append(" ".join(sentences[i:i+min_sent_per_paragraph]))
            logger.info(f"[spaCy] Párrafos generados: {paragraphs}")
            answer = "\n\n".join(paragraphs)
            logger.info(f"[spaCy] Respuesta final (con \\n\\n): {repr(answer)}")
        except Exception as e:
            # Si spaCy falla, dejar el texto como está
            logger.error(f"spaCy error: {e}")
        t3 = time.time()
        # Permitir múltiples chunks del mismo libro, pero sin duplicar chunk_id
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
        logger.info(f"⏱️ Tiempos: Retrieval+LLM: {t1-t0:.2f}s | Post-proc: {t3-t2:.2f}s | Total: {t3-t0:.2f}s")
        logger.info(f"✅ Pregunta respondida - LLM: {qa_service.current_provider.upper()}, Embeddings: {qa_service.current_embedding_provider.upper()}")
        return {
            "answer": answer,
            "sources": sources,
            "llm_provider": qa_service.current_provider,
            "embedding_provider": qa_service.current_embedding_provider
        }
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


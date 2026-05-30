import os
import json
import logging
from langchain_postgres import PGVector
from langchain_voyageai import VoyageAIEmbeddings
from config import CloudConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHUNKS_FILE = "chunks.json"

def main():
    """Crea base vectorial en pgvector con Voyage AI embeddings"""
    if not os.path.exists(CHUNKS_FILE):
        logger.error(f"❌ {CHUNKS_FILE} no existe. Ejecuta ingest.py primero.")
        return

    try:
        config = CloudConfig()

        with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                chunks = data
            elif isinstance(data, dict) and "chunks" in data:
                chunks = data["chunks"]
            else:
                logger.error("❌ chunks.json tiene una estructura inesperada.")
                return

        logger.info(f"📚 {len(chunks)} chunks cargados")

        texts = [chunk["text"] for chunk in chunks]
        metadatas = [
            {
                "source": chunk["source"],
                "chunk_id": chunk["chunk_id"],
            }
            for chunk in chunks
        ]

        embeddings = VoyageAIEmbeddings(
            voyage_api_key=config.voyage_api_key,
            model=config.voyage_model
        )

        BATCH_SIZE = 500
        total = len(chunks)
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        logger.info(f"🔄 Procesando {total} chunks en {total_batches} lotes de {BATCH_SIZE}...")

        store = PGVector(
            embeddings=embeddings,
            collection_name="lorechat_holmes",
            connection=config.database_url,
            pre_delete_collection=True,
        )

        for i in range(0, total, BATCH_SIZE):
            batch_num = i // BATCH_SIZE + 1
            end = min(i + BATCH_SIZE, total)
            logger.info(f"📦 Lote {batch_num}/{total_batches} — chunks {i+1}–{end}")
            store.add_texts(texts[i:end], metadatas=metadatas[i:end])
            logger.info(f"   ✅ Lote {batch_num}/{total_batches} insertado ({end - i} chunks)")

        logger.info(f"✅ {total} chunks insertados en pgvector (colección: lorechat_holmes)")

    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

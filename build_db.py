import os
import json
import logging
import psycopg2
from langchain_postgres import PGVector
from langchain_voyageai import VoyageAIEmbeddings
from config import CloudConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHUNKS_FILE = "chunks.json"


def contar_filas_en_db(database_url: str, collection_name: str) -> int:
    """Consulta directa a pgvector para contar filas reales en la tabla."""
    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM langchain_pg_embedding
                WHERE collection_id = (
                    SELECT uuid FROM langchain_pg_collection WHERE name = %s
                )
                """,
                (collection_name,),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


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

        logger.info(f"📚 {len(chunks)} chunks cargados desde {CHUNKS_FILE}")

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

        BATCH_SIZE = 100
        COLLECTION = "lorechat_holmes"
        total = len(chunks)
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        failed_batches = []

        logger.info(f"🔄 Procesando {total} chunks en {total_batches} lotes de {BATCH_SIZE}...")
        logger.info(f"🗄️  Base de datos: {config.database_url[:40]}...")

        store = PGVector(
            embeddings=embeddings,
            collection_name=COLLECTION,
            connection=config.database_url,
            pre_delete_collection=True,
        )

        for i in range(0, total, BATCH_SIZE):
            batch_num = i // BATCH_SIZE + 1
            end = min(i + BATCH_SIZE, total)
            logger.info(f"📦 Lote {batch_num}/{total_batches} — chunks {i+1}–{end} ...")

            try:
                store.add_texts(texts[i:end], metadatas=metadatas[i:end])

                # Verificación real contra la tabla de DigitalOcean
                filas = contar_filas_en_db(config.database_url, COLLECTION)
                logger.info(
                    f"   ✅ Lote {batch_num}/{total_batches} OK — "
                    f"filas en DB ahora: {filas} / {end} esperadas"
                )
                if filas < end:
                    logger.warning(
                        f"   ⚠️  Discrepancia: se esperaban {end} filas pero hay {filas}"
                    )

            except Exception as batch_err:
                logger.error(
                    f"   ❌ Lote {batch_num}/{total_batches} FALLÓ "
                    f"(chunks {i+1}–{end}): {batch_err}"
                )
                failed_batches.append((batch_num, i + 1, end))

        # Reporte final con conteo real en DB
        filas_final = contar_filas_en_db(config.database_url, COLLECTION)
        logger.info("─" * 60)
        logger.info(f"📊 Resumen final:")
        logger.info(f"   Chunks procesados : {total}")
        logger.info(f"   Filas en DB (real) : {filas_final}")
        logger.info(f"   Lotes fallidos     : {len(failed_batches)}")
        if failed_batches:
            for bn, start, end in failed_batches:
                logger.error(f"   ❌ Lote {bn} (chunks {start}–{end}) no se insertó")
        else:
            logger.info(f"✅ Todo OK — {filas_final} filas en colección '{COLLECTION}'")

    except Exception as e:
        logger.error(f"❌ Error general: {e}", exc_info=True)

if __name__ == "__main__":
    main()

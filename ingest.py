import os
import json
import logging
from typing import List, Dict, Any
import fitz  
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import CloudConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PDF_DIR = "pdfs"
OUTPUT_FILE = "chunks.json"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

def get_pdf_modtime(pdf_path: str) -> float:
    return os.path.getmtime(pdf_path)

def load_existing_chunks() -> Dict[str, Any]:
    if not os.path.exists(OUTPUT_FILE):
        return {"processed_pdfs": {}, "chunks": []}
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            # Estructura antigua: solo lista de chunks
            return {"processed_pdfs": {}, "chunks": data}
        if "processed_pdfs" not in data or "chunks" not in data:
            # Estructura inesperada, intentar rescatar chunks
            return {"processed_pdfs": {}, "chunks": data.get("chunks", [])}
        return data

def save_chunks(processed_pdfs: Dict[str, float], all_chunks: List[Dict[str, Any]]):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "processed_pdfs": processed_pdfs,
            "chunks": all_chunks
        }, f, ensure_ascii=False, indent=2)

def extract_text(pdf_path: str) -> str:
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            if page_text.strip():
                text += f"\n--- Página {page_num + 1} ---\n{page_text}"
        doc.close()
        logger.info(f"✅ PyMuPDF extrajo {len(text)} caracteres")
        return text
    except Exception as e:
        logger.error(f"PyMuPDF falló: {e}")
        return ""

def main():
    if not os.path.exists(PDF_DIR):
        logger.error(f"❌ Carpeta {PDF_DIR} no existe. Créala y pon tus PDFs ahí.")
        return

    try:
        config = CloudConfig()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

        # Cargar estado previo
        data = load_existing_chunks()
        processed_pdfs = data["processed_pdfs"]
        all_chunks = [chunk for chunk in data["chunks"] if "source" in chunk]

        # Mapear PDFs actuales
        pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
        pdfs_to_process = []
        for filename in pdf_files:
            pdf_path = os.path.join(PDF_DIR, filename)
            modtime = get_pdf_modtime(pdf_path)
            modtime_str = str(modtime)
            if filename not in processed_pdfs or processed_pdfs[filename] != modtime_str:
                pdfs_to_process.append((filename, pdf_path, modtime_str))

        if not pdfs_to_process:
            logger.info("✅ No hay PDFs nuevos o modificados para procesar.")
            return

        logger.info(f"📚 Procesando {len(pdfs_to_process)} PDFs nuevos o modificados...")

        new_chunks = []
        for filename, pdf_path, modtime_str in pdfs_to_process:
            logger.info(f"🔄 Procesando {filename}...")
            text = extract_text(pdf_path)
            if not text.strip():
                logger.warning(f"⚠️ {filename} no contiene texto")
                continue
            chunks = splitter.split_text(text)
            for i, chunk in enumerate(chunks):
                new_chunks.append({
                    "source": filename,
                    "chunk_id": i,
                    "text": chunk.strip()
                })
            logger.info(f"✅ {filename}: {len(chunks)} chunks")
            processed_pdfs[filename] = modtime_str

        # Eliminar chunks de PDFs que hayan sido modificados (para evitar duplicados)
        processed_filenames = set(f for f, _, _ in pdfs_to_process)
        all_chunks = [chunk for chunk in all_chunks if chunk["source"] not in processed_filenames]
        all_chunks.extend(new_chunks)

        save_chunks(processed_pdfs, all_chunks)
        logger.info(f"📊 Completado: {len(all_chunks)} chunks en {OUTPUT_FILE}")


    except Exception as e:
        logger.error(f"❌ Error general: {e}")

if __name__ == "__main__":
    main()

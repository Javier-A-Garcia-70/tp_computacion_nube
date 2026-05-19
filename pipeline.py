import subprocess
import sys
import time
import requests

def run_script(script):
    print(f"Ejecutando {script}...")
    result = subprocess.run([sys.executable, script], check=True)
    print(f"{script} completado.")
    return result

def wait_for_backend(url="http://localhost:8000/health", timeout=60):
    print("Esperando a que el backend esté listo...")
    for _ in range(timeout):
        try:
            r = requests.get(url)
            if r.status_code == 200:
                print("Backend listo.")
                return True
        except Exception:
            pass
        time.sleep(1)
    print("Timeout esperando al backend.")
    return False

def main():
    # 1. Ejecutar ingest.py (genera chunks.json)
    run_script("ingest.py")

    # 2. Ejecutar build_db.py (crea chroma_db)
    run_script("build_db.py")

    # 3. Iniciar backend FastAPI en subproceso
    print("Iniciando backend FastAPI...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--log-level", "warning"]
    )
    try:
        # 4. Esperar a que el backend esté listo
        if not wait_for_backend():
            print("No se pudo iniciar el backend. Abortando pipeline.")
            backend_proc.terminate()
            return

        # 5. Ejecutar clasifica_llm.py (clasifica los chunks)
        run_script("clasifica_llm.py")

        # 6. (Opcional) Volver a ejecutar build_db.py para actualizar chroma_db con los tipos
        run_script("build_db.py")

    finally:
        print("Deteniendo backend FastAPI...")
        if backend_proc.poll() is None:
            backend_proc.terminate()
            backend_proc.wait()
        else:
            print("El backend ya estaba detenido.")

    print("✅ Pipeline completo.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⛔ Pipeline interrumpido por el usuario. Cerrando subprocesos...")

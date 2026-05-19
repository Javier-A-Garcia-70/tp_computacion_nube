import sys
import argparse
import requests

BASE_URL = "http://localhost:8000"

def holmes_prompt(question):
    return (
        "Responde en primera persona como Sherlock Holmes, el detective de Baker Street 221B. "
        "Usa su estilo deductivo, preciso y ocasionalmente arrogante. "
        "Razona en voz alta cuando sea relevante, mostrando el proceso deductivo paso a paso. "
        "Puedes hacer referencias a casos anteriores documentados en la obra de Conan Doyle cuando aporten al razonamiento. "
        "No aclares tu identidad en la respuesta salvo que la pregunta lo requiera. "
        "Mantén el tono victoriano y la precisión característica del personaje. "
        "Separa los párrafos usando una línea vacía. "
        f"Pregunta: {question}"
    )

def print_sources(sources):
    if not sources:
        return
    print("\n📚 Fuentes consultadas:")
    for src in sources:
        print(f"• {src['source']} (chunk {src['chunk_id']})")
        print(f"  ↳ {src['preview']}\n")

def ask(question, modo="auto", nombre=None, timeout=180):
    response = requests.post(
        f"{BASE_URL}/ask",
        json={"question": question, "modo": modo, "nombre": nombre},
        headers={"Content-Type": "application/json"},
        timeout=timeout
    )
    response.raise_for_status()
    data = response.json()
    print(data.get("answer"), "\n")
    print_sources(data.get("sources", []))

def story(prompt, nombre=None, formato="chat", timeout=180):
    response = requests.post(
        f"{BASE_URL}/generate-story",
        json={"prompt": prompt, "nombre": nombre, "formato": formato},
        headers={"Content-Type": "application/json"},
        timeout=timeout
    )
    response.raise_for_status()

    if formato == "pdf":
        filename = response.headers.get("Content-Disposition", "").split("filename=")[-1] or "cuento.pdf"
        with open(f"cuentos/{filename}", "wb") as f:
            f.write(response.content)
        print(f"📄 PDF guardado en cuentos/{filename}")
    else:
        data = response.json()
        print(data.get("story"), "\n")
        print_sources(data.get("sources", []))

def interactivo(modo_holmes):
    last_sources = []
    while True:
        user_input = input("Escribe tu pregunta (o 'exit' para salir, ':f' para ver fuentes):\n> ").strip()
        if user_input.lower() in ["exit", "salir"]:
            break
        if user_input == ":f":
            if last_sources:
                print("📚 Fuentes consultadas:")
                for src in last_sources:
                    print(f"• {src['source']} (chunk {src['chunk_id']})")
                    print(f"  ↳ {src['preview']}\n")
            else:
                print("No hay fuentes para mostrar.")
            continue
        question = holmes_prompt(user_input) if modo_holmes else user_input
        try:
            response = requests.post(
                f"{BASE_URL}/ask",
                json={"question": question, "modo": "auto", "nombre": None},
                timeout=180
            )
            response.raise_for_status()
            data = response.json()
            print(data.get('answer'), "\n")
            last_sources = data.get("sources", [])
            if last_sources:
                print("(Fuentes disponibles: escribe ':f' para verlas en cualquier momento)\n")
        except Exception as e:
            print(f"Error consultando la API: {e}")

def main():
    parser = argparse.ArgumentParser(description="CLI para LoreChat Holmes")
    parser.add_argument("question", nargs="*", help="Pregunta o prompt")
    parser.add_argument("--modo", default="auto", choices=["auto", "factual", "cuento"], help="Modo de respuesta")
    parser.add_argument("--nombre", default=None, help="Tu nombre (para que Holmes no te llame Watson)")
    parser.add_argument("--holmes", action="store_true", help="Prepend prompt de Holmes a la pregunta")
    parser.add_argument("--story", action="store_true", help="Usar /generate-story en lugar de /ask")
    parser.add_argument("--pdf", action="store_true", help="Con --story, genera PDF en vez de texto")

    args = parser.parse_args()
    question = " ".join(args.question)
    if args.holmes and question:
        question = holmes_prompt(question)

    if not question:
        interactivo(modo_holmes=args.holmes)
        return

    if args.story:
        story(question, nombre=args.nombre, formato="pdf" if args.pdf else "chat")
    else:
        ask(question, modo=args.modo, nombre=args.nombre)

if __name__ == "__main__":
    main()

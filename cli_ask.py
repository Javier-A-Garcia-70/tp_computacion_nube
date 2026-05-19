import sys
import requests

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
        url = "http://localhost:8000/ask"
        payload = {"question": question}
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            print(data.get('answer'), "\n")
            last_sources = data.get("sources", [])
            if last_sources:
                print("(Fuentes disponibles: escribe ':f' para verlas en cualquier momento)\n")
        except Exception as e:
            print(f"Error consultando la API: {e}")

def main():
    args = sys.argv[1:]
    modo_holmes = False
    if "--holmes" in args:
        modo_holmes = True
        args.remove("--holmes")

    if not args:
        interactivo(modo_holmes)
        return

    question = " ".join(args)
    if modo_holmes:
        question = holmes_prompt(question)

    url = "http://localhost:8000/ask"
    payload = {"question": question}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(data.get('answer'), "\n")
        if data.get("sources"):
            print("📚 Fuentes consultadas:")
            for src in data.get("sources", []):
                print(f"• {src['source']} (chunk {src['chunk_id']})")
                print(f"  ↳ {src['preview']}\n")
    except Exception as e:
        print(f"Error consultando la API: {e}")

if __name__ == "__main__":
    main()

import { useState } from "react";
import ReactMarkdown from "react-markdown";

function App() {
  const asimovIntro = `🤖 "Please Explain"

En 1965, Isaac Asimov comenzó a escribir una sección llamada "Please Explain" -"Por favor, explique"- para Science Digest. Los lectores enviaban preguntas, él seleccionaba algunas y las respondía en unas 500 palabras, accediendo a su vasto conocimiento científico.
Lo que empezó como colaboraciones esporádicas se volvió mensual, y la revista cambió el nombre a "Isaac Asimov Explains" sin consultarle. Sesenta años después, ese "I.A. Explains" toma un nuevo significado: de Isaac Asimov a Inteligencia Artificial.

Durante más de ocho años, Asimov contestó un centenar de preguntas con esa característica mezcla de precisión científica y claridad divulgativa que lo hizo famoso. Como él mismo decía: "las respuestas dependen de las preguntas que formulan los lectores".

Aquí intentamos recrear esa sección con nuevas tecnologías.

Donde Asimov tenía su mente enciclopédica, acá tenemos inteligencia artificial procesando documentos especializados. Donde él escribía 500 palabras a máquina, ahora generamos respuestas instantáneas con referencias precisas. Donde los lectores esperaban meses por una respuesta, aquí obtenés conocimiento al momento.
Pero la esencia permanece: seguir obteniendo respuestas de Asimov, como si él siguiera ahí, consultando ahora una biblioteca digital infinita en lugar de su prodigiosa memoria.
-
Preguntá lo que quieras. Si la información existe en la base de conocimiento, vas a tener tu respuesta.
"Si tengo ocasión (y sé lo suficiente) la contestaré".`;

  const [messages, setMessages] = useState([
    { role: "info", text: asimovIntro }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendQuestion = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMsg = { role: "user", text: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setLoading(true);
    try {
      // Asimov prompt logic (inline)
      const asimovPrompt = (
        "Responde directamente en primera persona, con el estilo, conocimiento y profundidad de Isaac Asimov. " +
        "No aclares tu identidad en la respuesta ni hagas introducciones innecesarias cuando la pregunta no sea sobre ti. " +
        "Sé claro, analítico y utiliza referencias a la ciencia ficción y filosofía si es relevante. " +
        "Si la pregunta es ambigua, formula una contra-pregunta para clarificar. " +
        "Incluye referencias a fuentes si es aportan a la respuesta, pero no abuses del recurso. " +
        "Puedes usar un tono conversacional y ocasionalmente humorístico, pero mantén la precisión científica. " +
        "También puedes usar un lenguaje poético o metafórico, o profundo si lo amerita la respuesta. " +
        "Separa los párrafos usando una línea vacía (doble Enter)." +
        `Pregunta: ${input}`
      );
      const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/ask";
      const res = await fetch(`${API_URL}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: asimovPrompt }),
      });
      const data = await res.json();
      console.log("Respuesta recibida:", data.answer);
      setMessages((msgs) => [
        ...msgs.slice(0, -1), // Remove the last user message (avoid double)
        userMsg,
        { role: "asimov", text: data.answer, sources: data.sources || [] },
      ]);
    } catch (err) {
      setMessages((msgs) => [
        ...msgs.slice(0, -1), // Remove the last user message (avoid double)
        userMsg,
        { role: "error", text: "Error consultando la API." },
      ]);
    }
    setInput("");
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <header className="p-4 bg-gray-800 text-white text-xl font-bold">
        Isaac Asimov Explains
      </header>
      <main className="flex-1 p-4 overflow-y-auto">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`p-3 rounded-lg ${
                msg.role === "user"
                  ? "bg-blue-100 text-blue-900 self-end"
                  : msg.role === "asimov"
                  ? "bg-green-100 text-green-900"
                  : msg.role === "info"
                  ? "bg-yellow-50 border-l-4 border-yellow-400 text-gray-800"
                  : "bg-red-100 text-red-900"
              }`}
            >
              {msg.role === "asimov" ? (
                <div className="prose prose-green prose-xl break-words" style={{ '--tw-prose-p-margin-bottom': '1.5em' }}>
                  {msg.text ? (
                    msg.text
                      .split(/\n{2,}/)
                      .map((paragraph, idx) => (
                        <p key={idx} style={{ marginBottom: '1.5em' }}>{paragraph}</p>
                      ))
                  ) : (
                    <p>Sin respuesta</p>
                  )}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 text-xs text-gray-600">
                      <span className="italic">
                        Fuentes disponibles ({msg.sources.length})
                      </span>
                    </div>
                  )}
                </div>
              ) : msg.role === "info" ? (
                <div className="prose prose-base space-y-4 break-words">
                  <ReactMarkdown>{msg.text || ""}</ReactMarkdown>
                </div>
              ) : (
                msg.text || "Error"
              )}
            </div>
          ))}
          {loading && (
            <div className="p-3 bg-gray-200 rounded-lg text-gray-500">
              Pensando...
            </div>
          )}
        </div>
      </main>
      <form
        className="p-4 bg-white border-t flex gap-2"
        onSubmit={sendQuestion}
      >
        <input
          className="flex-1 border rounded px-3 py-2"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Escribe tu pregunta..."
          disabled={loading}
        />
        <button
          className="bg-blue-600 text-white px-4 py-2 rounded"
          type="submit"
          disabled={loading}
        >
          Enviar
        </button>
      </form>
    </div>
  );
}

export default App;

import { useState } from "react";
import ReactMarkdown from "react-markdown";

const INTRO = `🔍 **LoreChat Holmes**

*"Cuando hayas eliminado lo imposible, lo que quede, por improbable que parezca, debe ser la verdad."*

Bienvenido a Baker Street 221B. Sherlock Holmes responde tus preguntas basándose en el corpus completo de Arthur Conan Doyle.

Podés hacerle preguntas sobre sus casos, métodos deductivos y vida en la época victoriana. También podés pedirle que escriba un cuento de misterio con los personajes que quieras.`;

function App() {
  const [messages, setMessages] = useState([{ role: "info", text: INTRO }]);
  const [input, setInput] = useState("");
  const [nombre, setNombre] = useState("");
  const [loading, setLoading] = useState(false);

  const sendQuestion = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = { role: "user", text: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setLoading(true);

    try {
      const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/ask";
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: input,
          modo: "auto",
          nombre: nombre.trim() || null,
        }),
      });
      const data = await res.json();
      setMessages((msgs) => [
        ...msgs,
        { role: "holmes", text: data.answer, sources: data.sources || [], modo: data.modo },
      ]);
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        { role: "error", text: "Error consultando la API." },
      ]);
    }
    setInput("");
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      <header className="p-4 bg-gray-800 text-white flex items-center gap-3 border-b border-gray-700">
        <span className="text-2xl">🔍</span>
        <span className="text-xl font-bold tracking-wide">LoreChat Holmes</span>
      </header>

      <main className="flex-1 p-4 overflow-y-auto">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`p-4 rounded-lg ${
                msg.role === "user"
                  ? "bg-blue-900 text-blue-100 ml-8"
                  : msg.role === "holmes"
                  ? "bg-gray-800 text-gray-100 border border-amber-700"
                  : msg.role === "info"
                  ? "bg-gray-800 text-gray-300 border-l-4 border-amber-500"
                  : "bg-red-900 text-red-200"
              }`}
            >
              {msg.role === "holmes" ? (
                <div>
                  {msg.modo === "cuento" && (
                    <div className="text-xs text-amber-400 mb-2 font-semibold uppercase tracking-widest">
                      📖 Cuento
                    </div>
                  )}
                  <div className="prose prose-invert prose-amber max-w-none">
                    {msg.text
                      .split(/\n{2,}/)
                      .map((p, idx) => (
                        <p key={idx} style={{ marginBottom: "1.2em" }}>{p}</p>
                      ))}
                  </div>
                  {msg.sources.length > 0 && (
                    <div className="mt-3 text-xs text-gray-500 italic">
                      {msg.sources.length} fuente{msg.sources.length > 1 ? "s" : ""} consultada{msg.sources.length > 1 ? "s" : ""}
                    </div>
                  )}
                </div>
              ) : msg.role === "info" ? (
                <div className="prose prose-invert prose-sm max-w-none">
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
              ) : (
                <span>{msg.text}</span>
              )}
            </div>
          ))}
          {loading && (
            <div className="p-4 bg-gray-800 rounded-lg text-amber-400 italic border border-gray-700">
              Holmes está deduciendo...
            </div>
          )}
        </div>
      </main>

      <form className="p-4 bg-gray-800 border-t border-gray-700 space-y-2" onSubmit={sendQuestion}>
        <input
          className="w-full border border-gray-600 bg-gray-900 text-gray-200 rounded px-3 py-1.5 text-sm placeholder-gray-500 focus:outline-none focus:border-amber-500"
          type="text"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          placeholder="Tu nombre (opcional — para que Holmes no te llame Watson)"
        />
        <div className="flex gap-2">
          <input
            className="flex-1 border border-gray-600 bg-gray-900 text-gray-100 rounded px-3 py-2 placeholder-gray-500 focus:outline-none focus:border-amber-500"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Preguntá algo o pedí un cuento..."
            disabled={loading}
          />
          <button
            className="bg-amber-600 hover:bg-amber-500 text-white px-5 py-2 rounded font-semibold disabled:opacity-50"
            type="submit"
            disabled={loading}
          >
            Enviar
          </button>
        </div>
      </form>
    </div>
  );
}

export default App;

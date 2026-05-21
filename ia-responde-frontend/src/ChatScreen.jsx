import { useState, useRef, useEffect } from "react";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/ask";
const API_BASE = API_URL.replace("/ask", "");

const COLORS = {
  bg:             "#EDE5D0",
  header:         "#DDD3B8",
  inputBar:       "#DDD3B8",
  inputBg:        "#FFFFFF",
  bubbleAI:       "#FFFFFF",
  bubbleLoading:  "#F0EBE0",
  bubbleUser:     "#7C6E44",
  bubbleUserText: "#F5EDD0",
  textPrimary:    "#1a140a",
  textMuted:      "#8a7a60",
  textDim:        "#a09070",
  accent:         "#7C6E44",
};

const AVATARS = {
  holmes: "linear-gradient(160deg,#3D2B1A 20%,#1E1208 60%,#0A0604 100%)",
};

const CUENTO_WORDS = [
  "escrib","crea","cre ","inventa","cuento","historia","relato",
  "genera","imagina","narra","redacta","compone","libro",
];

const LOADING_MSGS = {
  factual: [
    "Holmes está deduciendo...",
    "El detective examina la evidencia disponible...",
    "Una mente bien ordenada tarda lo que necesita...",
  ],
  cuento: [
    "Holmes toma su pipa y cierra los ojos...",
    "Las llamas de la chimenea parpadean en Baker Street...",
    "Watson toma nota en silencio desde su sillón...",
    "El relato toma forma en la mente del detective...",
    "Holmes narra con su estilo victoriano impecable...",
  ],
  pdf: [
    "Holmes descuelga el auricular. —Watson, le necesito de inmediato.",
    "Watson llega a Baker Street con su maletín de escritura.",
    "—Siéntese, Watson. Le dictaré el relato desde el principio.",
    "La pluma rasga el papel en silencio concentrado...",
    "Holmes revisa cada párrafo con ojo crítico e impecable.",
    "Watson añade los últimos retoques al manuscrito.",
    "Holmes sella el sobre con lacre carmesí.",
  ],
};

const STORY_ACK_MSGS = [
  "Ajá. Watson, su pluma si no le importa. Voy a necesitar unos instantes para ordenar los hechos en mi mente.",
  "Interesante solicitud. Watson, acompáñeme — esto requiere de nuestra mejor prosa. Un momento.",
  "Bien. Cierre la puerta, Watson, y tome su libreta. Voy a dictarle el relato.",
  "Una historia, dice. Perfecto. Watson se encargará de la narrativa mientras yo dispongo los elementos del caso.",
  "Entendido. Watson tiene la pluma lista. Permítame concentrarme un instante.",
  "Como gusta. No es el tipo de problema que resuelvo con la lupa, pero la pluma tampoco se me da mal.",
];

function hasStoryIntent(text) {
  const lower = text.toLowerCase();
  return CUENTO_WORDS.some(w => lower.includes(w));
}

function detectType(text) {
  return hasStoryIntent(text) ? "cuento" : "factual";
}

function detectPdfIntent(text) {
  const lower = text.toLowerCase();
  const hasPdfAction = ["llevar","llevarme","imprimir","hijos","físico","fisico"].some(w => lower.includes(w));
  const hasBook = lower.includes("libro");
  return hasPdfAction && (hasBook || hasStoryIntent(text));
}

const CHARACTER_IMAGES = {
  holmes: "/sherlock.jpg",
};

function Avatar({ avatarKey, size = 36 }) {
  const img = CHARACTER_IMAGES[avatarKey];
  if (img) {
    return (
      <div style={{ width: size, height: size, borderRadius: "50%", overflow: "hidden", flexShrink: 0 }}>
        <img src={img} alt={avatarKey} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </div>
    );
  }
  return (
    <div style={{
      width: size, height: size, borderRadius: "50%",
      background: AVATARS[avatarKey] || AVATARS.holmes,
      flexShrink: 0, position: "relative", overflow: "hidden",
    }}>
      <div style={{
        position: "absolute", top: "18%", left: "50%",
        transform: "translateX(-50%)",
        width: "42%", height: "52%",
        borderRadius: "50% 50% 44% 44%",
        background: "rgba(255,220,180,.15)",
      }} />
    </div>
  );
}

function SourcesList({ sources }) {
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState(null);

  return (
    <div style={{ marginTop: 8, borderTop: "1px solid #d4c4a8", paddingTop: 6 }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          background: "none", border: "none", cursor: "pointer",
          fontSize: 11, color: COLORS.accent, fontWeight: 600, padding: 0,
        }}
      >
        {open ? "▾" : "▸"} {sources.length} fragmento{sources.length > 1 ? "s" : ""} consultado{sources.length > 1 ? "s" : ""}
      </button>
      {open && (
        <div style={{ marginTop: 4, display: "flex", flexDirection: "column", gap: 3 }}>
          {sources.map((s, i) => (
            <div key={i}>
              <button
                onClick={() => setExpanded(expanded === i ? null : i)}
                style={{
                  background: "none", border: "none", cursor: "pointer",
                  fontSize: 10, color: COLORS.textMuted,
                  textAlign: "left", padding: 0, width: "100%",
                }}
              >
                {expanded === i ? "▾" : "▸"}{" "}
                <span style={{ color: COLORS.accent }}>{s.source || "fuente"}</span>
                {s.chunk_id && <span style={{ color: COLORS.textDim }}> · chunk {s.chunk_id}</span>}
              </button>
              {expanded === i && (
                <div style={{
                  marginTop: 2, marginLeft: 10, padding: "4px 8px",
                  background: "#f5f0e8", borderRadius: 6,
                  fontSize: 10, color: COLORS.textMuted, lineHeight: 1.4,
                }}>
                  {s.preview}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function renderText(text) {
  // Bold: **text**
  const parts = text.split(/(\*\*[^*]+\*\*|#{1,3} [^\n]+)/g);
  return parts.map((part, i) => {
    if (/^\*\*[^*]+\*\*$/.test(part)) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (/^#{1,3} /.test(part)) {
      const level = part.match(/^(#+)/)[1].length;
      const content = part.replace(/^#{1,3} /, "");
      const size = level === 1 ? 16 : level === 2 ? 14 : 13;
      return <div key={i} style={{ fontWeight: 700, fontSize: size, marginTop: 10, marginBottom: 4 }}>{content}</div>;
    }
    return <span key={i}>{part}</span>;
  });
}

function BubbleText({ text, loading }) {
  if (loading) return <span style={{ fontStyle: "italic" }}>{text}</span>;
  const paragraphs = text.split(/\n{2,}/);
  return (
    <div>
      {paragraphs.map((p, i) => (
        <p key={i} style={{ margin: i === 0 ? 0 : "0.9em 0 0 0" }}>{renderText(p)}</p>
      ))}
    </div>
  );
}

function Bubble({ msg, avatarKey, onDownloadPdf }) {
  const isAI = msg.role === "ai";
  return (
    <div style={{
      display: "flex", alignItems: "flex-end", gap: 8,
      justifyContent: isAI ? "flex-start" : "flex-end",
      marginBottom: 10,
    }}>
      {isAI && <Avatar avatarKey={avatarKey} size={30} />}
      <div style={{
        maxWidth: "74%",
        padding: "10px 14px",
        borderRadius: isAI ? "18px 18px 18px 4px" : "18px 18px 4px 18px",
        background: isAI ? (msg.loading ? COLORS.bubbleLoading : COLORS.bubbleAI) : COLORS.bubbleUser,
        color: isAI ? COLORS.textPrimary : COLORS.bubbleUserText,
        fontSize: 14, lineHeight: 1.55,
      }}>
        <BubbleText text={msg.text} loading={msg.loading} />
        {msg.sources && msg.sources.length > 0 && (
          <SourcesList sources={msg.sources} />
        )}
        {msg.modo === "cuento" && onDownloadPdf && (
          <div style={{ marginTop: 10, borderTop: "1px solid #d4c4a8", paddingTop: 8 }}>
            <p style={{ fontSize: 11, color: COLORS.textDim, fontStyle: "italic", margin: "0 0 6px 0" }}>
              Si desea llevarse el relato, puedo llamar a Watson para que lo transcriba en papel.
            </p>
            <button
              onClick={() => onDownloadPdf(msg.prompt)}
              style={{
                background: COLORS.accent, border: "none", color: "#F5EDD0",
                padding: "5px 12px", borderRadius: 12, fontSize: 11,
                cursor: "pointer", fontFamily: "inherit",
              }}
            >
              📄 Watson, transcríbalo en papel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

const WELCOME = "Buenos días. Soy Sherlock Holmes, de Baker Street 221B. ¿En qué puedo serle útil?";

export default function ChatScreen({ character = "holmes", name = "Sherlock Holmes", userName = null, onBack }) {
  const [messages, setMessages] = useState([
    { id: 1, role: "ai", text: WELCOME },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingType, setLoadingType] = useState("factual");
  const [loadingIdx, setLoadingIdx] = useState(0);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfLoadingIdx, setPdfLoadingIdx] = useState(0);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, pdfLoading]);

  useEffect(() => {
    if (!loading) { setLoadingIdx(0); return; }
    const msgs = LOADING_MSGS[loadingType];
    const t = setInterval(() => setLoadingIdx(i => (i + 1) % msgs.length), 3000);
    return () => clearInterval(t);
  }, [loading, loadingType]);

  useEffect(() => {
    if (!pdfLoading) { setPdfLoadingIdx(0); return; }
    const msgs = LOADING_MSGS.pdf;
    const t = setInterval(() => setPdfLoadingIdx(i => (i + 1) % msgs.length), 3000);
    return () => clearInterval(t);
  }, [pdfLoading]);

  async function downloadPdf(prompt) {
    setPdfLoading(true);
    try {
      const res = await fetch(`${API_BASE}/generate-story`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, nombre: userName || null, formato: "pdf" }),
      });
      const blob = await res.blob();
      const disposition = res.headers.get("Content-Disposition") || "";
      const filenameMatch = disposition.match(/filename="?([^";\n]+)"?/);
      const filename = filenameMatch ? filenameMatch[1].trim() : "cuento_holmes.pdf";
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      setMessages(prev => [...prev, {
        id: Date.now(), role: "ai",
        text: "Watson ha terminado. El relato está listo para llevárselo.",
      }]);
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now(), role: "ai",
        text: "Ha habido un contratiempo con el manuscrito. Disculpe.",
      }]);
    }
    setPdfLoading(false);
  }

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading || pdfLoading) return;

    const currentInput = text;
    const type = detectType(currentInput);
    const wantsPdf = detectPdfIntent(currentInput);

    setMessages(prev => [...prev, { id: Date.now(), role: "user", text: currentInput }]);
    setInput("");

    if (wantsPdf) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1, role: "ai",
        text: "Entendido. Permítame un momento — Watson ya está al tanto y prepara su pluma. No se vaya muy lejos.",
      }]);
      downloadPdf(currentInput);
      return;
    }

    setLoadingType(type);

    // Respuesta inmediata antes de ponerse a pensar
    if (type === "cuento") {
      const ack = STORY_ACK_MSGS[Math.floor(Math.random() * STORY_ACK_MSGS.length)];
      setMessages(prev => [...prev, { id: Date.now() + 1, role: "ai", text: ack }]);
    }

    setLoading(true);

    try {
      const history = messages
        .filter(m => m.role === "user" || m.role === "ai")
        .slice(-6)
        .map(m => ({ role: m.role === "ai" ? "holmes" : "user", content: m.text }));

      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: currentInput,
          modo: "auto",
          nombre: userName || null,
          history,
        }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, {
        id: Date.now() + 1, role: "ai",
        text: data.answer,
        sources: data.sources || [],
        modo: data.modo,
        prompt: currentInput,
      }]);
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now() + 1, role: "ai",
        text: "Ha ocurrido un error al consultar la API.",
      }]);
    }
    setLoading(false);
  }

  function handleKey(e) {
    if (e.key === "Enter") sendMessage();
  }

  return (
    <div style={{
      display: "flex", flexDirection: "column", height: "100%",
      background: COLORS.bg, fontFamily: "'Inter', sans-serif",
    }}>
      {/* Header */}
      <div style={{
        display: "flex", alignItems: "center", gap: 10,
        padding: "10px 16px 12px",
        background: COLORS.header, flexShrink: 0,
      }}>
        {onBack && (
          <button
            onClick={onBack}
            style={{
              background: "none", border: "none", cursor: "pointer",
              fontSize: 24, color: "#4a3c28", lineHeight: 1, padding: "0 4px 0 0",
            }}
          >
            ‹
          </button>
        )}
        <Avatar avatarKey={character} size={36} />
        <span style={{ flex: 1, fontSize: 15, fontWeight: 600, color: COLORS.textPrimary }}>
          {name}
        </span>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1, overflowY: "auto",
        padding: "0 16px 12px",
        display: "flex", flexDirection: "column",
      }}>
        {/* Intro avatar */}
        <div style={{
          display: "flex", flexDirection: "column",
          alignItems: "center", padding: "20px 0 16px", gap: 8, flexShrink: 0,
        }}>
          <Avatar avatarKey={character} size={90} />
          <span style={{ fontSize: 14, fontWeight: 600, color: COLORS.textPrimary }}>{name}</span>
          <span style={{
            fontSize: 11, color: COLORS.textDim, fontStyle: "italic",
            textAlign: "center", maxWidth: 280, lineHeight: 1.5,
          }}>
            "Cuando hayas eliminado lo imposible, lo que quede, por improbable que parezca, debe ser la verdad."
          </span>
        </div>

        {messages.map(msg => (
          <Bubble
            key={msg.id}
            msg={msg}
            avatarKey={character}
            onDownloadPdf={msg.modo === "cuento" ? downloadPdf : null}
          />
        ))}

        {loading && (
          <Bubble
            msg={{ id: "loading", role: "ai", text: LOADING_MSGS[loadingType][loadingIdx], loading: true }}
            avatarKey={character}
          />
        )}

        {pdfLoading && (
          <Bubble
            msg={{ id: "pdfloading", role: "ai", text: LOADING_MSGS.pdf[pdfLoadingIdx], loading: true }}
            avatarKey={character}
          />
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div style={{
        display: "flex", alignItems: "center", gap: 10,
        padding: "10px 16px 22px",
        background: COLORS.inputBar, flexShrink: 0,
      }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Preguntá algo o pedí un cuento..."
          disabled={loading || pdfLoading}
          style={{
            flex: 1, background: COLORS.inputBg,
            border: "none", borderRadius: 22,
            padding: "10px 16px", fontSize: 13,
            fontFamily: "inherit", color: COLORS.textMuted,
            outline: "none",
            opacity: (loading || pdfLoading) ? 0.6 : 1,
          }}
        />
        <button
          onClick={sendMessage}
          disabled={loading || pdfLoading}
          style={{
            width: 36, height: 36, borderRadius: "50%",
            background: (loading || pdfLoading) ? "#b0a080" : COLORS.accent,
            border: "none",
            cursor: (loading || pdfLoading) ? "default" : "pointer",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="#fff">
            <path d="M2 21l21-9L2 3v7l15 2-15 2z"/>
          </svg>
        </button>
      </div>
    </div>
  );
}

import { useState } from "react";
import ChatScreen from "./ChatScreen";

const CHARACTERS = [
  { key: "marcus",   name: "Marcus Aurelius" },
  { key: "gandhi",   name: "Mahatma Gandhi" },
  { key: "aristotle",name: "Aristotle" },
  { key: "tesla",    name: "Nikola Tesla" },
];

export default function App() {
  const [selected, setSelected] = useState(CHARACTERS[0]);

  return (
    <div style={{
      minHeight: "100vh",
      background: "#C8BFA8",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "flex-start",
      padding: "2rem 1rem",
      gap: "1rem",
      fontFamily: "'Inter', sans-serif",
    }}>
      {/* Character selector */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "center" }}>
        {CHARACTERS.map(c => (
          <button
            key={c.key}
            onClick={() => setSelected(c)}
            style={{
              padding: "6px 14px",
              borderRadius: 20,
              border: "none",
              background: selected.key === c.key ? "#7C6E44" : "#DDD3B8",
              color: selected.key === c.key ? "#F5EDD0" : "#2a2010",
              fontSize: 13,
              cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            {c.name}
          </button>
        ))}
      </div>

      {/* Responsive chat container */}
      <div style={{
        width: "100%",
        maxWidth: 420,
        height: "min(780px, calc(100vh - 120px))",
        borderRadius: 32,
        overflow: "hidden",
        boxShadow: "0 20px 60px rgba(0,0,0,.3)",
      }}>
        <ChatScreen
          key={selected.key}
          character={selected.key}
          name={selected.name}
          onBack={() => alert("← Volver al inicio")}
        />
      </div>
    </div>
  );
}

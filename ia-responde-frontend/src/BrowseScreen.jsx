import { useState, useRef, useEffect } from "react";

const COLORS = {
  bg:      "#EDE5D0",
  header:  "#DDD3B8",
  text:    "#1a140a",
  textMuted: "#8a7a60",
  menuBg:  "#FFFFFF",
  danger:  "#8B2020",
  overlay: "rgba(0,0,0,.35)",
};

const AVATARS = {
  holmes: "linear-gradient(160deg,#3D2B1A 20%,#1E1208 60%,#0A0604 100%)",
};

const CATEGORIES = [
  {
    icon: "\uD83D\uDCDA",
    label: "Literatura",
    people: [
      { key: "holmes", name: "Sherlock Holmes" },
    ],
  },
];

const CHARACTER_IMAGES = {
  holmes: "/sherlock.jpg",
};

function Avatar({ avatarKey, size = 72 }) {
  const img = CHARACTER_IMAGES[avatarKey];
  if (img) {
    return (
      <div style={{ width: size, height: size, borderRadius: "50%", overflow: "hidden", flexShrink: 0 }}>
        <img src={img} alt={avatarKey} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </div>
    );
  }
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        background: AVATARS[avatarKey] || "#9B8A6A",
        flexShrink: 0,
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: "18%", left: "50%",
          transform: "translateX(-50%)",
          width: "42%", height: "52%",
          borderRadius: "50% 50% 44% 44%",
          background: "rgba(255,220,180,.22)",
        }}
      />
    </div>
  );
}

function PersonCard({ person, onSelect }) {
  return (
    <div
      onClick={() => onSelect(person)}
      style={{
        display: "flex", flexDirection: "column",
        alignItems: "center", gap: 7,
        cursor: "pointer", flexShrink: 0,
      }}
    >
      <Avatar avatarKey={person.key} size={72} />
      <span style={{
        fontSize: 11, color: COLORS.text,
        textAlign: "center", maxWidth: 76, lineHeight: 1.3,
      }}>
        {person.name}
      </span>
    </div>
  );
}

function Category({ cat, onSelect }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{
        display: "flex", alignItems: "center", gap: 6,
        fontSize: 15, fontWeight: 600, color: COLORS.text,
        padding: "0 20px", marginBottom: 14,
      }}>
        <span>{cat.icon}</span> {cat.label}
      </div>
      <div style={{
        display: "flex", gap: 14,
        overflowX: "auto", padding: "0 20px 4px",
        scrollbarWidth: "none",
      }}>
        {cat.people.map((p, i) => (
          <PersonCard key={`${p.key}-${i}`} person={p} onSelect={onSelect} />
        ))}
      </div>
    </div>
  );
}

export default function BrowseScreen({ onSelectCharacter, user, displayName, onChangeName, onLogout, onRincon }) {
  const [menuOpen, setMenuOpen]   = useState(false);
  const [editOpen, setEditOpen]   = useState(false);
  const [draft,    setDraft]      = useState("");
  const inputRef                  = useRef(null);

  useEffect(() => {
    if (editOpen) {
      setDraft(displayName || "");
      setTimeout(() => inputRef.current?.focus(), 80);
    }
  }, [editOpen, displayName]);

  function handleSaveName() {
    const trimmed = draft.trim();
    if (trimmed) onChangeName(trimmed);
    setEditOpen(false);
  }

  // Iniciales de fallback si no hay foto
  const initials = (displayName || "?")[0].toUpperCase();

  return (
    <div style={{
      display: "flex", flexDirection: "column",
      height: "100%",
      background: COLORS.bg,
      fontFamily: "'Inter', sans-serif",
      position: "relative",
      overflow: "hidden",
    }}>

      {/* ── Overlay menú lateral ── */}
      {menuOpen && (
        <div
          onClick={() => setMenuOpen(false)}
          style={{
            position: "absolute", inset: 0,
            background: COLORS.overlay, zIndex: 9,
          }}
        />
      )}

      {/* ── Modal editar nombre ── */}
      {editOpen && (
        <div
          onClick={() => setEditOpen(false)}
          style={{
            position: "absolute", inset: 0,
            background: COLORS.overlay, zIndex: 20,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: "#FDFAF4", borderRadius: 18,
              padding: "28px 28px 22px",
              width: 280,
              display: "flex", flexDirection: "column", gap: 16,
              boxShadow: "0 12px 40px rgba(0,0,0,.22)",
            }}
          >
            <div style={{ fontSize: 15, fontWeight: 700, color: COLORS.text }}>
              Cambiar nombre de usuario
            </div>
            <input
              ref={inputRef}
              value={draft}
              onChange={e => setDraft(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter") handleSaveName(); if (e.key === "Escape") setEditOpen(false); }}
              maxLength={40}
              style={{
                border: "1.5px solid #D4C9B0",
                borderRadius: 10, padding: "9px 12px",
                fontSize: 14, color: COLORS.text,
                background: "#FFF", outline: "none",
                fontFamily: "inherit",
              }}
            />
            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
              <button
                onClick={() => setEditOpen(false)}
                style={{
                  background: "none", border: "1.5px solid #D4C9B0",
                  borderRadius: 10, padding: "7px 16px",
                  fontSize: 13, cursor: "pointer",
                  color: COLORS.textMuted, fontFamily: "inherit",
                }}
              >
                Cancelar
              </button>
              <button
                onClick={handleSaveName}
                style={{
                  background: "#7C6E44", border: "none",
                  borderRadius: 10, padding: "7px 16px",
                  fontSize: 13, cursor: "pointer",
                  color: "#F5EDD0", fontFamily: "inherit", fontWeight: 600,
                }}
              >
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Slide menu ── */}
      <div style={{
        position: "absolute",
        top: 0, left: 0, bottom: 0,
        width: 220,
        background: COLORS.menuBg,
        zIndex: 10,
        transform: menuOpen ? "translateX(0)" : "translateX(-100%)",
        transition: "transform .25s ease",
        display: "flex", flexDirection: "column",
        paddingTop: 60,
        boxShadow: "4px 0 20px rgba(0,0,0,.15)",
      }}>
        {[
          { icon: "📚", label: "Rincón del Profe", action: "rincon" },
          { icon: "🏠", label: "Para Casa", action: null },
          { icon: "💬", label: "Chat", action: null },
        ].map(item => (
          <button
            key={item.label}
            onClick={() => { if (item.action === "rincon") { setMenuOpen(false); onRincon && onRincon(); } else setMenuOpen(false); }}
            style={{
              display: "flex", alignItems: "center", gap: 12,
              padding: "16px 24px",
              fontSize: 14, fontWeight: 500, color: COLORS.text,
              background: "none", border: "none", cursor: "pointer",
              textAlign: "left", width: "100%",
            }}
          >
            <span style={{ fontSize: 17, width: 22, textAlign: "center" }}>{item.icon}</span>
            {item.label}
          </button>
        ))}

        <div style={{ flex: 1 }} />

        {/* Configuración justo antes de Cerrar Sesión */}
        <button
          onClick={() => setMenuOpen(false)}
          style={{
            display: "flex", alignItems: "center", gap: 12,
            padding: "16px 24px",
            fontSize: 14, fontWeight: 500, color: COLORS.text,
            background: "none", border: "none",
            cursor: "pointer", textAlign: "left", width: "100%",
          }}
        >
          <span style={{ fontSize: 17, width: 22, textAlign: "center" }}>⚙️</span>
          Configuración
        </button>

        {/* Cerrar sesión */}
        <button
          onClick={() => { setMenuOpen(false); onLogout && onLogout(); }}
          style={{
            display: "flex", alignItems: "center", gap: 12,
            padding: "16px 24px",
            fontSize: 14, fontWeight: 500, color: COLORS.danger,
            background: "none",
            borderTop: "1px solid rgba(0,0,0,.1)",
            borderLeft: "none", borderRight: "none", borderBottom: "none",
            cursor: "pointer", textAlign: "left", width: "100%",
          }}
        >
          <span style={{ fontSize: 17, width: 22, textAlign: "center" }}>🚪</span>
          Cerrar Sesión
        </button>
      </div>

      {/* ── Header ── */}
      <div style={{
        display: "flex", alignItems: "center",
        justifyContent: "space-between",
        padding: "8px 20px 12px",
        background: COLORS.header,
        flexShrink: 0,
      }}>
        {/* Hamburger */}
        <button
          onClick={() => setMenuOpen(true)}
          style={{ background: "none", border: "none", cursor: "pointer", padding: 4 }}
        >
          {[0,1,2].map(i => (
            <span key={i} style={{
              display: "block", width: 20, height: 2,
              background: COLORS.text, borderRadius: 2,
              marginBottom: i < 2 ? 4 : 0,
            }} />
          ))}
        </button>

        {/* Profile */}
        <div
          onClick={() => setEditOpen(true)}
          style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}
          title="Cambiar nombre"
        >
          <span style={{ fontSize: 13, fontWeight: 500, color: COLORS.text }}>
            {displayName || "Usuario"}
          </span>
          {user?.picture ? (
            <img
              src={user.picture}
              alt="perfil"
              referrerPolicy="no-referrer"
              style={{ width: 34, height: 34, borderRadius: "50%", objectFit: "cover" }}
            />
          ) : (
            <div style={{
              width: 34, height: 34, borderRadius: "50%",
              background: "linear-gradient(135deg,#9B8A6A,#5A3A1A)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 13, fontWeight: 600, color: "#F5EDD0",
            }}>
              {initials}
            </div>
          )}
        </div>
      </div>

      {/* ── Scroll content ── */}
      <div style={{
        flex: 1, overflowY: "auto",
        padding: "8px 0 20px",
        scrollbarWidth: "none",
      }}>
        {CATEGORIES.map(cat => (
          <Category
            key={cat.label}
            cat={cat}
            onSelect={onSelectCharacter}
          />
        ))}
      </div>

      {/* Home indicator */}
      <div style={{
        width: 110, height: 4,
        background: "rgba(26,20,10,.2)",
        borderRadius: 2, margin: "0 auto 8px",
        flexShrink: 0,
      }} />
    </div>
  );
}

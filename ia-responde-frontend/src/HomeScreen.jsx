import T from "./theme";
import SECTIONS from "./sections";

export default function HomeScreen({ user, onNavigate }) {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Buenos días" : hour < 19 ? "Buenas tardes" : "Buenas noches";
  const firstName = user?.name?.split(" ")[0] || "";

  return (
    <div style={{
      display: "flex", flexDirection: "column",
      alignItems: "center",
      height: "100%", background: T.bg,
      fontFamily: "'Inter', sans-serif",
      padding: "0 24px",
      overflowY: "auto",
    }}>
      {/* Logo */}
      <img
        src="/logo_rincon_libro.png"
        alt="El Rincón del Libro"
        style={{ width: 200, maxWidth: "70%", objectFit: "contain", marginTop: 48, marginBottom: 8 }}
      />

      {/* Saludo */}
      <div style={{ fontSize: 14, color: T.textMuted, marginBottom: 40, textAlign: "center" }}>
        {greeting}{firstName ? `, ${firstName}` : ""}
      </div>

      {/* Cards de sección */}
      <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: 14 }}>
        {SECTIONS.map(s => (
          <button
            key={s.view}
            onClick={() => onNavigate(s.view)}
            style={{
              display: "flex", alignItems: "center",
              justifyContent: "space-between",
              padding: "18px 20px",
              background: T.surface,
              border: `1px solid ${T.border}`,
              borderRadius: 14,
              cursor: "pointer",
              boxShadow: "0 2px 8px rgba(60,30,10,.07)",
              width: "100%",
              textAlign: "left",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <div style={{
                width: 44, height: 44, borderRadius: 12,
                background: T.accentSurface,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 22, flexShrink: 0,
              }}>
                {s.icon}
              </div>
              <div>
                <div style={{ fontSize: 15, fontWeight: 600, color: T.text }}>
                  {s.label}
                </div>
                {s.description && (
                  <div style={{ fontSize: 12, color: T.textMuted, marginTop: 2 }}>
                    {s.description}
                  </div>
                )}
              </div>
            </div>
            {/* Flecha */}
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M9 18l6-6-6-6" stroke={T.accentLight} strokeWidth="2.5"
                strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        ))}
      </div>
    </div>
  );
}

import SECTIONS from "./sections";
import T from "./theme";

export default function SideMenu({ open, onClose, onNavigate, onLogout, currentView }) {
  return (
    <>
      {open && (
        <div onClick={onClose} style={{
          position: "absolute", inset: 0, background: T.overlay, zIndex: 9,
        }} />
      )}
      <div style={{
        position: "absolute", top: 0, left: 0, bottom: 0, width: 220,
        background: T.card, zIndex: 10,
        transform: open ? "translateX(0)" : "translateX(-100%)",
        transition: "transform .25s ease",
        display: "flex", flexDirection: "column",
        boxShadow: open ? "4px 0 20px rgba(0,0,0,.15)" : "none",
      }}>
        {/* Logo */}
        <div style={{ paddingTop: 24, paddingRight: 20, paddingBottom: 16, paddingLeft: 20, borderBottom: `1px solid ${T.border}` }}>
          <img src="/logo_rincon_libro.png" alt="El Rincón del Libro"
            style={{ width: 90, objectFit: "contain" }} />
        </div>

        {/* Nav */}
        <div style={{ flex: 1, paddingTop: 8 }}>
          {SECTIONS.map(s => {
            const active = currentView === s.view;
            return (
              <button key={s.view} onClick={() => onNavigate(s.view)} style={{
                display: "flex", alignItems: "center", gap: 12,
                padding: "14px 20px", width: "100%",
                fontSize: 14, fontWeight: active ? 600 : 400,
                color: active ? T.accent : T.text,
                background: active ? T.accentSoft : "none",
                border: "none", cursor: "pointer", textAlign: "left",
                borderLeft: active ? `3px solid ${T.accent}` : "3px solid transparent",
              }}>
                <span style={{ fontSize: 17, width: 22, textAlign: "center" }}>{s.icon}</span>
                {s.label}
              </button>
            );
          })}
        </div>

        {/* Footer */}
        <button onClick={onClose} style={{
          display: "flex", alignItems: "center", gap: 12,
          padding: "14px 20px", width: "100%",
          fontSize: 14, color: T.textMuted,
          background: "none", border: "none", cursor: "pointer", textAlign: "left",
        }}>
          <span style={{ fontSize: 17, width: 22, textAlign: "center" }}>⚙️</span>
          Configuración
        </button>

        <button onClick={onLogout} style={{
          display: "flex", alignItems: "center", gap: 12,
          padding: "14px 20px", width: "100%",
          fontSize: 14, fontWeight: 500, color: T.danger,
          background: "none",
          borderTop: `1px solid ${T.border}`,
          borderLeft: "none", borderRight: "none", borderBottom: "none",
          cursor: "pointer", textAlign: "left",
        }}>
          <span style={{ fontSize: 17, width: 22, textAlign: "center" }}>🚪</span>
          Cerrar Sesión
        </button>
      </div>
    </>
  );
}

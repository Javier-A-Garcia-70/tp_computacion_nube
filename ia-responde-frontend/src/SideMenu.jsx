import SECTIONS from "./sections";

const COLORS = {
  menuBg:  "#FFFFFF",
  text:    "#663A2A",
  danger:  "#8B2020",
  overlay: "rgba(0,0,0,.35)",
  active:  "#F0D8C8",
};

export default function SideMenu({ open, onClose, onNavigate, onLogout, currentView }) {
  return (
    <>
      {open && (
        <div
          onClick={onClose}
          style={{ position: "absolute", inset: 0, background: COLORS.overlay, zIndex: 9 }}
        />
      )}

      <div style={{
        position: "absolute", top: 0, left: 0, bottom: 0,
        width: 220, background: COLORS.menuBg, zIndex: 10,
        transform: open ? "translateX(0)" : "translateX(-100%)",
        transition: "transform .25s ease",
        display: "flex", flexDirection: "column",
        boxShadow: "4px 0 20px rgba(0,0,0,.15)",
      }}>
        {/* Logo */}
        <div style={{ padding: "24px 20px 16px", borderBottom: "1px solid rgba(0,0,0,.08)" }}>
          <img src="/logo_rincon_libro.png" alt="El Rincón del Libro" style={{ width: 140, objectFit: "contain" }} />
        </div>

        {/* Nav — generado desde sections.js */}
        <div style={{ flex: 1, paddingTop: 8 }}>
          {SECTIONS.map(s => (
            <button
              key={s.view}
              onClick={() => onNavigate(s.view)}
              style={{
                display: "flex", alignItems: "center", gap: 12,
                padding: "14px 20px", width: "100%",
                fontSize: 14, fontWeight: currentView === s.view ? 600 : 400,
                color: COLORS.text,
                background: currentView === s.view ? COLORS.active : "none",
                border: "none", cursor: "pointer", textAlign: "left",
              }}
            >
              <span style={{ fontSize: 17, width: 22, textAlign: "center" }}>{s.icon}</span>
              {s.label}
            </button>
          ))}
        </div>

        {/* Footer */}
        <button
          onClick={onClose}
          style={{
            display: "flex", alignItems: "center", gap: 12,
            padding: "14px 20px", width: "100%",
            fontSize: 14, color: COLORS.text,
            background: "none", border: "none", cursor: "pointer", textAlign: "left",
          }}
        >
          <span style={{ fontSize: 17, width: 22, textAlign: "center" }}>⚙️</span>
          Configuración
        </button>

        <button
          onClick={onLogout}
          style={{
            display: "flex", alignItems: "center", gap: 12,
            padding: "14px 20px", width: "100%",
            fontSize: 14, fontWeight: 500, color: COLORS.danger,
            background: "none",
            borderTop: "1px solid rgba(0,0,0,.1)",
            borderLeft: "none", borderRight: "none", borderBottom: "none",
            cursor: "pointer", textAlign: "left",
          }}
        >
          <span style={{ fontSize: 17, width: 22, textAlign: "center" }}>🚪</span>
          Cerrar Sesión
        </button>
      </div>
    </>
  );
}

const COLORS = {
  header: "#98B6C8",
  text:   "#663A2A",
};

export default function AppHeader({ title, user, onOpenMenu }) {
  const initials = (user?.name || "?")[0].toUpperCase();

  return (
    <div style={{
      display:         "flex",
      alignItems:      "center",
      justifyContent:  "space-between",
      padding:         "8px 16px",
      background:      COLORS.header,
      flexShrink:      0,
      minHeight:       52,
    }}>
      {/* Hamburguesa */}
      <button
        onClick={onOpenMenu}
        style={{ background: "none", border: "none", cursor: "pointer", padding: 6 }}
        aria-label="Menú"
      >
        {[0,1,2].map(i => (
          <span key={i} style={{
            display: "block", width: 20, height: 2,
            background: COLORS.text, borderRadius: 2,
            marginBottom: i < 2 ? 4 : 0,
          }} />
        ))}
      </button>

      {/* Título de sección */}
      <span style={{
        fontSize:    15,
        fontWeight:  600,
        color:       COLORS.text,
        letterSpacing: "-0.2px",
      }}>
        {title}
      </span>

      {/* Avatar del usuario */}
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
          background: "linear-gradient(135deg,#D47649,#663A2A)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 13, fontWeight: 700, color: "#fff",
        }}>
          {initials}
        </div>
      )}
    </div>
  );
}

import AppHeader from "./AppHeader";

const COLORS = {
  bg:        "#D2E4F0",
  text:      "#663A2A",
  textMuted: "#7A9AB0",
};

const AVATARS = {
  holmes: "linear-gradient(160deg,#3D2B1A 20%,#1E1208 60%,#0A0604 100%)",
};

const CATEGORIES = [
  {
    icon: "📚",
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
    <div style={{
      width: size, height: size, borderRadius: "50%",
      background: AVATARS[avatarKey] || "#9B8A6A",
      flexShrink: 0,
    }} />
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

export default function BrowseScreen({ onSelectCharacter, user, onOpenMenu }) {
  return (
    <div style={{
      display: "flex", flexDirection: "column",
      height: "100%",
      background: COLORS.bg,
      fontFamily: "'Inter', sans-serif",
    }}>
      <AppHeader title="Chat" user={user} onOpenMenu={onOpenMenu} />

      <div style={{
        flex: 1, overflowY: "auto",
        padding: "16px 0 20px",
        scrollbarWidth: "none",
      }}>
        {CATEGORIES.map(cat => (
          <Category key={cat.label} cat={cat} onSelect={onSelectCharacter} />
        ))}
      </div>

      <div style={{
        width: 110, height: 4,
        background: "rgba(26,20,10,.2)",
        borderRadius: 2, margin: "0 auto 8px",
        flexShrink: 0,
      }} />
    </div>
  );
}

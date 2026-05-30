import AppHeader from "./AppHeader";
import T from "./theme";

const CHARACTER_IMAGES = { holmes: "/sherlock.jpg" };

const CATEGORIES = [
  { icon: "📚", label: "Literatura", people: [{ key: "holmes", name: "Sherlock Holmes" }] },
];

function Avatar({ avatarKey, size = 72 }) {
  const img = CHARACTER_IMAGES[avatarKey];
  if (img) return (
    <div style={{ width: size, height: size, borderRadius: "50%", overflow: "hidden", flexShrink: 0 }}>
      <img src={img} alt={avatarKey} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    </div>
  );
  return <div style={{ width: size, height: size, borderRadius: "50%", background: T.border, flexShrink: 0 }} />;
}

function PersonCard({ person, onSelect }) {
  return (
    <div onClick={() => onSelect(person)} style={{
      display: "flex", flexDirection: "column", alignItems: "center",
      gap: 7, cursor: "pointer", flexShrink: 0,
    }}>
      <Avatar avatarKey={person.key} size={72} />
      <span style={{ fontSize: 11, color: T.text, textAlign: "center", maxWidth: 76, lineHeight: 1.3 }}>
        {person.name}
      </span>
    </div>
  );
}

export default function BrowseScreen({ onSelectCharacter, user, onOpenMenu }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: T.bg, fontFamily: "'Inter', sans-serif" }}>
      <AppHeader title="Chat" user={user} onOpenMenu={onOpenMenu} />
      <div style={{ flex: 1, overflowY: "auto", padding: "16px 0 20px", scrollbarWidth: "none" }}>
        {CATEGORIES.map(cat => (
          <div key={cat.label} style={{ marginBottom: 24 }}>
            <div style={{
              display: "flex", alignItems: "center", gap: 6,
              fontSize: 15, fontWeight: 600, color: T.text,
              padding: "0 20px", marginBottom: 14,
            }}>
              <span>{cat.icon}</span> {cat.label}
            </div>
            <div style={{ display: "flex", gap: 14, overflowX: "auto", padding: "0 20px 4px", scrollbarWidth: "none" }}>
              {cat.people.map(p => <PersonCard key={p.key} person={p} onSelect={onSelectCharacter} />)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

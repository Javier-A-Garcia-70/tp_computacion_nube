import { useState } from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";
import SECTIONS from "./sections";
import LoginScreen from "./LoginScreen";
import BrowseScreen from "./BrowseScreen";
import ChatScreen from "./ChatScreen";
import RinconProfeScreen from "./RinconProfeScreen";
import ParaCasaScreen from "./ParaCasaScreen";
import SideMenu from "./SideMenu";

const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || "";

/**
 * Mapa view → componente.
 * Para agregar una pantalla nueva: agregá la sección en sections.js
 * y registrá su componente acá.
 */
function renderView(view, props) {
  switch (view) {
    case "rincon": return <RinconProfeScreen {...props} />;
    case "casa":   return <ParaCasaScreen      {...props} />;
    case "browse": return <BrowseScreen      {...props} />;
    default:       return <BrowseScreen      {...props} />;
  }
}

export default function App() {
  const [user,        setUser]        = useState(null);
  const [displayName, setDisplayName] = useState("");
  const [view,        setView]        = useState("rincon");
  const [character,   setCharacter]   = useState(null);
  const [menuOpen,    setMenuOpen]    = useState(false);

  // Label del header se lee desde sections.js, no hardcodeado
  const currentSection = SECTIONS.find(s => s.view === view);

  function handleLogin(userData) {
    setUser(userData);
    setDisplayName(userData.name || "");
    setView("rincon");
  }

  function handleLogout() {
    setUser(null); setDisplayName(""); setView("browse");
    setCharacter(null); setMenuOpen(false);
  }

  function navigate(dest) {
    setView(dest); setMenuOpen(false); setCharacter(null);
  }

  const sharedProps = {
    user,
    displayName,
    onOpenMenu: () => setMenuOpen(true),
    onSelectCharacter: (person) => { setCharacter(person); setView("chat"); setMenuOpen(false); },
    onChangeName: setDisplayName,
  };

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div className="lorechat-outer">
        <div className="lorechat-container" style={{ position: "relative" }}>
          {!user ? (
            <LoginScreen onLogin={handleLogin} />
          ) : view === "chat" ? (
            <ChatScreen
              key={character?.key}
              character={character?.key || "holmes"}
              name={character?.name || "Sherlock Holmes"}
              userName={displayName}
              onBack={() => setView("browse")}
            />
          ) : (
            <>
              <SideMenu
                open={menuOpen}
                onClose={() => setMenuOpen(false)}
                onNavigate={navigate}
                onLogout={handleLogout}
                currentView={view}
              />
              {renderView(view, { ...sharedProps, sectionLabel: currentSection?.label || "" })}
            </>
          )}
        </div>
      </div>
    </GoogleOAuthProvider>
  );
}

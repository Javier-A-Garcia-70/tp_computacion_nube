import { useState } from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";
import LoginScreen from "./LoginScreen";
import BrowseScreen from "./BrowseScreen";
import ChatScreen from "./ChatScreen";
import RinconProfeScreen from "./RinconProfeScreen";

const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || "";

export default function App() {
  const [user,        setUser]        = useState(null);
  const [displayName, setDisplayName] = useState("");
  const [view,        setView]        = useState("rincon");
  const [character,   setCharacter]   = useState(null);

  function handleLogin(userData) {
    setUser(userData);
    setDisplayName(userData.name || "");
    setView("rincon");
  }

  function handleLogout() {
    setUser(null);
    setDisplayName("");
    setView("browse");
    setCharacter(null);
  }

  function handleSelectCharacter(person) {
    setCharacter(person);
    setView("chat");
  }

  function handleBack() {
    setView("browse");
    setCharacter(null);
  }

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div className="lorechat-outer">
        <div className="lorechat-container">
          {!user ? (
            <LoginScreen onLogin={handleLogin} />
          ) : view === "browse" ? (
            <BrowseScreen
              onSelectCharacter={handleSelectCharacter}
              user={user}
              displayName={displayName}
              onChangeName={setDisplayName}
              onLogout={handleLogout}
              onRincon={() => setView("rincon")}
            />
          ) : view === "rincon" ? (
            <RinconProfeScreen onBack={handleBack} />
          ) : (
            <ChatScreen
              key={character?.key}
              character={character?.key || "holmes"}
              name={character?.name || "Sherlock Holmes"}
              userName={displayName}
              onBack={handleBack}
            />
          )}
        </div>
      </div>
    </GoogleOAuthProvider>
  );
}

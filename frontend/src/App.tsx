import { useEffect, useState } from "react";
import { type AuthUser, api, clearToken, getToken } from "./api";
import { AuthBar } from "./components/AuthBar";
import { DeckList } from "./components/DeckList";
import { StudySession } from "./components/StudySession";

export function App() {
  const [deckId, setDeckId] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);

  // Restore session from a stored token on load.
  useEffect(() => {
    if (!getToken()) return;
    api
      .me()
      .then(setUser)
      .catch(() => clearToken());
  }, []);

  function logout() {
    clearToken();
    setUser(null);
  }

  return (
    <div className="container">
      <header className="app">
        <div>
          <h1>MedChem Flashcards</h1>
          <span className="tag">functional groups · spaced repetition</span>
        </div>
        <AuthBar user={user} onAuth={setUser} onLogout={logout} />
      </header>
      {deckId ? (
        <StudySession deckId={deckId} loggedIn={user !== null} onExit={() => setDeckId(null)} />
      ) : (
        <DeckList onStudy={setDeckId} />
      )}
    </div>
  );
}

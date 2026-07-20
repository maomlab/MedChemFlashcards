import { useEffect, useState } from "react";
import { api } from "../api";
import type { DeckSummary } from "../types";

interface Props {
  onStudy: (deckId: string) => void;
}

export function DeckList({ onStudy }: Props) {
  const [decks, setDecks] = useState<DeckSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listDecks()
      .then(setDecks)
      .catch((e: unknown) => setError(String(e)));
  }, []);

  if (error) return <p className="error">Failed to load decks: {error}</p>;
  if (!decks) return <p className="center">Loading decks…</p>;

  return (
    <div className="deck-grid">
      {decks.map((d) => (
        <button key={d.id} className="deck-card" onClick={() => onStudy(d.id)}>
          <h3>{d.title}</h3>
          <p>{d.description}</p>
          <div className="meta">
            <span>{d.card_count} cards</span>
            <span className="level">{d.level}</span>
          </div>
        </button>
      ))}
    </div>
  );
}

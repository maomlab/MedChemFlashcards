import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { CardDetail, CardSummary, DeckDetail } from "../types";
import {
  type Grade,
  dueQueue,
  getState,
  isoDate,
  loadStore,
  review,
  saveStore,
} from "../srs";
import { pushOne } from "../sync";
import { CardDetailView } from "./CardDetailView";

interface Props {
  deckId: string;
  loggedIn: boolean;
  onExit: () => void;
}

const GRADES: { grade: Grade; label: string; hint: string }[] = [
  { grade: "again", label: "Again", hint: "forgot" },
  { grade: "hard", label: "Hard", hint: "" },
  { grade: "good", label: "Good", hint: "" },
  { grade: "easy", label: "Easy", hint: "" },
];

export function StudySession({ deckId, loggedIn, onExit }: Props) {
  const [deck, setDeck] = useState<DeckDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [queue, setQueue] = useState<string[]>([]);
  const [showBack, setShowBack] = useState(false);
  const [detail, setDetail] = useState<CardDetail | null>(null);
  const [reviewed, setReviewed] = useState(0);
  const [started, setStarted] = useState(false);

  const today = useMemo(() => isoDate(new Date()), []);

  useEffect(() => {
    api
      .getDeck(deckId)
      .then(setDeck)
      .catch((e: unknown) => setError(String(e)));
  }, [deckId]);

  const cardsById = useMemo(() => {
    const m = new Map<string, CardSummary>();
    deck?.cards.forEach((c) => m.set(c.id, c));
    return m;
  }, [deck]);

  function begin(mode: "due" | "all") {
    if (!deck) return;
    const ids = deck.cards.map((c) => c.id);
    const store = loadStore();
    const q = mode === "all" ? shuffle(ids) : dueQueue(store, ids, today);
    setQueue(q);
    setReviewed(0);
    setShowBack(false);
    setDetail(null);
    setStarted(true);
  }

  const currentId = queue[0];

  async function reveal() {
    if (!currentId) return;
    setShowBack(true);
    if (!detail || detail.id !== currentId) {
      try {
        setDetail(await api.getCard(currentId));
      } catch (e) {
        setError(String(e));
      }
    }
  }

  function grade(g: Grade) {
    if (!currentId) return;
    const store = loadStore();
    const next = review(getState(store, currentId, today), g, today);
    store[currentId] = next;
    saveStore(store);
    if (loggedIn) void pushOne(next); // best-effort server sync

    const rest = queue.slice(1);
    if (g === "again") rest.push(currentId); // re-show later this session
    setQueue(rest);
    setShowBack(false);
    setDetail(null);
    setReviewed((n) => n + 1);
  }

  if (error) return <Shell onExit={onExit}><p className="error">Error: {error}</p></Shell>;
  if (!deck) return <Shell onExit={onExit}><p className="center">Loading…</p></Shell>;

  if (!started) {
    const store = loadStore();
    const dueCount = deck.cards.filter((c) => getState(store, c.id, today).due <= today).length;
    return (
      <Shell onExit={onExit}>
        <div className="center">
          <h2>{deck.title}</h2>
          <p>{dueCount} of {deck.cards.length} cards due for review.</p>
          <div className="reveal-row">
            {dueCount > 0 ? (
              <button className="btn btn-primary" onClick={() => begin("due")}>
                Review {dueCount} due
              </button>
            ) : (
              <button className="btn btn-primary" onClick={() => begin("all")}>
                Nothing due — cram all {deck.cards.length}
              </button>
            )}
          </div>
        </div>
      </Shell>
    );
  }

  if (!currentId) {
    return (
      <Shell onExit={onExit}>
        <div className="center">
          <h2>Session complete 🎉</h2>
          <p>You reviewed {reviewed} card{reviewed === 1 ? "" : "s"}.</p>
          <button className="btn btn-primary" onClick={onExit}>Back to decks</button>
        </div>
      </Shell>
    );
  }

  const summary = cardsById.get(currentId)!;

  return (
    <Shell onExit={onExit}>
      <div className="progress">
        <span>{deck.title}</span>
        <span>{queue.length} left · {reviewed} done</span>
      </div>
      <div className="card">
        <div className="depiction" dangerouslySetInnerHTML={{ __html: summary.svg }} />
        {!showBack ? (
          <>
            <p className="prompt">Which functional group is highlighted?</p>
            <div className="reveal-row">
              <button className="btn btn-primary" onClick={reveal}>Show answer</button>
            </div>
          </>
        ) : detail ? (
          <>
            <CardDetailView card={detail} />
            <div className="grade-row">
              {GRADES.map((g) => (
                <button key={g.grade} className={`grade ${g.grade}`} onClick={() => grade(g.grade)}>
                  {g.label}
                  {g.hint && <small>{g.hint}</small>}
                </button>
              ))}
            </div>
          </>
        ) : (
          <p className="center">Loading…</p>
        )}
      </div>
    </Shell>
  );
}

function Shell({ children, onExit }: { children: React.ReactNode; onExit: () => void }) {
  return (
    <div className="study">
      <button className="btn-link" onClick={onExit}>← All decks</button>
      {children}
    </div>
  );
}

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

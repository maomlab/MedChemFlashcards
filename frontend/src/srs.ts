// Spaced-repetition scheduling (SM-2) with localStorage persistence.
//
// This is a pure scheduler plus a thin storage layer. The review grades map to
// SM-2 qualities; "Again" is a lapse. Long-term state (ease, interval, due date)
// persists per card id so anonymous users keep progress across reloads. FSRS is
// a planned upgrade — the review() signature is grade-based to allow swapping.

export type Grade = "again" | "hard" | "good" | "easy";

export interface CardState {
  id: string;
  reps: number;
  ease: number; // ease factor, >= 1.3
  intervalDays: number;
  due: string; // ISO date (YYYY-MM-DD)
  lapses: number;
  lastReviewed: string | null;
}

const GRADE_QUALITY: Record<Grade, number> = { again: 1, hard: 3, good: 4, easy: 5 };
const MIN_EASE = 1.3;
const STORAGE_KEY = "medchem.srs.v1";

export function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function addDays(iso: string, days: number): string {
  const d = new Date(iso + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return isoDate(d);
}

export function newCardState(id: string, today: string): CardState {
  return { id, reps: 0, ease: 2.5, intervalDays: 0, due: today, lapses: 0, lastReviewed: null };
}

/** Apply a grade to a card's state, returning the next state (pure). */
export function review(state: CardState, grade: Grade, today: string): CardState {
  const q = GRADE_QUALITY[grade];
  let { reps, ease, intervalDays, lapses } = state;

  if (q < 3) {
    reps = 0;
    intervalDays = 1;
    lapses += 1;
  } else {
    if (reps === 0) intervalDays = 1;
    else if (reps === 1) intervalDays = 6;
    else intervalDays = Math.round(intervalDays * ease);
    reps += 1;
  }
  ease = Math.max(MIN_EASE, ease + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)));

  return {
    ...state,
    reps,
    ease: Math.round(ease * 100) / 100,
    intervalDays,
    lapses,
    due: addDays(today, intervalDays),
    lastReviewed: today,
  };
}

export function isDue(state: CardState, today: string): boolean {
  return state.due <= today;
}

// --- Persistence -------------------------------------------------------------

type Store = Record<string, CardState>;

export function loadStore(): Store {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Store) : {};
  } catch {
    return {};
  }
}

export function saveStore(store: Store): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
}

export function getState(store: Store, id: string, today: string): CardState {
  return store[id] ?? newCardState(id, today);
}

/** Cards from `ids` that are new or due today, in randomized order. */
export function dueQueue(store: Store, ids: string[], today: string): string[] {
  const due = ids.filter((id) => isDue(getState(store, id, today), today));
  for (let i = due.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [due[i], due[j]] = [due[j], due[i]];
  }
  return due;
}

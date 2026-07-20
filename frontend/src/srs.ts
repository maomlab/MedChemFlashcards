// Spaced-repetition scheduling with FSRS (Free Spaced Repetition Scheduler),
// the v4.5 algorithm with published default weights. FSRS models each card's
// memory as stability (S, days until retrievability decays to ~90%) and
// difficulty (D, 1-10). It schedules better than SM-2 by using elapsed time and
// retrievability rather than a fixed ease multiplier.
//
// State persists per card in localStorage so anonymous users keep progress; the
// server stores an opaque copy (see sync.ts) so the scheduler can evolve without
// a backend migration. Scheduling is in whole days (a daily-review app); within
// a session, "Again" re-queues the card immediately (see StudySession).

export type Grade = "again" | "hard" | "good" | "easy";
const GRADE_VALUE: Record<Grade, number> = { again: 1, hard: 2, good: 3, easy: 4 };

export interface CardState {
  id: string;
  stability: number;
  difficulty: number;
  due: string; // ISO date (YYYY-MM-DD)
  lastReview: string | null;
  reps: number;
  lapses: number;
}

// FSRS-4.5 default parameters.
const W = [
  0.4, 0.6, 2.4, 5.8, 4.93, 0.94, 0.86, 0.01, 1.49, 0.14, 0.94, 2.18, 0.05, 0.34, 1.26, 0.29,
  2.61,
];
const DECAY = -0.5;
const FACTOR = 19 / 81; // 0.9^(1/DECAY) - 1
const REQUEST_RETENTION = 0.9;
const MIN_INTERVAL = 1;
const MAX_INTERVAL = 36500;
const STORAGE_KEY = "medchem.srs.v2";

const clamp = (x: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, x));

export function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function addDays(iso: string, days: number): string {
  const d = new Date(iso + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return isoDate(d);
}

function daysBetween(fromIso: string, toIso: string): number {
  const ms = new Date(toIso + "T00:00:00Z").getTime() - new Date(fromIso + "T00:00:00Z").getTime();
  return Math.max(0, Math.round(ms / 86_400_000));
}

// --- FSRS core (pure) --------------------------------------------------------

function retrievability(elapsedDays: number, stability: number): number {
  return Math.pow(1 + (FACTOR * elapsedDays) / stability, DECAY);
}

function initStability(g: number): number {
  return Math.max(W[g - 1], 0.1);
}

function initDifficulty(g: number): number {
  return clamp(W[4] - (g - 3) * W[5], 1, 10);
}

function nextInterval(stability: number): number {
  const ivl = (stability / FACTOR) * (Math.pow(REQUEST_RETENTION, 1 / DECAY) - 1);
  return clamp(Math.round(ivl), MIN_INTERVAL, MAX_INTERVAL);
}

function nextDifficulty(d: number, g: number): number {
  const next = d - W[6] * (g - 3);
  const reverted = W[7] * initDifficulty(4) + (1 - W[7]) * next; // mean reversion
  return clamp(reverted, 1, 10);
}

function nextStabilityOnRecall(d: number, s: number, r: number, g: number): number {
  const hard = g === 2 ? W[15] : 1;
  const easy = g === 4 ? W[16] : 1;
  return (
    s *
    (1 +
      Math.exp(W[8]) *
        (11 - d) *
        Math.pow(s, -W[9]) *
        (Math.exp((1 - r) * W[10]) - 1) *
        hard *
        easy)
  );
}

function nextStabilityOnLapse(d: number, s: number, r: number): number {
  const post = W[11] * Math.pow(d, -W[12]) * (Math.pow(s + 1, W[13]) - 1) * Math.exp((1 - r) * W[14]);
  return Math.min(post, s); // post-lapse stability never exceeds prior stability
}

export function newCardState(id: string, today: string): CardState {
  return { id, stability: 0, difficulty: 0, due: today, lastReview: null, reps: 0, lapses: 0 };
}

/** Apply a grade to a card's state, returning the next state (pure). */
export function review(state: CardState, grade: Grade, today: string): CardState {
  const g = GRADE_VALUE[grade];
  let stability: number;
  let difficulty: number;

  if (state.reps === 0) {
    stability = initStability(g);
    difficulty = initDifficulty(g);
  } else {
    const r = retrievability(daysBetween(state.lastReview ?? today, today), state.stability);
    difficulty = nextDifficulty(state.difficulty, g);
    stability =
      g === 1
        ? nextStabilityOnLapse(difficulty, state.stability, r)
        : nextStabilityOnRecall(difficulty, state.stability, r, g);
  }

  const interval = nextInterval(stability);
  return {
    ...state,
    stability: Math.round(stability * 1000) / 1000,
    difficulty: Math.round(difficulty * 1000) / 1000,
    reps: state.reps + 1,
    lapses: state.lapses + (g === 1 ? 1 : 0),
    lastReview: today,
    due: addDays(today, interval),
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

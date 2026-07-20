// Bridge between the local (localStorage) scheduler store and the server.
// On login we merge both directions; after each graded review we push the one
// updated card. All server calls are best-effort so the app stays usable offline.

import { api, type ServerProgress } from "./api";
import { type CardState, loadStore, saveStore } from "./srs";

function toServer(s: CardState): ServerProgress {
  return {
    card_id: s.id,
    due: s.due,
    last_reviewed: s.lastReview,
    state: {
      stability: s.stability,
      difficulty: s.difficulty,
      reps: s.reps,
      lapses: s.lapses,
    },
  };
}

function fromServer(e: ServerProgress): CardState {
  return {
    id: e.card_id,
    due: e.due,
    lastReview: e.last_reviewed,
    stability: e.state.stability ?? 0,
    difficulty: e.state.difficulty ?? 0,
    reps: e.state.reps ?? 0,
    lapses: e.state.lapses ?? 0,
  };
}

/** Push local progress up, pull the merged set back, and replace local with it. */
export async function syncAll(): Promise<void> {
  const local = loadStore();
  const merged = await api.putProgress(Object.values(local).map(toServer));
  const next: Record<string, CardState> = {};
  for (const e of merged) next[e.card_id] = fromServer(e);
  saveStore(next);
}

/** Best-effort push of a single card's updated state (called after grading). */
export async function pushOne(state: CardState): Promise<void> {
  try {
    await api.putProgress([toServer(state)]);
  } catch {
    /* offline or unauthenticated — local store remains the source of truth */
  }
}

import type { CardDetail, DeckDetail, DeckSummary } from "./types";

// Static mode (VITE_STATIC=1) serves precomputed JSON from `${base}data/` instead
// of a live API — used for GitHub Pages / any static host. Accounts and progress
// sync are unavailable in this mode; anonymous localStorage progress still works.
export const IS_STATIC = import.meta.env.VITE_STATIC === "1";
const DATA = `${import.meta.env.BASE_URL}data`;

const TOKEN_KEY = "medchem.token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

function headers(withBody: boolean): Record<string, string> {
  const h: Record<string, string> = {};
  if (withBody) h["Content-Type"] = "application/json";
  const token = getToken();
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

async function req<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(url, { ...init, headers: headers(init?.body != null) });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(resp.status, detail);
  }
  return (await resp.json()) as T;
}

export interface AuthUser {
  id: number;
  email: string;
}
export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}
// Scheduler state is stored opaquely server-side so the algorithm can change
// without a backend migration.
export interface ServerProgress {
  card_id: string;
  due: string;
  last_reviewed: string | null;
  state: Record<string, number>;
}

export const api = {
  listDecks: () =>
    IS_STATIC ? req<DeckSummary[]>(`${DATA}/decks.json`) : req<DeckSummary[]>("/api/decks"),
  getDeck: (id: string) =>
    IS_STATIC ? req<DeckDetail>(`${DATA}/decks/${id}.json`) : req<DeckDetail>(`/api/decks/${id}`),
  getCard: (id: string) =>
    IS_STATIC ? req<CardDetail>(`${DATA}/cards/${id}.json`) : req<CardDetail>(`/api/cards/${id}`),

  register: (email: string, password: string) =>
    req<TokenResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    req<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => req<AuthUser>("/api/auth/me"),
  getProgress: () => req<ServerProgress[]>("/api/progress"),
  putProgress: (entries: ServerProgress[]) =>
    req<ServerProgress[]>("/api/progress", {
      method: "PUT",
      body: JSON.stringify({ entries }),
    }),
};

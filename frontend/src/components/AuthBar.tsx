import { useState } from "react";
import { ApiError, api, type AuthUser, clearToken, setToken } from "../api";
import { syncAll } from "../sync";

interface Props {
  user: AuthUser | null;
  onAuth: (user: AuthUser) => void;
  onLogout: () => void;
}

export function AuthBar({ user, onAuth, onLogout }: Props) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) {
    return (
      <div className="authbar">
        <span className="user-email">{user.email}</span>
        <button className="btn-link" onClick={onLogout}>
          Log out
        </button>
      </div>
    );
  }

  if (!open) {
    return (
      <div className="authbar">
        <button className="btn-link" onClick={() => setOpen(true)}>
          Log in / Register
        </button>
      </div>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const resp = mode === "login" ? await api.login(email, password) : await api.register(email, password);
      setToken(resp.access_token);
      await syncAll(); // merge anonymous progress with the account
      onAuth(resp.user);
      setOpen(false);
      setEmail("");
      setPassword("");
    } catch (err) {
      clearToken();
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      <input
        type="email"
        placeholder="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        autoComplete="email"
      />
      <input
        type="password"
        placeholder="password (min 8)"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        minLength={8}
        autoComplete={mode === "login" ? "current-password" : "new-password"}
      />
      <button className="btn btn-primary" type="submit" disabled={busy}>
        {mode === "login" ? "Log in" : "Register"}
      </button>
      <button
        type="button"
        className="btn-link"
        onClick={() => {
          setMode(mode === "login" ? "register" : "login");
          setError(null);
        }}
      >
        {mode === "login" ? "Need an account?" : "Have an account?"}
      </button>
      <button type="button" className="btn-link" onClick={() => setOpen(false)}>
        Cancel
      </button>
      {error && <span className="error">{error}</span>}
    </form>
  );
}

"""Tests for authentication and progress sync endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

CREDS = {"email": "chemist@example.com", "password": "correct horse battery"}


def _register(client: TestClient, **over: object) -> dict:
    body = {**CREDS, **over}
    return client.post("/api/auth/register", json=body).json()


def test_register_returns_token_and_user(client: TestClient) -> None:
    resp = client.post("/api/auth/register", json=CREDS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == "chemist@example.com"


def test_register_normalizes_email_and_rejects_duplicate(client: TestClient) -> None:
    client.post("/api/auth/register", json=CREDS)
    dup = client.post("/api/auth/register", json={**CREDS, "email": "CHEMIST@example.com"})
    assert dup.status_code == 409


def test_register_rejects_short_password(client: TestClient) -> None:
    resp = client.post("/api/auth/register", json={**CREDS, "password": "short"})
    assert resp.status_code == 422


def test_login_success_and_failure(client: TestClient) -> None:
    client.post("/api/auth/register", json=CREDS)
    ok = client.post("/api/auth/login", json=CREDS)
    assert ok.status_code == 200
    bad = client.post("/api/auth/login", json={**CREDS, "password": "wrong wrong wrong"})
    assert bad.status_code == 401


def test_me_requires_valid_token(client: TestClient) -> None:
    token = _register(client)["access_token"]
    assert client.get("/api/auth/me").status_code == 401
    bad = client.get("/api/auth/me", headers={"Authorization": "Bearer nonsense"})
    assert bad.status_code == 401
    ok = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200
    assert ok.json()["email"] == "chemist@example.com"


def _auth(client: TestClient) -> dict[str, str]:
    token = _register(client)["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_progress_requires_auth(client: TestClient) -> None:
    assert client.get("/api/progress").status_code == 401


def test_progress_sync_upsert_and_fetch(client: TestClient) -> None:
    headers = _auth(client)
    entries = [
        {
            "card_id": "carboxylic-acid",
            "reps": 2,
            "ease": 2.5,
            "interval_days": 6,
            "due": "2026-07-26",
            "lapses": 0,
            "last_reviewed": "2026-07-20",
        },
    ]
    put = client.put("/api/progress", json={"entries": entries}, headers=headers)
    assert put.status_code == 200
    assert put.json()[0]["card_id"] == "carboxylic-acid"

    got = client.get("/api/progress", headers=headers)
    assert got.status_code == 200
    assert len(got.json()) == 1
    assert got.json()[0]["reps"] == 2


def test_progress_merge_last_reviewed_wins(client: TestClient) -> None:
    headers = _auth(client)
    base = {"card_id": "amide", "ease": 2.5, "interval_days": 1, "lapses": 0}
    client.put(
        "/api/progress",
        json={"entries": [{**base, "reps": 3, "due": "2026-07-25", "last_reviewed": "2026-07-20"}]},
        headers=headers,
    )
    # Older review must not overwrite the newer stored state.
    client.put(
        "/api/progress",
        json={"entries": [{**base, "reps": 1, "due": "2026-07-19", "last_reviewed": "2026-07-18"}]},
        headers=headers,
    )
    got = client.get("/api/progress", headers=headers).json()
    assert got[0]["reps"] == 3
    # A newer review does overwrite.
    client.put(
        "/api/progress",
        json={"entries": [{**base, "reps": 5, "due": "2026-08-01", "last_reviewed": "2026-07-22"}]},
        headers=headers,
    )
    got = client.get("/api/progress", headers=headers).json()
    assert got[0]["reps"] == 5


def test_progress_is_per_user(client: TestClient) -> None:
    h1 = _auth(client)
    client.put(
        "/api/progress",
        json={
            "entries": [
                {
                    "card_id": "amide",
                    "reps": 1,
                    "ease": 2.5,
                    "interval_days": 1,
                    "due": "2026-07-21",
                    "lapses": 0,
                    "last_reviewed": "2026-07-20",
                }
            ]
        },
        headers=h1,
    )
    token2 = client.post(
        "/api/auth/register", json={"email": "other@example.com", "password": "another good one"}
    ).json()["access_token"]
    h2 = {"Authorization": f"Bearer {token2}"}
    assert client.get("/api/progress", headers=h2).json() == []

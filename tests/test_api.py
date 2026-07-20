"""API endpoint tests against a seeded database."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_decks(client: TestClient) -> None:
    resp = client.get("/api/decks")
    assert resp.status_code == 200
    decks = resp.json()
    ids = {d["id"] for d in decks}
    assert "common-functional-groups" in ids
    cfg = next(d for d in decks if d["id"] == "common-functional-groups")
    assert cfg["card_count"] >= 10
    # decks are ordered
    assert [d["order"] for d in decks] == sorted(d["order"] for d in decks)


def test_get_deck_detail(client: TestClient) -> None:
    resp = client.get("/api/decks/common-functional-groups")
    assert resp.status_code == 200
    deck = resp.json()
    assert deck["title"] == "Common Functional Groups"
    card_ids = {c["id"] for c in deck["cards"]}
    assert "carboxylic-acid" in card_ids
    assert all(c["svg"].startswith("<svg") for c in deck["cards"])


def test_get_deck_404(client: TestClient) -> None:
    assert client.get("/api/decks/nope").status_code == 404


def test_get_card_detail(client: TestClient) -> None:
    resp = client.get("/api/cards/carboxylic-acid")
    assert resp.status_code == 200
    card = resp.json()
    assert card["name"] == "Carboxylic Acid"
    assert card["computed"]["formula"] == "C2H4O2"
    assert card["provenance"]
    assert any(ex["name"] == "Ibuprofen" for ex in card["examples"])


def test_get_card_svg(client: TestClient) -> None:
    resp = client.get("/api/cards/carboxylic-acid/svg")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/svg+xml")
    assert resp.text.startswith("<svg")


def test_get_card_404(client: TestClient) -> None:
    assert client.get("/api/cards/nope").status_code == 404

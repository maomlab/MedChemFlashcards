"""Tests for the static JSON export used by the Pages/static deployment."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from medchem_flashcards.curate.export_static import export_static

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT = REPO_ROOT / "content"


@pytest.mark.skipif(not CONTENT.exists(), reason="no authored content present")
def test_export_static_produces_api_shaped_files(tmp_path: Path) -> None:
    out = tmp_path / "data"
    report = export_static(CONTENT, out_dir=out)
    assert report.ok, report.summary()

    # decks.json is a list of summaries, ordered by deck order.
    decks = json.loads((out / "decks.json").read_text())
    assert len(decks) == report.n_decks
    assert [d["order"] for d in decks] == sorted(d["order"] for d in decks)
    assert all({"id", "title", "card_count"} <= d.keys() for d in decks)

    # Per-deck detail carries card summaries with inline SVG.
    deck_id = decks[0]["id"]
    detail = json.loads((out / "decks" / f"{deck_id}.json").read_text())
    assert detail["card_count"] == len(detail["cards"])
    assert all(c["svg"].startswith("<svg") for c in detail["cards"])

    # Per-card detail matches the CardDetail shape the SPA consumes.
    card = json.loads((out / "cards" / "carboxylic-acid.json").read_text())
    assert card["computed"]["formula"] == "C2H4O2"
    assert card["svg"].startswith("<svg")
    assert card["provenance"]


def test_export_static_aborts_on_qc_failure(tmp_path: Path) -> None:
    deck = tmp_path / "content" / "bad-deck"
    deck.mkdir(parents=True)
    (deck / "deck.yaml").write_text("id: bad-deck\ntitle: Bad\ndescription: Bad deck.\n")
    (deck / "thing.yaml").write_text(
        "id: thing\ndeck: bad-deck\nname: Thing\n"
        'smarts: "[CX3](=O)[OX2H1]"\nrepresentative_smiles: "CC(=O)O"\n'
        "properties:\n  typical_pka: '4-5'\n"
        "relevance: Missing provenance.\nprovenance:\n  - {field: smarts, source: rdkit}\n"
    )
    report = export_static(tmp_path / "content", out_dir=tmp_path / "data")
    assert not report.ok
    assert not (tmp_path / "data" / "decks.json").exists()

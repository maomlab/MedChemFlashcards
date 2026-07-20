"""Integration tests for enrichment, QC, and ingestion against shipped content."""

from __future__ import annotations

from pathlib import Path

import pytest

from medchem_flashcards.curate.enrich import enrich_card
from medchem_flashcards.curate.ingest import ingest_content
from medchem_flashcards.curate.loader import load_content
from medchem_flashcards.curate.qc import run_qc
from medchem_flashcards.db.models import Card, Deck
from medchem_flashcards.db.session import make_engine, session_scope

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT = REPO_ROOT / "content"


@pytest.mark.skipif(not CONTENT.exists(), reason="no authored content present")
def test_shipped_content_passes_qc() -> None:
    report = run_qc(CONTENT)
    assert report.ok, report.render()
    assert report.n_cards > 0


def test_enrich_card_computes_props_and_svg() -> None:
    loaded = load_content(CONTENT)
    card = next(c for c in loaded.all_cards if c.id == "carboxylic-acid")
    enriched = enrich_card(card)
    assert enriched.computed.formula == "C2H4O2"
    assert enriched.computed.h_donors == 1
    assert enriched.svg.startswith("<svg")


@pytest.mark.skipif(not CONTENT.exists(), reason="no authored content present")
def test_ingest_builds_queryable_db(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    report = ingest_content(CONTENT, db_path=db_path, assets_dir=tmp_path / "assets")
    assert report.ok, report.summary()
    assert report.n_cards == report.n_cards  # sanity

    engine = make_engine(db_path)
    with session_scope(engine) as session:
        n_decks = session.query(Deck).count()
        n_cards = session.query(Card).count()
        card = session.get(Card, "carboxylic-acid")
        assert card is not None
        assert card.deck_id == "common-functional-groups"
        assert card.svg.startswith("<svg")
        assert card.payload["computed"]["formula"] == "C2H4O2"
    assert n_decks == report.n_decks
    assert n_cards == report.n_cards


def test_ingest_aborts_on_qc_failure(tmp_path: Path) -> None:
    # A deck whose single card omits provenance for a curated pKa must fail the gate.
    deck = tmp_path / "content" / "bad-deck"
    deck.mkdir(parents=True)
    (deck / "deck.yaml").write_text(
        "id: bad-deck\ntitle: Bad\ndescription: Bad deck for testing.\n"
    )
    (deck / "thing.yaml").write_text(
        "id: thing\n"
        "deck: bad-deck\n"
        "name: Thing\n"
        'smarts: "[CX3](=O)[OX2H1]"\n'
        'representative_smiles: "CC(=O)O"\n'
        "properties:\n  typical_pka: '4-5'\n"
        "relevance: Missing provenance for typical_pka.\n"
        "provenance:\n  - {field: smarts, source: rdkit}\n"
    )
    report = ingest_content(tmp_path / "content", db_path=tmp_path / "out.db")
    assert not report.ok
    assert any("QC gate failed" in e for e in report.errors)
    assert not (tmp_path / "out.db").exists()

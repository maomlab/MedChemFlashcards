"""Ingestion pipeline: content -> enrich -> SQLite (+ SVG export).

Rebuilds the database from scratch on each run (the DB is a build artifact). QC
is run first; a failing QC report aborts ingestion so the database never
contains content that violates the quality gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from medchem_flashcards.chem import ChemError
from medchem_flashcards.curate.enrich import enrich_card
from medchem_flashcards.curate.loader import ContentError, load_content
from medchem_flashcards.curate.qc import run_qc
from medchem_flashcards.db.models import Card, Deck
from medchem_flashcards.db.session import init_db, make_engine, session_scope


@dataclass
class IngestReport:
    n_decks: int = 0
    n_cards: int = 0
    errors: list[str] = field(default_factory=list)
    db_path: Path | None = None

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        status = "OK" if self.ok else "FAILED"
        head = f"Ingest {status}: {self.n_cards} cards / {self.n_decks} decks"
        if self.db_path:
            head += f" -> {self.db_path}"
        if self.errors:
            head += "\n" + "\n".join(f"  ERROR: {e}" for e in self.errors)
        return head


def ingest_content(
    content_dir: Path,
    db_path: Path,
    assets_dir: Path | None = None,
    *,
    run_quality_gate: bool = True,
) -> IngestReport:
    """Build ``db_path`` from ``content_dir``. Returns a report; never raises for
    expected content/chemistry problems (they are collected as errors)."""
    report = IngestReport()

    if run_quality_gate:
        qc = run_qc(content_dir)
        if not qc.ok:
            report.errors.append("QC gate failed; run `medchem qc` for details")
            report.errors.extend(f"{i.where}: {i.message}" for i in qc.errors)
            return report

    try:
        loaded = load_content(content_dir)
    except ContentError as exc:
        report.errors.append(str(exc))
        return report

    report.n_decks = len(loaded.decks)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(db_path)
    init_db(engine, drop=True)

    svg_dir = assets_dir / "svg" if assets_dir else None
    if svg_dir:
        svg_dir.mkdir(parents=True, exist_ok=True)

    with session_scope(engine) as session:
        for loaded_deck in loaded.decks:
            meta = loaded_deck.meta
            session.add(
                Deck(
                    id=meta.id,
                    title=meta.title,
                    description=meta.description,
                    order=meta.order,
                    level=meta.level,
                    prerequisites=list(meta.prerequisites),
                )
            )
            for card in loaded_deck.cards:
                try:
                    enriched = enrich_card(card)
                except ChemError as exc:
                    report.errors.append(f"{card.deck}/{card.id}: {exc}")
                    continue
                session.add(
                    Card(
                        id=enriched.id,
                        deck_id=enriched.deck,
                        name=enriched.name,
                        difficulty=enriched.difficulty,
                        smarts=enriched.smarts,
                        representative_smiles=enriched.representative_smiles,
                        svg=enriched.svg,
                        tags=list(enriched.tags),
                        payload=enriched.model_dump(mode="json"),
                    )
                )
                report.n_cards += 1
                if svg_dir:
                    (svg_dir / f"{enriched.id}.svg").write_text(enriched.svg)

    report.db_path = db_path
    return report

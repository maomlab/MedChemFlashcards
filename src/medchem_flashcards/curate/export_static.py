"""Export content as static JSON mirroring the read API, for static hosting.

Produces a directory tree consumable by the SPA in static mode (no backend):

    <out>/decks.json            # list[DeckSummary]
    <out>/decks/<deck>.json     # DeckDetail (with card summaries incl. SVG)
    <out>/cards/<card>.json     # EnrichedCard (full card detail)

The shapes are the exact Pydantic response models the FastAPI endpoints return,
so the frontend consumes them identically whether served by the API or as files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from medchem_flashcards.api.schemas import CardSummary, DeckDetail, DeckSummary
from medchem_flashcards.chem import ChemError
from medchem_flashcards.curate.enrich import enrich_card
from medchem_flashcards.curate.loader import ContentError, load_content
from medchem_flashcards.curate.qc import run_qc


@dataclass
class ExportReport:
    n_decks: int = 0
    n_cards: int = 0
    out_dir: Path | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        status = "OK" if self.ok else "FAILED"
        head = f"Static export {status}: {self.n_cards} cards / {self.n_decks} decks"
        if self.out_dir:
            head += f" -> {self.out_dir}"
        if self.errors:
            head += "\n" + "\n".join(f"  ERROR: {e}" for e in self.errors)
        return head


def _write_json(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def export_static(
    content_dir: Path,
    out_dir: Path,
    *,
    run_quality_gate: bool = True,
) -> ExportReport:
    """Write the static JSON tree under ``out_dir``. Returns a report; content or
    chemistry problems are collected as errors rather than raised."""
    report = ExportReport()

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

    cards_dir = out_dir / "cards"
    decks_dir = out_dir / "decks"
    summaries: list[DeckSummary] = []

    for loaded_deck in loaded.decks:
        meta = loaded_deck.meta
        card_summaries: list[CardSummary] = []
        for card in loaded_deck.cards:
            try:
                enriched = enrich_card(card)
            except ChemError as exc:
                report.errors.append(f"{card.deck}/{card.id}: {exc}")
                continue
            _write_json(cards_dir / f"{enriched.id}.json", enriched.model_dump_json())
            card_summaries.append(
                CardSummary(
                    id=enriched.id,
                    name=enriched.name,
                    deck=enriched.deck,
                    difficulty=enriched.difficulty,
                    tags=enriched.tags,
                    svg=enriched.svg,
                )
            )
            report.n_cards += 1

        detail = DeckDetail(
            id=meta.id,
            title=meta.title,
            description=meta.description,
            order=meta.order,
            level=meta.level,
            card_count=len(card_summaries),
            prerequisites=list(meta.prerequisites),
            cards=card_summaries,
        )
        _write_json(decks_dir / f"{meta.id}.json", detail.model_dump_json())
        summaries.append(
            DeckSummary(
                id=meta.id,
                title=meta.title,
                description=meta.description,
                order=meta.order,
                level=meta.level,
                card_count=len(card_summaries),
            )
        )

    summaries.sort(key=lambda d: d.order)
    _write_json(out_dir / "decks.json", json.dumps([d.model_dump(mode="json") for d in summaries]))
    report.n_decks = len(summaries)
    report.out_dir = out_dir
    return report

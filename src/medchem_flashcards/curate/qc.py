"""Data-quality checks over authored content.

Runs structural, chemical, provenance, licensing, and cross-reference checks and
produces a :class:`QCReport`. ``ERROR`` issues fail the build (non-zero exit);
``WARNING`` issues are advisory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from medchem_flashcards.chem import ChemError
from medchem_flashcards.chem.matching import has_match, parse_smarts, parse_smiles
from medchem_flashcards.curate.loader import ContentError, load_content
from medchem_flashcards.licensing import is_approved
from medchem_flashcards.schema.card import CardContent

# Curated fields that assert a sourceable quantitative fact and therefore
# require provenance. Editorial labels (polarity) and RDKit-derived counts are
# intentionally excluded.
_CURATED_PROP_FIELDS = (
    "typical_pka",
    "charge_at_ph7_4",
)


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class Issue:
    severity: Severity
    where: str
    message: str


@dataclass
class QCReport:
    issues: list[Issue] = field(default_factory=list)
    n_decks: int = 0
    n_cards: int = 0

    def add(self, severity: Severity, where: str, message: str) -> None:
        self.issues.append(Issue(severity, where, message))

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity is Severity.WARNING]

    @property
    def ok(self) -> bool:
        return not self.errors

    def render(self) -> str:
        lines = [f"QC: {self.n_cards} cards across {self.n_decks} decks"]
        for issue in self.issues:
            lines.append(f"  [{issue.severity.value}] {issue.where}: {issue.message}")
        lines.append(f"{len(self.errors)} error(s), {len(self.warnings)} warning(s)")
        lines.append("QC PASSED" if self.ok else "QC FAILED")
        return "\n".join(lines)


def _required_provenance_fields(card: CardContent) -> set[str]:
    fields = {"smarts"}
    for name in _CURATED_PROP_FIELDS:
        if getattr(card.properties, name) is not None:
            fields.add(name)
    if card.examples:
        fields.add("examples")
    return fields


def _check_card(card: CardContent, report: QCReport) -> None:
    where = f"{card.deck}/{card.id}"

    # Chemistry: SMILES / SMARTS parse.
    try:
        parse_smiles(card.representative_smiles)
    except ChemError as exc:
        report.add(Severity.ERROR, where, str(exc))
    for pattern in {card.smarts, card.effective_highlight_smarts}:
        try:
            parse_smarts(pattern)
        except ChemError as exc:
            report.add(Severity.ERROR, where, str(exc))

    # The card's own motif should be present in its representative molecule.
    try:
        mol = parse_smiles(card.representative_smiles)
        if not has_match(mol, card.smarts):
            report.add(
                Severity.WARNING,
                where,
                f"smarts {card.smarts!r} does not match representative_smiles "
                f"{card.representative_smiles!r}",
            )
    except ChemError:
        pass  # already reported above

    # Example molecules must parse.
    for ex in card.examples:
        try:
            parse_smiles(ex.smiles)
        except ChemError as exc:
            report.add(Severity.ERROR, where, f"example {ex.name!r}: {exc}")

    # Provenance coverage.
    provided = {p.field for p in card.provenance}
    for missing in sorted(_required_provenance_fields(card) - provided):
        report.add(Severity.ERROR, where, f"missing provenance for field '{missing}'")

    # Licensing: source keys must be approved.
    for p in card.provenance:
        if p.source is not None and not is_approved(p.source):
            report.add(
                Severity.ERROR,
                where,
                f"provenance for '{p.field}' cites unapproved source '{p.source}'",
            )


def run_qc(content_dir: Path) -> QCReport:
    """Load and check all content, returning a report."""
    report = QCReport()
    try:
        loaded = load_content(content_dir)
    except ContentError as exc:
        report.add(Severity.ERROR, "content", str(exc))
        return report

    report.n_decks = len(loaded.decks)
    report.n_cards = len(loaded.all_cards)

    # Global uniqueness of card ids; collect ids for cross-reference checks.
    seen_ids: dict[str, str] = {}
    for card in loaded.all_cards:
        if card.id in seen_ids:
            report.add(
                Severity.ERROR,
                f"{card.deck}/{card.id}",
                f"duplicate card id (also in deck '{seen_ids[card.id]}')",
            )
        seen_ids[card.id] = card.deck

    # Per-deck duplicate names.
    for deck in loaded.decks:
        names: dict[str, str] = {}
        for card in deck.cards:
            key = card.name.lower()
            if key in names:
                report.add(
                    Severity.WARNING,
                    f"{deck.meta.id}/{card.id}",
                    f"duplicate name {card.name!r} (also {names[key]})",
                )
            names[key] = card.id

    for card in loaded.all_cards:
        _check_card(card, report)
        # Dangling bioisostere references (advisory: target may be unauthored).
        for bio in card.bioisosteres:
            if bio not in seen_ids:
                report.add(
                    Severity.WARNING,
                    f"{card.deck}/{card.id}",
                    f"bioisostere '{bio}' is not a known card id",
                )

    return report

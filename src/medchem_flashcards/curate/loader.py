"""Load and validate authored content from the ``content/`` directory.

Layout::

    content/
      <deck-id>/
        deck.yaml          # DeckMeta
        <card-id>.yaml     # CardContent (one per card)

Loading is pure (no RDKit): it parses YAML and validates against the Pydantic
schema, raising :class:`ContentError` with a file-qualified message on failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import ValidationError

from medchem_flashcards.schema.card import CardContent
from medchem_flashcards.schema.deck import DeckMeta


class ContentError(Exception):
    """Raised when a content file is malformed or fails schema validation."""


@dataclass(frozen=True)
class LoadedDeck:
    meta: DeckMeta
    cards: list[CardContent]
    source_dir: Path


@dataclass
class LoadResult:
    decks: list[LoadedDeck] = field(default_factory=list)

    @property
    def all_cards(self) -> list[CardContent]:
        return [c for d in self.decks for c in d.cards]


def _read_yaml(path: Path) -> dict[str, object]:
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ContentError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ContentError(f"{path}: expected a mapping at the top level")
    return data


def load_deck(deck_dir: Path) -> LoadedDeck:
    """Load a single deck directory into validated models."""
    meta_path = deck_dir / "deck.yaml"
    if not meta_path.exists():
        raise ContentError(f"{deck_dir}: missing deck.yaml")
    try:
        meta = DeckMeta.model_validate(_read_yaml(meta_path))
    except ValidationError as exc:
        raise ContentError(f"{meta_path}: {exc}") from exc

    cards: list[CardContent] = []
    for card_path in sorted(deck_dir.glob("*.yaml")):
        if card_path.name == "deck.yaml":
            continue
        try:
            card = CardContent.model_validate(_read_yaml(card_path))
        except ValidationError as exc:
            raise ContentError(f"{card_path}: {exc}") from exc
        if card.deck != meta.id:
            raise ContentError(
                f"{card_path}: card.deck '{card.deck}' does not match deck id '{meta.id}'"
            )
        if card.id != card_path.stem:
            raise ContentError(
                f"{card_path}: card.id '{card.id}' does not match filename '{card_path.stem}'"
            )
        cards.append(card)

    return LoadedDeck(meta=meta, cards=cards, source_dir=deck_dir)


def load_content(content_dir: Path) -> LoadResult:
    """Load every deck under ``content_dir`` (directories with a deck.yaml)."""
    if not content_dir.exists():
        raise ContentError(f"content directory not found: {content_dir}")
    result = LoadResult()
    for deck_dir in sorted(p for p in content_dir.iterdir() if p.is_dir()):
        if not (deck_dir / "deck.yaml").exists():
            continue
        result.decks.append(load_deck(deck_dir))
    return result

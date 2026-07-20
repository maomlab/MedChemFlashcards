"""Deck metadata schema (authored as ``content/<deck>/deck.yaml``)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from medchem_flashcards.schema.card import NonEmpty, Slug, _Strict


class DeckMeta(_Strict):
    """Metadata for a deck. Card membership is derived from files on disk."""

    id: Slug
    title: NonEmpty
    description: NonEmpty
    order: int = 0
    level: Literal["intro", "core", "advanced"] = "core"
    prerequisites: list[Slug] = Field(default_factory=list)

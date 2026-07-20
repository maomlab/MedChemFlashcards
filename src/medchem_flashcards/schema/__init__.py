"""Canonical data schema for MedChem Flashcards.

The Pydantic models here are the single source of truth. Authored content in
``content/*.yaml`` is validated against :class:`CardContent`; the ingestion
pipeline produces :class:`EnrichedCard` (content + RDKit-computed properties +
rendered SVG) for storage and serving. ``export_schema.py`` emits versioned JSON
Schema from these models.
"""

from __future__ import annotations

from medchem_flashcards.schema.card import (
    CardContent,
    ComputedProperties,
    CuratedProperties,
    Depiction,
    EnrichedCard,
    Example,
    Provenance,
    Reference,
)
from medchem_flashcards.schema.deck import DeckMeta

__all__ = [
    "CardContent",
    "ComputedProperties",
    "CuratedProperties",
    "DeckMeta",
    "Depiction",
    "EnrichedCard",
    "Example",
    "Provenance",
    "Reference",
]

SCHEMA_VERSION = "1.0.0"

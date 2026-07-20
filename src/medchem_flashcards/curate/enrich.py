"""Enrich authored cards with RDKit-computed properties and a rendered SVG."""

from __future__ import annotations

from medchem_flashcards.chem.depict import render_svg
from medchem_flashcards.chem.matching import parse_smiles
from medchem_flashcards.chem.properties import compute_properties
from medchem_flashcards.schema.card import CardContent, EnrichedCard


def enrich_card(card: CardContent) -> EnrichedCard:
    """Compute descriptors and render the highlighted depiction for a card.

    Raises :class:`~medchem_flashcards.chem.ChemError` if the representative
    SMILES cannot be parsed.
    """
    mol = parse_smiles(card.representative_smiles)
    computed = compute_properties(mol)
    svg = render_svg(card.representative_smiles, card.effective_highlight_smarts)
    return EnrichedCard(**card.model_dump(), computed=computed, svg=svg)

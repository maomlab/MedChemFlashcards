"""Tests for the Pydantic content schema."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from medchem_flashcards.schema.card import CardContent, Provenance


def _minimal_card(**overrides: object) -> dict:
    data: dict = {
        "id": "carboxylic-acid",
        "deck": "common-functional-groups",
        "name": "Carboxylic Acid",
        "smarts": "[CX3](=O)[OX2H1]",
        "representative_smiles": "CC(=O)O",
        "relevance": "Ionizable acidic group.",
    }
    data.update(overrides)
    return data


def test_minimal_card_valid() -> None:
    card = CardContent.model_validate(_minimal_card())
    assert card.difficulty == 1
    assert card.effective_highlight_smarts == "[CX3](=O)[OX2H1]"


def test_highlight_smarts_override() -> None:
    card = CardContent.model_validate(_minimal_card(depiction={"highlight_smarts": "[OX2H1]"}))
    assert card.effective_highlight_smarts == "[OX2H1]"


def test_slug_validation_rejects_bad_id() -> None:
    with pytest.raises(ValidationError):
        CardContent.model_validate(_minimal_card(id="Carboxylic Acid"))


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        CardContent.model_validate(_minimal_card(typo_field="x"))


def test_difficulty_bounds() -> None:
    with pytest.raises(ValidationError):
        CardContent.model_validate(_minimal_card(difficulty=6))


def test_provenance_requires_exactly_one_of_source_or_ref() -> None:
    with pytest.raises(ValidationError):
        Provenance.model_validate({"field": "smarts"})
    with pytest.raises(ValidationError):
        Provenance.model_validate({"field": "smarts", "source": "rdkit", "ref": "x"})
    ok = Provenance.model_validate({"field": "smarts", "source": "rdkit"})
    assert ok.source == "rdkit"


def test_provenance_ref_must_resolve() -> None:
    with pytest.raises(ValidationError, match="not defined in references"):
        CardContent.model_validate(
            _minimal_card(provenance=[{"field": "typical_pka", "ref": "missing"}])
        )
    card = CardContent.model_validate(
        _minimal_card(
            references=[{"id": "silverman-2014", "citation": "Silverman & Holladay 2014"}],
            provenance=[{"field": "typical_pka", "ref": "silverman-2014"}],
        )
    )
    assert card.provenance[0].ref == "silverman-2014"

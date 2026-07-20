"""Tests for content loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from medchem_flashcards.curate.loader import ContentError, load_content

DECK_YAML = """
id: common-functional-groups
title: Common Functional Groups
description: Everyday functional groups in drug-like molecules.
order: 1
level: intro
"""

CARD_YAML = """
id: carboxylic-acid
deck: common-functional-groups
name: Carboxylic Acid
smarts: "[CX3](=O)[OX2H1]"
representative_smiles: "CC(=O)O"
relevance: Ionizable acidic group.
"""


def _write_deck(root: Path) -> None:
    deck = root / "common-functional-groups"
    deck.mkdir(parents=True)
    (deck / "deck.yaml").write_text(DECK_YAML)
    (deck / "carboxylic-acid.yaml").write_text(CARD_YAML)


def test_load_content_ok(tmp_path: Path) -> None:
    _write_deck(tmp_path)
    result = load_content(tmp_path)
    assert len(result.decks) == 1
    assert result.decks[0].meta.title == "Common Functional Groups"
    assert [c.id for c in result.all_cards] == ["carboxylic-acid"]


def test_filename_must_match_id(tmp_path: Path) -> None:
    deck = tmp_path / "common-functional-groups"
    deck.mkdir(parents=True)
    (deck / "deck.yaml").write_text(DECK_YAML)
    (deck / "wrong-name.yaml").write_text(CARD_YAML)
    with pytest.raises(ContentError, match="does not match filename"):
        load_content(tmp_path)


def test_deck_id_must_match(tmp_path: Path) -> None:
    deck = tmp_path / "common-functional-groups"
    deck.mkdir(parents=True)
    (deck / "deck.yaml").write_text(DECK_YAML)
    (deck / "carboxylic-acid.yaml").write_text(
        CARD_YAML.replace("deck: common-functional-groups", "deck: other-deck")
    )
    with pytest.raises(ContentError, match="does not match deck id"):
        load_content(tmp_path)


def test_missing_content_dir(tmp_path: Path) -> None:
    with pytest.raises(ContentError, match="content directory not found"):
        load_content(tmp_path / "nope")

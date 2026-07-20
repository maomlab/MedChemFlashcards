"""Tests for the RDKit cheminformatics core."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from medchem_flashcards.chem import ChemError
from medchem_flashcards.chem.depict import render_svg
from medchem_flashcards.chem.matching import (
    has_match,
    match_atoms,
    matched_atom_indices,
    parse_smiles,
)
from medchem_flashcards.chem.properties import compute_properties_from_smiles


def test_parse_invalid_smiles_raises() -> None:
    with pytest.raises(ChemError):
        parse_smiles("this-is-not-smiles((")


def test_carboxylic_acid_match() -> None:
    mol = parse_smiles("CC(=O)O")
    assert has_match(mol, "[CX3](=O)[OX2H1]")
    assert matched_atom_indices(mol, "[CX3](=O)[OX2H1]") == {1, 2, 3}


def test_properties_acetic_acid() -> None:
    props = compute_properties_from_smiles("CC(=O)O")
    assert props.formula == "C2H4O2"
    assert props.mol_weight == pytest.approx(60.05, abs=0.1)
    assert props.h_donors == 1
    # RDKit CalcNumHBA uses the stricter definition: only the carbonyl O counts
    # for a carboxylic acid (the hydroxyl O is a donor), giving 1, not the
    # Lipinski N+O count of 2.
    assert props.h_acceptors == 1
    assert props.num_rings == 0


def test_render_svg_contains_svg_element() -> None:
    svg = render_svg("CC(=O)O", "[CX3](=O)[OX2H1]")
    assert svg.startswith("<svg")
    assert "</svg>" in svg
    assert not svg.startswith("<?xml")


def test_render_svg_is_deterministic() -> None:
    a = render_svg("c1ccccc1O", "[OX2H1]")
    b = render_svg("c1ccccc1O", "[OX2H1]")
    assert a == b


def test_render_svg_no_highlight_when_pattern_absent() -> None:
    # benzene has no hydroxyl; should still render without error
    svg = render_svg("c1ccccc1", "[OX2H1]")
    assert svg.startswith("<svg")


# --- Property-based invariants -------------------------------------------------

_SIMPLE_SMILES = st.sampled_from(
    ["CCO", "CC(=O)O", "c1ccccc1", "c1ccccc1O", "CCN", "O=C(N)C", "c1ccncc1", "CS(=O)(=O)N"]
)


@given(smiles=_SIMPLE_SMILES)
@settings(max_examples=8, deadline=None)
def test_matched_atoms_are_valid_indices(smiles: str) -> None:
    mol = parse_smiles(smiles)
    n = mol.GetNumAtoms()
    for match in match_atoms(mol, "[#6]"):
        for idx in match:
            assert 0 <= idx < n


@given(smiles=_SIMPLE_SMILES)
@settings(max_examples=8, deadline=None)
def test_properties_are_nonnegative(smiles: str) -> None:
    props = compute_properties_from_smiles(smiles)
    assert props.mol_weight > 0
    assert props.tpsa >= 0
    assert props.h_donors >= 0
    assert props.h_acceptors >= 0
    assert 0.0 <= props.fraction_csp3 <= 1.0

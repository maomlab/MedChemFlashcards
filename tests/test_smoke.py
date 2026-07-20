"""Smoke tests: the package imports and its core dependencies are available."""

from __future__ import annotations


def test_package_imports() -> None:
    import medchem_flashcards

    assert medchem_flashcards.__version__


def test_rdkit_available() -> None:
    from rdkit import Chem

    mol = Chem.MolFromSmiles("CC(=O)O")
    assert mol is not None
    assert mol.GetNumAtoms() == 4

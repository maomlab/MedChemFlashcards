"""Parsing and substructure matching with RDKit."""

from __future__ import annotations

from rdkit import Chem
from rdkit.Chem import Mol

from medchem_flashcards.chem import ChemError


def parse_smiles(smiles: str) -> Mol:
    """Parse a SMILES string into a molecule, or raise :class:`ChemError`."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ChemError(f"invalid SMILES: {smiles!r}")
    return mol


def parse_smarts(smarts: str) -> Mol:
    """Parse a SMARTS pattern into a query molecule, or raise :class:`ChemError`."""
    pattern = Chem.MolFromSmarts(smarts)
    if pattern is None:
        raise ChemError(f"invalid SMARTS: {smarts!r}")
    return pattern


def match_atoms(mol: Mol, smarts: str) -> list[tuple[int, ...]]:
    """Return all substructure matches of ``smarts`` in ``mol`` (atom-index tuples)."""
    pattern = parse_smarts(smarts)
    return [tuple(m) for m in mol.GetSubstructMatches(pattern, uniquify=True)]


def matched_atom_indices(mol: Mol, smarts: str) -> set[int]:
    """Union of all atom indices hit by any match of ``smarts``."""
    return {idx for match in match_atoms(mol, smarts) for idx in match}


def has_match(mol: Mol, smarts: str) -> bool:
    return mol.HasSubstructMatch(parse_smarts(smarts))

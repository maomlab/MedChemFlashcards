"""Compute physicochemical descriptors from a molecule (all RDKit-derived)."""

from __future__ import annotations

from typing import Any, cast

from rdkit.Chem import Crippen, Descriptors, Mol, rdMolDescriptors

from medchem_flashcards.chem.matching import parse_smiles
from medchem_flashcards.schema.card import ComputedProperties

# RDKit's pure-Python descriptor modules attach these functions dynamically, so
# static analysis can't see them; treat the modules as untyped at the boundary.
_descriptors = cast(Any, Descriptors)
_crippen = cast(Any, Crippen)


def compute_properties(mol: Mol) -> ComputedProperties:
    """Compute the standard descriptor set for a molecule."""
    return ComputedProperties(
        formula=rdMolDescriptors.CalcMolFormula(mol),
        mol_weight=round(_descriptors.MolWt(mol), 2),
        clogp=round(_crippen.MolLogP(mol), 2),
        tpsa=round(rdMolDescriptors.CalcTPSA(mol), 2),
        h_donors=rdMolDescriptors.CalcNumHBD(mol),
        h_acceptors=rdMolDescriptors.CalcNumHBA(mol),
        rotatable_bonds=rdMolDescriptors.CalcNumRotatableBonds(mol),
        fraction_csp3=round(rdMolDescriptors.CalcFractionCSP3(mol), 3),
        num_rings=rdMolDescriptors.CalcNumRings(mol),
        num_aromatic_rings=rdMolDescriptors.CalcNumAromaticRings(mol),
    )


def compute_properties_from_smiles(smiles: str) -> ComputedProperties:
    return compute_properties(parse_smiles(smiles))

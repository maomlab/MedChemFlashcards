"""Render 2D SVG depictions with the key functional-group motif highlighted.

Output is deterministic (CoordGen layout, fixed drawing options) so generated
SVGs are diffable and safe to golden-test. The highlight colour is chosen to
read on both light and dark card backgrounds.
"""

from __future__ import annotations

from typing import Any

from rdkit.Chem import Mol, rdCoordGen
from rdkit.Chem.Draw import rdMolDraw2D

from medchem_flashcards.chem.matching import match_atoms, parse_smiles

# A warm amber that stays legible on light and dark backgrounds.
_HIGHLIGHT_RGBA = (0.98, 0.70, 0.20, 0.55)


def _highlight_bonds(mol: Mol, atom_ids: set[int]) -> list[int]:
    bonds: list[int] = []
    for bond in mol.GetBonds():
        if bond.GetBeginAtomIdx() in atom_ids and bond.GetEndAtomIdx() in atom_ids:
            bonds.append(bond.GetIdx())
    return bonds


def render_svg(
    smiles: str,
    highlight_smarts: str | None = None,
    *,
    width: int = 350,
    height: int = 300,
) -> str:
    """Render ``smiles`` to an SVG string, highlighting atoms matching the SMARTS.

    Every distinct match of ``highlight_smarts`` is highlighted. If the pattern
    does not match (or is ``None``), the molecule is drawn without highlighting.
    """
    mol = parse_smiles(smiles)
    rdCoordGen.AddCoords(mol)

    highlight_atoms: list[int] = []
    highlight_bonds: list[int] = []
    if highlight_smarts:
        atom_ids = {idx for match in match_atoms(mol, highlight_smarts) for idx in match}
        highlight_atoms = sorted(atom_ids)
        highlight_bonds = _highlight_bonds(mol, atom_ids)

    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    opts: Any = drawer.drawOptions()  # untyped RDKit draw-options struct
    opts.clearBackground = False
    opts.bondLineWidth = 2
    atom_colors = dict.fromkeys(highlight_atoms, _HIGHLIGHT_RGBA)
    bond_colors = dict.fromkeys(highlight_bonds, _HIGHLIGHT_RGBA)
    rdMolDraw2D.PrepareAndDrawMolecule(
        drawer,
        mol,
        highlightAtoms=highlight_atoms,
        highlightBonds=highlight_bonds,
        highlightAtomColors=atom_colors,
        highlightBondColors=bond_colors,
    )
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    # Strip the XML prolog so the <svg> embeds cleanly inline in HTML.
    if svg.startswith("<?xml"):
        svg = svg[svg.index("<svg") :]
    return svg

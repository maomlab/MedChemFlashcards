"""Render 2D SVG depictions with the key functional-group motif highlighted.

Output is deterministic (CoordGen layout, fixed drawing options) so generated
SVGs are diffable and safe to golden-test. Atoms use RDKit's standard element
(CPK) palette — oxygen red, nitrogen blue, sulfur yellow, and so on.

The motif is highlighted by colouring its *bonds* rather than its atoms: RDKit
recolours highlighted atom labels to a flat colour, which would override the
element colours, so bond-only highlighting keeps every atom its true CPK colour
while still marking the functional group. A single-atom motif (which has no
internal bond) falls back to highlighting that atom's incident bonds so it
remains visible.
"""

from __future__ import annotations

from typing import Any

from rdkit.Chem import Mol, rdCoordGen
from rdkit.Chem.Draw import rdMolDraw2D

from medchem_flashcards.chem.matching import matched_atom_indices, parse_smiles

# A warm amber that stays legible on light and dark backgrounds.
_HIGHLIGHT_RGBA = (0.98, 0.70, 0.20, 0.55)


def _highlight_bonds(mol: Mol, atom_ids: set[int]) -> list[int]:
    """Bonds to highlight for the motif: bonds internal to the matched atom set,
    plus incident bonds of any matched atom that has no internal bond (so a
    single-atom motif still shows a highlight)."""
    bonds: set[int] = set()
    unbonded = set(atom_ids)
    for bond in mol.GetBonds():
        begin, end = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        if begin in atom_ids and end in atom_ids:
            bonds.add(bond.GetIdx())
            unbonded.discard(begin)
            unbonded.discard(end)
    for idx in unbonded:
        for bond in mol.GetAtomWithIdx(idx).GetBonds():
            bonds.add(bond.GetIdx())
    return sorted(bonds)


def render_svg(
    smiles: str,
    highlight_smarts: str | None = None,
    *,
    width: int = 350,
    height: int = 300,
) -> str:
    """Render ``smiles`` to an SVG string with standard CPK atom colours, marking
    the bonds of the ``highlight_smarts`` motif.

    Every distinct match of ``highlight_smarts`` contributes to the highlight. If
    the pattern does not match (or is ``None``), the molecule is drawn plain.
    """
    mol = parse_smiles(smiles)
    rdCoordGen.AddCoords(mol)

    highlight_bonds: list[int] = []
    if highlight_smarts:
        highlight_bonds = _highlight_bonds(mol, matched_atom_indices(mol, highlight_smarts))

    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    opts: Any = drawer.drawOptions()  # untyped RDKit draw-options struct
    opts.clearBackground = False
    opts.bondLineWidth = 2
    bond_colors = dict.fromkeys(highlight_bonds, _HIGHLIGHT_RGBA)
    rdMolDraw2D.PrepareAndDrawMolecule(
        drawer,
        mol,
        highlightAtoms=[],
        highlightBonds=highlight_bonds,
        highlightBondColors=bond_colors,
    )
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    # Strip the XML prolog so the <svg> embeds cleanly inline in HTML.
    if svg.startswith("<?xml"):
        svg = svg[svg.index("<svg") :]
    return svg

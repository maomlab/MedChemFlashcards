"""Cheminformatics core: parsing, matching, properties, and SVG depiction (RDKit)."""

from __future__ import annotations


class ChemError(ValueError):
    """Raised when a SMILES/SMARTS string is invalid or chemistry checks fail."""

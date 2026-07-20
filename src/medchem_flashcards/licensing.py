"""Approved data sources and licensing enforcement.

Mirrors the table in ``LICENSES.md``. The QC pipeline rejects any provenance
whose ``source`` key is not listed here, keeping content redistributable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceLicense:
    key: str
    name: str
    license: str
    attribution: str


APPROVED_SOURCES: dict[str, SourceLicense] = {
    s.key: s
    for s in [
        SourceLicense(
            "rdkit",
            "RDKit",
            "BSD-3-Clause",
            "Powered by RDKit — https://www.rdkit.org",
        ),
        SourceLicense(
            "rdkit-filtercatalog",
            "RDKit FilterCatalog (PAINS/BRENK/NIH/ZINC)",
            "BSD-3-Clause",
            "PAINS: Baell & Holloway (2010); BRENK: Brenk et al. (2008)",
        ),
        SourceLicense(
            "pubchem",
            "PubChem (NIH/NLM)",
            "Public domain",
            "Courtesy of the U.S. National Library of Medicine",
        ),
        SourceLicense(
            "chembl",
            "ChEMBL (EMBL-EBI)",
            "CC BY-SA 3.0",
            "ChEMBL, EMBL-EBI (CC BY-SA 3.0)",
        ),
        SourceLicense(
            "wikidata",
            "Wikidata",
            "CC0 1.0",
            "Wikidata (CC0)",
        ),
        SourceLicense(
            "ertl-2017",
            "Ertl (2017) J. Cheminform.",
            "Open access (CC BY)",
            "Ertl P. (2017) J. Cheminform. 9:36",
        ),
    ]
}


def is_approved(source_key: str) -> bool:
    return source_key in APPROVED_SOURCES

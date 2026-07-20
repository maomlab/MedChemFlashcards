"""Card schema: authored content and its enriched (pipeline-computed) form."""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

Slug = Annotated[str, StringConstraints(pattern=SLUG_RE.pattern, min_length=1)]
NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class _Strict(BaseModel):
    """Base with forbidden extras so typos in authored YAML are caught."""

    model_config = ConfigDict(extra="forbid")


class Reference(_Strict):
    """A literature/citation reference, addressable by ``id`` from provenance."""

    id: Slug
    citation: NonEmpty
    url: str | None = None


class Provenance(_Strict):
    """Attribution for a single non-computed field.

    Exactly one of ``source`` (an approved source key, see ``LICENSES.md``) or
    ``ref`` (an id in the card's ``references``) must be given.
    """

    field: NonEmpty
    source: str | None = None
    ref: str | None = None
    url: str | None = None
    retrieved: date | None = None
    license: str | None = None

    @model_validator(mode="after")
    def _require_source_or_ref(self) -> Provenance:
        if bool(self.source) == bool(self.ref):
            raise ValueError("provenance needs exactly one of 'source' or 'ref'")
        return self


class Example(_Strict):
    """An example molecule (drug or key biomolecule) containing the group."""

    name: NonEmpty
    smiles: NonEmpty
    role: str | None = None
    chembl_id: str | None = None
    pubchem_cid: int | None = None
    wikidata_id: str | None = None


class Depiction(_Strict):
    """Depiction directives. ``highlight_smarts`` defaults to the card SMARTS."""

    highlight_smarts: str | None = None


class CuratedProperties(_Strict):
    """Human-curated physicochemical descriptors.

    Only quantitative, sourceable facts live here (``typical_pka``,
    ``charge_at_ph7_4``) and require provenance. H-bond donor/acceptor counts are
    RDKit-derived (see :class:`ComputedProperties`) and are never hand-authored.
    ``polarity`` is an optional editorial teaching label, not a sourced datum.
    """

    typical_pka: str | None = None
    charge_at_ph7_4: int | None = None
    polarity: Literal["low", "medium", "high"] | None = None
    notes: str | None = None


class ComputedProperties(_Strict):
    """RDKit-derived descriptors, computed from ``representative_smiles``.

    Never hand-authored; the pipeline fills these and attributes them to RDKit.
    """

    formula: str
    mol_weight: float
    clogp: float
    tpsa: float
    h_donors: int
    h_acceptors: int
    rotatable_bonds: int
    fraction_csp3: float
    num_rings: int
    num_aromatic_rings: int


class CardContent(_Strict):
    """A functional-group flashcard as authored in ``content/<deck>/<id>.yaml``."""

    id: Slug
    deck: Slug
    name: NonEmpty
    aliases: list[str] = Field(default_factory=list)
    smarts: NonEmpty
    representative_smiles: NonEmpty
    depiction: Depiction = Field(default_factory=Depiction)
    properties: CuratedProperties = Field(default_factory=CuratedProperties)
    relevance: NonEmpty
    examples: list[Example] = Field(default_factory=list)
    bioisosteres: list[Slug] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    difficulty: int = Field(1, ge=1, le=5)
    references: list[Reference] = Field(default_factory=list)
    provenance: list[Provenance] = Field(default_factory=list)

    @model_validator(mode="after")
    def _refs_resolve(self) -> CardContent:
        ref_ids = {r.id for r in self.references}
        for p in self.provenance:
            if p.ref is not None and p.ref not in ref_ids:
                raise ValueError(f"provenance ref '{p.ref}' not defined in references")
        return self

    @property
    def effective_highlight_smarts(self) -> str:
        return self.depiction.highlight_smarts or self.smarts


class EnrichedCard(CardContent):
    """A card after ingestion: authored content plus computed props and SVG."""

    computed: ComputedProperties
    svg: str

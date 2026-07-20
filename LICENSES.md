# Data sources & licensing

MedChem Flashcards content is derived **only** from open-source, redistributable
databases and software. This file is the authoritative source-to-license map.
The QC pipeline (`medchem qc`) fails the build if a card cites a source that is
absent from this table or flagged non-redistributable.

## Approved sources

| Source key | Source | License | Attribution / notes |
|---|---|---|---|
| `rdkit` | RDKit (functional-group definitions, ring perception, descriptors) | BSD-3-Clause | "Powered by RDKit — https://www.rdkit.org" |
| `rdkit-filtercatalog` | RDKit `FilterCatalog` (PAINS_A/B/C, BRENK, NIH, ZINC) | BSD-3-Clause | PAINS from Baell & Holloway (2010) J. Med. Chem.; BRENK from Brenk et al. (2008) ChemMedChem |
| `pubchem` | PubChem (NIH/NLM) | Public domain (works of the U.S. government) | Cite PubChem CID; https://pubchem.ncbi.nlm.nih.gov |
| `chembl` | ChEMBL (EMBL-EBI) | CC BY-SA 3.0 | Attribution + share-alike; cite ChEMBL ID and release |
| `wikidata` | Wikidata | CC0 1.0 | No attribution required; cite Q-id for traceability |
| `ertl-2017` | Ertl (2017) "An algorithm to identify functional groups in organic molecules" | Open-access article | J. Cheminform. 9:36 |

## Literature references

Curated facts that are not machine-derived (e.g., typical pKa, therapeutic role)
cite a reference by `ref:` key defined in the card's `references` block. Prefer
open-access sources; textbook citations are permitted for well-established
chemistry facts.

## Rules

1. Every non-computed field needs a `provenance` entry naming a `source key`
   above **or** a `ref:` literature citation.
2. Computed properties (MW, cLogP, TPSA, HBD/HBA, etc.) are attributed to
   `rdkit` automatically by the pipeline — do not hand-author them.
3. Do **not** ingest license-restricted databases (e.g., DrugBank academic
   license, SwissBioisostere terms). If in doubt, leave it out and cite the
   primary literature instead.
4. ChEMBL's CC BY-SA propagates to derived content: attributions are surfaced in
   the app UI and in exported decks.

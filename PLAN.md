# MedChem Flashcards — Development & Implementation Plan

> Companion to `OBJECTIVES.md`. This plan turns the objectives into a concrete,
> phased build with named technologies, a data schema, a data-sourcing strategy,
> and a testing/QC approach. Decisions marked **[confirm]** are the few genuine
> forks worth a quick sign-off before or during the relevant phase.

---

## 0. Implementation status (2026-07-20)

| Phase | Status |
|---|---|
| 0 — Scaffolding & tooling (uv, ruff, mypy, pytest, nox, CI) | ✅ done |
| 1 — Schema & data model (Pydantic + JSON Schema + SQLAlchemy) | ✅ done |
| 2 — Cheminformatics core (RDKit properties + highlighted SVG) | ✅ done |
| 3 — Curation pipeline & QC (provenance/licensing gate) | ✅ done |
| 4 — Seed content (168 cards across 11 decks) | ✅ done |
| 5 — Backend API (FastAPI: decks, cards, SVG) | ✅ done |
| 6 — Frontend SPA (React + TS + Vite deck/card views) | ✅ done |
| 7 — Spaced repetition (FSRS + localStorage study loop) | ✅ done |
| 8 — Auth & progress sync (accounts, JWT, server-side merge) | ✅ done |
| 9 — Packaging & deploy (Docker image, FastAPI-served SPA, offline PWA) | ✅ done |

Quality gates all green: `ruff`, `mypy --strict` (30 files), 41 pytest tests,
7 vitest tests, frontend `tsc`/build. The 168 authored cards pass the
provenance/licensing QC gate (0 errors, 0 warnings).

**Scheduler.** Upgraded from SM-2 to **FSRS-4.5** (stability/difficulty model,
published default weights). The backend stores scheduler state as an opaque JSON
blob (`Progress.state`) so future algorithm changes need no DB migration.

**Content (168 cards, 11 decks).** Common Functional Groups 40 · Aromatic
Heterocycles 22 · Bioisosteres 10 · PAINS & Reactive 16 · MedChem Tools 14 ·
Saturated Heterocycles 9 · Amino Acid Side Chains 20 (all proteinogenic) ·
Phosphorus & Sulfur Groups 9 · Nucleobases & Nucleotides 10 · Privileged
Scaffolds 10 · Halogen & Fluorine Motifs 8. The six decks beyond the original
five broaden scope to ring systems, biomolecule side chains, nucleic-acid
components, recurring drug scaffolds, and halogen/P/S motifs. Amino-acid and
sugar cards highlight just the characteristic motif on the parent molecule.

**Packaging.** Multi-stage `Dockerfile` (Node build of the SPA → Python runtime
with RDKit, content DB baked in at build time, SPA served by FastAPI, user DB on
a `/data` volume). Basic offline **PWA** (manifest, icon, runtime-caching service
worker). Note: the Docker image was not built in the dev environment (no running
daemon); the lockfile is verified in sync so the `--frozen` install is valid.

**Auth architecture note.** User accounts and review progress live in a
**separate SQLite database** (`$MEDCHEM_USER_DB`, default `data/users.db`) from
the content database (`$MEDCHEM_DB`), because the content DB is a disposable
build artifact that `medchem ingest` drops and rebuilds. Passwords are argon2
hashed; sessions are JWTs (`$MEDCHEM_SECRET`); progress sync merges client and
server state per card by most-recent review (last-reviewed-wins). Anonymous use
remains fully functional — login only adds cross-device persistence.

All nine phases are implemented. Natural next steps beyond this plan: further
content growth and expert review, PNG PWA icons for broader install support, an
actual Docker image build in CI, and optional FSRS parameter optimization from
real review logs.

## 1. Product summary

A local-or-hosted flashcard app that teaches medicinal-chemistry functional
groups to cheminformatics/drug-discovery researchers, using spaced repetition.
Content is organized into decks (Common Functional Groups, Aromatic
Heterocycles, Bioisosteres, PAINS & Reactive Groups, Medicinal Chemistry Tools).
Each card carries a name, a high-quality 2D SVG depiction with the key motif
highlighted, physicochemical properties, functional relevance, and example
drugs/biomolecules. Data is curated from reliable databases via an RDKit
pipeline, stored as validated JSON and loaded into SQLite, and served to a
JavaScript single-page app. Users can learn anonymously or log in to persist
progress.

---

## 2. Architecture at a glance

```
 content/                RDKit curation          SQLite            FastAPI            SPA (browser)
 *.yaml/json  ──ingest──▶  + QC + provenance ──▶  medchem.db  ──▶  REST/JSON  ──▶  React + TS
 (authored)               (Pydantic-validated)   (SQLAlchemy)      (Pydantic)       (FSRS scheduler)
                                                                                     localStorage / sync
```

- **Content** is authored as human-readable YAML/JSON files under version control
  (source of truth), not hand-edited in the database.
- An **ingestion + QC pipeline** validates each card against a Pydantic/JSON
  Schema, computes properties with RDKit, renders SVGs, checks provenance, and
  loads everything into SQLite.
- The **backend** is a typed Python package that both owns the pipeline and
  serves a read-mostly REST API (plus write endpoints for progress/auth).
- The **frontend** is a TypeScript SPA that renders cards, runs the spaced-
  repetition scheduler locally, and syncs progress to the backend when logged in.

---

## 3. Technology choices

| Layer | Choice | Rationale |
|---|---|---|
| Package/env mgmt | **uv** (required by objectives), `src/` layout, `pyproject.toml` | Fast, reproducible, lockfile-based |
| Cheminformatics | **RDKit** (via `rdkit` wheels) | SMILES/SMARTS parsing, 2D coords, SVG drawing, substructure highlight, property calc, PAINS FilterCatalog |
| Data validation | **Pydantic v2** | Single source for JSON Schema + runtime validation + API models |
| ORM / DB | **SQLAlchemy 2.0 (typed)** + **SQLite**, **Alembic** migrations | Required stack; typed ORM pairs with mypy |
| API | **FastAPI** + **uvicorn** | Async, auto OpenAPI docs, Pydantic-native |
| Lint/format | **ruff** (lint + format) | One tool, fast |
| Typecheck | **mypy** (strict) — optionally pyright in editor | Enforces the "typechecking" objective |
| Tests | **pytest**, `pytest-cov`, `hypothesis` (property tests for chem invariants) | Standard, strong |
| Task runner | **nox** (or `poe`/Makefile) | Reproducible dev/QC/CI tasks |
| Pre-commit | **pre-commit** (ruff, mypy, schema check) | Guardrails |
| Frontend | **React + TypeScript + Vite** | "Clean SPA"; mature, easy local run & static hosting **[confirm]** |
| Styling | **Tailwind CSS** + Headless UI (or shadcn/ui) | Fast, consistent, accessible |
| SR algorithm | **FSRS** (fallback SM-2) | Modern, better retention than SM-2 |
| Client storage | **localStorage/IndexedDB** (anon) → sync to API (logged in) | Works without login per objectives |
| Auth | **FastAPI + session or JWT**, `passlib`/`argon2`; optional OAuth later | Optional login; keep minimal in v1 |
| CI | **GitHub Actions** (lint, typecheck, test, schema validate, build) | Standard |

**[confirm] Frontend framework.** React+TS+Vite is the recommendation. Lighter
alternatives (Svelte/SvelteKit, or vanilla TS + Lit) are viable if you prefer a
smaller footprint. React chosen for ecosystem (KaTeX/chem widgets, component
libraries) and hiring familiarity.

---

## 4. Repository layout

```
medchem_flashcards/
├── OBJECTIVES.md
├── PLAN.md
├── pyproject.toml            # uv project, deps, tool config (ruff/mypy/pytest)
├── uv.lock
├── noxfile.py
├── .pre-commit-config.yaml
├── .github/workflows/ci.yml
├── README.md
├── src/medchem_flashcards/
│   ├── __init__.py
│   ├── schema/               # Pydantic models = canonical JSON Schema
│   │   ├── card.py           # FunctionalGroupCard, Example, Property, Provenance
│   │   ├── deck.py           # Deck metadata
│   │   └── export_schema.py  # dumps JSON Schema to schema/*.json
│   ├── chem/                 # RDKit wrappers
│   │   ├── depict.py         # SMILES/SMARTS → highlighted SVG
│   │   ├── properties.py     # MW, cLogP, TPSA, HBD/HBA, rings, charge@pH7
│   │   └── matching.py       # substructure match / validation
│   ├── curate/               # ingestion + QC pipeline
│   │   ├── ingest.py         # YAML/JSON → validate → enrich → SQLite
│   │   ├── qc.py             # consistency checks, provenance audit, reports
│   │   └── sources.py        # source adapters (PubChem/ChEMBL/RDKit catalogs)
│   ├── db/
│   │   ├── models.py         # SQLAlchemy ORM
│   │   ├── session.py
│   │   └── migrations/       # Alembic
│   ├── api/
│   │   ├── main.py           # FastAPI app
│   │   ├── routers/          # decks, cards, review, auth, progress
│   │   ├── deps.py
│   │   └── security.py
│   └── srs/                  # server-side scheduling helpers (optional; client is primary)
├── content/                  # authored decks (source of truth)
│   ├── common-functional-groups/
│   │   └── carboxylic-acid.yaml ...
│   ├── aromatic-heterocycles/
│   ├── bioisosteres/
│   ├── pains-reactive-groups/
│   └── medchem-tools/
├── schema/                   # generated JSON Schema (published artifact)
├── assets/svg/               # generated depictions (or served from DB)
├── data/medchem.db           # built SQLite (gitignored; reproducible)
├── tests/                    # pytest (unit + integration + schema)
└── frontend/                 # Vite React TS app
    ├── package.json
    ├── src/
    │   ├── api/              # typed client generated from OpenAPI
    │   ├── srs/              # FSRS scheduler + local persistence
    │   ├── components/       # Card, DeckList, ReviewSession, SvgViewer
    │   ├── pages/
    │   └── store/
    └── index.html
```

---

## 5. Data schema (canonical, Pydantic-generated JSON Schema)

Each functional-group card, authored in YAML, validated on ingest. Example:

```yaml
id: carboxylic-acid
deck: common-functional-groups
name: Carboxylic Acid
aliases: [carboxyl]
smarts: "[CX3](=O)[OX2H1]"          # defines the motif for matching/highlighting
representative_smiles: "CC(=O)O"     # a minimal molecule showing the group
depiction:
  highlight_smarts: "[CX3](=O)[OX2H1]"   # atoms/bonds to highlight (defaults to smarts)
  # svg generated by pipeline → assets/svg/carboxylic-acid.svg
properties:                          # curated + RDKit-computed (marked source)
  typical_pka: {value: "4–5", source_ref: silverman-2014}
  hbond_donor: true
  hbond_acceptor: true
  charge_at_ph7.4: -1
  polarity: high
relevance: >
  Ionizable acidic group; drives aqueous solubility and salt-bridge binding.
  Prominent in NSAIDs. Metabolic liabilities include acyl glucuronidation.
examples:
  - {name: Ibuprofen, smiles: "CC(C)Cc1ccc(cc1)C(C)C(=O)O", chembl_id: CHEMBL521, role: NSAID}
  - {name: Aspirin,   smiles: "CC(=O)Oc1ccccc1C(=O)O",      chembl_id: CHEMBL25,  role: NSAID}
bioisosteres: [tetrazole, acyl-sulfonamide, oxadiazolone]
tags: [acidic, ionizable, hydrogen-bonding]
difficulty: 1
provenance:                          # every non-computed fact is attributable
  - {field: smarts, source: "RDKit Functional Group definitions", url: "...", retrieved: 2026-07-20, license: BSD-3-Clause}
  - {ref: silverman-2014, citation: "Silverman & Holladay, The Organic Chemistry of Drug Design, 3rd ed."}
references:
  - {id: silverman-2014, citation: "..."}
```

Deck metadata (`deck.yaml`): `id`, `title`, `description`, `order`, `level`,
`prerequisites`, `card_ids`.

**Design rules**
- Computed properties (MW, TPSA, cLogP, HBD/HBA from RDKit) are recomputed on
  ingest and never hand-authored — reproducibility over trust.
- Every hand-entered fact needs a `provenance` entry (source + retrieved date +
  license). QC fails the build if a required field lacks provenance.
- The Pydantic models are the single source of truth; `export_schema.py` emits
  versioned JSON Schema into `schema/` (published for external contributors).

---

## 6. Data sourcing & licensing strategy

Reliability and clean licensing are first-class requirements.

| Data | Preferred open source | Notes |
|---|---|---|
| Functional-group SMARTS | RDKit FunctionalGroups fdef, Ertl functional-group algorithm, Checkmol/matched patterns | Open; the backbone of the "Common Functional Groups" deck |
| Aromatic heterocycles | RDKit ring perception + curated list from open textbooks/reviews | Compute ring properties; cite text sources |
| PAINS / reactive groups | **RDKit `FilterCatalog`** (PAINS_A/B/C, BRENK, NIH, ZINC) | Directly available in RDKit; ideal, well-cited |
| Bioisosteres | Hand-curated from open review literature; note SwissBioisostere/DrugBank are **license-restricted** — do **not** ingest | **[confirm]** curation effort; start with a small vetted set |
| Example drugs/biomolecules | **ChEMBL** (CC BY-SA), **PubChem** (public domain), Wikidata (CC0) | Avoid DrugBank (non-commercial license) |
| Physicochemical properties | **Computed with RDKit** (MW, cLogP, TPSA, HBD/HBA, rotatable bonds, fraction Csp3, aromatic rings) | Reproducible; pKa only as curated literature values (RDKit doesn't predict pKa) |

**Licensing guardrails:** maintain a `LICENSES.md` mapping each source to its
license; the QC step blocks ingest of any source flagged non-redistributable.
ChEMBL's CC BY-SA implies attribution + share-alike for derived content —
surface attributions in the UI and docs.

---

## 7. Phased delivery

Each phase ends with green CI (lint + mypy + tests) and a runnable artifact.

### Phase 0 — Scaffolding & tooling (foundation)
- `uv init` (`src/` layout), configure ruff/mypy(strict)/pytest/coverage in
  `pyproject.toml`, add `nox` sessions (`lint`, `typecheck`, `test`, `schema`,
  `ingest`), pre-commit, and GitHub Actions CI.
- `README.md` with dev quickstart (`uv sync`, `nox`).
- **Exit:** `nox` passes on an empty skeleton with a smoke test.

### Phase 1 — Schema & data model
- Pydantic models for Card/Deck/Example/Property/Provenance; `export_schema.py`
  emits versioned JSON Schema. SQLAlchemy ORM + first Alembic migration.
- Round-trip tests: YAML → Pydantic → ORM → query.
- **Exit:** schema published in `schema/`; empty DB builds via migration.

### Phase 2 — Cheminformatics core (RDKit)
- `chem/depict.py`: SMILES → 2D coords → SVG (rdMolDraw2D) with the
  `highlight_smarts` atoms/bonds highlighted (color-coded, legible, dark/light
  friendly). Deterministic output (fixed coordgen options) for diff-able SVGs.
- `chem/properties.py`: descriptor calculations. `chem/matching.py`: validate
  SMARTS parses and matches `representative_smiles`.
- Tests incl. Hypothesis property tests (e.g., "highlight atoms ⊆ molecule
  atoms", "valid SMILES yields non-empty SVG").
- **Exit:** given a card YAML, produce a correct highlighted SVG + property set.

### Phase 3 — Curation pipeline & QC
- `curate/ingest.py`: discover content files → validate → enrich (SVG +
  computed props) → upsert to SQLite. Idempotent, incremental.
- `curate/qc.py`: report duplicates (by SMARTS/name), unparseable SMILES/SMARTS,
  missing/danging provenance, cross-references (bioisostere ids resolve), license
  violations. Emits a human-readable QC report + non-zero exit on hard failures.
- `curate/sources.py`: adapters for RDKit FilterCatalog and optional
  PubChem/ChEMBL enrichment (cached, offline-friendly, rate-limited).
- **Exit:** `nox -s ingest` builds `data/medchem.db` from `content/` with a clean
  QC report.

### Phase 4 — Seed content (vertical slice)
- Author the **Common Functional Groups** deck fully (~30–50 cards) as the
  reference deck. Add 3–5 cards each for the other four decks to prove structure.
- This is the pipeline's real test and de-risks schema gaps early.
- **Exit:** one complete deck + skeletons of the rest, all passing QC.

### Phase 5 — Backend API (FastAPI)
- Read endpoints: `GET /decks`, `GET /decks/{id}`, `GET /cards/{id}`,
  `GET /cards/{id}/svg`, `GET /schema`. Pydantic response models; OpenAPI at
  `/docs`. CORS for the SPA. Serve SVGs (from DB or `assets/`).
- Integration tests with `httpx`/`TestClient` against a seeded temp DB.
- **Exit:** SPA-ready API returning real deck data.

### Phase 6 — Frontend SPA (read path)
- Vite React TS app: deck browser, card detail (SVG + properties + relevance +
  examples), search/filter. Generate a typed API client from OpenAPI.
- Runs locally (`npm run dev`) and builds to static assets hostable anywhere;
  document serving the built SPA from FastAPI too.
- **Exit:** browse decks and view cards end-to-end.

### Phase 7 — Spaced repetition engine
- Implement **FSRS** client-side; a `ReviewSession` flow (show prompt → reveal →
  grade Again/Hard/Good/Easy → schedule). Persist state in IndexedDB/localStorage
  for anonymous users. Deck-scoped and cross-deck review modes; randomized order.
- **[confirm] card front/back design:** e.g., front = SVG with motif highlighted,
  back = name + properties + relevance; plus reverse mode (name → draw/recognize).
- Unit tests for the scheduler (interval progression, lapses).
- **Exit:** a full anonymous study loop with persistence across reloads.

### Phase 8 — Auth & progress sync (optional login)
- Minimal accounts (email+password, argon2) with JWT/session; `POST /auth/*`.
- `GET/PUT /progress` to store per-user review state; client syncs local →
  server on login and merges. Anonymous remains fully functional.
- Security review: authz on progress endpoints, rate limiting, input validation.
- **Exit:** log in, progress persists server-side and syncs across devices.

### Phase 9 — Content scale-up, packaging & deploy
- Flesh out remaining decks to target counts; expand QC coverage.
- Package: `uvx`/console-script to run the server; Docker image bundling SPA +
  API + prebuilt DB; docs for local run and hosted deploy.
- Optional: static/offline PWA build for pure client-side use (bundle DB as JSON).
- **Exit:** one-command run locally and a deployable image.

---

## 8. Cross-cutting concerns

- **Testing:** unit (chem, schema, srs), integration (pipeline, API), property
  tests (chem invariants), and a golden-file test for a few SVGs to catch
  rendering regressions. Target meaningful coverage on `chem/`, `curate/`, `api/`.
- **Reproducibility:** DB and SVGs are build artifacts regenerated from
  `content/` + code; nothing hand-edited downstream. Pin RDKit version (SVG
  output can shift between versions).
- **Provenance/QC as gates:** CI runs `ingest` + `qc` on every PR; missing
  provenance or license violations fail the build.
- **Accessibility & theming:** legible SVG highlight colors in light/dark;
  keyboard-driven review; ARIA on interactive controls.
- **Versioning:** semver the JSON Schema; migrations for DB; content changes
  reviewed like code.

---

## 9. Key decisions to confirm

1. **Frontend framework** — React+TS+Vite (recommended) vs. Svelte vs. lightweight
   vanilla/Lit.
2. **Auth scope for v1** — ship anonymous-only first and add accounts in Phase 8
   (recommended), or make login part of the initial release.
3. **Bioisosteres sourcing** — how much hand-curation to invest given that the
   best databases (SwissBioisostere, DrugBank) are license-restricted; start with
   a small vetted literature set?
4. **SVG storage** — store generated SVGs in SQLite (single-file portability) vs.
   as files under `assets/` (simpler diffing/CDN). Recommendation: store in DB for
   portability, keep a file export for review.
5. **Deck size targets** — proposed ~30–50 cards for Common Functional Groups;
   confirm scope per deck for v1.

---

## 10. Suggested immediate next steps

1. Confirm decisions in §9 (or accept the recommendations).
2. Execute **Phase 0** scaffolding (uv project, tooling, CI).
3. Execute **Phases 1–2** to stand up the schema + RDKit depiction/property core.
4. Build the **Phase 4** vertical slice (one full deck) to validate the pipeline
   before scaling content and adding the API/SPA.

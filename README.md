# MedChem Flashcards

Spaced-repetition flashcards that teach medicinal-chemistry functional groups to
cheminformatics and drug-discovery researchers. Content is curated from
open-source chemistry databases with an RDKit pipeline, validated against a JSON
schema, stored in SQLite, served by FastAPI, and studied in a JavaScript SPA.

See [`OBJECTIVES.md`](OBJECTIVES.md) for goals and [`PLAN.md`](PLAN.md) for the
full implementation plan.

## Requirements

- [uv](https://docs.astral.sh/uv/) for Python environment/dependency management
- Python >= 3.10 (RDKit wheels)
- Node >= 18 (frontend, later phases)

## Quickstart

```bash
uv sync                     # create venv, install deps (incl. dev group)
uv run nox                  # run lint + typecheck + tests
uv run medchem --help       # CLI entry point
```

### Common tasks (via nox)

```bash
uv run nox -s lint          # ruff check + format --check
uv run nox -s typecheck     # mypy (strict)
uv run nox -s test          # pytest with coverage
uv run nox -s schema        # export JSON Schema to schema/
uv run nox -s ingest        # build data/medchem.db from content/
uv run nox -s qc            # run data QC report over content/
```

## Running the full app

Build the content database, then either run the two dev servers or serve the
built SPA directly from FastAPI.

```bash
# 1. Build the SQLite database (+ SVGs) from authored content
uv run medchem ingest

# 2a. Development: API on :8000 + hot-reloading SPA on :5173 (proxies /api)
uv run medchem serve --reload           # terminal 1
cd frontend && npm install && npm run dev  # terminal 2, open http://localhost:5173

# 2b. Single-command: build the SPA once, FastAPI serves it at /
cd frontend && npm install && npm run build && cd ..
uv run medchem serve                    # open http://127.0.0.1:8000
```

The API is documented at `/docs` (OpenAPI). Study progress is stored in the
browser (localStorage) so anonymous users keep their spaced-repetition state.
Optionally, users can register/log in to sync progress across devices.

### Accounts & configuration

Accounts and progress are stored in a **separate** database from content so that
rebuilding content never touches user data.

| Env var | Default | Purpose |
|---|---|---|
| `MEDCHEM_DB` | `data/medchem.db` | Content database (rebuilt by `medchem ingest`) |
| `MEDCHEM_USER_DB` | `data/users.db` | Accounts + progress (persistent) |
| `MEDCHEM_SECRET` | dev fallback | JWT signing secret — **set a strong value in production** |
| `MEDCHEM_SPA_DIR` | `frontend/dist` | Built SPA directory FastAPI serves at `/` |

Passwords are argon2-hashed; sessions are JWTs. Anonymous use is fully
functional — logging in only adds cross-device persistence, merging local and
server progress per card by most-recent review. Scheduling uses **FSRS-4.5**;
the app is a **PWA** and works offline for previously viewed content.

## Docker

A multi-stage build compiles the SPA, installs the Python runtime (with RDKit),
bakes the content database into the image, and serves everything from FastAPI.

```bash
docker build -t medchem-flashcards .
docker run -p 8000:8000 \
  -e MEDCHEM_SECRET="$(openssl rand -hex 32)" \
  -v medchem-users:/data \
  medchem-flashcards
# open http://localhost:8000
```

User accounts/progress persist in the `/data` volume; the content database is
rebuilt into the image on every build, so it never collides with user data.

## Data sourcing & attribution

Content is derived only from open-source, redistributable databases. Every
hand-entered fact carries provenance (source, retrieval date, license); the QC
step fails the build if provenance or licensing is missing. See
[`LICENSES.md`](LICENSES.md) for the source-to-license map and required
attributions.

## License

Code is MIT (see `pyproject.toml`). Curated content inherits the licenses of its
upstream sources — consult `LICENSES.md` before redistributing.

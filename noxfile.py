"""Task runner for MedChem Flashcards.

Run everything with ``uv run nox`` or a single session with
``uv run nox -s <name>``. Sessions reuse the uv-managed environment so they run
against the locked dependency set.
"""

from __future__ import annotations

import nox

nox.options.default_venv_backend = "uv"
nox.options.sessions = ["lint", "typecheck", "test"]

PYTHON = "3.10"


@nox.session(python=PYTHON)
def lint(session: nox.Session) -> None:
    """Ruff lint + format check."""
    session.install("ruff")
    session.run("ruff", "check", "src", "tests", "noxfile.py")
    session.run("ruff", "format", "--check", "src", "tests", "noxfile.py")


@nox.session(python=PYTHON)
def typecheck(session: nox.Session) -> None:
    """Static type checking with mypy (strict)."""
    session.install("-e", ".", "mypy", "types-PyYAML", "pydantic")
    session.run("mypy", "src")


@nox.session(python=PYTHON)
def test(session: nox.Session) -> None:
    """Run the test suite with coverage."""
    session.install("-e", ".")
    session.install("pytest", "pytest-cov", "hypothesis")
    session.run("pytest", "--cov", "--cov-report=term-missing", *session.posargs)


@nox.session(python=PYTHON)
def schema(session: nox.Session) -> None:
    """Export the canonical JSON Schema from the Pydantic models."""
    session.install("-e", ".")
    session.run("python", "-m", "medchem_flashcards.schema.export_schema")


@nox.session(python=PYTHON)
def ingest(session: nox.Session) -> None:
    """Build the SQLite database from the authored content/ directory."""
    session.install("-e", ".")
    session.run("medchem", "ingest", *session.posargs)


@nox.session(python=PYTHON)
def qc(session: nox.Session) -> None:
    """Run the data QC report over content/ (non-zero exit on hard failures)."""
    session.install("-e", ".")
    session.run("medchem", "qc", *session.posargs)

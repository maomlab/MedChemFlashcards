"""Command-line interface for MedChem Flashcards.

Subcommands are thin wrappers over the library. They are wired up incrementally
as the pipeline lands; each command imports its implementation lazily so the CLI
stays importable even before every subsystem exists.
"""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(
    add_completion=False,
    help="Build, validate, and serve MedChem Flashcards content.",
    no_args_is_help=True,
)

DEFAULT_CONTENT = Path("content")
DEFAULT_DB = Path("data/medchem.db")


@app.command()
def ingest(
    content: Path = typer.Option(DEFAULT_CONTENT, help="Authored content directory."),
    db: Path = typer.Option(DEFAULT_DB, help="Output SQLite database path."),
    assets: Path = typer.Option(Path("assets"), help="Directory for generated SVGs."),
) -> None:
    """Validate content, render depictions, compute properties, and load SQLite."""
    from medchem_flashcards.curate.ingest import ingest_content

    report = ingest_content(content_dir=content, db_path=db, assets_dir=assets)
    typer.echo(report.summary())
    raise typer.Exit(code=0 if report.ok else 1)


@app.command()
def qc(
    content: Path = typer.Option(DEFAULT_CONTENT, help="Authored content directory."),
) -> None:
    """Run data-quality checks over authored content and print a report."""
    from medchem_flashcards.curate.qc import run_qc

    report = run_qc(content_dir=content)
    typer.echo(report.render())
    raise typer.Exit(code=0 if report.ok else 1)


@app.command(name="export-static")
def export_static_cmd(
    content: Path = typer.Option(DEFAULT_CONTENT, help="Authored content directory."),
    out: Path = typer.Option(
        Path("frontend/public/data"), help="Output directory for static JSON."
    ),
) -> None:
    """Export content as static JSON (mirrors the read API) for static hosting."""
    from medchem_flashcards.curate.export_static import export_static

    report = export_static(content_dir=content, out_dir=out)
    typer.echo(report.summary())
    raise typer.Exit(code=0 if report.ok else 1)


@app.command()
def serve(
    db: Path = typer.Option(DEFAULT_DB, help="SQLite database to serve."),
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8000),
    reload: bool = typer.Option(False, help="Enable autoreload (development)."),
) -> None:
    """Run the FastAPI server."""
    import os

    import uvicorn

    os.environ.setdefault("MEDCHEM_DB", str(db))
    uvicorn.run("medchem_flashcards.api.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":  # pragma: no cover
    app()

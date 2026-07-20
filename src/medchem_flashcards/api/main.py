"""FastAPI application factory and ASGI entry point."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from medchem_flashcards import __version__
from medchem_flashcards.api.routers import auth, cards, decks, progress

# Built SPA location (frontend/dist). Overridable for packaged deployments.
_DEFAULT_SPA = Path(__file__).resolve().parents[3] / "frontend" / "dist"


def _spa_dir() -> Path | None:
    path = Path(os.environ.get("MEDCHEM_SPA_DIR", _DEFAULT_SPA))
    return path if (path / "index.html").exists() else None


def create_app() -> FastAPI:
    app = FastAPI(
        title="MedChem Flashcards API",
        version=__version__,
        summary="Serve medicinal-chemistry functional-group flashcards.",
    )
    # The SPA may be served from a different origin during development.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["*"],
    )

    @app.get("/api/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    app.include_router(decks.router, prefix="/api")
    app.include_router(cards.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(progress.router, prefix="/api")

    # Serve the built SPA at the root when present (single-command local run).
    # Mounted last so /api routes take precedence.
    spa = _spa_dir()
    if spa is not None:
        app.mount("/", StaticFiles(directory=spa, html=True), name="spa")
    return app


app = create_app()

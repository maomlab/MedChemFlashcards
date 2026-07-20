"""Export the canonical JSON Schema from the Pydantic models.

Run via ``uv run nox -s schema`` or ``python -m
medchem_flashcards.schema.export_schema``. CI checks the emitted files are
up to date so the published schema never drifts from the models.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from medchem_flashcards.schema import SCHEMA_VERSION
from medchem_flashcards.schema.card import CardContent, EnrichedCard
from medchem_flashcards.schema.deck import DeckMeta

SCHEMA_DIR = Path("schema")

_MODELS: dict[str, type[BaseModel]] = {
    "card-content": CardContent,
    "enriched-card": EnrichedCard,
    "deck-meta": DeckMeta,
}


def export(out_dir: Path = SCHEMA_DIR) -> list[Path]:
    """Write one JSON Schema file per model; return the paths written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, model in _MODELS.items():
        schema = model.model_json_schema()
        schema["$id"] = f"https://medchem-flashcards/schema/{name}-{SCHEMA_VERSION}.json"
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        path = out_dir / f"{name}.json"
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
        written.append(path)
    return written


def main() -> None:
    paths = export()
    for p in paths:
        print(f"wrote {p}")


if __name__ == "__main__":
    main()

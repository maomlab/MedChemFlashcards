"""API response models (distinct from storage/content models)."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

from medchem_flashcards.schema.card import EnrichedCard

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class DeckSummary(BaseModel):
    id: str
    title: str
    description: str
    order: int
    level: str
    card_count: int


class CardSummary(BaseModel):
    """Lightweight card view for deck listings and review queues."""

    id: str
    name: str
    deck: str
    difficulty: int
    tags: list[str]
    svg: str


class DeckDetail(DeckSummary):
    prerequisites: list[str]
    cards: list[CardSummary]


# Full card detail is the enriched content model itself.
CardDetail = EnrichedCard


# --- Auth & progress ---------------------------------------------------------


class Credentials(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=200)

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("invalid email address")
        return v


class UserOut(BaseModel):
    id: int
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProgressEntry(BaseModel):
    """A single card's spaced-repetition state (mirrors the client scheduler)."""

    card_id: str
    reps: int = 0
    ease: float = 2.5
    interval_days: int = 0
    due: str
    lapses: int = 0
    last_reviewed: str | None = None


class ProgressSync(BaseModel):
    entries: list[ProgressEntry] = Field(default_factory=list)

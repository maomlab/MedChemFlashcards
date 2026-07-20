"""SQLAlchemy ORM models.

Queryable fields (name, deck, difficulty, tags) are promoted to columns; the
full validated :class:`~medchem_flashcards.schema.card.EnrichedCard` is stored as
a JSON ``payload`` so the API can serve a card without reassembling it from many
columns. The database is a build artifact regenerated from ``content/``.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[str] = mapped_column(String, default="core")
    prerequisites: Mapped[list[str]] = mapped_column(JSON, default=list)

    cards: Mapped[list[Card]] = relationship(
        back_populates="deck", cascade="all, delete-orphan", order_by="Card.id"
    )


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    deck_id: Mapped[str] = mapped_column(ForeignKey("decks.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, default=1, index=True)
    smarts: Mapped[str] = mapped_column(String, nullable=False)
    representative_smiles: Mapped[str] = mapped_column(String, nullable=False)
    svg: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    deck: Mapped[Deck] = relationship(back_populates="cards")

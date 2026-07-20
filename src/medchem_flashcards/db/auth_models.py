"""User and progress ORM models.

These live in a **separate database** from content (decks/cards): the content DB
is a build artifact rebuilt by ``medchem ingest``, whereas user accounts and
review progress must persist. Hence a distinct declarative base and engine.

Review-state dates (``due``, ``last_reviewed``) are stored as ISO date strings to
match the client scheduler and keep merge comparisons trivial.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class UserBase(DeclarativeBase):
    pass


class User(UserBase):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    progress: Mapped[list[Progress]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Progress(UserBase):
    """Per-card review state. ``due`` and ``last_reviewed`` are promoted for
    querying and merge; ``state`` holds the scheduler-specific fields opaquely so
    the scheduling algorithm can change without a database migration."""

    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("user_id", "card_id", name="uq_user_card"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    card_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    due: Mapped[str] = mapped_column(String, nullable=False)
    last_reviewed: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="progress")

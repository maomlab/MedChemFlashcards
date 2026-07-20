"""User and progress ORM models.

These live in a **separate database** from content (decks/cards): the content DB
is a build artifact rebuilt by ``medchem ingest``, whereas user accounts and
review progress must persist. Hence a distinct declarative base and engine.

Review-state dates (``due``, ``last_reviewed``) are stored as ISO date strings to
match the client scheduler and keep merge comparisons trivial.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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
    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("user_id", "card_id", name="uq_user_card"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    card_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, default=0)
    ease: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    due: Mapped[str] = mapped_column(String, nullable=False)
    lapses: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="progress")

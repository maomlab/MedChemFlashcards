"""Engine and session factory helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from medchem_flashcards.db.auth_models import UserBase
from medchem_flashcards.db.models import Base


def make_engine(db_path: Path | str, *, echo: bool = False) -> Engine:
    """Create a SQLite engine with foreign-key enforcement enabled."""
    url = "sqlite://" if str(db_path) == ":memory:" else f"sqlite:///{db_path}"
    engine = create_engine(url, echo=echo, future=True)

    @event.listens_for(engine, "connect")
    def _fk_pragma(dbapi_conn, _record):  # type: ignore[no-untyped-def]
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    return engine


def init_db(engine: Engine, *, drop: bool = False) -> None:
    """Create content tables (optionally dropping existing ones first)."""
    if drop:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def init_user_db(engine: Engine) -> None:
    """Create the user/progress tables if absent (never dropped)."""
    UserBase.metadata.create_all(engine)


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


@contextmanager
def session_scope(engine: Engine) -> Iterator[Session]:
    """Transactional session scope: commit on success, roll back on error."""
    factory = session_factory(engine)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

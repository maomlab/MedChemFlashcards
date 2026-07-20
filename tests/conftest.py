"""Shared fixtures: a seeded database and an API test client."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from medchem_flashcards.api.deps import get_session, get_user_session
from medchem_flashcards.api.main import create_app
from medchem_flashcards.curate.ingest import ingest_content
from medchem_flashcards.db.session import init_user_db, make_engine, session_factory

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT = REPO_ROOT / "content"


@pytest.fixture(scope="session")
def seeded_engine(tmp_path_factory: pytest.TempPathFactory) -> Engine:
    if not CONTENT.exists():
        pytest.skip("no authored content present")
    db_path = tmp_path_factory.mktemp("db") / "test.db"
    report = ingest_content(CONTENT, db_path=db_path)
    assert report.ok, report.summary()
    return make_engine(db_path)


@pytest.fixture
def client(seeded_engine: Engine, tmp_path: Path) -> Iterator[TestClient]:
    app = create_app()

    user_engine = make_engine(tmp_path / "users.db")
    init_user_db(user_engine)

    def _content_session() -> Iterator[Session]:
        factory = session_factory(seeded_engine)
        with factory() as session:
            yield session

    def _user_session() -> Iterator[Session]:
        factory = session_factory(user_engine)
        with factory() as session:
            yield session

    app.dependency_overrides[get_session] = _content_session
    app.dependency_overrides[get_user_session] = _user_session
    with TestClient(app) as c:
        yield c

"""Shared FastAPI dependencies (content/user engines, sessions, current user)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from medchem_flashcards.api.security import decode_access_token
from medchem_flashcards.db.auth_models import User
from medchem_flashcards.db.session import (
    init_user_db,
    make_engine,
    session_factory,
)

DEFAULT_DB = "data/medchem.db"
DEFAULT_USER_DB = "data/users.db"


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Engine for the content database named by ``$MEDCHEM_DB``."""
    return make_engine(os.environ.get("MEDCHEM_DB", DEFAULT_DB))


@lru_cache(maxsize=1)
def get_user_engine() -> Engine:
    """Engine for the persistent user database named by ``$MEDCHEM_USER_DB``."""
    engine = make_engine(os.environ.get("MEDCHEM_USER_DB", DEFAULT_USER_DB))
    init_user_db(engine)
    return engine


def get_session() -> Iterator[Session]:
    factory = session_factory(get_engine())
    with factory() as session:
        yield session


def get_user_session() -> Iterator[Session]:
    factory = session_factory(get_user_engine())
    with factory() as session:
        yield session


_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: Session = Depends(get_user_session),
) -> User:
    """Resolve the authenticated user from a Bearer token, or raise 401."""
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid or missing credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise invalid
    payload = decode_access_token(credentials.credentials)
    if payload is None or "sub" not in payload:
        raise invalid
    user = session.get(User, int(payload["sub"]))
    if user is None:
        raise invalid
    return user

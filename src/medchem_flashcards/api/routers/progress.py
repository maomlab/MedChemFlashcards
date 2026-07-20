"""Per-user spaced-repetition progress: fetch and merge-sync."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from medchem_flashcards.api.deps import get_current_user, get_user_session
from medchem_flashcards.api.schemas import ProgressEntry, ProgressSync
from medchem_flashcards.db.auth_models import Progress, User

router = APIRouter(prefix="/progress", tags=["progress"])


def _to_entry(p: Progress) -> ProgressEntry:
    return ProgressEntry(
        card_id=p.card_id,
        due=p.due,
        last_reviewed=p.last_reviewed,
        state=p.state or {},
    )


def _newer(incoming: str | None, stored: str | None) -> bool:
    """True if the incoming review is at least as recent as the stored one.

    ISO date strings sort lexicographically; ``None`` (never reviewed) is oldest.
    """
    return (incoming or "") >= (stored or "")


def _all_entries(session: Session, user_id: int) -> list[ProgressEntry]:
    rows = session.scalars(select(Progress).where(Progress.user_id == user_id)).all()
    return [_to_entry(p) for p in rows]


@router.get("", response_model=list[ProgressEntry])
def get_progress(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_user_session),
) -> list[ProgressEntry]:
    return _all_entries(session, user.id)


@router.put("", response_model=list[ProgressEntry])
def sync_progress(
    body: ProgressSync,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_user_session),
) -> list[ProgressEntry]:
    """Merge client entries into the server store (last-reviewed wins) and return
    the full merged set so the client can reconcile its local copy."""
    existing = {
        p.card_id: p
        for p in session.scalars(select(Progress).where(Progress.user_id == user.id)).all()
    }
    for entry in body.entries:
        current = existing.get(entry.card_id)
        if current is None:
            session.add(
                Progress(
                    user_id=user.id,
                    card_id=entry.card_id,
                    due=entry.due,
                    last_reviewed=entry.last_reviewed,
                    state=entry.state,
                )
            )
        elif _newer(entry.last_reviewed, current.last_reviewed):
            current.due = entry.due
            current.last_reviewed = entry.last_reviewed
            current.state = entry.state
    session.commit()
    return _all_entries(session, user.id)

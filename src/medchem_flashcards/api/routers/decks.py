"""Deck listing and detail endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from medchem_flashcards.api.deps import get_session
from medchem_flashcards.api.schemas import CardSummary, DeckDetail, DeckSummary
from medchem_flashcards.db.models import Card, Deck

router = APIRouter(prefix="/decks", tags=["decks"])


def _card_counts(session: Session) -> dict[str, int]:
    rows = session.execute(select(Card.deck_id, func.count()).group_by(Card.deck_id)).tuples()
    return dict(rows.all())


@router.get("", response_model=list[DeckSummary])
def list_decks(session: Session = Depends(get_session)) -> list[DeckSummary]:
    counts = _card_counts(session)
    decks = session.execute(select(Deck).order_by(Deck.order)).scalars().all()
    return [
        DeckSummary(
            id=d.id,
            title=d.title,
            description=d.description,
            order=d.order,
            level=d.level,
            card_count=counts.get(d.id, 0),
        )
        for d in decks
    ]


@router.get("/{deck_id}", response_model=DeckDetail)
def get_deck(deck_id: str, session: Session = Depends(get_session)) -> DeckDetail:
    deck = session.get(Deck, deck_id)
    if deck is None:
        raise HTTPException(status_code=404, detail=f"deck '{deck_id}' not found")
    cards = [
        CardSummary(
            id=c.id,
            name=c.name,
            deck=c.deck_id,
            difficulty=c.difficulty,
            tags=c.tags,
            svg=c.svg,
        )
        for c in deck.cards
    ]
    return DeckDetail(
        id=deck.id,
        title=deck.title,
        description=deck.description,
        order=deck.order,
        level=deck.level,
        card_count=len(cards),
        prerequisites=deck.prerequisites,
        cards=cards,
    )

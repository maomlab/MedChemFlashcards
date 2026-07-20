"""Card detail and depiction endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from medchem_flashcards.api.deps import get_session
from medchem_flashcards.api.schemas import CardDetail
from medchem_flashcards.db.models import Card

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/{card_id}", response_model=CardDetail)
def get_card(card_id: str, session: Session = Depends(get_session)) -> dict[str, Any]:
    card = session.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"card '{card_id}' not found")
    # payload is a validated EnrichedCard dump; FastAPI re-validates via CardDetail.
    return card.payload


@router.get(
    "/{card_id}/svg",
    responses={200: {"content": {"image/svg+xml": {}}}},
    response_class=Response,
)
def get_card_svg(card_id: str, session: Session = Depends(get_session)) -> Response:
    card = session.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail=f"card '{card_id}' not found")
    return Response(content=card.svg, media_type="image/svg+xml")

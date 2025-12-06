from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas import card as schemas
from app.services import card_service

router = APIRouter()

@router.get("/", response_model=List[schemas.ApiCard])
def read_cards(db: Session = Depends(get_db)):
    return card_service.get_cards(db)

@router.post("/sync")
def sync_cards(cards: List[schemas.ApiCardCreate], db: Session = Depends(get_db)):
    card_service.sync_cards(db, cards)
    return {"status": "ok"}
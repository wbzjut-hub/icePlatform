# backend/app/services/card_service.py
from sqlalchemy.orm import Session
from app.models.card import ApiCard
from app.schemas.card import ApiCardCreate
from app.services.log_service import create_log  # <--- 导入日志服务


def get_cards(db: Session):
    return db.query(ApiCard).all()


def sync_cards(db: Session, cards: list[ApiCardCreate]):
    db.query(ApiCard).delete()
    for card in cards:
        db_item = ApiCard(**card.model_dump())
        db.add(db_item)

    # --- 记录日志 ---
    create_log(db, action="SYNC", target="ApiCard", content=cards)
    # ----------------

    db.commit()
    return cards
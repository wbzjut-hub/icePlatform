from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas import menu as schemas
from app.services import menu_service

router = APIRouter()

@router.get("/", response_model=List[schemas.MenuItem])
def read_menus(db: Session = Depends(get_db)):
    return menu_service.get_menus(db)

@router.post("/sync")
def sync_menus(menus: List[schemas.MenuItemCreate], db: Session = Depends(get_db)):
    menu_service.sync_menus(db, menus)
    return {"status": "ok"}
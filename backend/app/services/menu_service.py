# backend/app/services/menu_service.py
from sqlalchemy.orm import Session
from app.models.menu import MenuItem
from app.schemas.menu import MenuItemCreate
from app.services.log_service import create_log  # <--- 导入日志服务


def get_menus(db: Session):
    return db.query(MenuItem).all()


def sync_menus(db: Session, menus: list[MenuItemCreate]):
    db.query(MenuItem).delete()
    for menu in menus:
        db_item = MenuItem(**menu.model_dump())
        db.add(db_item)

    # --- 记录日志 ---
    create_log(db, action="SYNC", target="Menu", content=menus)
    # ----------------

    db.commit()
    return menus
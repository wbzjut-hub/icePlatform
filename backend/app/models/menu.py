from sqlalchemy import Column, String
from app.db.base import Base

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    path = Column(String)
    icon = Column(String)
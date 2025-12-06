from sqlalchemy import Column, String, JSON, Text
from app.db.base import Base

class ApiCard(Base):
    __tablename__ = "api_cards"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    url = Column(String)
    method = Column(String)
    # JSON 类型在 SQLite 中存储为 Text，但 SQLAlchemy 会自动序列化/反序列化
    params = Column(JSON, nullable=True)
    body = Column(Text, nullable=True)
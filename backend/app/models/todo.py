from sqlalchemy import Column, String, Boolean
from app.db.base import Base

class TodoItem(Base):
    __tablename__ = "todo_items"

    id = Column(String, primary_key=True, index=True)
    date = Column(String, index=True) # 格式: YYYY-MM-DD
    type = Column(String) # 'todo' 或 'note'
    text = Column(String)
    done = Column(Boolean, default=False)
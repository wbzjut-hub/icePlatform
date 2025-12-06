from sqlalchemy import Column, String, DateTime, JSON
from app.db.base import Base
import datetime
import uuid

class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, default="admin") # 目前系统只有admin，后续对接用户系统可动态获取
    action = Column(String)       # 操作类型: 'SYNC_MENU', 'SYNC_CARD', 'SYNC_TODO'
    target = Column(String)       # 操作对象: 'Menu', 'ApiCard', 'Todo'
    content = Column(JSON)        # 具体的请求数据/变更内容
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
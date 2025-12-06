from sqlalchemy import Column, String, Text, JSON, DateTime
from app.db.base import Base
import datetime
import uuid


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True)  # 工作流名称 (如: 日程管家)
    description = Column(String)  # 描述
    system_prompt = Column(Text)  # 系统提示词 (人设)

    # 关键字段：存储该工作流允许使用的工具名称列表，如 ["add_todo", "query_todos"]
    # 如果为空，则是纯聊天模式
    tools_config = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
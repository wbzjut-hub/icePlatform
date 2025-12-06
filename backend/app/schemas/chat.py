from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class MessageBase(BaseModel):
    role: str
    content: str
    # 🌟 新增
    usage: Optional[Any] = None

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class SessionBase(BaseModel):
    title: str

class SessionCreate(SessionBase):
    pass

class Session(SessionBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    model: str = "deepseek-chat"
    workflow_id: str = "wf_agent"
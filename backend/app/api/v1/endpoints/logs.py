# backend/app/api/v1/endpoints/logs.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Union, Optional, Any # <--- 1. 导入 Union
from app.db.session import get_db
from app.models.log import OperationLog
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class LogResponse(BaseModel):
    id: str
    username: str
    action: str
    target: str
    # <--- 2. 修改这里：使用 Union[..., ..., ...] 替代 |
    content: Union[dict, list, str, None]
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[LogResponse])
def read_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # 按时间倒序排列，最新的在前面
    return db.query(OperationLog).order_by(OperationLog.created_at.desc()).offset(skip).limit(limit).all()
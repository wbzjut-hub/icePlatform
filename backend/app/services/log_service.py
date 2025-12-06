# backend/app/services/log_service.py
from sqlalchemy.orm import Session
from app.models.log import OperationLog
import json


# 辅助函数：处理 Pydantic 对象转 JSON
def create_log(db: Session, action: str, target: str, content: any, username: str = "admin"):
    # 如果 content 是 Pydantic 模型列表，转为 dict 列表
    if isinstance(content, list):
        # 尝试判断列表里的元素是否是 Pydantic 模型
        try:
            json_content = [item.model_dump() for item in content]
        except AttributeError:
            json_content = content
    elif hasattr(content, "model_dump"):
        json_content = content.model_dump()
    else:
        json_content = content

    log_entry = OperationLog(
        action=action,
        target=target,
        content=json_content,
        username=username
    )

    db.add(log_entry)
    # 注意：这里不需要 db.commit()，因为这个函数通常会在其他业务逻辑的 commit 之前或之后调用
    # 为了保证日志一定写入，我们这里强制 commit，或者让调用方 commit
    db.commit()
    db.refresh(log_entry)
    return log_entry
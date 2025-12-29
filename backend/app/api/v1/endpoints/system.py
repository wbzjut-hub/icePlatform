# backend/app/api/v1/endpoints/system.py
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import engine, get_db  # 引入 get_db 用于数据库会话
from app.models.setting import SystemSetting  # 引入新定义的设置模型

router = APIRouter()


# --- 请求体模型 (Pydantic Models) ---

class PathRequest(BaseModel):
    path: str


class SettingsDto(BaseModel):
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    tavily_api_key: Optional[str] = None


# --- 原有功能: 数据库路径管理 ---

@router.get("/db-path")
def get_db_path():
    """获取当前数据库路径"""
    return {"path": str(settings.SQLALCHEMY_DATABASE_URL).replace("sqlite:///", "")}


@router.post("/move-db")
def move_db(req: PathRequest):
    """移动数据库文件到新目录"""
    try:
        print(f"收到移动请求，目标路径: {req.path}")

        # 1. 关键步骤：销毁当前的数据库连接池
        # 这会释放文件锁，允许文件被移动
        engine.dispose()

        # 2. 执行移动逻辑
        new_path = settings.move_database(req.path)

        return {
            "status": "ok",
            "new_path": new_path,
            "message": "数据库移动成功，请重启应用。"
        }

    except Exception as e:
        # 捕获详细错误并打印到控制台
        print(f"移动数据库失败: {str(e)}")
        # 返回 500 错误，并将具体的错误信息传给前端
        raise HTTPException(status_code=500, detail=f"移动失败: {str(e)}")


# --- 新增功能: 系统配置管理 (API Key) ---

@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    """获取系统设置 (API Key, Base URL)"""
    target_keys = ["openai_api_key", "openai_base_url", "tavily_api_key"]
    result = {}

    for k in target_keys:
        # 从数据库查询配置项
        setting = db.query(SystemSetting).filter(SystemSetting.key == k).first()
        
        if setting:
            result[k] = setting.value
        else:
            # 数据库没有时，回退到配置文件/环境变量的默认值
            # settings.OPENAI_API_KEY, settings.TAVILY_API_KEY 等
            # 将 key 转为大写 (openai_api_key -> OPENAI_API_KEY)
            default_val = getattr(settings, k.upper(), "")
            result[k] = default_val

    return result


@router.post("/settings")
def save_settings(data: SettingsDto, db: Session = Depends(get_db)):
    """保存系统设置"""
    # 准备要更新的数据
    updates = {
        "openai_api_key": data.openai_api_key,
        "openai_base_url": data.openai_base_url,
        "tavily_api_key": data.tavily_api_key
    }

    try:
        for key, value in updates.items():
            # 只有当 value 不为 None 时才处理 (允许空字符串，代表清空 Key)
            if value is not None:
                setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()

                if not setting:
                    # 如果不存在，创建新记录
                    new_setting = SystemSetting(key=key, value=value)
                    db.add(new_setting)
                else:
                    # 如果已存在，更新值
                    setting.value = value

        db.commit()
        return {"message": "配置已保存，即刻生效。"}

    except Exception as e:
        db.rollback()
        print(f"保存配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存配置失败: {str(e)}")
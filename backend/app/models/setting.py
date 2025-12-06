from sqlalchemy import Column, String
from app.db.base import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    # 使用 key-value 结构，方便扩展其他设置
    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=True)
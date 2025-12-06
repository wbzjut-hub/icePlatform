from pydantic import BaseModel

class MenuItemBase(BaseModel):
    id: str
    name: str
    path: str
    icon: str

class MenuItemCreate(MenuItemBase):
    pass

class MenuItem(MenuItemBase):
    class Config:
        from_attributes = True # 允许从 ORM 模型读取数据 (Pydantic v2)
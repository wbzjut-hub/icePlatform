from pydantic import BaseModel
from typing import List, Optional, Any

class ParamItem(BaseModel):
    key: str
    value: str
    enabled: bool

class ApiCardBase(BaseModel):
    id: str
    name: str
    url: str
    method: str
    params: Optional[List[ParamItem]] = []
    body: Optional[str] = ""

class ApiCardCreate(ApiCardBase):
    pass

class ApiCard(ApiCardBase):
    class Config:
        from_attributes = True
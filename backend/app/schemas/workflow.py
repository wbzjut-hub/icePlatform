from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    tools_config: List[str] = []

class WorkflowCreate(WorkflowBase):
    pass

class Workflow(WorkflowBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True
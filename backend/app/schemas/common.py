from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class ResponseBase(BaseModel, Generic[T]):
    code: int = 200
    message: str = "Success"
    data: Optional[T] = None
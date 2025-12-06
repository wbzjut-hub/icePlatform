from pydantic import BaseModel

class TodoItemBase(BaseModel):
    id: str
    text: str
    done: bool

# 前端传来的是一个大对象，我们需要定义对应的结构来接收
class DailyData(BaseModel):
    todos: list[TodoItemBase]
    notes: list[TodoItemBase]

class TodoSyncRequest(BaseModel):
    date: str
    data: DailyData
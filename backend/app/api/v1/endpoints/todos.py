from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
from app.db.session import get_db
from app.models.todo import TodoItem
from app.schemas import todo as schemas
from app.services.log_service import create_log

router = APIRouter()


# 获取所有数据，并按日期组装成前端需要的格式 Map<Date, {todos, notes}>
@router.get("/all")
@router.get("/all")
def read_all_todos(db: Session = Depends(get_db)):
    print("👉 Entered read_all_todos handler")
    try:
        items = db.query(TodoItem).all()
        print(f"👉 Query successful, items count: {len(items)}")
    except Exception as e:
        print(f"👉 Query FAILED: {e}")
        raise e
        
    result = {}

    for item in items:
        if item.date not in result:
            result[item.date] = {"todos": [], "notes": []}

        # 构造对象
        obj = {"id": item.id, "text": item.text, "done": item.done}

        if item.type == 'todo':
            result[item.date]["todos"].append(obj)
        else:
            result[item.date]["notes"].append(obj)

    return result


# 同步特定日期的数据
@router.post("/sync/{date}")
def sync_daily_todos(date: str, data: schemas.DailyData, db: Session = Depends(get_db)):
    # 1. 删除旧数据
    db.query(TodoItem).filter(TodoItem.date == date).delete()

    # 2. 写入 Todos
    for t in data.todos:
        db.add(TodoItem(id=t.id, date=date, type='todo', text=t.text, done=t.done))

    # 3. 写入 Notes
    for n in data.notes:
        db.add(TodoItem(id=n.id, date=date, type='note', text=n.text, done=n.done))

    # --- 记录日志 ---
    # 记录具体是哪一天的同步
    create_log(db, action=f"SYNC_DATE_{date}", target="Todo/Note", content=data)
    # ----------------

    db.commit()
    return {"status": "ok"}
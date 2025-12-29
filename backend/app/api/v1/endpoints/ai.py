from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, AsyncGenerator
import os
import json
from app.db.session import get_db
from app.schemas.chat import ChatRequest, Session as SessionSchema, Message as MessageSchema
from app.schemas.workflow import WorkflowCreate, Workflow as WorkflowSchema
from app.models.chat import ChatSession, ChatMessage
from app.models.workflow import Workflow as WorkflowModel
from app.services.ai_service import ai_service

router = APIRouter()


# --- 工作流管理 ---
@router.get("/workflows", response_model=List[WorkflowSchema])
def get_workflows(db: Session = Depends(get_db)):
    return db.query(WorkflowModel).order_by(WorkflowModel.created_at.asc()).all()


@router.post("/workflows", response_model=WorkflowSchema)
def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    db_obj = WorkflowModel(name=workflow.name, description=workflow.description, system_prompt=workflow.system_prompt,
                           tools_config=workflow.tools_config)
    db.add(db_obj);
    db.commit();
    db.refresh(db_obj)

    # 🌟 Auto-sync Markdown Documentation (Create)
    try:
        current_path = os.path.dirname(os.path.abspath(__file__))
        project_root = current_path
        found_docs = False
        
        for _ in range(8):
            if os.path.exists(os.path.join(project_root, 'docs')):
                found_docs = True
                break
            project_root = os.path.dirname(project_root)
            
        if found_docs:
            experts_dir = os.path.join(project_root, 'docs', 'experts')
            if os.path.exists(experts_dir):
                safe_name = db_obj.name.split('(')[0].strip().replace(' ', '_')
                filename = f"{safe_name}.md"
                filepath = os.path.join(experts_dir, filename)
                
                content = f"""# {db_obj.name}

## Description
{db_obj.description}

## System Prompt
```text
{db_obj.system_prompt}
```

## Tools
{', '.join(db_obj.tools_config) if db_obj.tools_config else 'None'}
"""
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Auto-created doc: {filepath}")
    except Exception as e:
        print(f"Failed to auto-create markdown doc: {e}")

    return db_obj


@router.put("/workflows/{workflow_id}", response_model=WorkflowSchema)
def update_workflow(workflow_id: str, workflow: WorkflowCreate, db: Session = Depends(get_db)):
    if workflow_id in ["wf_general", "wf_agent"]: 
        raise HTTPException(status_code=400, detail="系统预置智能体无法修改")
    
    db_obj = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not db_obj: 
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    db_obj.name = workflow.name
    db_obj.description = workflow.description
    db_obj.system_prompt = workflow.system_prompt
    db_obj.tools_config = workflow.tools_config
    
    db.commit()
    db.refresh(db_obj)

    # 🌟 Auto-sync Markdown Documentation (Update)
    try:
        current_path = os.path.dirname(os.path.abspath(__file__))
        project_root = current_path
        found_docs = False
        
        for _ in range(8):
            if os.path.exists(os.path.join(project_root, 'docs')):
                found_docs = True
                break
            project_root = os.path.dirname(project_root)
            
        if found_docs:
            experts_dir = os.path.join(project_root, 'docs', 'experts')
            if os.path.exists(experts_dir):
                safe_name = db_obj.name.split('(')[0].strip().replace(' ', '_')
                filename = f"{safe_name}.md"
                filepath = os.path.join(experts_dir, filename)
                
                if os.path.exists(filepath):
                    content = f"""# {db_obj.name}

## Description
{db_obj.description}

## System Prompt
```text
{db_obj.system_prompt}
```

## Tools
{', '.join(db_obj.tools_config) if db_obj.tools_config else 'None'}
"""
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Auto-updated doc: {filepath}")
    except Exception as e:
        print(f"Failed to auto-update markdown doc: {e}")

    return db_obj


@router.delete("/workflows/{workflow_id}")
def delete_workflow(workflow_id: str, db: Session = Depends(get_db)):
    if workflow_id in ["wf_general", "wf_agent"]: raise HTTPException(status_code=400, detail="系统预置智能体无法删除")
    wf = db.query(WorkflowModel).filter(WorkflowModel.id == workflow_id).first()
    if not wf: raise HTTPException(status_code=404, detail="Workflow not found")
    db.delete(wf);
    db.commit()
    return {"status": "ok"}


# --- 会话管理 ---
@router.get("/sessions", response_model=List[SessionSchema])
def get_sessions(db: Session = Depends(get_db)):
    return db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()


@router.get("/sessions/{session_id}/messages", response_model=List[MessageSchema])
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(
        ChatMessage.created_at.asc()).all()


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session: raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session);
    db.commit()
    return {"status": "ok"}


# --- 核心对话 (非流式) ---
@router.post("/chat")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    session_id = request.session_id

    # 1. 会话处理
    if not session_id:
        title = request.message[:20] if len(request.message) > 0 else "新对话"
        new_session = ChatSession(title=title)
        db.add(new_session);
        db.commit();
        db.refresh(new_session)
        session_id = new_session.id
    else:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            new_session = ChatSession(id=session_id, title="日程管家 (专属)")
            db.add(new_session);
            db.commit();
            db.refresh(new_session)

    # 2. 保存用户消息
    user_msg = ChatMessage(session_id=session_id, role="user", content=request.message)
    db.add(user_msg);
    db.commit()

    # 3. 调用 AI 服务 (获取 result 字典)
    result = await ai_service.chat_with_workflow(
        db=db,
        message=request.message,
        session_id=session_id,
        workflow_id=request.workflow_id
    )

    reply_text = result["reply"]
    token_usage = result.get("usage")
    actions = result.get("actions", [])

    # 4. 保存 AI 回复 (带 usage)
    ai_msg = ChatMessage(session_id=session_id, role="assistant", content=reply_text, usage=token_usage)
    db.add(ai_msg);
    db.commit()

    return {
        "session_id": session_id,
        "reply": reply_text,
        "session_title": db.query(ChatSession).get(session_id).title,
        "usage": token_usage,
        "actions": actions
    }


# --- 🌟 流式对话 (SSE) ---
@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Stream chat responses using Server-Sent Events"""
    session_id = request.session_id

    # 1. 会话处理 - 获取专家名称
    workflow = db.query(WorkflowModel).filter(WorkflowModel.id == request.workflow_id).first()
    expert_name = workflow.name if workflow else "专家咨询"
    
    if not session_id:
        title = expert_name
        new_session = ChatSession(title=title)
        db.add(new_session);
        db.commit();
        db.refresh(new_session)
        session_id = new_session.id
    else:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            new_session = ChatSession(id=session_id, title=expert_name)
            db.add(new_session);
            db.commit();
            db.refresh(new_session)

    # 2. 保存用户消息
    user_msg = ChatMessage(session_id=session_id, role="user", content=request.message)
    db.add(user_msg);
    db.commit()

    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generator function for SSE streaming"""
        full_content = ""
        usage_data = None
        
        try:
            async for chunk in ai_service.chat_with_workflow_stream(
                db=db,
                message=request.message,
                session_id=session_id,
                workflow_id=request.workflow_id
            ):
                if chunk.get("type") == "content":
                    content = chunk.get("content", "")
                    full_content += content
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                elif chunk.get("type") == "usage":
                    usage_data = chunk.get("usage")
                    yield f"data: {json.dumps({'type': 'usage', 'usage': usage_data})}\n\n"
                elif chunk.get("type") == "error":
                    yield f"data: {json.dumps({'type': 'error', 'error': chunk.get('error')})}\n\n"
            
            # Save full response to database
            if full_content:
                ai_msg = ChatMessage(session_id=session_id, role="assistant", content=full_content, usage=usage_data)
                db.add(ai_msg)
                db.commit()
            
            # Send done event
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
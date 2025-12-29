# backend/main.py

from app.core.config import settings, setup_ffmpeg_path

# 1. 先初始化 FFmpeg 路径
setup_ffmpeg_path()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.base import Base
from app.db.session import engine, SessionLocal

# 🌟 1. 核心：导入所有模型
import app.models
from app.models.workflow import Workflow
from app.models.chat import ChatSession  # <--- [新增] 导入会话模型
from app.models.setting import SystemSetting

# 🌟 2. 核心：创建数据库表
Base.metadata.create_all(bind=engine)


# --- 初始化数据 (工作流 + 固定会话) ---
def init_data():
    db = SessionLocal()
    try:
        # ================== A. 初始化工作流 ==================
        # 改动：不要使用 return 直接结束函数，而是用 if 判断包裹，
        # 这样即使工作流已存在，代码也会继续往下执行去检查 Session
        if not db.query(Workflow).first():
            print("正在初始化默认工作流配置...")

            # 1. 通用助手
            wf_general = Workflow(
                id="wf_general",
                name="通用助手",
                description="普通的聊天机器人，无工具权限。",
                system_prompt="你是一个乐于助人的AI助手，运行在 IcePlatform 上。请用 Markdown 格式回答。",
                tools_config=[]
            )

            # 2. 日程管家 (Agent Mode)
            wf_agent = Workflow(
                id="wf_agent",
                name="日程管家",
                description="可以帮你管理待办事项的智能体。",
                system_prompt="""你是一个专业的日程管理助手 IcePlatform Agent。
当前时间是: {current_time}。

你的职责：
1. 管理待办事项：当用户说“添加任务”、“提醒我”时，请务必调用 `add_todo` 工具。
2. 查询日程：当用户问“今天有什么事”、“查询明天日程”时，请务必调用 `query_todos` 工具。
3. 日期推断：请根据当前时间，自行计算出用户口中“明天”、“下周五”的具体日期 (YYYY-MM-DD)。

请用 Markdown 格式回复。""",
                tools_config=["add_todo", "query_todos"]
            )

            # 3. 联网研究员
            wf_researcher = Workflow(
                id="wf_researcher",
                name="联网研究员",
                description="拥有互联网搜索能力的智能体。",
                system_prompt="""你是一个拥有联网能力的AI研究员。
当前时间是: {current_time}。
当用户询问你需要外部知识才能回答的问题（如实时新闻、天气、最新技术）时，请务必使用 `web_search` 工具。""",
                tools_config=["web_search"]
            )

            db.add_all([wf_general, wf_agent, wf_researcher])
            db.commit()
            print("✅ 默认工作流初始化完成！")
        else:
            print("⏩ 工作流数据已存在，跳过。")

        # ================== B. [新增] 初始化机器人专属会话 ==================
        # 这是一个固定的 Session ID，前端会写死这个 ID 来调用
        ROBOT_SESSION_ID = "fixed_session_robot"

        if not db.query(ChatSession).filter(ChatSession.id == ROBOT_SESSION_ID).first():
            print(f"正在初始化机器人专属会话 ({ROBOT_SESSION_ID})...")
            robot_session = ChatSession(
                id=ROBOT_SESSION_ID,
                title="🤖 日程管家 (专属)",
                # created_at 会自动使用默认时间，不需要手动指定
            )
            db.add(robot_session)
            db.commit()
            print("✅ 机器人专属会话初始化完成！")
        else:
            print("⏩ 机器人专属会话已存在，跳过。")

    except Exception as e:
        print(f"❌ 初始化数据失败: {e}")
        db.rollback()
    finally:
        db.close()


# 执行初始化
init_data()

# --- FastAPI App ---
app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 调试中间件：打印所有 500 错误的详细堆栈
from fastapi import Request
from fastapi.responses import JSONResponse
import traceback
from datetime import datetime

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        print(f"🔥 500 ERROR: {e}")
        traceback.print_exc()
        
        # 强制写入错误日志文件 (绝对路径)
        try:
            with open("/Users/wangbo/Desktop/Object/aiTalking/backend_debug.log", "a") as f:
                f.write(f"\n====================\n")
                f.write(f"TIME: {datetime.now()}\n")
                f.write(f"URL: {request.url}\n")
                f.write(f"ERROR: {e}\n")
                traceback.print_exc(file=f)
        except Exception as log_err:
            print(f"❌ Failed to write log: {log_err}")
            
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error", "trace": str(e)})

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": "IcePlatform Backend Running",
        "db": str(settings.SQLALCHEMY_DATABASE_URL)
    }


if __name__ == "__main__":
    import uvicorn
    import sys

    # 判断运行环境
    if getattr(sys, 'frozen', False):
        # 生产环境 (打包后): 不支持 reload，直接运行 app 对象
        uvicorn.run(app, host="0.0.0.0", port=8008)
    else:
        # 开发环境: 开启热重载 (reload=True)
        # 注意: reload 模式下必须传入 import string ("main:app") 而不是 app 对象
        uvicorn.run("main:app", host="0.0.0.0", port=8008, reload=True)
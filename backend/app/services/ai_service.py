from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from app.core.config import settings
from app.models.chat import ChatSession, ChatMessage
from app.models.workflow import Workflow
from app.models.setting import SystemSetting  # <--- [新增] 导入设置模型
from app.services.tools import get_todo_tools
import datetime
import json


class AIService:
    # 获取所有可用工具的注册表
    def _get_tool_registry(self, db: Session):
        raw_tools = get_todo_tools(db)
        return {t.name: t for t in raw_tools}

    async def chat_with_workflow(self, db: Session, message: str, session_id: str, workflow_id: str = "wf_agent"):
        # 1. 获取工作流配置
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        # 🌟 修复逻辑：确保 workflow 和 prompt 一定有值
        if not workflow:
            # 回退机制：如果找不到指定的工作流，使用默认的
            workflow = Workflow(
                name="Fallback",
                system_prompt="你是一个智能助手 IcePlatform Agent。当前时间是: {current_time}。",
                tools_config=[]
            )

        # 2. 动态构建 System Prompt (注入时间)
        week_days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        now = datetime.datetime.now()
        week_day_str = week_days[now.weekday()]
        today_str = now.strftime("%Y-%m-%d %H:%M")

        # 🌟 确保变量被定义
        final_system_prompt = workflow.system_prompt.replace("{current_time}", f"{today_str} ({week_day_str})")

        # 3. 动态加载工具
        tool_registry = self._get_tool_registry(db)
        # 筛选工具
        active_tools = []
        if workflow.tools_config:
            active_tools = [tool_registry[name] for name in workflow.tools_config if name in tool_registry]

        # ================== [新增] 动态配置读取逻辑 ==================

        # A. 从数据库获取配置
        db_api_key = db.query(SystemSetting).filter(SystemSetting.key == "openai_api_key").first()
        db_base_url = db.query(SystemSetting).filter(SystemSetting.key == "openai_base_url").first()

        # B. 确定最终使用的配置 (DB > Env > 默认)
        final_api_key = db_api_key.value if (db_api_key and db_api_key.value) else settings.OPENAI_API_KEY
        final_base_url = db_base_url.value if (db_base_url and db_base_url.value) else settings.OPENAI_BASE_URL

        # C. 安全检查：如果没有 Key，直接返回提示，不调用 LLM
        if not final_api_key:
            return {
                "reply": "🚫 **未配置 API Key**\n\n请点击右上角的设置图标 (⚙️) 配置您的 AI 服务商密钥 (如 DeepSeek / OpenAI)。",
                "usage": None
            }

        # D. 自动判断模型名称 (根据 Base URL)
        # 如果 URL 包含 moonshot 用 moonshot-v1-8k，包含 deepseek 用 deepseek-chat，否则默认 gpt-3.5-turbo
        target_model = "deepseek-chat"
        if final_base_url and "moonshot" in final_base_url:
            target_model = "moonshot-v1-8k"
        elif final_base_url and "deepseek" in final_base_url:
            target_model = "deepseek-chat"
        elif not final_base_url or "openai" in str(final_base_url):
            target_model = "gpt-3.5-turbo"

        # 4. 初始化 LLM
        llm = ChatOpenAI(
            model=target_model,
            temperature=0.3,
            api_key=final_api_key,  # 使用动态 Key
            base_url=final_base_url  # 使用动态 URL
        )

        # ================== [结束] ==================

        if active_tools:
            llm_with_tools = llm.bind_tools(active_tools)
        else:
            llm_with_tools = llm

        # 5. 构建上下文
        history_messages = [SystemMessage(content=final_system_prompt)]

        # 获取最近历史记录
        recent_msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(
            ChatMessage.created_at.asc()).limit(8).all()
        for msg in recent_msgs:
            if msg.role == "user":
                history_messages.append(HumanMessage(content=msg.content))
            else:
                history_messages.append(AIMessage(content=msg.content))

        # 加上当前消息
        if not history_messages or history_messages[-1].content != message:
            history_messages.append(HumanMessage(content=message))

        # 定义默认返回值
        usage_data = None
        reply_text = ""
        executed_actions = []  # 🌟 追踪执行的动作

        # 6. 执行推理
        try:
            ai_response = llm_with_tools.invoke(history_messages)

            # 捕获 Token (第一轮)
            if hasattr(ai_response, 'response_metadata'):
                usage_data = ai_response.response_metadata.get('token_usage')

            if hasattr(ai_response, 'tool_calls') and ai_response.tool_calls:
                history_messages.append(ai_response)

                for tool_call in ai_response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_id = tool_call["id"]

                    print(f"🔧 Workflow [{workflow.name}] Action: {tool_name}")

                    selected_tool = tool_registry.get(tool_name)
                    if selected_tool:
                        try:
                            tool_output = selected_tool.invoke(tool_args)
                            executed_actions.append(tool_name)  # 记录成功调用的工具
                        except Exception as tool_err:
                            tool_output = f"Error executing {tool_name}: {tool_err}"
                    else:
                        tool_output = f"Error: Tool '{tool_name}' not allowed."

                    history_messages.append(ToolMessage(tool_call_id=tool_id, content=str(tool_output)))

                # 第二轮调用
                final_response = llm_with_tools.invoke(history_messages)
                reply_text = final_response.content

                # 更新 Token
                if hasattr(final_response, 'response_metadata'):
                    usage_data = final_response.response_metadata.get('token_usage')
            else:
                reply_text = ai_response.content

        except Exception as e:
            print(f"Workflow Error: {e}")
            reply_text = f"Error: {str(e)}"

        return {
            "reply": reply_text,
            "usage": usage_data,
            "actions": executed_actions # 🌟 返回动作列表
        }


ai_service = AIService()
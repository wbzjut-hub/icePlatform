from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from app.core.config import settings
from app.models.chat import ChatSession, ChatMessage
from app.models.workflow import Workflow
from app.models.setting import SystemSetting
from app.services.tools import get_todo_tools
import datetime
import json
from typing import AsyncGenerator, Dict, Any


class AIService:
    # 获取所有可用工具的注册表
    def _get_tool_registry(self, db: Session):
        raw_tools = get_todo_tools(db)
        return {t.name: t for t in raw_tools}

    def _get_llm_config(self, db: Session):
        """Get LLM configuration from database or fallback to env"""
        db_api_key = db.query(SystemSetting).filter(SystemSetting.key == "openai_api_key").first()
        db_base_url = db.query(SystemSetting).filter(SystemSetting.key == "openai_base_url").first()

        final_api_key = db_api_key.value if (db_api_key and db_api_key.value) else settings.OPENAI_API_KEY
        final_base_url = db_base_url.value if (db_base_url and db_base_url.value) else settings.OPENAI_BASE_URL

        # Auto-detect model based on URL
        target_model = "deepseek-chat"
        if final_base_url and "moonshot" in final_base_url:
            target_model = "moonshot-v1-8k"
        elif final_base_url and "deepseek" in final_base_url:
            target_model = "deepseek-chat"
        elif not final_base_url or "openai" in str(final_base_url):
            target_model = "gpt-3.5-turbo"

        return final_api_key, final_base_url, target_model

    def _build_messages(self, db: Session, workflow: Workflow, message: str, session_id: str):
        """Build message history for LLM"""
        week_days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        now = datetime.datetime.now()
        week_day_str = week_days[now.weekday()]
        today_str = now.strftime("%Y-%m-%d %H:%M")

        final_system_prompt = workflow.system_prompt.replace("{current_time}", f"{today_str} ({week_day_str})")

        history_messages = [SystemMessage(content=final_system_prompt)]

        recent_msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(
            ChatMessage.created_at.asc()).limit(8).all()
        for msg in recent_msgs:
            if msg.role == "user":
                history_messages.append(HumanMessage(content=msg.content))
            else:
                history_messages.append(AIMessage(content=msg.content))

        if not history_messages or history_messages[-1].content != message:
            history_messages.append(HumanMessage(content=message))

        return history_messages

    async def chat_with_workflow(self, db: Session, message: str, session_id: str, workflow_id: str = "wf_agent"):
        """Non-streaming chat (original implementation)"""
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        if not workflow:
            workflow = Workflow(
                name="Fallback",
                system_prompt="你是一个智能助手 IcePlatform Agent。当前时间是: {current_time}。",
                tools_config=[]
            )

        final_api_key, final_base_url, target_model = self._get_llm_config(db)

        if not final_api_key:
            return {
                "reply": "🚫 **未配置 API Key**\n\n请点击右上角的设置图标 (⚙️) 配置您的 AI 服务商密钥 (如 DeepSeek / OpenAI)。",
                "usage": None
            }

        tool_registry = self._get_tool_registry(db)
        active_tools = []
        if workflow.tools_config:
            active_tools = [tool_registry[name] for name in workflow.tools_config if name in tool_registry]

        llm = ChatOpenAI(
            model=target_model,
            temperature=0.3,
            api_key=final_api_key,
            base_url=final_base_url
        )

        if active_tools:
            llm_with_tools = llm.bind_tools(active_tools)
        else:
            llm_with_tools = llm

        history_messages = self._build_messages(db, workflow, message, session_id)

        usage_data = None
        reply_text = ""
        executed_actions = []

        try:
            ai_response = llm_with_tools.invoke(history_messages)

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
                            executed_actions.append(tool_name)
                        except Exception as tool_err:
                            tool_output = f"Error executing {tool_name}: {tool_err}"
                    else:
                        tool_output = f"Error: Tool '{tool_name}' not allowed."

                    history_messages.append(ToolMessage(tool_call_id=tool_id, content=str(tool_output)))

                final_response = llm_with_tools.invoke(history_messages)
                reply_text = final_response.content

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
            "actions": executed_actions
        }

    async def chat_with_workflow_stream(
        self, db: Session, message: str, session_id: str, workflow_id: str = "wf_agent"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streaming chat - yields content chunks"""
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()

        if not workflow:
            workflow = Workflow(
                name="Fallback",
                system_prompt="你是一个智能助手 IcePlatform Agent。当前时间是: {current_time}。",
                tools_config=[]
            )

        final_api_key, final_base_url, target_model = self._get_llm_config(db)

        if not final_api_key:
            yield {"type": "error", "error": "未配置 API Key，请在设置中配置。"}
            return

        tool_registry = self._get_tool_registry(db)
        active_tools = []
        if workflow.tools_config:
            active_tools = [tool_registry[name] for name in workflow.tools_config if name in tool_registry]

        llm = ChatOpenAI(
            model=target_model,
            temperature=0.3,
            api_key=final_api_key,
            base_url=final_base_url,
            streaming=True  # Enable streaming
        )

        if active_tools:
            llm_with_tools = llm.bind_tools(active_tools)
        else:
            llm_with_tools = llm

        history_messages = self._build_messages(db, workflow, message, session_id)

        try:
            # Use astream for async streaming
            async for chunk in llm_with_tools.astream(history_messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield {"type": "content", "content": chunk.content}
                
                # Check for usage info in the last chunk
                if hasattr(chunk, 'response_metadata') and chunk.response_metadata:
                    usage = chunk.response_metadata.get('token_usage')
                    if usage:
                        yield {"type": "usage", "usage": usage}

        except Exception as e:
            print(f"Streaming Error: {e}")
            yield {"type": "error", "error": str(e)}


ai_service = AIService()
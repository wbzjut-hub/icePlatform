from langchain_core.tools import tool
from sqlalchemy.orm import Session
from app.models.todo import TodoItem
from app.core.config import settings
import datetime
import uuid
import os

# 🌟 [修改] 搜索工具导入逻辑：优先使用新包，消除警告
SEARCH_AVAILABLE = False
TavilySearchResults = None

try:
    # 1. 尝试导入新版 (推荐)
    from langchain_tavily import TavilySearchResults

    SEARCH_AVAILABLE = True
except ImportError:
    try:
        # 2. 回退到旧版 (会有警告，但在旧环境中可用)
        from langchain_community.tools.tavily_search import TavilySearchResults

        SEARCH_AVAILABLE = True
    except ImportError:
        pass


def get_todo_tools(db: Session):
    tools = []

    @tool
    def add_todo(content: str, target_date: str = None, type: str = "todo"):
        """添加待办事项到数据库。
        Args:
            content: 待办内容 (例如: "买牛奶", "写代码")
            target_date: 日期字符串，格式 YYYY-MM-DD。如果用户没说，默认今天。
            type: 类型，固定为 "todo"。
        """
        if not target_date:
            target_date = datetime.datetime.now().strftime("%Y-%m-%d")

        new_item = TodoItem(
            id=f"ai_{uuid.uuid4().hex[:8]}",
            date=target_date,
            type=type,
            text=content
        )
        try:
            db.add(new_item)
            db.commit()
            return f"成功添加待办: 【{content}】 到 {target_date}"
        except Exception as e:
            return f"写入数据库失败: {e}"

    tools.append(add_todo)

    @tool
    def query_todos(query_date: str):
        """查询指定日期的待办事项。
        Args:
            query_date: 日期字符串，格式 YYYY-MM-DD。
        """
        items = db.query(TodoItem).filter(TodoItem.date == query_date).all()
        if not items:
            return f"{query_date} 没有待办事项。"

        result = f"{query_date} 的待办清单:\n"
        for i, item in enumerate(items, 1):
            status = "[x]" if item.done else "[ ]"
            result += f"{i}. {status} {item.text}\n"
        return result

    tools.append(query_todos)

    # 🌟 [修改] 联网搜索工具配置
    if SEARCH_AVAILABLE and TavilySearchResults:
        # 优先从 settings 读取，其次从环境变量读取
        api_key = getattr(settings, "TAVILY_API_KEY", None) or os.environ.get("TAVILY_API_KEY")

        if api_key:
            # max_results 控制搜索结果数量
            tavily_tool = TavilySearchResults(max_results=3, tavily_api_key=api_key)

            @tool
            def web_search(query: str):
                """联网搜索工具。当用户询问实时信息（如天气、新闻、股价）时使用。
                Args:
                    query: 搜索关键词。
                """
                try:
                    # invoke 返回的是结构化数据，转字符串给 LLM
                    return str(tavily_tool.invoke({"query": query}))
                except Exception as e:
                    return f"搜索失败: {e}"

            tools.append(web_search)

    return tools
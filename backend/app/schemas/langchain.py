from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-3.5-turbo" # 或者是 deepseek-chat 等
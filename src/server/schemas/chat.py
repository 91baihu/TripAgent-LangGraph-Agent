"""对话相关 Pydantic 模型"""

from typing import Optional, List
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """单条对话消息"""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=5000)


class ChatRequest(BaseModel):
    """对话请求"""
    messages: List[ChatMessage] = Field(..., min_items=1, max_items=50)
    travel_plan: Optional[dict] = Field(default=None, description="已有的旅行计划（增量修改时传入）")
    stream: bool = Field(default=True, description="是否使用 SSE 流式返回")

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "user", "content": "帮我规划3天北京亲子游，孩子5岁"}
                ],
                "stream": True,
            }
        }


class ChatReply(BaseModel):
    """对话回复（非流式）"""
    reply: str
    trace: List[dict] = Field(default_factory=list)
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    message: str
    request_id: Optional[str] = None

"""
OpenAI 兼容 API 数据模型

完全兼容 OpenAI Chat Completion API 格式。
"""

from typing import Literal

from pydantic import BaseModel, Field


# ===== 请求模型 =====
class ChatMessage(BaseModel):
    """对话消息"""

    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    """OpenAI Chat Completion 请求"""

    model: str = Field(default="deepseek-chat", description="模型名称（兼容性参数）")
    messages: list[ChatMessage] = Field(..., min_length=1, description="对话消息列表")
    stream: bool = Field(default=False, description="是否启用流式响应")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int | None = Field(default=None, ge=1, description="最大生成 Token 数")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="核采样参数")


# ===== 响应模型 =====
class ChatCompletionChoice(BaseModel):
    """响应选项"""

    index: int
    message: ChatMessage
    finish_reason: Literal["stop", "length", "tool_calls"] | None = None


class ChatCompletionUsage(BaseModel):
    """Token 使用统计"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """OpenAI Chat Completion 响应"""

    id: str = Field(..., description="响应ID")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(..., description="Unix 时间戳")
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage


# ===== 流式响应模型 =====
class ChatCompletionChunkDelta(BaseModel):
    """流式响应增量"""

    role: str | None = None
    content: str | None = None


class ChatCompletionChunkChoice(BaseModel):
    """流式响应选项"""

    index: int
    delta: ChatCompletionChunkDelta
    finish_reason: str | None = None


class ChatCompletionChunk(BaseModel):
    """OpenAI 流式响应块"""

    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: list[ChatCompletionChunkChoice]


# ===== 模型列表（/v1/models） =====
class OpenAIModelRef(BaseModel):
    """OpenAI 模型引用对象（兼容 /v1/models 返回项）。"""

    id: str
    object: Literal["model"] = "model"
    created: int
    owned_by: str


class OpenAIModelList(BaseModel):
    """OpenAI 模型列表响应（/v1/models）。"""

    object: Literal["list"] = "list"
    data: list[OpenAIModelRef]


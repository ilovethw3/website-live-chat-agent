"""
LangGraph Agent 状态定义

AgentState 定义了 Agent 在执行过程中的所有状态信息。
"""

from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Agent 状态

    使用 TypedDict 定义状态结构，LangGraph 会自动处理状态更新。

    Attributes:
        messages: 对话消息历史（自动合并）
        retrieved_docs: 从 Milvus 检索到的知识库文档列表
        tool_calls: 工具调用记录（用于调试和追踪）
        session_id: 会话ID（用于 Checkpointer）
        next_step: 路由决策结果（"retrieve" 或 "direct"）
        error: 错误信息（如果执行失败）
        confidence_score: 置信度分数（0-1，用于判断是否需要人工介入）
    """

    # 对话消息（使用 add_messages reducer 自动合并历史）
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # 检索到的知识库文档
    retrieved_docs: list[str]

    # 工具调用记录
    tool_calls: list[dict]

    # 会话ID
    session_id: str

    # 路由决策
    next_step: str | None

    # 错误信息
    error: str | None

    # 置信度分数
    confidence_score: float | None


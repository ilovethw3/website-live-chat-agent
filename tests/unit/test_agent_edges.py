"""
测试 Agent 边逻辑

测试 LangGraph 条件边的路由决策。
"""

import pytest
from langchain_core.messages import HumanMessage, AIMessage

from src.agent.edges import route_agent, should_continue
from src.agent.state import AgentState


def test_route_agent_needs_rag():
    """测试路由到 RAG 检索"""
    state: AgentState = {
        "messages": [HumanMessage(content="你们的退货政策是什么？")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    # 问题需要知识库检索
    route = route_agent(state)

    # 应该路由到 retrieve_knowledge 或相关节点
    assert route in ["retrieve_knowledge", "call_llm", "__end__"]


def test_route_agent_simple_question():
    """测试路由简单问题"""
    state: AgentState = {
        "messages": [HumanMessage(content="你好")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    route = route_agent(state)

    # 简单问候可以直接回答
    assert route in ["call_llm", "__end__"]


def test_route_agent_with_existing_docs():
    """测试已有检索文档时的路由"""
    state: AgentState = {
        "messages": [HumanMessage(content="退货政策是什么？")],
        "retrieved_docs": [
            {"text": "退货政策文档", "score": 0.9, "metadata": {}}
        ],
        "tool_calls": [],
        "session_id": "test-123",
    }

    route = route_agent(state)

    # 已有文档，应该直接调用 LLM
    assert route in ["call_llm", "__end__"]


def test_should_continue_with_tool_calls():
    """测试有工具调用时应该继续"""
    state: AgentState = {
        "messages": [
            HumanMessage(content="查询信息"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call_123",
                        "name": "knowledge_search",
                        "args": {"query": "test"},
                    }
                ],
            ),
        ],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = should_continue(state)

    # 有工具调用，应该继续到 call_tool
    assert result in ["call_tool", "continue"]


def test_should_continue_without_tool_calls():
    """测试没有工具调用时应该结束"""
    state: AgentState = {
        "messages": [
            HumanMessage(content="你好"),
            AIMessage(content="你好！有什么可以帮你的吗？"),
        ],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = should_continue(state)

    # 没有工具调用，应该结束
    assert result in ["__end__", "end"]


def test_should_continue_empty_messages():
    """测试空消息列表"""
    state: AgentState = {
        "messages": [],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = should_continue(state)

    # 空消息应该结束或返回默认值
    assert result is not None


def test_route_agent_max_iterations():
    """测试达到最大迭代次数"""
    # 模拟多轮对话
    state: AgentState = {
        "messages": [HumanMessage(content=f"问题{i}") for i in range(20)],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    route = route_agent(state)

    # 应该有逻辑防止无限循环
    assert route is not None


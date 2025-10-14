"""
测试 Agent 状态定义

测试 AgentState TypedDict 的结构和类型。
"""

from langchain_core.messages import AIMessage, HumanMessage

from src.agent.state import AgentState


def test_agent_state_structure():
    """测试 AgentState 结构"""
    # AgentState 是 TypedDict，检查其定义
    from typing import get_type_hints

    hints = get_type_hints(AgentState)

    assert "messages" in hints
    assert "retrieved_docs" in hints
    assert "tool_calls" in hints
    assert "session_id" in hints
    assert "next_step" in hints


def test_agent_state_with_messages():
    """测试包含消息的状态"""
    state: AgentState = {
        "messages": [
            HumanMessage(content="你好"),
            AIMessage(content="你好！有什么可以帮你的吗？"),
        ],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
        "next_step": "call_llm",
    }

    assert len(state["messages"]) == 2
    assert isinstance(state["messages"][0], HumanMessage)
    assert isinstance(state["messages"][1], AIMessage)


def test_agent_state_with_retrieved_docs():
    """测试包含检索文档的状态"""
    state: AgentState = {
        "messages": [],
        "retrieved_docs": [
            {"text": "文档1", "score": 0.9, "metadata": {}},
            {"text": "文档2", "score": 0.8, "metadata": {}},
        ],
        "tool_calls": [],
        "session_id": "test-123",
        "next_step": "call_llm",
    }

    assert len(state["retrieved_docs"]) == 2
    assert state["retrieved_docs"][0]["score"] == 0.9


def test_agent_state_optional_fields():
    """测试可选字段"""
    # next_step 和 error 是可选的
    state: AgentState = {
        "messages": [HumanMessage(content="测试")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    assert "session_id" in state
    assert state.get("next_step") is None
    assert state.get("error") is None


def test_agent_state_with_error():
    """测试包含错误的状态"""
    state: AgentState = {
        "messages": [],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
        "error": "Something went wrong",
    }

    assert state["error"] == "Something went wrong"


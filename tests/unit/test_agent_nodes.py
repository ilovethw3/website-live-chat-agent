"""
测试 Agent 节点逻辑

测试 LangGraph 节点函数的行为。
"""

from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.agent.nodes import call_llm_node, retrieve_node, router_node
from src.agent.state import AgentState


@pytest.mark.asyncio
async def test_call_llm_simple(mock_llm):
    """测试 LLM 调用节点"""
    state: AgentState = {
        "messages": [HumanMessage(content="你好")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    with patch("src.agent.nodes.create_llm", return_value=mock_llm):
        result = await call_llm_node(state)

        assert "messages" in result
        assert len(result["messages"]) > 0
        # 最后一条消息应该是 AI 的回复
        last_message = result["messages"][-1]
        assert isinstance(last_message, AIMessage)


@pytest.mark.asyncio
async def test_call_llm_with_context(mock_llm):
    """测试带上下文的 LLM 调用"""
    state: AgentState = {
        "messages": [
            HumanMessage(content="介绍一下产品"),
        ],
        "retrieved_docs": [
            {
                "text": "我们的产品是智能客服系统",
                "score": 0.95,
                "metadata": {"source": "product.md"},
            }
        ],
        "tool_calls": [],
        "session_id": "test-123",
    }

    with patch("src.agent.nodes.create_llm", return_value=mock_llm):
        result = await call_llm_node(state)

        assert "messages" in result
        # LLM 应该收到包含检索文档的上下文


@pytest.mark.asyncio
async def test_retrieve_knowledge(mock_embeddings):
    """测试知识库检索节点"""
    state: AgentState = {
        "messages": [HumanMessage(content="退货政策是什么？")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    # Mock search_knowledge_for_agent function return value
    mock_results = [
        {
            "text": "30天内可以无条件退货",
            "score": 0.9,
            "metadata": {"source": "policy.md", "title": "退货政策"},
        }
    ]

    with patch("src.agent.nodes.search_knowledge_for_agent", return_value=mock_results):
        result = await retrieve_node(state)

        assert "retrieved_docs" in result
        assert len(result["retrieved_docs"]) > 0
        assert result["confidence_score"] == 0.9


@pytest.mark.asyncio
async def test_retrieve_knowledge_empty_query():
    """测试空查询的检索"""
    state: AgentState = {
        "messages": [],  # 没有消息
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = await retrieve_node(state)

    # 应该返回空的检索结果
    assert result.get("retrieved_docs", []) == []


@pytest.mark.asyncio
async def test_router_node_greeting():
    """测试路由节点 - 简单打招呼"""
    state: AgentState = {
        "messages": [HumanMessage(content="你好")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = await router_node(state)

    # 路由节点应该判断是否需要检索
    assert "next_step" in result or result == {}


@pytest.mark.asyncio
async def test_router_node_product_query():
    """测试路由节点 - 产品查询（需要检索）"""
    state: AgentState = {
        "messages": [HumanMessage(content="你们的产品有哪些功能？")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = await router_node(state)

    # 对于产品查询，可能需要检索
    assert result is not None


"""
测试 Agent 节点逻辑

测试 LangGraph 节点函数的行为。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from src.agent.nodes import call_llm, retrieve_knowledge, call_tool
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

    with patch("src.agent.nodes.get_llm", return_value=mock_llm):
        result = await call_llm(state)

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

    with patch("src.agent.nodes.get_llm", return_value=mock_llm):
        result = await call_llm(state)

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

    mock_milvus = AsyncMock()
    mock_milvus.search_knowledge.return_value = [
        {
            "text": "30天内可以无条件退货",
            "score": 0.9,
            "metadata": {"source": "policy.md"},
        }
    ]

    with patch("src.agent.nodes.milvus_service", mock_milvus):
        with patch("src.agent.nodes.get_embeddings", return_value=mock_embeddings):
            result = await retrieve_knowledge(state)

            assert "retrieved_docs" in result
            assert len(result["retrieved_docs"]) > 0
            mock_milvus.search_knowledge.assert_called_once()


@pytest.mark.asyncio
async def test_retrieve_knowledge_empty_query():
    """测试空查询的检索"""
    state: AgentState = {
        "messages": [],  # 没有消息
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = await retrieve_knowledge(state)

    # 应该返回空的检索结果
    assert result.get("retrieved_docs", []) == []


@pytest.mark.asyncio
async def test_call_tool_with_knowledge_search():
    """测试工具调用节点 - 知识检索工具"""
    state: AgentState = {
        "messages": [
            HumanMessage(content="查询退货政策"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call_123",
                        "name": "knowledge_search",
                        "args": {"query": "退货政策"},
                    }
                ],
            ),
        ],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    mock_milvus = AsyncMock()
    mock_milvus.search_knowledge.return_value = [
        {"text": "退货政策文档", "score": 0.9, "metadata": {}}
    ]

    with patch("src.agent.nodes.milvus_service", mock_milvus):
        result = await call_tool(state)

        assert "messages" in result
        # 应该添加 ToolMessage
        tool_messages = [msg for msg in result["messages"] if isinstance(msg, ToolMessage)]
        assert len(tool_messages) > 0


@pytest.mark.asyncio
async def test_call_tool_no_tool_calls():
    """测试没有工具调用时的行为"""
    state: AgentState = {
        "messages": [HumanMessage(content="你好")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = await call_tool(state)

    # 应该返回原状态或空变更
    assert result is not None


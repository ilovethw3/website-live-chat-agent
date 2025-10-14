"""
测试 LangGraph Agent 完整流程

测试 Agent 的端到端执行流程。
"""

from unittest.mock import patch

import pytest
from langchain_core.messages import HumanMessage

from src.agent.graph import get_agent_app
from src.agent.state import AgentState


@pytest.mark.asyncio
async def test_agent_graph_simple_chat(mock_llm, mock_milvus_service):
    """测试简单对话流程"""
    with patch("src.agent.nodes.get_llm", return_value=mock_llm):
        with patch("src.agent.nodes.milvus_service", mock_milvus_service):
            app = get_agent_app()

            initial_state: AgentState = {
                "messages": [HumanMessage(content="你好")],
                "retrieved_docs": [],
                "tool_calls": [],
                "session_id": "test-session-123",
            }

            config = {"configurable": {"thread_id": "test-thread-1"}}

            # 执行 Agent
            result = await app.ainvoke(initial_state, config=config)

            assert "messages" in result
            assert len(result["messages"]) > 1  # 至少有用户消息和 AI 回复


@pytest.mark.asyncio
async def test_agent_graph_with_rag(mock_llm, mock_milvus_service, mock_embeddings):
    """测试带 RAG 检索的流程"""
    # Mock Milvus 返回相关文档
    mock_milvus_service.search_knowledge.return_value = [
        {
            "text": "我们的退货政策是30天内无条件退货",
            "score": 0.95,
            "metadata": {"source": "policy.md"},
        }
    ]

    with patch("src.agent.nodes.get_llm", return_value=mock_llm):
        with patch("src.agent.nodes.milvus_service", mock_milvus_service):
            with patch("src.agent.nodes.get_embeddings", return_value=mock_embeddings):
                app = get_agent_app()

                initial_state: AgentState = {
                    "messages": [HumanMessage(content="退货政策是什么？")],
                    "retrieved_docs": [],
                    "tool_calls": [],
                    "session_id": "test-session-456",
                }

                config = {"configurable": {"thread_id": "test-thread-2"}}

                result = await app.ainvoke(initial_state, config=config)

                assert "messages" in result
                # 应该调用过 Milvus 检索
                mock_milvus_service.search_knowledge.assert_called()


@pytest.mark.asyncio
async def test_agent_graph_multi_turn(mock_llm, mock_milvus_service):
    """测试多轮对话"""
    with patch("src.agent.nodes.get_llm", return_value=mock_llm):
        with patch("src.agent.nodes.milvus_service", mock_milvus_service):
            app = get_agent_app()

            config = {"configurable": {"thread_id": "test-thread-3"}}

            # 第一轮对话
            state1: AgentState = {
                "messages": [HumanMessage(content="你好")],
                "retrieved_docs": [],
                "tool_calls": [],
                "session_id": "test-session-789",
            }

            result1 = await app.ainvoke(state1, config=config)
            assert len(result1["messages"]) >= 2

            # 第二轮对话（基于第一轮的状态）
            state2: AgentState = {
                **result1,
                "messages": result1["messages"]
                + [HumanMessage(content="你叫什么名字？")],
            }

            result2 = await app.ainvoke(state2, config=config)
            assert len(result2["messages"]) > len(result1["messages"])


@pytest.mark.asyncio
async def test_agent_graph_error_handling(mock_llm):
    """测试错误处理"""
    # Mock LLM 抛出异常
    mock_llm.ainvoke.side_effect = Exception("LLM error")

    with patch("src.agent.nodes.get_llm", return_value=mock_llm):
        app = get_agent_app()

        initial_state: AgentState = {
            "messages": [HumanMessage(content="测试")],
            "retrieved_docs": [],
            "tool_calls": [],
            "session_id": "test-error",
        }

        config = {"configurable": {"thread_id": "test-thread-error"}}

        # Agent 应该能处理异常
        with pytest.raises(Exception):
            await app.ainvoke(initial_state, config=config)


@pytest.mark.asyncio
async def test_agent_graph_state_persistence(mock_llm, mock_milvus_service):
    """测试状态持久化"""
    with patch("src.agent.nodes.get_llm", return_value=mock_llm):
        with patch("src.agent.nodes.milvus_service", mock_milvus_service):
            app = get_agent_app()

            thread_id = "test-thread-persist"
            config = {"configurable": {"thread_id": thread_id}}

            # 第一次调用
            state1: AgentState = {
                "messages": [HumanMessage(content="记住我叫张三")],
                "retrieved_docs": [],
                "tool_calls": [],
                "session_id": "test-persist-1",
            }

            _ = await app.ainvoke(state1, config=config)

            # 第二次调用，使用相同的 thread_id
            state2: AgentState = {
                "messages": [HumanMessage(content="我叫什么名字？")],
                "retrieved_docs": [],
                "tool_calls": [],
                "session_id": "test-persist-2",
            }

            result2 = await app.ainvoke(state2, config=config)

            # 状态应该被保留（取决于 checkpointer 实现）
            assert "messages" in result2


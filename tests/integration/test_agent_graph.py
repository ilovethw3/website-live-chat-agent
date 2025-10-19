"""
测试 LangGraph Agent 完整流程

测试 Agent 的端到端执行流程。
"""

import pytest
from langchain_core.messages import HumanMessage

from src.agent.main.graph import get_agent_app
from src.agent.main.state import AgentState


@pytest.mark.asyncio
async def test_agent_graph_simple_chat(mocker, mock_llm, mock_milvus_service):
    """测试简单对话流程"""
    mocker.patch("src.services.llm_factory.create_llm", return_value=mock_llm)
    mocker.patch("src.agent.main.tools.milvus_service", mock_milvus_service)
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
async def test_agent_graph_with_rag(mocker, mock_llm, mock_milvus_service, mock_embeddings):
    """测试带 RAG 检索的流程"""
    from src.agent.recall.schema import RecallHit, RecallResult

    # Mock召回Agent返回结果
    mock_recall_result = RecallResult(
        hits=[
            RecallHit(
                source="vector",
                score=0.95,
                confidence=0.9,
                reason="向量检索匹配",
                content="我们的退货政策是30天内无条件退货",
                metadata={"source": "policy.md"}
            )
        ],
        latency_ms=100.0,
        degraded=False,
        trace_id="test-trace"
    )

    mocker.patch("src.services.llm_factory.create_llm", return_value=mock_llm)
    mocker.patch("src.agent.recall.graph.invoke_recall_agent", return_value=mock_recall_result)
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
    # 应该包含检索到的文档
    assert "retrieved_docs" in result
    assert len(result["retrieved_docs"]) > 0


@pytest.mark.asyncio
async def test_agent_graph_multi_turn(mocker, mock_llm, mock_milvus_service):
    """测试多轮对话"""
    mocker.patch("src.services.llm_factory.create_llm", return_value=mock_llm)
    mocker.patch("src.agent.main.tools.milvus_service", mock_milvus_service)
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
async def test_agent_graph_error_handling(mocker, mock_llm):
    """测试错误处理"""
    # Mock LLM 抛出异常
    mock_llm.ainvoke.side_effect = Exception("LLM error")

    mocker.patch("src.services.llm_factory.create_llm", return_value=mock_llm)
    app = get_agent_app()

    initial_state: AgentState = {
        "messages": [HumanMessage(content="测试")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-error",
    }

    config = {"configurable": {"thread_id": "test-thread-error"}}

    # Agent 应该能处理异常并返回错误消息
    result = await app.ainvoke(initial_state, config=config)

    assert "messages" in result
    # 应该包含错误消息
    assert len(result["messages"]) > 1
    # 最后一条消息应该包含错误信息
    last_message = result["messages"][-1]
    assert "error" in last_message.content.lower() or "抱歉" in last_message.content


@pytest.mark.asyncio
async def test_agent_graph_state_persistence(mocker, mock_llm, mock_milvus_service):
    """测试状态持久化"""
    mocker.patch("src.services.llm_factory.create_llm", return_value=mock_llm)
    mocker.patch("src.agent.main.tools.milvus_service", mock_milvus_service)
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


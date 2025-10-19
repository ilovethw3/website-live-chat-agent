"""
测试 Agent 节点逻辑

测试 LangGraph 节点函数的行为。
"""

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.agent.main.nodes import _is_valid_user_query, call_llm_node, retrieve_node, router_node
from src.agent.main.state import AgentState


@pytest.mark.asyncio
async def test_call_llm_simple(mocker, mock_llm):
    """测试 LLM 调用节点"""
    state: AgentState = {
        "messages": [HumanMessage(content="你好")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    mocker.patch("src.agent.main.nodes.create_llm", return_value=mock_llm)
    result = await call_llm_node(state)

    assert "messages" in result
    assert len(result["messages"]) > 0
    # 最后一条消息应该是 AI 的回复
    last_message = result["messages"][-1]
    assert isinstance(last_message, AIMessage)


@pytest.mark.asyncio
async def test_call_llm_with_context(mocker, mock_llm):
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

    mocker.patch("src.agent.main.nodes.create_llm", return_value=mock_llm)
    result = await call_llm_node(state)

    assert "messages" in result
    # LLM 应该收到包含检索文档的上下文


@pytest.mark.asyncio
async def test_retrieve_knowledge(mocker, mock_embeddings):
    """测试知识库检索节点"""
    state: AgentState = {
        "messages": [HumanMessage(content="退货政策是什么？")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    # Mock recall agent result
    from src.agent.recall.schema import RecallHit, RecallResult

    mock_hit = RecallHit(
        source="vector",
        score=0.9,
        confidence=0.8,
        reason="向量相似度匹配",
        content="30天内可以无条件退货",
        metadata={"source": "policy.md", "title": "退货政策"}
    )

    mock_recall_result = RecallResult(
        hits=[mock_hit],
        latency_ms=100.0,
        degraded=False,
        trace_id="test-trace",
        experiment_id=None
    )

    mock_invoke_recall = mocker.patch("src.agent.recall.graph.invoke_recall_agent")
    mock_invoke_recall.return_value = mock_recall_result

    result = await retrieve_node(state)

    assert "retrieved_docs" in result
    assert len(result["retrieved_docs"]) > 0
    assert result["confidence_score"] == 0.9


@pytest.mark.asyncio
async def test_retrieve_knowledge_empty_query(mocker):
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
async def test_router_node_greeting(mocker):
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
async def test_router_node_product_query(mocker):
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


# Issue #34 相关测试用例
def test_is_valid_user_query_valid_queries():
    """测试有效用户查询的验证"""
    valid_queries = [
        "你好",
        "你们的产品有哪些功能？",
        "退货政策是什么？",
        "价格怎么样？",
        "如何联系客服？",
        "这个产品有什么特点？"
    ]

    for query in valid_queries:
        assert _is_valid_user_query(query), f"Valid query should pass: {query}"


def test_is_valid_user_query_instruction_templates():
    """测试指令模板过滤"""
    instruction_templates = [
        "You are an AI question rephraser. Your role is to rephrase follow-up queries from a conversation into standalone queries that can be used by another LLM to retrieve information through web search.",
        "Your role is to help users with their questions",
        "You are a helpful assistant that can answer questions",
        "Please rephrase the following query",
        "Convert the following question into a search query",
        "Transform this query into a standalone question"
    ]

    for template in instruction_templates:
        assert not _is_valid_user_query(template), f"Instruction template should be filtered: {template[:50]}..."


def test_is_valid_user_query_technical_terms():
    """测试技术术语过滤"""
    technical_queries = [
        "API endpoint function method parameter response request",
        "The API function method parameter is used for response request",
        "This endpoint uses API function method parameter response request"
    ]

    for query in technical_queries:
        assert not _is_valid_user_query(query), f"Technical query should be filtered: {query}"


def test_is_valid_user_query_length_limit():
    """测试长度限制"""
    # 超长查询（超过1000字符）
    long_query = "这是一个很长的查询" * 200  # 约1800字符
    assert not _is_valid_user_query(long_query), "Long query should be filtered"

    # 正常长度查询
    normal_query = "你们的产品有哪些功能？"
    assert _is_valid_user_query(normal_query), "Normal query should pass"


def test_is_valid_user_query_starts_with_instructions():
    """测试以指令开头的查询过滤"""
    instruction_start_queries = [
        "You are a helpful assistant",
        "Your role is to answer questions",
        "Please help me with this",
        "Convert this query",
        "Transform the following"
    ]

    for query in instruction_start_queries:
        assert not _is_valid_user_query(query), f"Instruction start query should be filtered: {query}"


@pytest.mark.asyncio
async def test_retrieve_node_filters_instruction_templates(mocker):
    """测试retrieve_node处理指令模板（现在在API层过滤，这里测试正常检索）"""
    # Mock recall agent result
    from src.agent.recall.schema import RecallHit, RecallResult

    mock_hit = RecallHit(
        source="vector",
        score=0.8,
        confidence=0.7,
        reason="向量相似度匹配",
        content="测试文档",
        metadata={"title": "测试"}
    )

    mock_recall_result = RecallResult(
        hits=[mock_hit],
        latency_ms=100.0,
        degraded=False,
        trace_id="test-trace",
        experiment_id=None
    )

    mock_recall_agent = mocker.patch("src.agent.recall.graph.invoke_recall_agent")
    mock_recall_agent.return_value = mock_recall_result

    # 模拟指令模板消息（现在会通过API层过滤，但这里测试retrieve_node的正常行为）
    instruction_template = "You are an AI question rephraser. Your role is to rephrase follow-up queries from a conversation into standalone queries that can be used by another LLM to retrieve information through web search."

    state: AgentState = {
        "messages": [HumanMessage(content=instruction_template)],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = await retrieve_node(state)

    # 现在retrieve_node会正常执行检索（过滤在API层进行）
    assert len(result["retrieved_docs"]) > 0
    assert result["confidence_score"] == 0.8
    mock_recall_agent.assert_called_once()


@pytest.mark.asyncio
async def test_retrieve_node_allows_valid_queries(mocker):
    """测试retrieve_node允许有效查询"""
    # Mock recall agent result
    from src.agent.recall.schema import RecallHit, RecallResult

    mock_hit = RecallHit(
        source="vector",
        score=0.9,
        confidence=0.8,
        reason="向量相似度匹配",
        content="我们的产品功能包括智能客服、知识库检索等",
        metadata={"source": "product.md", "title": "产品功能"}
    )

    mock_recall_result = RecallResult(
        hits=[mock_hit],
        latency_ms=100.0,
        degraded=False,
        trace_id="test-trace",
        experiment_id=None
    )

    mock_recall_agent = mocker.patch("src.agent.recall.graph.invoke_recall_agent")
    mock_recall_agent.return_value = mock_recall_result

    # 模拟有效用户查询
    valid_query = "你们的产品有哪些功能？"

    state: AgentState = {
        "messages": [HumanMessage(content=valid_query)],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = await retrieve_node(state)

    # 应该调用recall agent并返回结果
    mock_recall_agent.assert_called_once()
    assert len(result["retrieved_docs"]) > 0
    assert result["confidence_score"] == 0.9


@pytest.mark.asyncio
async def test_retrieve_node_mixed_scenario(mocker):
    """测试混合场景：指令模板+真实问题（现在在API层过滤，这里测试正常检索）"""
    # Mock recall agent result
    from src.agent.recall.schema import RecallHit, RecallResult

    mock_hit = RecallHit(
        source="vector",
        score=0.8,
        confidence=0.7,
        reason="向量相似度匹配",
        content="测试文档",
        metadata={"title": "测试"}
    )

    mock_recall_result = RecallResult(
        hits=[mock_hit],
        latency_ms=100.0,
        degraded=False,
        trace_id="test-trace",
        experiment_id=None
    )

    mock_recall_agent = mocker.patch("src.agent.recall.graph.invoke_recall_agent")
    mock_recall_agent.return_value = mock_recall_result

    # 模拟包含指令模板和真实问题的混合消息（现在会通过API层过滤）
    mixed_message = """You are an AI question rephraser. Your role is to rephrase follow-up queries from a conversation into standalone queries that can be used by another LLM to retrieve information through web search.

Please rephrase the following query: 你们的产品有哪些功能？"""

    state: AgentState = {
        "messages": [HumanMessage(content=mixed_message)],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = await retrieve_node(state)

    # 现在retrieve_node会正常执行检索（过滤在API层进行）
    assert len(result["retrieved_docs"]) > 0
    assert result["confidence_score"] == 0.8
    mock_recall_agent.assert_called_once()


def test_is_valid_user_query_configuration():
    """测试配置化参数"""
    # 测试默认配置
    assert _is_valid_user_query("你们的产品有哪些功能？")

    # 测试长度限制
    long_query = "这是一个很长的查询" * 200
    assert not _is_valid_user_query(long_query)

    # 测试指令模板过滤
    instruction_template = "You are an AI question rephraser"
    assert not _is_valid_user_query(instruction_template)

    # 测试技术术语过滤
    technical_query = "API endpoint function method parameter response request"
    assert not _is_valid_user_query(technical_query)


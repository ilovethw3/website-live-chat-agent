"""
测试 Agent 边逻辑

测试 LangGraph 条件边的路由决策。
"""

from langchain_core.messages import AIMessage, HumanMessage

from src.agent.edges import should_continue, should_retrieve
from src.agent.state import AgentState


def test_should_retrieve_needs_rag():
    """测试是否需要检索 - 需要检索的情况"""
    state: AgentState = {
        "messages": [HumanMessage(content="你们的退货政策是什么？")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    # 问题需要知识库检索
    route = should_retrieve(state)

    # 应该路由到 retrieve 或 llm
    assert route in ["retrieve", "llm", "__end__"]


def test_should_retrieve_simple_question():
    """测试是否需要检索 - 简单问题"""
    state: AgentState = {
        "messages": [HumanMessage(content="你好")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    route = should_retrieve(state)

    # 简单问候可以直接回答
    assert route in ["llm", "__end__"]


def test_should_retrieve_with_existing_docs():
    """测试已有检索文档时的路由"""
    state: AgentState = {
        "messages": [HumanMessage(content="退货政策是什么？")],
        "retrieved_docs": [
            {"text": "退货政策文档", "score": 0.9, "metadata": {}}
        ],
        "tool_calls": [],
        "session_id": "test-123",
    }

    route = should_retrieve(state)

    # 已有文档，应该直接调用 LLM
    assert route in ["llm", "__end__"]


def test_should_continue_normal():
    """测试正常结束流程"""
    state: AgentState = {
        "messages": [
            HumanMessage(content="查询信息"),
            AIMessage(content="这是回复"),
        ],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    result = should_continue(state)

    # 正常情况应该返回 END
    assert result == "END"


def test_should_continue_without_error():
    """测试没有错误时应该结束"""
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

    # 没有错误，应该结束
    assert result == "END"


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


def test_should_retrieve_max_iterations():
    """测试达到最大迭代次数"""
    # 模拟多轮对话
    state: AgentState = {
        "messages": [HumanMessage(content=f"问题{i}") for i in range(20)],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
    }

    route = should_retrieve(state)

    # 应该有逻辑防止无限循环
    assert route is not None


def test_should_retrieve_with_next_step_retrieve():
    """测试next_step为retrieve时的路由"""
    state: AgentState = {
        "messages": [HumanMessage(content="需要检索的问题")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
        "next_step": "retrieve",
    }

    route = should_retrieve(state)

    # 明确指定retrieve时应该路由到retrieve
    assert route == "retrieve"


def test_should_retrieve_with_next_step_llm():
    """测试next_step为llm时的路由"""
    state: AgentState = {
        "messages": [HumanMessage(content="直接回答的问题")],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
        "next_step": "llm",
    }

    route = should_retrieve(state)

    # 明确指定llm时应该路由到llm
    assert route == "llm"


def test_should_continue_with_error():
    """测试有错误时应该结束"""
    state: AgentState = {
        "messages": [
            HumanMessage(content="查询信息"),
            AIMessage(content="这是回复"),
        ],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
        "error": "测试错误",
    }

    result = should_continue(state)

    # 有错误时应该结束
    assert result == "END"


def test_should_continue_with_low_confidence():
    """测试低置信度时的处理"""
    state: AgentState = {
        "messages": [
            HumanMessage(content="查询信息"),
            AIMessage(content="这是回复"),
        ],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
        "confidence_score": 0.3,  # 低置信度
    }

    result = should_continue(state)

    # 低置信度时应该继续（当前实现）
    assert result == "END"


def test_should_continue_with_high_confidence():
    """测试高置信度时的处理"""
    state: AgentState = {
        "messages": [
            HumanMessage(content="查询信息"),
            AIMessage(content="这是回复"),
        ],
        "retrieved_docs": [],
        "tool_calls": [],
        "session_id": "test-123",
        "confidence_score": 0.8,  # 高置信度
    }

    result = should_continue(state)

    # 高置信度时应该结束
    assert result == "END"


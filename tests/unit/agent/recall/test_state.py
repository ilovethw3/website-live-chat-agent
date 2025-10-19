"""
召回Agent状态测试

测试RecallState结构定义和基本功能。
"""

from src.agent.recall.schema import RecallHit, RecallRequest, RecallResult
from src.agent.recall.state import RecallState


def test_recall_state_structure():
    """测试RecallState结构"""
    state: RecallState = {
        "request": RecallRequest(
            query="test",
            session_id="test-session",
            trace_id="test-trace",
        ),
        "config": {"sources": ["vector"]},
        "start_time": 0.0,
        "hits": [],
        "result": None,
    }

    # 验证所有必需字段存在
    assert "request" in state
    assert "config" in state
    assert "start_time" in state
    assert "hits" in state
    assert "result" in state

    # 验证字段类型
    assert isinstance(state["request"], RecallRequest)
    assert isinstance(state["config"], dict)
    assert isinstance(state["start_time"], float)
    assert isinstance(state["hits"], list)
    assert state["result"] is None or isinstance(state["result"], RecallResult)


def test_recall_state_with_hits():
    """测试RecallState包含hits的情况"""
    hit = RecallHit(
        source="vector",
        score=0.85,
        confidence=0.9,
        reason="向量相似度匹配",
        content="测试内容",
        metadata={"title": "测试文档"}
    )

    state: RecallState = {
        "request": RecallRequest(
            query="test query",
            session_id="test-session",
            trace_id="test-trace",
        ),
        "config": {"sources": ["vector"], "weights": {"vector": 1.0}},
        "start_time": 1234567890.0,
        "hits": [hit],
        "result": None,
    }

    assert len(state["hits"]) == 1
    assert state["hits"][0].source == "vector"
    assert state["hits"][0].score == 0.85


def test_recall_state_with_result():
    """测试RecallState包含result的情况"""
    hit = RecallHit(
        source="vector",
        score=0.85,
        confidence=0.9,
        reason="向量相似度匹配",
        content="测试内容",
        metadata={"title": "测试文档"}
    )

    result = RecallResult(
        hits=[hit],
        latency_ms=150.0,
        degraded=False,
        trace_id="test-trace",
        experiment_id=None,
    )

    state: RecallState = {
        "request": RecallRequest(
            query="test query",
            session_id="test-session",
            trace_id="test-trace",
        ),
        "config": {"sources": ["vector"]},
        "start_time": 1234567890.0,
        "hits": [hit],
        "result": result,
    }

    assert state["result"] is not None
    assert isinstance(state["result"], RecallResult)
    assert len(state["result"].hits) == 1
    assert state["result"].latency_ms == 150.0
    assert not state["result"].degraded

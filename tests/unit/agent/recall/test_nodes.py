"""
召回节点单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.recall.nodes import (
    _deduplicate_hits,
    fallback_node,
    fanout_node,
    merge_node,
    output_node,
    prepare_node,
)
from src.agent.recall.schema import RecallHit, RecallRequest, RecallResult


@pytest.fixture
def recall_state():
    """创建测试用的RecallState"""
    return {
        "request": RecallRequest(
            query="test query",
            session_id="test-session",
            trace_id="test-trace",
        ),
        "config": {
            "sources": ["vector"],
            "weights": {"vector": 1.0},
            "timeout_ms": 500,
            "retry": 1,
        },
        "start_time": 1234567890.0,
        "hits": [],
        "result": None,
    }


class TestPrepareNode:
    """测试prepare_node"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings"""
        with patch('src.agent.recall.nodes.settings') as mock:
            mock.recall_sources = ["vector", "faq"]
            mock.recall_source_weights = "vector:1.0,faq:0.8"
            mock.recall_timeout_ms = 500
            mock.recall_retry = 1
            mock.recall_merge_strategy = "weighted"
            mock.recall_degrade_threshold = 0.5
            mock.recall_fallback_enabled = True
            mock.recall_experiment_enabled = False
            mock.recall_experiment_platform = None
            yield mock

    @pytest.mark.asyncio
    async def test_prepare_node_basic(self, mock_settings):
        """测试基础配置加载"""
        request = RecallRequest(
            query="测试查询",
            session_id="session-123",
            trace_id="trace-456"
        )

        state = {"request": request}

        result = await prepare_node(state)

        assert "config" in result
        assert "start_time" in result
        assert result["config"]["sources"] == ["vector", "faq"]
        assert result["config"]["weights"]["vector"] == 1.0
        assert result["config"]["weights"]["faq"] == 0.8

    @pytest.mark.asyncio
    async def test_prepare_node_with_experiment(self, mock_settings):
        """测试实验配置"""
        mock_settings.recall_experiment_enabled = True

        request = RecallRequest(
            query="测试查询",
            session_id="session-123",
            trace_id="trace-456",
            experiment_id="exp-recall-v2"
        )

        state = {"request": request}

        result = await prepare_node(state)

        assert result["config"]["experiment_id"] == "exp-recall-v2"
        assert result["config"]["experiment_enabled"] is True


class TestFanoutNode:
    """测试fanout_node"""

    @pytest.fixture
    def mock_sources(self):
        """Mock召回源"""
        with patch('src.agent.recall.nodes.VectorRecallSource') as mock_vector, \
             patch('src.agent.recall.nodes.FAQRecallSource') as mock_faq:

            # Mock向量召回源
            mock_vector_instance = MagicMock()
            mock_vector_instance.acquire = AsyncMock(return_value=[
                RecallHit(
                    source="vector",
                    score=0.85,
                    confidence=0.82,
                    reason="向量匹配",
                    content="向量内容",
                    metadata={}
                )
            ])
            mock_vector.return_value = mock_vector_instance

            # Mock FAQ召回源
            mock_faq_instance = MagicMock()
            mock_faq_instance.acquire = AsyncMock(return_value=[
                RecallHit(
                    source="faq",
                    score=0.75,
                    confidence=0.70,
                    reason="FAQ匹配",
                    content="FAQ内容",
                    metadata={}
                )
            ])
            mock_faq.return_value = mock_faq_instance

            yield mock_vector_instance, mock_faq_instance

    @pytest.mark.asyncio
    async def test_fanout_node_success(self, mock_sources):
        """测试成功并行调用"""
        request = RecallRequest(
            query="测试查询",
            session_id="session-123",
            trace_id="trace-456"
        )

        state = {
            "request": request,
            "config": {
                "sources": ["vector", "faq"],
                "timeout_ms": 500,
                "retry": 1
            }
        }

        result = await fanout_node(state)

        assert "hits" in result
        assert len(result["hits"]) == 2
        sources = [hit.source for hit in result["hits"]]
        assert "vector" in sources
        assert "faq" in sources

    @pytest.mark.asyncio
    async def test_fanout_node_timeout(self, mock_sources):
        """测试超时处理"""
        # Mock超时异常
        mock_sources[0].acquire = AsyncMock(side_effect=TimeoutError("Timeout"))

        request = RecallRequest(
            query="测试查询",
            session_id="session-123",
            trace_id="trace-456"
        )

        state = {
            "request": request,
            "config": {
                "sources": ["vector"],
                "timeout_ms": 100  # 短超时
            }
        }

        result = await fanout_node(state)

        assert "hits" in result
        assert len(result["hits"]) == 0


class TestMergeNode:
    """测试merge_node"""

    @pytest.mark.asyncio
    async def test_merge_node_basic(self):
        """测试基础合并"""
        source_results = {
            "vector": [
                RecallHit(
                    source="vector",
                    score=0.85,
                    confidence=0.82,
                    reason="向量匹配",
                    content="向量内容",
                    metadata={}
                )
            ],
            "faq": [
                RecallHit(
                    source="faq",
                    score=0.75,
                    confidence=0.70,
                    reason="FAQ匹配",
                    content="FAQ内容",
                    metadata={}
                )
            ]
        }

        # 合并所有hits
        all_hits = []
        for hits in source_results.values():
            all_hits.extend(hits)

        state = {
            "hits": all_hits,
            "config": {
                "weights": {"vector": 1.0, "faq": 0.8}
            },
            "request": RecallRequest(
                query="测试",
                session_id="session-123",
                trace_id="trace-456",
                top_k=5
            )
        }

        result = await merge_node(state)

        assert "hits" in result
        assert len(result["hits"]) == 2
        # 应该按分数排序
        assert result["hits"][0].score >= result["hits"][1].score

    @pytest.mark.asyncio
    async def test_merge_node_with_weights(self):
        """测试权重合并"""
        source_results = {
            "vector": [
                RecallHit(
                    source="vector",
                    score=0.5,  # 原始分数
                    confidence=0.82,
                    reason="向量匹配",
                    content="向量内容",
                    metadata={}
                )
            ],
            "faq": [
                RecallHit(
                    source="faq",
                    score=0.5,  # 原始分数
                    confidence=0.70,
                    reason="FAQ匹配",
                    content="FAQ内容",
                    metadata={}
                )
            ]
        }

        # 合并所有hits
        all_hits = []
        for hits in source_results.values():
            all_hits.extend(hits)

        state = {
            "hits": all_hits,
            "config": {
                "weights": {"vector": 1.0, "faq": 0.5}  # FAQ权重更低
            },
            "request": RecallRequest(
                query="测试",
                session_id="session-123",
                trace_id="trace-456",
                top_k=5
            )
        }

        result = await merge_node(state)

        assert "hits" in result
        assert len(result["hits"]) == 2
        # vector应该排在前面（权重更高）
        assert result["hits"][0].source == "vector"
        assert result["hits"][0].score == 0.5  # 1.0 * 0.5
        assert result["hits"][1].source == "faq"
        assert result["hits"][1].score == 0.25  # 0.5 * 0.5


class TestFallbackNode:
    """测试fallback_node"""

    @pytest.mark.asyncio
    async def test_fallback_node_no_fallback(self):
        """测试不需要降级"""
        merged_hits = [
            RecallHit(
                source="vector",
                score=0.85,
                confidence=0.82,
                reason="向量匹配",
                content="向量内容",
                metadata={}
            )
        ]

        state = {
            "hits": merged_hits,
            "config": {
                "degrade_threshold": 0.5,
                "fallback_enabled": True
            }
        }

        result = await fallback_node(state)

        # fallback_node不更新任何字段时返回空字典
        assert result == {}
        # 不需要降级时，fallback_node不更新任何字段

    @pytest.mark.asyncio
    async def test_fallback_node_low_score(self):
        """测试低分降级"""
        merged_hits = [
            RecallHit(
                source="vector",
                score=0.3,  # 低于阈值
                confidence=0.3,
                reason="向量匹配",
                content="向量内容",
                metadata={}
            )
        ]

        state = {
            "hits": merged_hits,
            "config": {
                "degrade_threshold": 0.5,
                "fallback_enabled": True
            }
        }

        result = await fallback_node(state)

        # 降级时返回fallback hits
        assert len(result["hits"]) == 1
        assert result["hits"][0].source == "fallback"

    @pytest.mark.asyncio
    async def test_fallback_node_empty_results(self):
        """测试空结果降级"""
        state = {
            "hits": [],
            "config": {
                "degrade_threshold": 0.5,
                "fallback_enabled": True
            }
        }

        result = await fallback_node(state)

        # 空结果时返回fallback hits
        assert len(result["hits"]) == 1
        assert result["hits"][0].source == "fallback"

    @pytest.mark.asyncio
    async def test_fallback_node_disabled(self):
        """测试降级功能关闭"""
        state = {
            "hits": [],
            "config": {
                "degrade_threshold": 0.5,
                "fallback_enabled": False  # 关闭降级
            }
        }

        result = await fallback_node(state)

        # fallback_node不更新任何字段时返回空字典
        assert result == {}


class TestOutputNode:
    """测试output_node"""

    @pytest.mark.asyncio
    async def test_output_node_basic(self):
        """测试基础输出"""
        merged_hits = [
            RecallHit(
                source="vector",
                score=0.85,
                confidence=0.82,
                reason="向量匹配",
                content="向量内容",
                metadata={}
            )
        ]

        state = {
            "request": RecallRequest(
                query="测试查询",
                session_id="session-123",
                trace_id="trace-456"
            ),
            "hits": merged_hits,
            "start_time": 1000.0
        }

        with patch('time.time', return_value=1000.5):  # 模拟500ms延迟
            result = await output_node(state)

        assert "result" in result
        assert isinstance(result["result"], RecallResult)
        assert result["result"].hits == merged_hits
        assert result["result"].degraded is False
        assert result["result"].trace_id == "trace-456"


class TestDeduplicateHits:
    """测试去重函数"""

    def test_deduplicate_hits_no_duplicates(self):
        """测试无重复的去重"""
        hits = [
            RecallHit(
                source="vector",
                score=0.85,
                confidence=0.82,
                reason="向量匹配",
                content="内容1",
                metadata={}
            ),
            RecallHit(
                source="faq",
                score=0.75,
                confidence=0.70,
                reason="FAQ匹配",
                content="内容2",
                metadata={}
            )
        ]

        result = _deduplicate_hits(hits)

        assert len(result) == 2
        assert result == hits

    def test_deduplicate_hits_with_duplicates(self):
        """测试有重复的去重"""
        hits = [
            RecallHit(
                source="vector",
                score=0.85,
                confidence=0.82,
                reason="向量匹配",
                content="相同内容",
                metadata={}
            ),
            RecallHit(
                source="faq",
                score=0.75,  # 分数更低
                confidence=0.70,
                reason="FAQ匹配",
                content="相同内容",
                metadata={}
            )
        ]

        result = _deduplicate_hits(hits)

        assert len(result) == 1
        assert result[0].source == "vector"  # 保留高分
        assert result[0].score == 0.85

    def test_deduplicate_hits_empty(self):
        """测试空列表去重"""
        result = _deduplicate_hits([])

        assert len(result) == 0

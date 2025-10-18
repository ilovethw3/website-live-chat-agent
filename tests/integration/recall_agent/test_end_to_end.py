"""
召回Agent端到端集成测试
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.agent.recall.graph import invoke_recall_agent
from src.agent.recall.schema import RecallRequest, RecallResult


class TestRecallAgentEndToEnd:
    """测试召回Agent端到端流程"""

    @pytest.fixture
    def recall_request(self):
        """创建召回请求"""
        return RecallRequest(
            query="你们的退货政策是什么？",
            session_id="session-123",
            trace_id="trace-456",
            top_k=5
        )

    @pytest.mark.asyncio
    @patch('src.agent.recall.nodes.settings')
    @patch('src.agent.recall.sources.vector_source.create_embeddings')
    @patch('src.agent.recall.sources.vector_source.milvus_service')
    async def test_recall_agent_vector_only(self, mock_milvus, mock_embeddings, mock_settings, recall_request):
        """测试仅向量召回的端到端流程"""
        # Mock配置
        mock_settings.recall_sources = ["vector"]
        mock_settings.recall_source_weights = "vector:1.0"
        mock_settings.recall_timeout_ms = 500
        mock_settings.recall_retry = 1
        mock_settings.recall_merge_strategy = "weighted"
        mock_settings.recall_degrade_threshold = 0.5
        mock_settings.recall_fallback_enabled = True
        mock_settings.recall_experiment_enabled = False
        mock_settings.recall_experiment_platform = None

        # Mock embeddings
        mock_embeddings.return_value.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])

        # Mock milvus service
        mock_milvus.search_knowledge = AsyncMock(return_value=[
            {
                "text": "我们的退货政策：收到商品后30天内可申请退货...",
                "score": 0.85,
                "metadata": {"title": "退货政策", "url": "https://example.com/return"}
            }
        ])

        # 调用召回Agent
        result = await invoke_recall_agent(recall_request)

        # 验证结果
        assert isinstance(result, RecallResult)
        assert len(result.hits) == 1
        assert result.hits[0].source == "vector"
        assert result.hits[0].score == 0.85
        assert "退货政策" in result.hits[0].content
        assert result.degraded is False
        assert result.trace_id == "trace-456"
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    @patch('src.agent.recall.nodes.settings')
    async def test_recall_agent_multi_source(self, mock_settings, recall_request):
        """测试多源召回的端到端流程"""
        # Mock配置
        mock_settings.recall_sources = ["vector", "faq", "keyword"]
        mock_settings.recall_source_weights = "vector:1.0,faq:0.8,keyword:0.6"
        mock_settings.recall_timeout_ms = 500
        mock_settings.recall_retry = 1
        mock_settings.recall_merge_strategy = "weighted"
        mock_settings.recall_degrade_threshold = 0.5
        mock_settings.recall_fallback_enabled = True
        mock_settings.recall_experiment_enabled = False
        mock_settings.recall_experiment_platform = None

        # 调用召回Agent（会使用真实的FAQ和关键词召回源）
        result = await invoke_recall_agent(recall_request)

        # 验证结果
        assert isinstance(result, RecallResult)
        assert len(result.hits) > 0
        assert result.degraded is False
        assert result.trace_id == "trace-456"
        assert result.latency_ms > 0

        # 验证召回源
        sources = [hit.source for hit in result.hits]
        assert "faq" in sources or "keyword" in sources  # 至少有一个非向量源

    @pytest.mark.asyncio
    @patch('src.agent.recall.nodes.settings')
    async def test_recall_agent_fallback(self, mock_settings, recall_request):
        """测试降级场景"""
        # Mock配置 - 设置高降级阈值
        mock_settings.recall_sources = ["vector"]
        mock_settings.recall_source_weights = "vector:1.0"
        mock_settings.recall_timeout_ms = 500
        mock_settings.recall_retry = 1
        mock_settings.recall_merge_strategy = "weighted"
        mock_settings.recall_degrade_threshold = 0.9  # 高阈值，容易触发降级
        mock_settings.recall_fallback_enabled = True
        mock_settings.recall_experiment_enabled = False
        mock_settings.recall_experiment_platform = None

        # 使用不相关的查询，容易触发降级
        recall_request.query = "完全不相关的查询内容"

        # 调用召回Agent
        result = await invoke_recall_agent(recall_request)

        # 验证降级结果
        assert isinstance(result, RecallResult)
        assert result.degraded is True
        assert len(result.hits) == 1
        assert result.hits[0].source == "fallback"
        assert "抱歉" in result.hits[0].content

    @pytest.mark.asyncio
    @patch('src.agent.recall.nodes.settings')
    async def test_recall_agent_experiment(self, mock_settings, recall_request):
        """测试实验配置"""
        # Mock配置
        mock_settings.recall_sources = ["vector"]
        mock_settings.recall_source_weights = "vector:1.0"
        mock_settings.recall_timeout_ms = 500
        mock_settings.recall_retry = 1
        mock_settings.recall_merge_strategy = "weighted"
        mock_settings.recall_degrade_threshold = 0.5
        mock_settings.recall_fallback_enabled = True
        mock_settings.recall_experiment_enabled = True
        mock_settings.recall_experiment_platform = "internal"

        # 设置实验ID
        recall_request.experiment_id = "exp-recall-v2"

        # 调用召回Agent
        result = await invoke_recall_agent(recall_request)

        # 验证结果
        assert isinstance(result, RecallResult)
        assert result.experiment_id == "exp-recall-v2"

    @pytest.mark.asyncio
    @patch('src.agent.recall.nodes.settings')
    async def test_recall_agent_error_handling(self, mock_settings, recall_request):
        """测试错误处理"""
        # Mock配置
        mock_settings.recall_sources = ["vector"]
        mock_settings.recall_source_weights = "vector:1.0"
        mock_settings.recall_timeout_ms = 100  # 短超时
        mock_settings.recall_retry = 0
        mock_settings.recall_merge_strategy = "weighted"
        mock_settings.recall_degrade_threshold = 0.5
        mock_settings.recall_fallback_enabled = True
        mock_settings.recall_experiment_enabled = False
        mock_settings.recall_experiment_platform = None

        # 调用召回Agent（可能会超时或出错）
        result = await invoke_recall_agent(recall_request)

        # 验证结果（应该返回降级结果）
        assert isinstance(result, RecallResult)
        # 可能返回空结果或降级结果
        assert result.degraded is True or len(result.hits) == 0


class TestRecallAgentPerformance:
    """测试召回Agent性能"""

    @pytest.mark.asyncio
    @patch('src.agent.recall.nodes.settings')
    async def test_recall_agent_latency(self, mock_settings):
        """测试召回延迟"""
        # Mock配置
        mock_settings.recall_sources = ["faq"]  # 使用本地FAQ源，避免外部依赖
        mock_settings.recall_source_weights = "faq:1.0"
        mock_settings.recall_timeout_ms = 500
        mock_settings.recall_retry = 1
        mock_settings.recall_merge_strategy = "weighted"
        mock_settings.recall_degrade_threshold = 0.5
        mock_settings.recall_fallback_enabled = True
        mock_settings.recall_experiment_enabled = False
        mock_settings.recall_experiment_platform = None

        recall_request = RecallRequest(
            query="退货政策",
            session_id="session-123",
            trace_id="trace-456"
        )

        # 调用召回Agent
        result = await invoke_recall_agent(recall_request)

        # 验证延迟
        assert result.latency_ms < 1000  # 应该在1秒内完成
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    @patch('src.agent.recall.nodes.settings')
    async def test_recall_agent_concurrent(self, mock_settings):
        """测试并发召回"""
        # Mock配置
        mock_settings.recall_sources = ["faq", "keyword"]
        mock_settings.recall_source_weights = "faq:1.0,keyword:0.8"
        mock_settings.recall_timeout_ms = 500
        mock_settings.recall_retry = 1
        mock_settings.recall_merge_strategy = "weighted"
        mock_settings.recall_degrade_threshold = 0.5
        mock_settings.recall_fallback_enabled = True
        mock_settings.recall_experiment_enabled = False
        mock_settings.recall_experiment_platform = None

        # 并发调用多个召回请求
        import asyncio

        tasks = []
        for i in range(5):
            recall_request = RecallRequest(
                query=f"查询{i}",
                session_id=f"session-{i}",
                trace_id=f"trace-{i}"
            )
            tasks.append(invoke_recall_agent(recall_request))

        results = await asyncio.gather(*tasks)

        # 验证所有请求都成功完成
        assert len(results) == 5
        for result in results:
            assert isinstance(result, RecallResult)
            assert result.latency_ms > 0

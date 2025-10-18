"""
召回数据模型单元测试
"""

from src.agent.recall.schema import RecallHit, RecallRequest, RecallResult


class TestRecallRequest:
    """测试RecallRequest数据模型"""

    def test_recall_request_creation(self):
        """测试RecallRequest创建"""
        request = RecallRequest(
            query="测试查询",
            session_id="session-123",
            trace_id="trace-456"
        )

        assert request.query == "测试查询"
        assert request.session_id == "session-123"
        assert request.trace_id == "trace-456"
        assert request.user_profile is None
        assert request.context is None
        assert request.experiment_id is None
        assert request.top_k == 5

    def test_recall_request_with_optional_fields(self):
        """测试RecallRequest可选字段"""
        request = RecallRequest(
            query="测试查询",
            session_id="session-123",
            trace_id="trace-456",
            user_profile={"user_type": "premium"},
            context=["上下文1", "上下文2"],
            experiment_id="exp-123",
            top_k=10
        )

        assert request.user_profile == {"user_type": "premium"}
        assert request.context == ["上下文1", "上下文2"]
        assert request.experiment_id == "exp-123"
        assert request.top_k == 10


class TestRecallHit:
    """测试RecallHit数据模型"""

    def test_recall_hit_creation(self):
        """测试RecallHit创建"""
        hit = RecallHit(
            source="vector",
            score=0.85,
            confidence=0.82,
            reason="向量相似度匹配",
            content="这是召回的内容",
            metadata={"title": "文档标题", "url": "https://example.com"}
        )

        assert hit.source == "vector"
        assert hit.score == 0.85
        assert hit.confidence == 0.82
        assert hit.reason == "向量相似度匹配"
        assert hit.content == "这是召回的内容"
        assert hit.metadata == {"title": "文档标题", "url": "https://example.com"}

    def test_recall_hit_score_validation(self):
        """测试RecallHit分数验证"""
        # 正常分数
        hit = RecallHit(
            source="vector",
            score=0.5,
            confidence=0.5,
            reason="测试",
            content="内容",
            metadata={}
        )
        assert hit.score == 0.5

        # 边界分数
        hit = RecallHit(
            source="vector",
            score=1.0,
            confidence=1.0,
            reason="测试",
            content="内容",
            metadata={}
        )
        assert hit.score == 1.0


class TestRecallResult:
    """测试RecallResult数据模型"""

    def test_recall_result_creation(self):
        """测试RecallResult创建"""
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

        result = RecallResult(
            hits=hits,
            latency_ms=245.5,
            degraded=False,
            trace_id="trace-123"
        )

        assert len(result.hits) == 2
        assert result.latency_ms == 245.5
        assert result.degraded is False
        assert result.trace_id == "trace-123"
        assert result.experiment_id is None

    def test_recall_result_with_experiment(self):
        """测试RecallResult实验ID"""
        result = RecallResult(
            hits=[],
            latency_ms=100.0,
            degraded=False,
            trace_id="trace-123",
            experiment_id="exp-456"
        )

        assert result.experiment_id == "exp-456"

    def test_recall_result_empty_hits(self):
        """测试RecallResult空结果"""
        result = RecallResult(
            hits=[],
            latency_ms=50.0,
            degraded=True,
            trace_id="trace-123"
        )

        assert len(result.hits) == 0
        assert result.degraded is True

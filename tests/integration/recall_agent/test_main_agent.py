"""
主Agent集成测试
"""

from unittest.mock import patch

import pytest

from src.agent.nodes import retrieve_node
from src.agent.recall.schema import RecallHit, RecallResult


class TestMainAgentIntegration:
    """测试主Agent集成召回Agent"""

    @pytest.fixture
    def mock_state(self):
        """创建模拟的Agent状态"""
        from langchain_core.messages import HumanMessage

        return {
            "messages": [HumanMessage(content="你们的退货政策是什么？")],
            "session_id": "session-123",
            "user_profile": {"user_type": "premium"},
            "context": ["用户询问了产品信息"],
            "experiment_id": "exp-123"
        }

    @pytest.mark.asyncio
    @patch('src.agent.nodes.settings')
    @patch('src.agent.nodes.invoke_recall_agent')
    async def test_retrieve_node_integration_success(self, mock_invoke_recall, mock_settings, mock_state):
        """测试retrieve_node成功集成"""
        # Mock配置
        mock_settings.vector_top_k = 5

        # Mock召回Agent返回结果
        mock_recall_result = RecallResult(
            hits=[
                RecallHit(
                    source="vector",
                    score=0.85,
                    confidence=0.82,
                    reason="向量相似度匹配",
                    content="我们的退货政策：收到商品后30天内可申请退货...",
                    metadata={"title": "退货政策", "url": "https://example.com/return"}
                ),
                RecallHit(
                    source="faq",
                    score=0.75,
                    confidence=0.70,
                    reason="FAQ关键词匹配",
                    content="Q: 退货政策是什么？\nA: 我们提供30天无理由退货服务...",
                    metadata={"faq_id": "faq_001", "category": "退货政策"}
                )
            ],
            latency_ms=245.5,
            degraded=False,
            trace_id="trace-456",
            experiment_id="exp-123"
        )

        mock_invoke_recall.return_value = mock_recall_result

        # 调用retrieve_node
        result = await retrieve_node(mock_state)

        # 验证结果
        assert "retrieved_docs" in result
        assert "confidence_score" in result
        assert "recall_metrics" in result
        assert "tool_calls" in result

        # 验证文档格式
        assert len(result["retrieved_docs"]) == 2
        assert "[文档1]" in result["retrieved_docs"][0]
        assert "[召回源: vector]" in result["retrieved_docs"][0]
        assert "退货政策" in result["retrieved_docs"][0]

        # 验证置信度
        assert result["confidence_score"] == 0.85

        # 验证召回指标
        assert result["recall_metrics"]["latency_ms"] == 245.5
        assert result["recall_metrics"]["degraded"] is False
        assert result["recall_metrics"]["sources"] == ["vector", "faq"]
        assert result["recall_metrics"]["trace_id"] == "trace-456"

        # 验证工具调用记录
        tool_calls = result["tool_calls"]
        assert len(tool_calls) == 1
        assert tool_calls[0]["node"] == "retrieve"
        assert tool_calls[0]["results_count"] == 2
        assert tool_calls[0]["top_score"] == 0.85
        assert tool_calls[0]["recall_sources"] == ["vector", "faq"]
        assert tool_calls[0]["latency_ms"] == 245.5
        assert tool_calls[0]["degraded"] is False

    @pytest.mark.asyncio
    @patch('src.agent.nodes.settings')
    @patch('src.agent.nodes.invoke_recall_agent')
    async def test_retrieve_node_integration_empty_results(self, mock_invoke_recall, mock_settings, mock_state):
        """测试retrieve_node空结果"""
        # Mock配置
        mock_settings.vector_top_k = 5

        # Mock召回Agent返回空结果
        mock_recall_result = RecallResult(
            hits=[],
            latency_ms=100.0,
            degraded=True,
            trace_id="trace-456"
        )

        mock_invoke_recall.return_value = mock_recall_result

        # 调用retrieve_node
        result = await retrieve_node(mock_state)

        # 验证结果
        assert result["retrieved_docs"] == []
        assert result["confidence_score"] == 0.0
        assert result["recall_metrics"]["degraded"] is True

    @pytest.mark.asyncio
    @patch('src.agent.nodes.settings')
    @patch('src.agent.nodes.invoke_recall_agent')
    async def test_retrieve_node_integration_fallback(self, mock_invoke_recall, mock_settings, mock_state):
        """测试retrieve_node降级场景"""
        # Mock配置
        mock_settings.vector_top_k = 5

        # Mock召回Agent返回降级结果
        mock_recall_result = RecallResult(
            hits=[
                RecallHit(
                    source="fallback",
                    score=0.1,
                    confidence=0.1,
                    reason="召回降级：未找到足够相关的结果",
                    content="抱歉，我暂时无法找到相关信息。建议您：\n1. 尝试使用不同的关键词\n2. 联系人工客服获取帮助",
                    metadata={"fallback": True, "degrade_reason": "low_score"}
                )
            ],
            latency_ms=300.0,
            degraded=True,
            trace_id="trace-456"
        )

        mock_invoke_recall.return_value = mock_recall_result

        # 调用retrieve_node
        result = await retrieve_node(mock_state)

        # 验证结果
        assert len(result["retrieved_docs"]) == 1
        assert "[召回源: fallback]" in result["retrieved_docs"][0]
        assert "抱歉" in result["retrieved_docs"][0]
        assert result["confidence_score"] == 0.1
        assert result["recall_metrics"]["degraded"] is True

    @pytest.mark.asyncio
    @patch('src.agent.nodes.settings')
    @patch('src.agent.nodes.invoke_recall_agent')
    async def test_retrieve_node_integration_error_handling(self, mock_invoke_recall, mock_settings, mock_state):
        """测试retrieve_node错误处理"""
        # Mock配置
        mock_settings.vector_top_k = 5

        # Mock召回Agent抛出异常
        mock_invoke_recall.side_effect = Exception("召回Agent错误")

        # 调用retrieve_node（应该处理异常）
        result = await retrieve_node(mock_state)

        # 验证结果（应该返回空结果）
        assert result["retrieved_docs"] == []
        assert result["confidence_score"] == 0.0

    @pytest.mark.asyncio
    @patch('src.agent.nodes.settings')
    @patch('src.agent.nodes.invoke_recall_agent')
    async def test_retrieve_node_integration_multi_source(self, mock_invoke_recall, mock_settings, mock_state):
        """测试多源召回集成"""
        # Mock配置
        mock_settings.vector_top_k = 5

        # Mock召回Agent返回多源结果
        mock_recall_result = RecallResult(
            hits=[
                RecallHit(
                    source="vector",
                    score=0.85,
                    confidence=0.82,
                    reason="向量相似度匹配",
                    content="向量召回内容",
                    metadata={"title": "向量文档"}
                ),
                RecallHit(
                    source="faq",
                    score=0.75,
                    confidence=0.70,
                    reason="FAQ关键词匹配",
                    content="FAQ召回内容",
                    metadata={"faq_id": "faq_001"}
                ),
                RecallHit(
                    source="keyword",
                    score=0.65,
                    confidence=0.60,
                    reason="关键词规则匹配",
                    content="关键词召回内容",
                    metadata={"rule_id": "rule_001"}
                )
            ],
            latency_ms=200.0,
            degraded=False,
            trace_id="trace-456"
        )

        mock_invoke_recall.return_value = mock_recall_result

        # 调用retrieve_node
        result = await retrieve_node(mock_state)

        # 验证结果
        assert len(result["retrieved_docs"]) == 3
        assert "[召回源: vector]" in result["retrieved_docs"][0]
        assert "[召回源: faq]" in result["retrieved_docs"][1]
        assert "[召回源: keyword]" in result["retrieved_docs"][2]

        # 验证召回指标
        assert result["recall_metrics"]["sources"] == ["vector", "faq", "keyword"]

    @pytest.mark.asyncio
    @patch('src.agent.nodes.settings')
    @patch('src.agent.nodes.invoke_recall_agent')
    async def test_retrieve_node_integration_experiment(self, mock_invoke_recall, mock_settings, mock_state):
        """测试实验集成"""
        # Mock配置
        mock_settings.vector_top_k = 5

        # 设置实验ID
        mock_state["experiment_id"] = "exp-recall-v2"

        # Mock召回Agent返回实验结果
        mock_recall_result = RecallResult(
            hits=[
                RecallHit(
                    source="vector",
                    score=0.85,
                    confidence=0.82,
                    reason="向量相似度匹配",
                    content="实验召回内容",
                    metadata={"title": "实验文档"}
                )
            ],
            latency_ms=180.0,
            degraded=False,
            trace_id="trace-456",
            experiment_id="exp-recall-v2"
        )

        mock_invoke_recall.return_value = mock_recall_result

        # 调用retrieve_node
        result = await retrieve_node(mock_state)

        # 验证结果
        assert result["recall_metrics"]["trace_id"] == "trace-456"
        # 实验ID应该通过RecallRequest传递到召回Agent
        mock_invoke_recall.assert_called_once()
        call_args = mock_invoke_recall.call_args[0][0]  # 第一个参数是RecallRequest
        assert call_args.experiment_id == "exp-recall-v2"

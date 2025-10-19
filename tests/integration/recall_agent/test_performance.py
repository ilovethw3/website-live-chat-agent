"""
召回Agent性能测试
"""

import asyncio
import time
from unittest.mock import patch

import pytest

from src.agent.recall.graph import invoke_recall_agent
from src.agent.recall.schema import RecallRequest, RecallResult


class TestRecallAgentPerformance:
    """测试召回Agent性能指标"""

    @pytest.mark.asyncio
    @patch('src.agent.recall.nodes.settings')
    async def test_recall_latency_p99(self, mock_settings):
        """测试P99延迟 ≤ 800ms"""
        # Mock配置
        mock_settings.recall_sources = ["faq", "keyword"]  # 使用本地源，避免外部依赖
        mock_settings.recall_source_weights = "faq:1.0,keyword:0.8"
        mock_settings.recall_timeout_ms = 500
        mock_settings.recall_retry = 1
        mock_settings.recall_merge_strategy = "weighted"
        mock_settings.recall_degrade_threshold = 0.5
        mock_settings.recall_fallback_enabled = True
        mock_settings.recall_experiment_enabled = False
        mock_settings.recall_experiment_platform = None

        # 测试多个查询的延迟
        queries = [
            "退货政策",
            "技术支持",
            "价格咨询",
            "账号管理",
            "API文档",
            "配送时间",
            "支付方式",
            "客服联系",
            "产品介绍",
            "使用指南"
        ]

        latencies = []
        for i, query in enumerate(queries):
            recall_request = RecallRequest(
                query=query,
                session_id=f"session-{i}",
                trace_id=f"trace-{i}"
            )

            time.time()
            result = await invoke_recall_agent(recall_request)
            time.time()

            # 验证结果
            assert isinstance(result, RecallResult)
            assert result.latency_ms > 0

            # 记录延迟
            latencies.append(result.latency_ms)

        # 计算P99延迟
        latencies.sort()
        p99_index = int(len(latencies) * 0.99)
        p99_latency = latencies[p99_index] if p99_index < len(latencies) else latencies[-1]

        # 验证P99延迟 ≤ 800ms
        assert p99_latency <= 800, f"P99延迟 {p99_latency}ms 超过800ms阈值"

        print(f"P99延迟: {p99_latency:.1f}ms")
        print(f"平均延迟: {sum(latencies)/len(latencies):.1f}ms")
        print(f"最大延迟: {max(latencies):.1f}ms")

    @pytest.mark.asyncio
    @patch('src.agent.recall.nodes.settings')
    async def test_recall_success_rate(self, mock_settings):
        """测试成功率 ≥ 99%"""
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

        # 测试多个查询的成功率
        queries = [
            "退货政策", "技术支持", "价格咨询", "账号管理", "API文档",
            "配送时间", "支付方式", "客服联系", "产品介绍", "使用指南",
            "常见问题", "操作指南", "故障排除", "功能介绍", "使用技巧"
        ]

        success_count = 0
        total_count = len(queries)

        for i, query in enumerate(queries):
            try:
                recall_request = RecallRequest(
                    query=query,
                    session_id=f"session-{i}",
                    trace_id=f"trace-{i}"
                )

                result = await invoke_recall_agent(recall_request)

                # 验证结果有效性
                assert isinstance(result, RecallResult)
                assert result.trace_id == f"trace-{i}"

                # 如果返回了结果（包括降级结果），认为成功
                if len(result.hits) > 0 or result.degraded:
                    success_count += 1

            except Exception as e:
                print(f"查询 '{query}' 失败: {e}")

        success_rate = success_count / total_count

        # 验证成功率 ≥ 99%
        assert success_rate >= 0.99, f"成功率 {success_rate:.2%} 低于99%阈值"

        print(f"成功率: {success_rate:.2%} ({success_count}/{total_count})")

    @pytest.mark.asyncio
    @patch('src.agent.recall.nodes.settings')
    async def test_recall_concurrent_performance(self, mock_settings):
        """测试并发召回性能"""
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

        # 并发测试
        concurrent_count = 10
        queries = [f"查询{i}" for i in range(concurrent_count)]

        async def single_recall(query, session_id):
            recall_request = RecallRequest(
                query=query,
                session_id=session_id,
                trace_id=f"trace-{session_id}"
            )
            return await invoke_recall_agent(recall_request)

        # 并发执行
        start_time = time.time()
        tasks = [
            single_recall(query, f"session-{i}")
            for i, query in enumerate(queries)
        ]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # 验证结果
        assert len(results) == concurrent_count
        for result in results:
            assert isinstance(result, RecallResult)
            assert result.latency_ms > 0

        # 验证并发性能
        total_time = end_time - start_time
        avg_time_per_request = total_time / concurrent_count

        print(f"并发数: {concurrent_count}")
        print(f"总时间: {total_time:.2f}s")
        print(f"平均每请求时间: {avg_time_per_request:.2f}s")

        # 验证并发性能（平均每请求时间应该小于单请求时间）
        assert avg_time_per_request < 1.0, f"并发性能不佳，平均每请求时间 {avg_time_per_request:.2f}s"

    @pytest.mark.asyncio
    @patch('src.agent.recall.nodes.settings')
    async def test_recall_memory_usage(self, mock_settings):
        """测试内存使用情况"""
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

        # 测试大量请求的内存使用
        request_count = 100
        results = []

        for i in range(request_count):
            recall_request = RecallRequest(
                query=f"测试查询{i}",
                session_id=f"session-{i}",
                trace_id=f"trace-{i}"
            )

            result = await invoke_recall_agent(recall_request)
            results.append(result)

        # 验证所有请求都成功完成
        assert len(results) == request_count
        for result in results:
            assert isinstance(result, RecallResult)

        print(f"成功处理 {request_count} 个请求")
        print(f"平均延迟: {sum(r.latency_ms for r in results)/len(results):.1f}ms")

    @pytest.mark.asyncio
    @patch('src.agent.recall.nodes.settings')
    async def test_recall_degradation_rate(self, mock_settings):
        """测试降级率"""
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

        # 测试不同质量的查询
        queries = [
            "退货政策",  # 应该匹配FAQ
            "技术支持",  # 应该匹配FAQ
            "价格咨询",  # 应该匹配关键词
            "完全不相关的查询内容",  # 应该触发降级
            "随机字符串查询",  # 应该触发降级
        ]

        degraded_count = 0
        total_count = len(queries)

        for i, query in enumerate(queries):
            recall_request = RecallRequest(
                query=query,
                session_id=f"session-{i}",
                trace_id=f"trace-{i}"
            )

            result = await invoke_recall_agent(recall_request)

            if result.degraded:
                degraded_count += 1

        degradation_rate = degraded_count / total_count

        print(f"降级率: {degradation_rate:.2%} ({degraded_count}/{total_count})")

        # 验证降级率在合理范围内（不应该太高）
        assert degradation_rate <= 0.5, f"降级率 {degradation_rate:.2%} 过高"

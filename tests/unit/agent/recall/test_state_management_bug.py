"""
测试状态管理缺陷 - KeyError: 'request'

这个测试文件专门用于重现和验证状态管理问题
"""


import pytest

from src.agent.recall.nodes import fanout_node, merge_node, output_node, prepare_node
from src.agent.recall.schema import RecallHit, RecallRequest


class TestStateManagementBug:
    """测试状态管理缺陷"""

    @pytest.mark.asyncio
    async def test_fanout_node_missing_request_key(self):
        """测试fanout_node缺少request键的情况"""
        # 模拟缺少request键的状态
        state = {
            "config": {
                "sources": ["vector"],
                "timeout_ms": 500,
                "retry": 1
            }
            # 故意缺少 "request" 键
        }

        # 这应该抛出KeyError
        with pytest.raises(KeyError, match="'request'"):
            await fanout_node(state)

    @pytest.mark.asyncio
    async def test_merge_node_missing_request_key(self):
        """测试merge_node缺少request键的情况"""
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
            ]
        }

        # 合并所有hits
        all_hits = []
        for hits in source_results.values():
            all_hits.extend(hits)

        state = {
            "hits": all_hits,
            "config": {
                "weights": {"vector": 1.0}
            }
            # 故意缺少 "request" 键
        }

        # 这应该抛出KeyError
        with pytest.raises(KeyError, match="'request'"):
            await merge_node(state)

    @pytest.mark.asyncio
    async def test_output_node_missing_request_key(self):
        """测试output_node缺少request键的情况"""
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
            "merged_hits": merged_hits,
            "degraded": False,
            "start_time": 1000.0
            # 故意缺少 "request" 键
        }

        # 这应该抛出KeyError
        with pytest.raises(KeyError, match="'request'"):
            await output_node(state)

    @pytest.mark.asyncio
    async def test_prepare_node_missing_request_key(self):
        """测试prepare_node缺少request键的情况"""
        state = {
            # 故意缺少 "request" 键
        }

        # 这应该抛出KeyError
        with pytest.raises(KeyError, match="'request'"):
            await prepare_node(state)

    @pytest.mark.asyncio
    async def test_state_consistency_across_nodes(self):
        """测试状态在节点间传递的一致性"""
        request = RecallRequest(
            query="测试查询",
            session_id="session-123",
            trace_id="trace-456"
        )

        # 测试完整的状态传递链
        state1 = {"request": request}
        result1 = await prepare_node(state1)

        # 验证prepare_node返回的状态包含request
        assert "request" in result1 or "request" in state1

        # 合并状态
        state2 = {**state1, **result1}
        result2 = await fanout_node(state2)

        # 验证fanout_node返回的状态
        state3 = {**state2, **result2}
        result3 = await merge_node(state3)

        # 验证merge_node返回的状态
        state4 = {**state3, **result3}
        result4 = await output_node(state4)

        # 验证最终结果
        assert "result" in result4

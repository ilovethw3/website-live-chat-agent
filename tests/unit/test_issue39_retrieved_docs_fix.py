"""
Issue #39 修复测试

测试Agent层retrieved_docs类型错误修复。
"""

from unittest.mock import AsyncMock, patch

import pytest


class TestIssue39RetrievedDocsFix:
    """Issue #39 Agent层retrieved_docs类型错误修复测试"""

    @pytest.mark.asyncio
    async def test_call_llm_node_with_string_retrieved_docs(self):
        """测试call_llm_node处理字符串类型的retrieved_docs"""
        from langchain_core.messages import AIMessage, HumanMessage

        from src.agent.main.nodes import call_llm_node

        # 模拟状态，retrieved_docs是字符串列表
        state = {
            "messages": [HumanMessage(content="iPhone 15 价格是多少？")],
            "retrieved_docs": [
                "[文档1] iPhone 15 产品信息 (来源: https://example.com/products/iphone-15)\niPhone 15 价格信息：...",
                "[文档2] iPhone 15 产品信息 (来源: https://example.com/products/iphone-15)\niPhone 15 价格信息：...",
                "[文档3] 支付方式 (来源: https://example.com/payment)\n支付方式：..."
            ],
            "tool_calls": []
        }

        # 模拟LLM响应
        mock_response = AIMessage(content="根据我们的产品信息，iPhone 15的价格是...")

        with patch("src.agent.main.nodes.create_llm") as mock_create_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = mock_response
            mock_create_llm.return_value = mock_llm

            # 调用call_llm_node
            result = await call_llm_node(state)

            # 验证结果
            assert "messages" in result
            assert len(result["messages"]) == 1
            assert isinstance(result["messages"][0], AIMessage)
            assert result["messages"][0].content == "根据我们的产品信息，iPhone 15的价格是..."

            # 验证LLM被正确调用
            mock_llm.ainvoke.assert_called_once()
            call_args = mock_llm.ainvoke.call_args[0][0]
            assert len(call_args) == 2  # SystemMessage + HumanMessage
            assert "知识库上下文" in call_args[0].content

    @pytest.mark.asyncio
    async def test_call_llm_node_with_empty_retrieved_docs(self):
        """测试call_llm_node处理空的retrieved_docs"""
        from langchain_core.messages import AIMessage, HumanMessage

        from src.agent.main.nodes import call_llm_node

        # 模拟状态，retrieved_docs为空
        state = {
            "messages": [HumanMessage(content="你好")],
            "retrieved_docs": [],
            "tool_calls": []
        }

        # 模拟LLM响应
        mock_response = AIMessage(content="你好！我是客服助手，有什么可以帮助您的吗？")

        with patch("src.agent.main.nodes.create_llm") as mock_create_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = mock_response
            mock_create_llm.return_value = mock_llm

            # 调用call_llm_node
            result = await call_llm_node(state)

            # 验证结果
            assert "messages" in result
            assert len(result["messages"]) == 1
            assert isinstance(result["messages"][0], AIMessage)

            # 验证LLM被正确调用
            mock_llm.ainvoke.assert_called_once()
            call_args = mock_llm.ainvoke.call_args[0][0]
            assert len(call_args) == 2  # SystemMessage + HumanMessage
            assert "专业、友好的网站客服助手" in call_args[0].content

    @pytest.mark.asyncio
    async def test_call_llm_node_with_mixed_retrieved_docs(self):
        """测试call_llm_node处理混合类型的retrieved_docs"""
        from langchain_core.messages import AIMessage, HumanMessage

        from src.agent.main.nodes import call_llm_node

        # 模拟状态，retrieved_docs包含字符串和字典（异常情况）
        state = {
            "messages": [HumanMessage(content="测试混合类型")],
            "retrieved_docs": [
                "[文档1] 测试文档1",
                {"text": "测试文档2", "metadata": {"title": "测试"}},  # 字典类型
                "[文档3] 测试文档3"
            ],
            "tool_calls": []
        }

        # 模拟LLM响应
        mock_response = AIMessage(content="基于检索的响应")

        with patch("src.agent.main.nodes.create_llm") as mock_create_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = mock_response
            mock_create_llm.return_value = mock_llm

            # 调用call_llm_node
            result = await call_llm_node(state)

            # 验证结果
            assert "messages" in result
            assert len(result["messages"]) == 1
            assert isinstance(result["messages"][0], AIMessage)

            # 验证LLM被正确调用
            mock_llm.ainvoke.assert_called_once()
            call_args = mock_llm.ainvoke.call_args[0][0]
            assert len(call_args) == 2  # SystemMessage + HumanMessage
            assert "知识库上下文" in call_args[0].content

    @pytest.mark.asyncio
    async def test_call_llm_node_error_handling(self):
        """测试call_llm_node的错误处理"""
        from langchain_core.messages import HumanMessage

        from src.agent.main.nodes import call_llm_node

        # 模拟状态
        state = {
            "messages": [HumanMessage(content="测试错误处理")],
            "retrieved_docs": ["[文档1] 测试文档"],
            "tool_calls": []
        }

        # 模拟LLM调用失败
        with patch("src.agent.main.nodes.create_llm") as mock_create_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.side_effect = Exception("LLM调用失败")
            mock_create_llm.return_value = mock_llm

            # 调用call_llm_node
            result = await call_llm_node(state)

            # 验证错误处理
            assert "messages" in result
            assert "error" in result
            assert result["error"] == "LLM调用失败"
            assert "抱歉，系统遇到了一些问题" in result["messages"][0].content

    @pytest.mark.asyncio
    async def test_retrieve_node_output_format(self):
        """测试retrieve_node的输出格式"""
        from langchain_core.messages import HumanMessage

        from src.agent.main.nodes import retrieve_node

        # 模拟状态
        state = {
            "messages": [HumanMessage(content="iPhone 15 价格")],
            "retrieved_docs": [],
            "tool_calls": []
        }

        # 模拟知识库检索结果
        mock_results = [
            {
                "text": "iPhone 15 价格信息：...",
                "score": 0.95,
                "metadata": {"title": "iPhone 15 产品信息", "url": "https://example.com/products/iphone-15"}
            },
            {
                "text": "iPhone 15 规格信息：...",
                "score": 0.90,
                "metadata": {"title": "iPhone 15 规格", "url": "https://example.com/products/iphone-15"}
            }
        ]

        # Mock recall agent result
        from src.agent.recall.schema import RecallHit, RecallResult

        mock_hits = []
        for i, mock_result in enumerate(mock_results, 1):
            hit = RecallHit(
                source="vector",
                score=mock_result["score"],
                confidence=0.8,
                reason="向量相似度匹配",
                content=mock_result["text"],
                metadata=mock_result["metadata"]
            )
            mock_hits.append(hit)

        mock_recall_result = RecallResult(
            hits=mock_hits,
            latency_ms=100.0,
            degraded=False,
            trace_id="test-trace",
            experiment_id=None
        )

        with patch("src.agent.recall.graph.invoke_recall_agent", return_value=mock_recall_result):
            # 调用retrieve_node
            result = await retrieve_node(state)

            # 验证输出格式
            assert "retrieved_docs" in result
            assert "confidence_score" in result
            assert "tool_calls" in result

            # 验证retrieved_docs是字符串列表
            assert isinstance(result["retrieved_docs"], list)
            assert len(result["retrieved_docs"]) == 2
            assert all(isinstance(doc, str) for doc in result["retrieved_docs"])
            assert "[文档1]" in result["retrieved_docs"][0]
            assert "[文档2]" in result["retrieved_docs"][1]

    @pytest.mark.asyncio
    async def test_rag_workflow_integration(self):
        """测试RAG工作流集成"""
        from langchain_core.messages import HumanMessage

        from src.agent.main.nodes import call_llm_node, retrieve_node

        # 模拟状态
        state = {
            "messages": [HumanMessage(content="iPhone 15 价格是多少？")],
            "retrieved_docs": [],
            "tool_calls": []
        }

        # 模拟知识库检索结果
        mock_results = [
            {
                "text": "iPhone 15 价格信息：...",
                "score": 0.95,
                "metadata": {"title": "iPhone 15 产品信息", "url": "https://example.com/products/iphone-15"}
            }
        ]

        # Mock recall agent result
        from src.agent.recall.schema import RecallHit, RecallResult

        mock_hit = RecallHit(
            source="vector",
            score=mock_results[0]["score"],
            confidence=0.8,
            reason="向量相似度匹配",
            content=mock_results[0]["text"],
            metadata=mock_results[0]["metadata"]
        )

        mock_recall_result = RecallResult(
            hits=[mock_hit],
            latency_ms=100.0,
            degraded=False,
            trace_id="test-trace",
            experiment_id=None
        )

        with patch("src.agent.recall.graph.invoke_recall_agent", return_value=mock_recall_result):
            # 第一步：检索文档
            retrieve_result = await retrieve_node(state)

            # 验证检索结果
            assert "retrieved_docs" in retrieve_result
            assert len(retrieve_result["retrieved_docs"]) == 1
            assert isinstance(retrieve_result["retrieved_docs"][0], str)

            # 第二步：调用LLM
            updated_state = {**state, **retrieve_result}

            with patch("src.agent.main.nodes.create_llm") as mock_create_llm:
                from langchain_core.messages import AIMessage
                mock_llm = AsyncMock()
                mock_llm.ainvoke.return_value = AIMessage(content="根据我们的产品信息，iPhone 15的价格是...")
                mock_create_llm.return_value = mock_llm

                llm_result = await call_llm_node(updated_state)

                # 验证LLM结果
                assert "messages" in llm_result
                assert len(llm_result["messages"]) == 1
                assert "根据我们的产品信息" in llm_result["messages"][0].content

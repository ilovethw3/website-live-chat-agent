"""
Issue #41 修复测试

测试SiliconFlow Embedding API调用格式错误修复。
"""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.services.providers.siliconflow_provider import (
    SiliconFlowEmbeddingProvider,
    SiliconFlowEmbeddings,
)


class TestIssue41SiliconFlowEmbeddingFix:
    """Issue #41 SiliconFlow Embedding API调用格式错误修复测试"""

    def test_siliconflow_embeddings_text_input(self):
        """测试SiliconFlow Embeddings发送文本而不是token ID数组"""
        embeddings = SiliconFlowEmbeddings(
            api_key="test-key",
            model="BAAI/bge-large-zh-v1.5",
            base_url="https://api.siliconflow.cn/v1"
        )

        # 验证配置
        assert embeddings.api_key == "test-key"
        assert embeddings.model == "BAAI/bge-large-zh-v1.5"
        assert embeddings.base_url == "https://api.siliconflow.cn/v1"

    @pytest.mark.asyncio
    async def test_aembed_query_sends_text(self):
        """测试aembed_query发送文本格式"""
        embeddings = SiliconFlowEmbeddings(
            api_key="test-key",
            model="BAAI/bge-large-zh-v1.5"
        )

        # 模拟API响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}]
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await embeddings.aembed_query("退货")

            # 验证结果
            assert result == [0.1, 0.2, 0.3]

            # 验证API调用参数
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            assert call_args[1]["json"]["input"] == "退货"  # 文本格式
            assert call_args[1]["json"]["model"] == "BAAI/bge-large-zh-v1.5"
            assert "input" in call_args[1]["json"]
            assert isinstance(call_args[1]["json"]["input"], str)  # 确保是字符串

    @pytest.mark.asyncio
    async def test_aembed_documents_sends_text_list(self):
        """测试aembed_documents发送文本列表"""
        embeddings = SiliconFlowEmbeddings(
            api_key="test-key",
            model="BAAI/bge-large-zh-v1.5"
        )

        # 模拟API响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3]},
                {"embedding": [0.4, 0.5, 0.6]}
            ]
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await embeddings.aembed_documents(["退货", "退款"])

            # 验证结果
            assert len(result) == 2
            assert result[0] == [0.1, 0.2, 0.3]
            assert result[1] == [0.4, 0.5, 0.6]

            # 验证API调用参数
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            assert call_args[1]["json"]["input"] == ["退货", "退款"]  # 文本列表格式
            assert call_args[1]["json"]["model"] == "BAAI/bge-large-zh-v1.5"
            assert "input" in call_args[1]["json"]
            assert isinstance(call_args[1]["json"]["input"], list)  # 确保是列表
            assert all(isinstance(item, str) for item in call_args[1]["json"]["input"])  # 确保列表元素是字符串

    def test_embed_query_sync(self):
        """测试同步embed_query方法"""
        embeddings = SiliconFlowEmbeddings(
            api_key="test-key",
            model="BAAI/bge-large-zh-v1.5"
        )

        # 直接模拟异步方法返回结果
        with patch.object(embeddings, 'aembed_query', return_value=[0.1, 0.2, 0.3]) as mock_aembed:
            result = embeddings.embed_query("退货")

            assert result == [0.1, 0.2, 0.3]
            mock_aembed.assert_called_once_with("退货")

    def test_embed_documents_sync(self):
        """测试同步embed_documents方法"""
        embeddings = SiliconFlowEmbeddings(
            api_key="test-key",
            model="BAAI/bge-large-zh-v1.5"
        )

        # 直接模拟异步方法返回结果
        with patch.object(embeddings, 'aembed_documents', return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]) as mock_aembed:
            result = embeddings.embed_documents(["退货", "退款"])

            assert len(result) == 2
            assert result[0] == [0.1, 0.2, 0.3]
            assert result[1] == [0.4, 0.5, 0.6]
            mock_aembed.assert_called_once_with(["退货", "退款"])

    def test_siliconflow_embedding_provider_creation(self):
        """测试SiliconFlow Embedding Provider创建"""
        config = {
            "api_key": "test-key",
            "model": "BAAI/bge-large-zh-v1.5",
            "base_url": "https://api.siliconflow.cn/v1"
        }

        provider = SiliconFlowEmbeddingProvider(config)
        embeddings = provider.create_embeddings()

        # 验证创建的embeddings实例
        assert isinstance(embeddings, SiliconFlowEmbeddings)
        assert embeddings.api_key == "test-key"
        assert embeddings.model == "BAAI/bge-large-zh-v1.5"
        assert embeddings.base_url == "https://api.siliconflow.cn/v1"

    def test_siliconflow_embedding_provider_models(self):
        """测试SiliconFlow Embedding Provider支持的模型"""
        config = {"api_key": "test-key"}
        provider = SiliconFlowEmbeddingProvider(config)
        models = provider.get_models()

        expected_models = [
            "BAAI/bge-large-zh-v1.5",
            "BAAI/bge-base-zh-v1.5",
            "BAAI/bge-small-zh-v1.5",
            "BAAI/bge-large-en-v1.5",
            "BAAI/bge-base-en-v1.5"
        ]

        for model in expected_models:
            assert model in models

    def test_siliconflow_embedding_provider_required_fields(self):
        """测试SiliconFlow Embedding Provider必需字段"""
        config = {"api_key": "test-key"}
        provider = SiliconFlowEmbeddingProvider(config)
        required_fields = provider.get_required_config_fields()

        assert "api_key" in required_fields
        assert len(required_fields) == 1  # 只有api_key是必需的

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """测试API错误处理"""
        embeddings = SiliconFlowEmbeddings(
            api_key="test-key",
            model="BAAI/bge-large-zh-v1.5"
        )

        # 模拟API错误
        mock_response = Mock()
        mock_response.status_code = 500
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.HTTPStatusError("500 Internal Server Error", request=Mock(), response=mock_response)
            )

            with pytest.raises(httpx.HTTPStatusError):
                await embeddings.aembed_query("退货")

    @pytest.mark.asyncio
    async def test_api_request_format(self):
        """测试API请求格式确保发送文本"""
        embeddings = SiliconFlowEmbeddings(
            api_key="test-key",
            model="BAAI/bge-large-zh-v1.5"
        )

        # 模拟API响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}]
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            await embeddings.aembed_query("退货")

            # 验证请求格式
            call_args = mock_post.call_args
            request_data = call_args[1]["json"]

            # 确保发送的是文本，不是token ID数组
            assert request_data["input"] == "退货"
            assert isinstance(request_data["input"], str)
            assert request_data["model"] == "BAAI/bge-large-zh-v1.5"

            # 确保没有发送token ID数组格式
            assert not isinstance(request_data["input"], list)
            assert "encoding_format" not in request_data

    @pytest.mark.asyncio
    async def test_retry_mechanism_on_5xx_error(self):
        """测试5xx错误时的重试机制"""
        embeddings = SiliconFlowEmbeddings(
            api_key="test-key",
            model="BAAI/bge-large-zh-v1.5"
        )

        # 模拟第一次5xx错误，第二次成功
        mock_response_success = Mock()
        mock_response_success.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}]
        }
        mock_response_success.raise_for_status.return_value = None

        # 创建5xx错误的Mock响应
        mock_5xx_response = Mock()
        mock_5xx_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            # 第一次调用失败，第二次成功
            mock_post = AsyncMock(side_effect=[
                httpx.HTTPStatusError("500 Internal Server Error", request=Mock(), response=mock_5xx_response),
                mock_response_success
            ])
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await embeddings.aembed_query("退货")

            # 验证结果
            assert result == [0.1, 0.2, 0.3]
            # 验证重试了2次
            assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_4xx_error(self):
        """测试4xx错误时不重试"""
        embeddings = SiliconFlowEmbeddings(
            api_key="test-key",
            model="BAAI/bge-large-zh-v1.5"
        )

        # 创建4xx错误的Mock响应
        mock_4xx_response = Mock()
        mock_4xx_response.status_code = 400

        with patch("httpx.AsyncClient") as mock_client:
            # 模拟4xx错误
            mock_post = AsyncMock(side_effect=httpx.HTTPStatusError("400 Bad Request", request=Mock(), response=mock_4xx_response))
            mock_client.return_value.__aenter__.return_value.post = mock_post

            with pytest.raises(httpx.HTTPStatusError):
                await embeddings.aembed_query("退货")

            # 验证只调用了一次，没有重试
            assert mock_post.call_count == 1

    @pytest.mark.asyncio
    async def test_network_error_retry(self):
        """测试网络错误时的重试机制"""
        embeddings = SiliconFlowEmbeddings(
            api_key="test-key",
            model="BAAI/bge-large-zh-v1.5"
        )

        # 模拟网络错误，然后成功
        mock_response_success = Mock()
        mock_response_success.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}]
        }
        mock_response_success.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            # 第一次网络错误，第二次成功
            mock_post = AsyncMock(side_effect=[
                httpx.TimeoutException("Request timeout"),
                mock_response_success
            ])
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await embeddings.aembed_query("退货")

            # 验证结果
            assert result == [0.1, 0.2, 0.3]
            # 验证重试了2次
            assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """测试超过最大重试次数时的行为"""
        embeddings = SiliconFlowEmbeddings(
            api_key="test-key",
            model="BAAI/bge-large-zh-v1.5"
        )

        with patch("httpx.AsyncClient") as mock_client:
            # 模拟持续的网络错误
            mock_post = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
            mock_client.return_value.__aenter__.return_value.post = mock_post

            with pytest.raises(httpx.TimeoutException):
                await embeddings.aembed_query("退货")

            # 验证重试了最大次数 + 1 次（初始调用 + 重试次数）
            assert mock_post.call_count == embeddings.max_retries + 1

    def test_sync_methods_in_event_loop(self):
        """测试同步方法在事件循环中的行为"""
        embeddings = SiliconFlowEmbeddings(
            api_key="test-key",
            model="BAAI/bge-large-zh-v1.5"
        )

        # 模拟异步方法返回结果
        with patch.object(embeddings, 'aembed_query', return_value=[0.1, 0.2, 0.3]) as mock_aembed:
            # 模拟在事件循环中调用同步方法
            with patch('asyncio.get_running_loop') as mock_get_loop:
                # 模拟已有事件循环
                mock_loop = Mock()
                mock_get_loop.return_value = mock_loop

                # 模拟 ThreadPoolExecutor
                with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
                    mock_future = Mock()
                    mock_future.result.return_value = [0.1, 0.2, 0.3]
                    mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future

                    result = embeddings.embed_query("退货")

                    # 验证结果
                    assert result == [0.1, 0.2, 0.3]
                    # 验证使用了 ThreadPoolExecutor
                    mock_executor.assert_called_once()

    def test_sync_methods_outside_event_loop(self):
        """测试同步方法在事件循环外的行为"""
        embeddings = SiliconFlowEmbeddings(
            api_key="test-key",
            model="BAAI/bge-large-zh-v1.5"
        )

        # 模拟异步方法返回结果
        with patch.object(embeddings, 'aembed_query', return_value=[0.1, 0.2, 0.3]) as mock_aembed:
            # 模拟没有事件循环
            with patch('asyncio.get_running_loop', side_effect=RuntimeError("No running event loop")):
                with patch('asyncio.run') as mock_asyncio_run:
                    mock_asyncio_run.return_value = [0.1, 0.2, 0.3]

                    result = embeddings.embed_query("退货")

                    # 验证结果
                    assert result == [0.1, 0.2, 0.3]
                    # 验证使用了 asyncio.run，传入的是协程对象
                    mock_asyncio_run.assert_called_once()
                    # 验证调用参数是协程对象
                    call_args = mock_asyncio_run.call_args[0]
                    assert len(call_args) == 1
                    # 验证传入的是协程对象（通过检查类型）
                    import inspect
                    assert inspect.iscoroutine(call_args[0])

    @pytest.mark.asyncio
    async def test_sync_methods_in_async_context(self):
        """测试在异步上下文中调用同步方法"""
        embeddings = SiliconFlowEmbeddings(
            api_key="test-key",
            model="BAAI/bge-large-zh-v1.5"
        )

        # 模拟异步方法返回结果
        with patch.object(embeddings, 'aembed_query', return_value=[0.1, 0.2, 0.3]) as mock_aembed:
            # 在异步上下文中调用同步方法
            with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
                mock_future = Mock()
                mock_future.result.return_value = [0.1, 0.2, 0.3]
                mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future

                result = embeddings.embed_query("退货")

                # 验证结果
                assert result == [0.1, 0.2, 0.3]
                # 验证使用了 ThreadPoolExecutor
                mock_executor.assert_called_once()


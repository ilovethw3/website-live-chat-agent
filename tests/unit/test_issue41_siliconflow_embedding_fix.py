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
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.HTTPStatusError("500 Internal Server Error", request=Mock(), response=Mock())
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

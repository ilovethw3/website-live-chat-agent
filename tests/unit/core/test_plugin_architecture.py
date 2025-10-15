"""
插件化架构测试

测试插件化模型提供商系统的功能。
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.config import Settings
from src.services.providers import create_provider, get_provider, list_providers, register_provider
from src.services.providers.deepseek_provider import DeepSeekLLMProvider
from src.services.providers.openai_provider import OpenAIEmbeddingProvider, OpenAILLMProvider
from src.services.providers.siliconflow_provider import (
    SiliconFlowEmbeddingProvider,
    SiliconFlowLLMProvider,
)


class TestProviderRegistry:
    """测试提供商注册系统"""

    def test_get_provider_success(self):
        """测试获取提供商成功"""
        provider_class = get_provider("openai_llm")
        assert provider_class == OpenAILLMProvider

    def test_get_provider_not_found(self):
        """测试获取不存在的提供商"""
        with pytest.raises(ValueError, match="Unsupported provider"):
            get_provider("nonexistent_provider")

    def test_create_provider_success(self):
        """测试创建提供商实例成功"""
        config = {"api_key": "test-key", "model": "gpt-4o-mini"}
        provider = create_provider("openai_llm", config)
        assert isinstance(provider, OpenAILLMProvider)
        assert provider.config == config

    def test_list_providers(self):
        """测试列出所有提供商"""
        providers = list_providers()
        assert "openai_llm" in providers
        assert "deepseek_llm" in providers
        assert "siliconflow_llm" in providers
        assert "openai_embedding" in providers
        assert "deepseek_embedding" in providers
        assert "siliconflow_embedding" in providers

    def test_register_provider(self):
        """测试注册新提供商"""
        class TestProvider:
            pass

        register_provider("test_provider", TestProvider)
        provider_class = get_provider("test_provider")
        assert provider_class == TestProvider


class TestOpenAIProvider:
    """测试OpenAI提供商"""

    def test_llm_provider_creation(self):
        """测试OpenAI LLM提供商创建"""
        config = {
            "api_key": "test-openai-key",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        provider = OpenAILLMProvider(config)
        assert provider.config == config

    def test_llm_provider_required_fields(self):
        """测试OpenAI LLM提供商必需字段"""
        # 使用有效配置创建提供商实例
        config = {"api_key": "test-key"}
        provider = OpenAILLMProvider(config)
        required_fields = provider.get_required_config_fields()
        assert "api_key" in required_fields

    def test_llm_provider_models(self):
        """测试OpenAI LLM提供商支持的模型"""
        config = {"api_key": "test-key"}
        provider = OpenAILLMProvider(config)
        models = provider.get_models()
        assert "gpt-4o-mini" in models
        assert "gpt-4o" in models
        assert "gpt-3.5-turbo" in models

    def test_embedding_provider_creation(self):
        """测试OpenAI Embedding提供商创建"""
        config = {
            "api_key": "test-openai-key",
            "model": "text-embedding-3-small"
        }
        provider = OpenAIEmbeddingProvider(config)
        assert provider.config == config

    def test_embedding_provider_models(self):
        """测试OpenAI Embedding提供商支持的模型"""
        config = {"api_key": "test-key"}
        provider = OpenAIEmbeddingProvider(config)
        models = provider.get_models()
        assert "text-embedding-3-small" in models
        assert "text-embedding-3-large" in models


class TestDeepSeekProvider:
    """测试DeepSeek提供商"""

    def test_llm_provider_creation(self):
        """测试DeepSeek LLM提供商创建"""
        config = {
            "api_key": "test-deepseek-key",
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat"
        }
        provider = DeepSeekLLMProvider(config)
        assert provider.config == config

    def test_llm_provider_required_fields(self):
        """测试DeepSeek LLM提供商必需字段"""
        # 使用有效配置创建提供商实例
        config = {"api_key": "test-key", "base_url": "https://api.deepseek.com/v1"}
        provider = DeepSeekLLMProvider(config)
        required_fields = provider.get_required_config_fields()
        assert "api_key" in required_fields
        assert "base_url" in required_fields

    def test_llm_provider_models(self):
        """测试DeepSeek LLM提供商支持的模型"""
        config = {"api_key": "test-key", "base_url": "https://api.deepseek.com/v1"}
        provider = DeepSeekLLMProvider(config)
        models = provider.get_models()
        assert "deepseek-chat" in models
        assert "deepseek-coder" in models
        assert "deepseek-math" in models


class TestSiliconFlowProvider:
    """测试硅基流动提供商"""

    def test_llm_provider_creation(self):
        """测试硅基流动 LLM提供商创建"""
        config = {
            "api_key": "test-sf-key",
            "base_url": "https://api.siliconflow.cn/v1",
            "model": "Qwen/Qwen2.5-7B-Instruct"
        }
        provider = SiliconFlowLLMProvider(config)
        assert provider.config == config

    def test_llm_provider_required_fields(self):
        """测试硅基流动 LLM提供商必需字段"""
        # 使用有效配置创建提供商实例
        config = {"api_key": "test-key", "base_url": "https://api.siliconflow.cn/v1"}
        provider = SiliconFlowLLMProvider(config)
        required_fields = provider.get_required_config_fields()
        assert "api_key" in required_fields
        assert "base_url" in required_fields

    def test_llm_provider_models(self):
        """测试硅基流动 LLM提供商支持的模型"""
        config = {"api_key": "test-key", "base_url": "https://api.siliconflow.cn/v1"}
        provider = SiliconFlowLLMProvider(config)
        models = provider.get_models()
        assert "Qwen/Qwen2.5-7B-Instruct" in models
        assert "Qwen/Qwen2.5-14B-Instruct" in models
        assert "Qwen/Qwen2.5-32B-Instruct" in models

    def test_embedding_provider_models(self):
        """测试硅基流动 Embedding提供商支持的模型"""
        config = {"api_key": "test-key", "base_url": "https://api.siliconflow.cn/v1"}
        provider = SiliconFlowEmbeddingProvider(config)
        models = provider.get_models()
        assert "BAAI/bge-large-zh-v1.5" in models
        assert "BAAI/bge-base-zh-v1.5" in models
        assert "BAAI/bge-small-zh-v1.5" in models


class TestConfigSeparation:
    """测试配置分离功能"""

    def test_llm_embedding_independent_config(self):
        """测试LLM和Embedding可以独立配置"""
        settings = Settings(
            llm_provider="deepseek",
            deepseek_api_key="test-llm-key",
            deepseek_model="deepseek-chat",
            embedding_provider="openai",
            openai_api_key="test-embedding-key",
            embedding_model="text-embedding-3-small"
        )

        assert settings.llm_provider == "deepseek"
        assert settings.embedding_provider == "openai"
        assert settings.llm_model_name == "deepseek-chat"
        assert settings.embedding_model_name == "text-embedding-3-small"

    def test_siliconflow_support(self):
        """测试硅基流动平台支持"""
        settings = Settings(
            llm_provider="siliconflow",
            siliconflow_api_key="test-sf-key",
            siliconflow_llm_model="Qwen/Qwen2.5-7B-Instruct",
            embedding_provider="siliconflow",
            siliconflow_embedding_model="BAAI/bge-large-zh-v1.5"
        )

        assert settings.llm_provider == "siliconflow"
        assert settings.embedding_provider == "siliconflow"
        assert settings.llm_model_name == "Qwen/Qwen2.5-7B-Instruct"
        assert settings.embedding_model_name == "BAAI/bge-large-zh-v1.5"

    def test_mixed_model_combination(self):
        """测试混合模型组合"""
        settings = Settings(
            llm_provider="deepseek",
            deepseek_api_key="test-deepseek-key",
            deepseek_model="deepseek-chat",
            embedding_provider="openai",
            openai_api_key="test-openai-key",
            embedding_model="text-embedding-3-small"
        )

        # 验证LLM配置
        assert settings.llm_api_key == "test-deepseek-key"
        assert settings.llm_model_name == "deepseek-chat"
        assert settings.llm_base_url == "https://api.deepseek.com/v1"

        # 验证Embedding配置
        assert settings.embedding_api_key == "test-openai-key"
        assert settings.embedding_model_name == "text-embedding-3-small"
        assert settings.get_embedding_base_url() is None  # OpenAI使用默认URL

    def test_backward_compatibility(self):
        """测试向后兼容性"""
        # 测试现有配置仍然工作
        settings = Settings(
            llm_provider="deepseek",
            deepseek_api_key="test-key"
        )

        assert settings.llm_provider == "deepseek"
        assert settings.llm_api_key == "test-key"
        # 应该自动映射到新的配置结构
        assert settings.llm_model_name == "deepseek-chat"


class TestConfigValidation:
    """测试配置验证功能"""

    @patch('src.services.llm_factory.create_llm')
    @patch('src.services.llm_factory.create_embeddings')
    def test_validate_configuration_success(self, mock_embeddings, mock_llm):
        """测试配置验证成功"""
        mock_llm.return_value = MagicMock()
        mock_embeddings.return_value = MagicMock()

        settings = Settings(
            llm_provider="deepseek",
            deepseek_api_key="test-key",
            embedding_provider="openai",
            openai_api_key="test-key"
        )

        results = settings.validate_configuration()

        assert results["llm_valid"] is True
        assert results["embedding_valid"] is True

    @patch('src.services.llm_factory.create_llm')
    @patch('src.services.llm_factory.create_embeddings')
    def test_validate_configuration_failure(self, mock_embeddings, mock_llm):
        """测试配置验证失败"""
        mock_llm.side_effect = Exception("LLM配置错误")
        mock_embeddings.side_effect = Exception("Embedding配置错误")

        settings = Settings(
            llm_provider="deepseek",
            deepseek_api_key="test-key",
            embedding_provider="openai",
            openai_api_key="test-key"
        )

        results = settings.validate_configuration()

        assert results["llm_valid"] is False
        assert results["embedding_valid"] is False
        assert "LLM配置错误" in results["llm_error"]
        assert "Embedding配置错误" in results["embedding_error"]


class TestMigration:
    """测试配置迁移功能"""

    def test_migrate_legacy_config(self):
        """测试迁移旧配置"""
        from src.core.migration import migrate_legacy_config

        result = migrate_legacy_config()

        assert result["success"] is True
        assert "changes" in result
        assert "warnings" in result
        assert "new_config" in result

    def test_validate_migrated_config(self):
        """测试验证迁移后的配置"""
        from src.core.migration import validate_migrated_config

        result = validate_migrated_config()

        assert "success" in result
        assert "llm_valid" in result
        assert "embedding_valid" in result
        assert "errors" in result
        assert "warnings" in result

    def test_generate_migration_report(self):
        """测试生成迁移报告"""
        from src.core.migration import generate_migration_report

        report = generate_migration_report()

        assert isinstance(report, str)
        assert "# 配置迁移报告" in report
        assert "迁移状态" in report
        assert "变更内容" in report
        assert "配置验证" in report

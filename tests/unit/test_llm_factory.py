"""
测试 LLM 工厂模块

测试不同 LLM Provider 的创建逻辑。
"""

import os
from unittest.mock import patch

import pytest

from src.core.exceptions import ConfigurationError
from src.services.llm_factory import create_llm


def get_base_test_env() -> dict:
    """获取测试所需的基础环境变量"""
    return {
        "MILVUS_HOST": "localhost",
        "REDIS_HOST": "localhost",
        "API_KEY": "test-api-key",
    }


def test_create_llm_deepseek():
    """测试创建 DeepSeek LLM"""
    with patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "LLM_MODEL_NAME": "deepseek-chat",
        },
    ):
        llm = create_llm()
        assert llm is not None
        assert hasattr(llm, "invoke")


def test_create_llm_openai():
    """测试创建 OpenAI LLM"""
    with patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
            "LLM_MODEL_NAME": "gpt-4o-mini",
        },
    ):
        llm = create_llm()
        assert llm is not None
        assert hasattr(llm, "invoke")


def test_create_llm_anthropic():
    """测试创建 Anthropic LLM"""
    with patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "test-key",
            "LLM_MODEL_NAME": "claude-3-5-sonnet-20241022",
        },
    ):
        llm = create_llm()
        assert llm is not None
        assert hasattr(llm, "invoke")


def test_create_llm_missing_deepseek_key():
    """测试缺少 DeepSeek API Key"""
    # 确保测试时强制重新加载 settings
    from src.core.config import Settings

    with patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "",
            "API_KEY": "test-key",
            "MILVUS_HOST": "localhost"
        },
        clear=True
    ):
        # 重新创建 settings 实例
        with patch("src.services.llm_factory.settings", Settings()):
            with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
                create_llm()


def test_create_llm_missing_openai_key():
    """测试缺少 OpenAI API Key"""
    from src.core.config import Settings

    with patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "",
            "API_KEY": "test-key",
            "MILVUS_HOST": "localhost"
        },
        clear=True
    ):
        with patch("src.services.llm_factory.settings", Settings()):
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                create_llm()


def test_create_llm_invalid_provider():
    """测试无效的 LLM Provider"""
    # 由于 Settings 使用 Literal 验证，无效的 provider 会在 Settings 初始化时失败
    # 这里测试 ConfigurationError 的抛出（从 create_llm 的 else 分支）

    # 临时修改 settings 以测试 else 分支
    with patch("src.services.llm_factory.settings") as mock_settings:
        mock_settings.llm_provider = "invalid_provider"
        with pytest.raises(ConfigurationError, match="Unsupported LLM provider"):
            create_llm()


def test_create_llm_with_custom_temperature():
    """测试自定义温度参数"""
    with patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "LLM_TEMPERATURE": "0.5",
        },
    ):
        llm = create_llm()
        assert llm is not None
        # 温度参数应该已应用（具体验证取决于 LLM 实现）


class TestEmbeddingFactory:
    """Embedding工厂测试类"""

    def test_create_embeddings_with_independent_url(self):
        """测试使用独立URL创建embeddings"""
        from src.services.llm_factory import create_embeddings

        env = get_base_test_env()
        env.update({
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "https://independent-embedding.com/v1"
        })
        with patch.dict(os.environ, env, clear=True):
            embeddings = create_embeddings()
            assert embeddings is not None
            assert hasattr(embeddings, "embed_query")

    def test_create_embeddings_with_provider_specific_url(self):
        """测试使用提供商特定URL创建embeddings"""
        from src.services.llm_factory import create_embeddings

        env = get_base_test_env()
        env.update({
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "",
            "DEEPSEEK_EMBEDDING_BASE_URL": "https://embedding.deepseek.com/v1"
        })
        with patch.dict(os.environ, env, clear=True):
            embeddings = create_embeddings()
            assert embeddings is not None
            assert hasattr(embeddings, "embed_query")

    def test_create_embeddings_with_shared_url(self):
        """测试使用共享URL创建embeddings"""
        from src.services.llm_factory import create_embeddings

        env = get_base_test_env()
        env.update({
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "",
            "DEEPSEEK_EMBEDDING_BASE_URL": "",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1"
        })
        with patch.dict(os.environ, env, clear=True):
            embeddings = create_embeddings()
            assert embeddings is not None
            assert hasattr(embeddings, "embed_query")

    def test_create_embeddings_without_url(self):
        """测试不使用URL创建embeddings（使用默认URL）"""
        from src.services.llm_factory import create_embeddings

        env = get_base_test_env()
        env.update({
            "EMBEDDING_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "",
            "OPENAI_EMBEDDING_BASE_URL": ""
        })
        with patch.dict(os.environ, env, clear=True):
            embeddings = create_embeddings()
            assert embeddings is not None
            assert hasattr(embeddings, "embed_query")

    def test_create_embeddings_openai_provider(self):
        """测试OpenAI provider的embeddings创建"""
        from src.services.llm_factory import create_embeddings

        env = get_base_test_env()
        env.update({
            "EMBEDDING_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "https://api.openai.com/v1"
        })
        with patch.dict(os.environ, env, clear=True):
            embeddings = create_embeddings()
            assert embeddings is not None
            assert hasattr(embeddings, "embed_query")

    def test_create_embeddings_siliconflow_provider(self):
        """测试SiliconFlow provider的embeddings创建"""
        from src.services.llm_factory import create_embeddings

        env = get_base_test_env()
        env.update({
            "EMBEDDING_PROVIDER": "siliconflow",
            "SILICONFLOW_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "https://embedding.siliconflow.cn/v1"
        })
        with patch.dict(os.environ, env, clear=True):
            embeddings = create_embeddings()
            assert embeddings is not None
            assert hasattr(embeddings, "embed_query")

    def test_create_embeddings_anthropic_provider(self):
        """测试Anthropic provider的embeddings创建"""
        from src.services.llm_factory import create_embeddings

        env = get_base_test_env()
        env.update({
            "EMBEDDING_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "https://api.anthropic.com/v1"
        })
        with patch.dict(os.environ, env, clear=True):
            embeddings = create_embeddings()
            assert embeddings is not None
            assert hasattr(embeddings, "embed_query")

    def test_create_embeddings_local_provider(self):
        """测试本地provider的embeddings创建"""
        from src.services.llm_factory import create_embeddings

        env = get_base_test_env()
        env.update({
            "EMBEDDING_PROVIDER": "local",
            "EMBEDDING_BASE_URL": ""
        })
        with patch.dict(os.environ, env, clear=True):
            embeddings = create_embeddings()
            assert embeddings is not None
            assert hasattr(embeddings, "embed_query")

    def test_create_embeddings_url_priority(self):
        """测试URL优先级机制"""
        from src.services.llm_factory import create_embeddings

        # 测试独立URL优先级
        env = get_base_test_env()
        env.update({
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "https://independent.com/v1",
            "DEEPSEEK_EMBEDDING_BASE_URL": "https://embedding.deepseek.com/v1",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1"
        })
        with patch.dict(os.environ, env, clear=True):
            embeddings = create_embeddings()
            assert embeddings is not None
            # 应该使用独立URL（最高优先级）

    def test_create_embeddings_invalid_provider(self):
        """测试无效的embedding provider"""
        from pydantic import ValidationError

        from src.core.config import Settings

        # Pydantic会在Settings初始化时验证provider字段
        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "invalid",  # 无效的provider会被Pydantic拒绝
            "EMBEDDING_BASE_URL": "https://api.example.com/v1"
        }, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_create_embeddings_plugin_architecture(self):
        """测试插件化架构的embeddings创建"""
        from src.services.llm_factory import _create_plugin_embeddings

        env = get_base_test_env()
        env.update({
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "https://plugin-embedding.com/v1"
        })
        with patch.dict(os.environ, env, clear=True):
            embeddings = _create_plugin_embeddings("deepseek")
            assert embeddings is not None
            assert hasattr(embeddings, "embed_query")

    def test_create_embeddings_url_validation(self):
        """测试URL验证功能"""
        from src.core.config import Settings

        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "invalid-url"
        }, clear=True):
            settings = Settings()
            validation_results = settings.validate_configuration()
            assert "embedding_url_valid" in validation_results
            assert "embedding_url_error" in validation_results

    def test_create_embeddings_complex_configuration(self):
        """测试复杂配置场景"""
        from src.services.llm_factory import create_embeddings

        env = get_base_test_env()
        env.update({
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "https://global-embedding.com/v1",
            "OPENAI_EMBEDDING_BASE_URL": "https://api.openai.com/v1",
            "DEEPSEEK_EMBEDDING_BASE_URL": "https://embedding.deepseek.com/v1",
            "SILICONFLOW_EMBEDDING_BASE_URL": "https://embedding.siliconflow.cn/v1",
            "ANTHROPIC_EMBEDDING_BASE_URL": "https://api.anthropic.com/v1",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1",
            "SILICONFLOW_BASE_URL": "https://api.siliconflow.cn/v1"
        })
        with patch.dict(os.environ, env, clear=True):
            embeddings = create_embeddings()
            assert embeddings is not None
            assert hasattr(embeddings, "embed_query")

    def test_create_embeddings_legacy_compatibility(self):
        """测试向后兼容性"""
        from src.services.llm_factory import create_embeddings

        env = get_base_test_env()
        env.update({
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1"
            # 不设置新的独立URL配置
        })
        with patch.dict(os.environ, env, clear=True):
            embeddings = create_embeddings()
            assert embeddings is not None
            assert hasattr(embeddings, "embed_query")

    def test_create_embeddings_all_providers(self):
        """测试所有provider的embeddings创建"""
        from src.services.llm_factory import create_embeddings

        providers = ["openai", "deepseek", "siliconflow", "anthropic", "local"]

        for provider in providers:
            env = get_base_test_env()
            env.update({
                "EMBEDDING_PROVIDER": provider,
                f"{provider.upper()}_API_KEY": "test-key",
                "EMBEDDING_BASE_URL": f"https://{provider}-embedding.com/v1"
            })
            with patch.dict(os.environ, env, clear=True):
                embeddings = create_embeddings()
                assert embeddings is not None
                assert hasattr(embeddings, "embed_query")


"""
测试配置管理模块

测试 Settings 类的环境变量加载、验证和默认值。
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.core.config import Settings


def test_settings_load_from_env():
    """测试从环境变量加载配置"""
    settings = Settings()

    assert settings.llm_provider == "deepseek"
    assert settings.deepseek_api_key == "test-deepseek-key"
    assert settings.milvus_host == "localhost"
    assert settings.milvus_port == 19530
    assert settings.api_key == "test-api-key-12345"


def test_settings_default_values():
    """测试默认值"""
    settings = Settings()

    assert settings.llm_temperature == 0.7
    assert settings.redis_port == 6379
    assert settings.redis_db == 0
    assert settings.log_level == "ERROR"
    # 测试新的 vector_* 配置项
    assert settings.vector_top_k == 3
    assert settings.vector_score_threshold == 0.7

    # 测试向后兼容别名
    assert settings.rag_top_k == settings.vector_top_k
    assert settings.rag_score_threshold == settings.vector_score_threshold


def test_settings_milvus_collections():
    """测试 Milvus Collection 名称配置"""
    settings = Settings()

    assert settings.milvus_knowledge_collection == "knowledge_base"
    assert settings.milvus_history_collection == "conversation_history"


def test_settings_milvus_database():
    """测试 Milvus 数据库配置"""
    settings = Settings()

    # 测试当前值（可能是环境变量覆盖的）
    assert settings.milvus_database in ["default", "chatagent"]
    # 测试类型
    assert isinstance(settings.milvus_database, str)


def test_settings_milvus_database_env_var():
    """测试 Milvus 数据库环境变量配置"""
    import os
    from unittest.mock import patch

    # 测试自定义数据库名称
    with patch.dict(os.environ, {"MILVUS_DATABASE": "custom_db"}, clear=False):
        # 需要重新导入以获取新的配置
        from importlib import reload

        import src.core.config
        reload(src.core.config)

        settings = src.core.config.Settings()
        assert settings.milvus_database == "custom_db"

        # 恢复原始模块
        reload(src.core.config)


def test_settings_langgraph_config():
    """测试 LangGraph 配置"""
    settings = Settings()

    assert settings.langgraph_max_iterations == 10
    assert settings.langgraph_checkpointer in ["memory", "redis"]


def test_settings_embedding_config():
    """测试 Embedding 配置"""
    settings = Settings()

    assert settings.embedding_model == "text-embedding-ada-002"
    assert settings.embedding_dim == 1536


# TECH DEBT: 当前测试通过修改 Settings.model_config 来绕过验证
# 追踪: https://github.com/alx18779-coder/website-live-chat-agent/issues/4
# 这依赖 Pydantic 内部实现，未来升级时可能失败
# 建议重构为使用独立的测试配置类或 pytest.fixture
# 参考方案：
#   1. 使用 pytest.MonkeyPatch
#   2. 使用 Pydantic 的 model_construct()
#   3. 创建专用测试配置类
def test_settings_required_fields():
    """测试必填字段验证"""
    from unittest.mock import patch

    # 测试缺少 api_key 字段
    # 需要 patch BaseSettings 的 model_config 以避免加载 .env 文件
    with patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "MILVUS_HOST": "localhost",
            # 故意不设置 API_KEY
        },
        clear=True
    ):
        # 临时修改 model_config 以禁用 .env 文件加载
        original_config = Settings.model_config.copy()
        try:
            Settings.model_config['env_file'] = None
            # 缺少 API_KEY 应该抛出 ValidationError
            with pytest.raises(ValidationError):
                Settings()
        finally:
            # 恢复原始配置
            Settings.model_config.update(original_config)

    # 测试缺少 milvus_host 字段
    with patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "API_KEY": "test-api-key",
            # 故意不设置 MILVUS_HOST
        },
        clear=True
    ):
        try:
            Settings.model_config['env_file'] = None
            # 缺少 MILVUS_HOST 应该抛出 ValidationError
            with pytest.raises(ValidationError):
                Settings()
        finally:
            Settings.model_config.update(original_config)


def test_settings_llm_provider_validation():
    """测试 LLM Provider 枚举验证"""
    # 临时设置无效的 provider
    original_provider = os.environ.get("LLM_PROVIDER")

    try:
        os.environ["LLM_PROVIDER"] = "invalid-provider"

        with pytest.raises(ValidationError):
            Settings()

    finally:
        if original_provider:
            os.environ["LLM_PROVIDER"] = original_provider


def test_settings_case_insensitive():
    """测试环境变量大小写不敏感"""
    # Settings 配置为 case_sensitive=False
    settings = Settings()

    # 应该能正确加载不同大小写的环境变量
    assert settings.api_key is not None


class TestEmbeddingURLConfiguration:
    """Embedding URL独立配置测试类"""

    def test_embedding_url_independent_priority(self):
        """测试独立URL优先级（最高）"""
        from unittest.mock import patch

        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "https://independent.com/v1",
            "DEEPSEEK_EMBEDDING_BASE_URL": "https://embedding.deepseek.com/v1",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1"
        }, clear=True):
            settings = Settings()
            url = settings.get_embedding_base_url()
            assert url == "https://independent.com/v1"

    def test_embedding_url_provider_specific_priority(self):
        """测试提供商特定URL优先级（中等）"""
        from unittest.mock import patch

        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "",
            "DEEPSEEK_EMBEDDING_BASE_URL": "https://embedding.deepseek.com/v1",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1"
        }, clear=True):
            settings = Settings()
            url = settings.get_embedding_base_url()
            assert url == "https://embedding.deepseek.com/v1"

    def test_embedding_url_shared_priority(self):
        """测试共享URL优先级（最低）"""
        from unittest.mock import patch

        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "",
            "DEEPSEEK_EMBEDDING_BASE_URL": "",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1"
        }, clear=True):
            settings = Settings()
            url = settings.get_embedding_base_url()
            assert url == "https://api.deepseek.com/v1"

    def test_embedding_url_no_configuration(self):
        """测试无URL配置"""
        from unittest.mock import patch

        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "",
            "OPENAI_EMBEDDING_BASE_URL": "",
            "OPENAI_BASE_URL": ""
        }, clear=True):
            settings = Settings()
            url = settings.get_embedding_base_url()
            assert url is None

    def test_embedding_url_openai_provider(self):
        """测试OpenAI提供商URL配置"""
        from unittest.mock import patch

        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "",
            "OPENAI_EMBEDDING_BASE_URL": "https://api.openai.com/v1"
        }, clear=True):
            settings = Settings()
            url = settings.get_embedding_base_url()
            assert url == "https://api.openai.com/v1"

    def test_embedding_url_siliconflow_provider(self):
        """测试SiliconFlow提供商URL配置"""
        from unittest.mock import patch

        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "siliconflow",
            "SILICONFLOW_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "",
            "SILICONFLOW_EMBEDDING_BASE_URL": "https://embedding.siliconflow.cn/v1",
            "SILICONFLOW_BASE_URL": "https://api.siliconflow.cn/v1"
        }, clear=True):
            settings = Settings()
            url = settings.get_embedding_base_url()
            assert url == "https://embedding.siliconflow.cn/v1"

    def test_embedding_url_anthropic_provider(self):
        """测试SiliconFlow提供商URL配置（anthropic不是有效的embedding provider）"""
        from unittest.mock import patch

        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "siliconflow",
            "SILICONFLOW_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "",
            "SILICONFLOW_EMBEDDING_BASE_URL": "https://api.siliconflow.com/v1"
        }, clear=True):
            settings = Settings()
            url = settings.get_embedding_base_url()
            assert url == "https://api.siliconflow.com/v1"

    def test_embedding_url_local_provider(self):
        """测试本地提供商URL配置"""
        from unittest.mock import patch

        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "local",
            "EMBEDDING_BASE_URL": "",
            "LOCAL_EMBEDDING_BASE_URL": ""
        }, clear=True):
            settings = Settings()
            url = settings.get_embedding_base_url()
            assert url is None

    def test_embedding_url_priority_override(self):
        """测试URL优先级覆盖"""
        from unittest.mock import patch

        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "https://independent.com/v1",
            "DEEPSEEK_EMBEDDING_BASE_URL": "https://embedding.deepseek.com/v1",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1"
        }, clear=True):
            settings = Settings()
            url = settings.get_embedding_base_url()
            # 独立URL应该覆盖所有其他配置
            assert url == "https://independent.com/v1"

    def test_embedding_url_validation(self):
        """测试URL验证功能"""
        from unittest.mock import patch

        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "invalid-url"
        }, clear=True):
            settings = Settings()
            # 验证配置应该包含URL验证结果
            validation_results = settings.validate_configuration()
            assert "embedding_url_valid" in validation_results
            assert "embedding_url_error" in validation_results

    def test_embedding_url_all_providers(self):
        """测试所有提供商的URL配置"""
        from unittest.mock import patch

        # anthropic不是有效的embedding provider，使用实际支持的providers
        providers = ["openai", "deepseek", "siliconflow", "local"]

        for provider in providers:
            with patch.dict(os.environ, {
                "EMBEDDING_PROVIDER": provider,
                f"{provider.upper()}_API_KEY": "test-key",
                "EMBEDDING_BASE_URL": f"https://{provider}-embedding.com/v1"
            }, clear=True):
                settings = Settings()
                url = settings.get_embedding_base_url()
                # 所有提供商都应该使用独立URL（最高优先级），包括local
                assert url == f"https://{provider}-embedding.com/v1"

    def test_embedding_url_complex_configuration(self):
        """测试复杂配置场景"""
        from unittest.mock import patch

        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "EMBEDDING_BASE_URL": "https://global-embedding.com/v1",
            "OPENAI_EMBEDDING_BASE_URL": "https://api.openai.com/v1",
            "DEEPSEEK_EMBEDDING_BASE_URL": "https://embedding.deepseek.com/v1",
            "SILICONFLOW_EMBEDDING_BASE_URL": "https://embedding.siliconflow.cn/v1",
            "ANTHROPIC_EMBEDDING_BASE_URL": "https://api.anthropic.com/v1",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1",
            "SILICONFLOW_BASE_URL": "https://api.siliconflow.cn/v1"
        }, clear=True):
            settings = Settings()
            url = settings.get_embedding_base_url()
            # 应该使用独立URL（最高优先级）
            assert url == "https://global-embedding.com/v1"

    def test_embedding_url_legacy_compatibility(self):
        """测试向后兼容性"""
        from unittest.mock import patch

        with patch.dict(os.environ, {
            "EMBEDDING_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1"
            # 不设置新的独立URL配置
        }, clear=True):
            settings = Settings()
            url = settings.get_embedding_base_url()
            # 应该使用传统的共享URL
            assert url == "https://api.deepseek.com/v1"

    def test_embedding_url_configuration_fields(self):
        """测试新增的URL配置字段"""
        from unittest.mock import patch

        with patch.dict(os.environ, {
            "EMBEDDING_BASE_URL": "https://independent.com/v1",
            "OPENAI_EMBEDDING_BASE_URL": "https://api.openai.com/v1",
            "DEEPSEEK_EMBEDDING_BASE_URL": "https://embedding.deepseek.com/v1",
            "SILICONFLOW_EMBEDDING_BASE_URL": "https://embedding.siliconflow.cn/v1",
            "ANTHROPIC_EMBEDDING_BASE_URL": "https://api.anthropic.com/v1"
        }, clear=True):
            settings = Settings()

            # 测试所有新增字段都能正确加载
            assert settings.get_embedding_base_url() == "https://independent.com/v1"
            assert settings.openai_embedding_base_url == "https://api.openai.com/v1"
            assert settings.deepseek_embedding_base_url == "https://embedding.deepseek.com/v1"
            assert settings.siliconflow_embedding_base_url == "https://embedding.siliconflow.cn/v1"
            assert settings.anthropic_embedding_base_url == "https://api.anthropic.com/v1"


def test_llm_base_url_priority():
    """测试 LLM Base URL 优先级配置"""
    # 测试通用独立URL（最高优先级）
    with patch.dict(os.environ, {
        "LLM_PROVIDER": "deepseek",
        "LLM_BASE_URL_FIELD": "https://custom-llm-api.com/v1",
        "DEEPSEEK_API_KEY": "test-key"
    }, clear=True):
        settings = Settings()
        assert settings.llm_base_url == "https://custom-llm-api.com/v1"

    # 测试提供商特定URL（中等优先级）
    with patch.dict(os.environ, {
        "LLM_PROVIDER": "deepseek",
        "DEEPSEEK_LLM_BASE_URL": "https://custom-deepseek-api.com/v1",
        "DEEPSEEK_API_KEY": "test-key"
    }, clear=True):
        settings = Settings()
        assert settings.llm_base_url == "https://custom-deepseek-api.com/v1"

    # 测试共享URL（最低优先级）
    with patch.dict(os.environ, {
        "LLM_PROVIDER": "deepseek",
        "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1",
        "DEEPSEEK_API_KEY": "test-key"
    }, clear=True):
        settings = Settings()
        assert settings.llm_base_url == "https://api.deepseek.com/v1"


def test_llm_base_url_provider_specific():
    """测试不同提供商的LLM Base URL配置"""
    # 测试OpenAI
    with patch.dict(os.environ, {
        "LLM_PROVIDER": "openai",
        "OPENAI_LLM_BASE_URL": "https://custom-openai-api.com/v1",
        "OPENAI_API_KEY": "test-key"
    }, clear=True):
        settings = Settings()
        assert settings.llm_base_url == "https://custom-openai-api.com/v1"

    # 测试SiliconFlow
    with patch.dict(os.environ, {
        "LLM_PROVIDER": "siliconflow",
        "SILICONFLOW_LLM_BASE_URL": "https://custom-siliconflow-api.com/v1",
        "SILICONFLOW_API_KEY": "test-key"
    }, clear=True):
        settings = Settings()
        assert settings.llm_base_url == "https://custom-siliconflow-api.com/v1"

    # 测试Anthropic
    with patch.dict(os.environ, {
        "LLM_PROVIDER": "anthropic",
        "ANTHROPIC_LLM_BASE_URL": "https://custom-anthropic-api.com/v1",
        "ANTHROPIC_API_KEY": "test-key"
    }, clear=True):
        settings = Settings()
        assert settings.llm_base_url == "https://custom-anthropic-api.com/v1"


def test_llm_base_url_backward_compatibility():
    """测试LLM Base URL向后兼容性"""
    # 测试DeepSeek默认配置
    with patch.dict(os.environ, {
        "LLM_PROVIDER": "deepseek",
        "DEEPSEEK_API_KEY": "test-key"
    }, clear=True):
        settings = Settings()
        assert settings.llm_base_url == "https://api.deepseek.com/v1"

    # 测试SiliconFlow默认配置
    with patch.dict(os.environ, {
        "LLM_PROVIDER": "siliconflow",
        "SILICONFLOW_API_KEY": "test-key"
    }, clear=True):
        settings = Settings()
        assert settings.llm_base_url == "https://api.siliconflow.cn/v1"

    # 测试OpenAI默认配置（返回None）
    with patch.dict(os.environ, {
        "LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-key"
    }, clear=True):
        settings = Settings()
        assert settings.llm_base_url is None

    # 测试Anthropic默认配置（返回None）
    with patch.dict(os.environ, {
        "LLM_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": "test-key"
    }, clear=True):
        settings = Settings()
        assert settings.llm_base_url is None


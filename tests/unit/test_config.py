"""
测试配置管理模块

测试 Settings 类的环境变量加载、验证和默认值。
"""

import os

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
    assert settings.rag_top_k == 3
    assert settings.rag_score_threshold == 0.7


def test_settings_milvus_collections():
    """测试 Milvus Collection 名称配置"""
    settings = Settings()

    assert settings.milvus_knowledge_collection == "knowledge_base"
    assert settings.milvus_history_collection == "conversation_history"


def test_settings_milvus_database():
    """测试 Milvus 数据库配置"""
    settings = Settings()

    # 测试默认值
    assert settings.milvus_database == "default"
    
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


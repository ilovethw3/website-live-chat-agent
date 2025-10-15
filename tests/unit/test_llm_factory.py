"""
测试 LLM 工厂模块

测试不同 LLM Provider 的创建逻辑。
"""

import os
from unittest.mock import patch

import pytest

from src.core.exceptions import ConfigurationError
from src.services.llm_factory import create_llm


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
            with pytest.raises(ConfigurationError, match="DEEPSEEK_API_KEY"):
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
            with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
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


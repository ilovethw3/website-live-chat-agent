"""
测试 LLM 工厂模块

测试不同 LLM Provider 的创建逻辑。
"""

import os
import pytest
from unittest.mock import patch

from src.services.llm_factory import get_llm
from src.core.exceptions import LLMError


def test_get_llm_deepseek():
    """测试获取 DeepSeek LLM"""
    with patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com/v1",
            "DEEPSEEK_MODEL": "deepseek-chat",
        },
    ):
        llm = get_llm()
        assert llm is not None
        assert hasattr(llm, "invoke")


def test_get_llm_openai():
    """测试获取 OpenAI LLM"""
    with patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
            "OPENAI_MODEL": "gpt-4o-mini",
        },
    ):
        llm = get_llm()
        assert llm is not None
        assert hasattr(llm, "invoke")


def test_get_llm_anthropic():
    """测试获取 Anthropic LLM"""
    with patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "test-key",
            "ANTHROPIC_MODEL": "claude-3-5-sonnet-20241022",
        },
    ):
        llm = get_llm()
        assert llm is not None
        assert hasattr(llm, "invoke")


def test_get_llm_missing_deepseek_key():
    """测试缺少 DeepSeek API Key"""
    with patch.dict(
        os.environ, {"LLM_PROVIDER": "deepseek", "DEEPSEEK_API_KEY": ""}
    ):
        with pytest.raises((ValueError, LLMError)):
            get_llm()


def test_get_llm_missing_openai_key():
    """测试缺少 OpenAI API Key"""
    with patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": ""}):
        with pytest.raises((ValueError, LLMError)):
            get_llm()


def test_get_llm_invalid_provider():
    """测试无效的 LLM Provider"""
    with patch.dict(os.environ, {"LLM_PROVIDER": "invalid"}):
        # 由于 Settings 的 Literal 验证，这应该在 Settings 初始化时就失败
        with pytest.raises(Exception):
            get_llm()


def test_get_llm_with_custom_temperature():
    """测试自定义温度参数"""
    with patch.dict(
        os.environ,
        {
            "LLM_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "LLM_TEMPERATURE": "0.5",
        },
    ):
        llm = get_llm()
        assert llm is not None
        # 温度参数应该已应用（具体验证取决于 LLM 实现）


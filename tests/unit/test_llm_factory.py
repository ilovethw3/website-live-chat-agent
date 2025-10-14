"""
测试 LLM 工厂模块

测试不同 LLM Provider 的创建逻辑。
"""

import os
import pytest
from unittest.mock import patch

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
    with patch.dict(
        os.environ, {"LLM_PROVIDER": "deepseek", "DEEPSEEK_API_KEY": ""}
    ):
        with pytest.raises((ValueError, Exception)):
            create_llm()


def test_create_llm_missing_openai_key():
    """测试缺少 OpenAI API Key"""
    with patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": ""}):
        with pytest.raises((ValueError, Exception)):
            create_llm()


def test_create_llm_invalid_provider():
    """测试无效的 LLM Provider"""
    with patch.dict(os.environ, {"LLM_PROVIDER": "invalid"}):
        # 由于 Settings 的 Literal 验证，这应该在 Settings 初始化时就失败
        with pytest.raises(Exception):
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


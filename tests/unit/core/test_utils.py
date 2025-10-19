"""
测试核心工具函数

测试文本处理、截断、分块等功能。
"""

import pytest

from src.core.utils import chunk_text_for_embedding, truncate_text_to_tokens


def test_truncate_text_to_tokens_short_text():
    """测试短文本不需要截断"""
    text = "这是一个短文本"
    result = truncate_text_to_tokens(text, max_tokens=512)
    assert result == text


def test_truncate_text_to_tokens_long_text():
    """测试长文本截断"""
    # 创建一个很长的文本
    long_text = "这是一个很长的文本。" * 200  # 约1400字符

    result = truncate_text_to_tokens(long_text, max_tokens=10)

    # 结果应该被截断
    assert len(result) < len(long_text)
    assert len(result) > 0


def test_truncate_text_to_tokens_exact_length():
    """测试文本长度刚好等于限制"""
    text = "测试文本"
    result = truncate_text_to_tokens(text, max_tokens=512)
    assert result == text


def test_chunk_text_for_embedding_short_text():
    """测试短文本不需要分块"""
    text = "这是一个短文本"
    chunks = chunk_text_for_embedding(text, max_tokens=512)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_for_embedding_long_text():
    """测试长文本分块"""
    # 创建一个很长的文本
    long_text = "这是一个很长的文本。" * 200  # 约1400字符

    chunks = chunk_text_for_embedding(long_text, max_tokens=10)

    # 应该被分成多个块
    assert len(chunks) > 1
    assert all(len(chunk) > 0 for chunk in chunks)

    # 验证所有块连接起来应该等于原文本（或接近）
    # 注意：由于tokenizer的边界，可能会有轻微差异
    total_length = sum(len(chunk) for chunk in chunks)
    assert total_length >= len(long_text) * 0.8  # 至少80%的文本被保留


def test_chunk_text_for_embedding_empty_text():
    """测试空文本"""
    chunks = chunk_text_for_embedding("", max_tokens=512)
    assert len(chunks) == 1
    assert chunks[0] == ""


def test_chunk_text_for_embedding_single_character():
    """测试单字符文本"""
    chunks = chunk_text_for_embedding("a", max_tokens=512)
    assert len(chunks) == 1
    assert chunks[0] == "a"


def test_truncate_text_to_tokens_fallback():
    """测试降级方案（tiktoken失败时）"""
    # 模拟tiktoken失败的情况
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("tiktoken.get_encoding", lambda x: None)

        long_text = "这是一个很长的文本。" * 100
        result = truncate_text_to_tokens(long_text, max_tokens=10)

        # 应该使用字符截断降级方案
        assert len(result) <= 20  # 10 tokens * 2 chars per token
        assert len(result) > 0


def test_chunk_text_for_embedding_fallback():
    """测试分块降级方案（tiktoken失败时）"""
    # 模拟tiktoken失败的情况
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("tiktoken.get_encoding", lambda x: None)

        long_text = "这是一个很长的文本。" * 100
        chunks = chunk_text_for_embedding(long_text, max_tokens=10)

        # 应该使用字符分块降级方案
        assert len(chunks) > 1
        assert all(len(chunk) <= 20 for chunk in chunks)  # 10 tokens * 2 chars per token




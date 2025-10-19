"""
工具函数单元测试
"""

from src.core.utils import chunk_text_for_embedding, generate_trace_id, truncate_text_to_tokens


class TestGenerateTraceId:
    """测试generate_trace_id函数"""

    def test_generate_trace_id_format(self):
        """测试trace_id格式"""
        trace_id = generate_trace_id()

        assert trace_id.startswith("trace-")
        assert len(trace_id) == 14  # "trace-" + 8位hex
        assert trace_id[6:].isalnum()  # 后面8位是字母数字

    def test_generate_trace_id_uniqueness(self):
        """测试trace_id唯一性"""
        trace_ids = [generate_trace_id() for _ in range(100)]

        # 应该生成100个不同的trace_id
        assert len(set(trace_ids)) == 100

    def test_generate_trace_id_consistency(self):
        """测试trace_id一致性"""
        # 多次调用应该生成不同的ID
        id1 = generate_trace_id()
        id2 = generate_trace_id()

        assert id1 != id2
        assert id1.startswith("trace-")
        assert id2.startswith("trace-")


class TestTruncateTextToTokens:
    """测试truncate_text_to_tokens函数"""

    def test_truncate_short_text(self):
        """测试短文本不截断"""
        text = "这是一个短文本"
        result = truncate_text_to_tokens(text, max_tokens=100)

        assert result == text

    def test_truncate_long_text(self):
        """测试长文本截断"""
        text = "这是一个很长的文本" * 100  # 创建长文本
        result = truncate_text_to_tokens(text, max_tokens=10)

        assert len(result) < len(text)
        assert result.startswith("这是一个很长的文本")

    def test_truncate_empty_text(self):
        """测试空文本"""
        result = truncate_text_to_tokens("", max_tokens=10)

        assert result == ""


class TestChunkTextForEmbedding:
    """测试chunk_text_for_embedding函数"""

    def test_chunk_short_text(self):
        """测试短文本不分块"""
        text = "短文本"
        chunks = chunk_text_for_embedding(text, max_tokens=100)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_long_text(self):
        """测试长文本分块"""
        text = "这是一个很长的文本" * 50  # 创建长文本
        chunks = chunk_text_for_embedding(text, max_tokens=10)

        assert len(chunks) > 1
        # 所有块都应该包含原文本内容
        combined = "".join(chunks)
        assert combined.startswith("这是一个很长的文本")

    def test_chunk_empty_text(self):
        """测试空文本分块"""
        chunks = chunk_text_for_embedding("", max_tokens=10)

        assert len(chunks) == 1
        assert chunks[0] == ""

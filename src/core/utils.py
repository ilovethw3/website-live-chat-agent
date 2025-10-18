"""
文本处理工具函数

提供文本截断、分块等功能，用于处理 embedding API 的 token 限制。
"""

import uuid
from typing import List

import tiktoken


def truncate_text_to_tokens(text: str, max_tokens: int = 512, model: str = "cl100k_base") -> str:
    """
    截断文本到指定token数

    Args:
        text: 输入文本
        max_tokens: 最大token数，默认512
        model: tokenizer模型，默认cl100k_base

    Returns:
        截断后的文本
    """
    try:
        encoding = tiktoken.get_encoding(model)
        tokens = encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return encoding.decode(tokens[:max_tokens])
    except Exception:
        # 降级方案：按字符截断（粗略估算 1 token ≈ 2-3 字符）
        max_chars = max_tokens * 2
        return text[:max_chars]


def chunk_text_for_embedding(text: str, max_tokens: int = 512) -> List[str]:
    """
    将长文本分块，每块不超过max_tokens

    Args:
        text: 输入文本
        max_tokens: 每块最大token数，默认512

    Returns:
        文本块列表
    """
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)

        if len(tokens) <= max_tokens:
            return [text]

        chunks = []
        for i in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunks.append(encoding.decode(chunk_tokens))

        return chunks
    except Exception:
        # 降级方案：按字符分块
        max_chars = max_tokens * 2
        return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]


def generate_trace_id() -> str:
    """
    生成唯一的追踪ID
    
    Returns:
        格式为 "trace-{uuid4}" 的追踪ID
    """
    return f"trace-{uuid.uuid4().hex[:8]}"

"""
Issue #37 修复测试

测试 finish_reason 字段的 content_filter 值验证。
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.models.openai_schema import ChatCompletionChoice, ChatMessage


class TestIssue37FinishReason:
    """Issue #37 finish_reason 字段测试"""

    def test_finish_reason_content_filter_validation(self):
        """测试 finish_reason 字段支持 content_filter 值"""
        # 测试 Pydantic 模型验证
        choice = ChatCompletionChoice(
            index=0,
            message=ChatMessage(role="assistant", content="测试消息"),
            finish_reason="content_filter"
        )

        # 应该成功创建，不抛出验证错误
        assert choice.finish_reason == "content_filter"
        assert choice.index == 0
        assert choice.message.role == "assistant"

    def test_finish_reason_all_valid_values(self):
        """测试所有有效的 finish_reason 值"""
        valid_values = ["stop", "length", "tool_calls", "content_filter"]

        for value in valid_values:
            choice = ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content="测试消息"),
                finish_reason=value
            )
            assert choice.finish_reason == value

    def test_finish_reason_none_value(self):
        """测试 finish_reason 为 None 的情况"""
        choice = ChatCompletionChoice(
            index=0,
            message=ChatMessage(role="assistant", content="测试消息"),
            finish_reason=None
        )
        assert choice.finish_reason is None

    def test_finish_reason_invalid_value(self):
        """测试无效的 finish_reason 值应该抛出验证错误"""
        with pytest.raises(Exception):  # 应该抛出 Pydantic 验证错误
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content="测试消息"),
                finish_reason="invalid_reason"
            )

    def test_api_content_filter_response(self):
        """测试API返回 content_filter finish_reason 不报错"""
        client = TestClient(app)

        # 模拟消息过滤场景，应该返回 content_filter
        with patch("src.api.v1.openai_compat._validate_message_source") as mock_validate:
            # 模拟消息被过滤
            mock_validate.return_value = False

            response = client.post(
                "/v1/chat/completions",
                headers={"Authorization": "Bearer test-api-key-12345"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "test"}],
                    "stream": False
                }
            )

            # 应该返回200状态码，不应该是500错误
            assert response.status_code == 200

            # 验证响应包含 content_filter
            response_data = response.json()
            assert response_data["choices"][0]["finish_reason"] == "content_filter"

    def test_api_stream_content_filter_response(self):
        """测试流式API返回 content_filter finish_reason 不报错"""
        client = TestClient(app)

        # 模拟消息过滤场景
        with patch("src.api.v1.openai_compat._validate_message_source") as mock_validate:
            # 模拟消息被过滤
            mock_validate.return_value = False

            response = client.post(
                "/v1/chat/completions",
                headers={"Authorization": "Bearer test-api-key-12345"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "test"}],
                    "stream": True
                }
            )

            # 应该返回200状态码，不应该是500错误
            assert response.status_code == 200

            # 验证响应内容包含 content_filter
            response_text = response.text
            assert "content_filter" in response_text

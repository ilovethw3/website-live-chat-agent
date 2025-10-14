"""
测试 OpenAI 兼容的 Chat Completions API

测试 /v1/chat/completions 端点的功能。
"""

from unittest.mock import patch


def test_chat_completions_unauthorized(test_client):
    """测试未授权访问"""
    response = test_client.post(
        "/v1/chat/completions",
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "test"}],
        },
    )

    assert response.status_code == 403


def test_chat_completions_invalid_api_key(test_client):
    """测试无效 API Key"""
    response = test_client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer wrong-key"},
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "test"}],
        },
    )

    assert response.status_code == 403


def test_chat_completions_simple(test_client, api_headers, mock_llm, mock_milvus_service):
    """测试简单对话"""
    with patch("src.services.llm_factory.create_llm", return_value=mock_llm):
        with patch("src.agent.tools.milvus_service", mock_milvus_service):
            response = test_client.post(
                "/v1/chat/completions",
                headers=api_headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "你好"}],
                    "stream": False,
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert "id" in data
            assert "object" in data
            assert data["object"] == "chat.completion"
            assert "choices" in data
            assert len(data["choices"]) > 0
            assert "message" in data["choices"][0]
            assert data["choices"][0]["message"]["role"] == "assistant"
            assert "content" in data["choices"][0]["message"]


def test_chat_completions_with_multiple_messages(
    test_client, api_headers, mock_llm, mock_milvus_service
):
    """测试多轮对话"""
    with patch("src.services.llm_factory.create_llm", return_value=mock_llm):
        with patch("src.agent.tools.milvus_service", mock_milvus_service):
            response = test_client.post(
                "/v1/chat/completions",
                headers=api_headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "user", "content": "你好"},
                        {"role": "assistant", "content": "你好！有什么可以帮你的吗？"},
                        {"role": "user", "content": "介绍一下你们的产品"},
                    ],
                    "stream": False,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["choices"][0]["message"]["role"] == "assistant"


def test_chat_completions_streaming(
    test_client, api_headers, mock_llm, mock_milvus_service
):
    """测试流式响应"""
    with patch("src.services.llm_factory.create_llm", return_value=mock_llm):
        with patch("src.agent.tools.milvus_service", mock_milvus_service):
            response = test_client.post(
                "/v1/chat/completions",
                headers=api_headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "你好"}],
                    "stream": True,
                },
            )

            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

            # 读取流式响应
            content = response.text
            assert "data:" in content or len(content) > 0


def test_chat_completions_missing_messages(test_client, api_headers):
    """测试缺少 messages 字段"""
    response = test_client.post(
        "/v1/chat/completions",
        headers=api_headers,
        json={
            "model": "deepseek-chat",
            # 缺少 messages
        },
    )

    assert response.status_code == 422  # Validation error


def test_chat_completions_empty_messages(test_client, api_headers):
    """测试空 messages 列表"""
    response = test_client.post(
        "/v1/chat/completions",
        headers=api_headers,
        json={
            "model": "deepseek-chat",
            "messages": [],
        },
    )

    assert response.status_code == 422  # Validation error


def test_chat_completions_with_temperature(
    test_client, api_headers, mock_llm, mock_milvus_service
):
    """测试自定义 temperature 参数"""
    with patch("src.services.llm_factory.create_llm", return_value=mock_llm):
        with patch("src.agent.tools.milvus_service", mock_milvus_service):
            response = test_client.post(
                "/v1/chat/completions",
                headers=api_headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "测试"}],
                    "temperature": 0.5,
                    "stream": False,
                },
            )

            assert response.status_code == 200


def test_chat_completions_with_max_tokens(
    test_client, api_headers, mock_llm, mock_milvus_service
):
    """测试 max_tokens 参数"""
    with patch("src.services.llm_factory.create_llm", return_value=mock_llm):
        with patch("src.agent.tools.milvus_service", mock_milvus_service):
            response = test_client.post(
                "/v1/chat/completions",
                headers=api_headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "测试"}],
                    "max_tokens": 100,
                    "stream": False,
                },
            )

            assert response.status_code == 200


def test_chat_completions_usage_info(
    test_client, api_headers, mock_llm, mock_milvus_service
):
    """测试返回的 token 使用信息"""
    with patch("src.services.llm_factory.create_llm", return_value=mock_llm):
        with patch("src.agent.tools.milvus_service", mock_milvus_service):
            response = test_client.post(
                "/v1/chat/completions",
                headers=api_headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "测试"}],
                    "stream": False,
                },
            )

            assert response.status_code == 200
            data = response.json()

            # 应该包含 usage 信息
            assert "usage" in data
            assert "prompt_tokens" in data["usage"]
            assert "completion_tokens" in data["usage"]
            assert "total_tokens" in data["usage"]


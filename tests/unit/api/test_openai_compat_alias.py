"""
单元测试: 模型别名功能

测试 /v1/models 和 /v1/chat/completions 端点在启用/禁用别名时的行为
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from src.core.config import settings
from src.main import app


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


class TestModelAlias:
    """模型别名功能测试"""

    def test_list_models_alias_disabled(self, client):
        """测试别名禁用时（默认），返回实际模型名"""
        with patch.object(settings, 'model_alias_enabled', False):
            response = client.get(
                "/v1/models",
                headers={"Authorization": f"Bearer {settings.api_key}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["object"] == "list"

            # 应该返回实际模型名
            model_ids = [m["id"] for m in data["data"]]
            assert settings.llm_model_name in model_ids

            # 检查 owned_by 字段
            chat_model = next(m for m in data["data"] if m["id"] == settings.llm_model_name)
            assert "provider:" in chat_model["owned_by"]

    def test_list_models_alias_enabled(self, client):
        """测试别名启用时，返回别名模型名"""
        with patch.object(settings, 'model_alias_enabled', True), \
             patch.object(settings, 'model_alias_name', 'gpt-4o-mini'), \
             patch.object(settings, 'model_alias_owned_by', 'openai'), \
             patch.object(settings, 'hide_embedding_models', True):

            response = client.get(
                "/v1/models",
                headers={"Authorization": f"Bearer {settings.api_key}"}
            )

            assert response.status_code == 200
            data = response.json()

            # 应该返回别名
            model_ids = [m["id"] for m in data["data"]]
            assert "gpt-4o-mini" in model_ids
            assert settings.llm_model_name not in model_ids  # 不应该有实际模型名

            # 检查 owned_by
            alias_model = next(m for m in data["data"] if m["id"] == "gpt-4o-mini")
            assert alias_model["owned_by"] == "openai"

    def test_list_models_hide_embeddings(self, client):
        """测试隐藏 embedding 模型"""
        with patch.object(settings, 'model_alias_enabled', True), \
             patch.object(settings, 'hide_embedding_models', True):

            response = client.get(
                "/v1/models",
                headers={"Authorization": f"Bearer {settings.api_key}"}
            )

            data = response.json()
            model_ids = [m["id"] for m in data["data"]]

            # 应该只有一个模型（聊天模型）
            assert len(model_ids) == 1

    def test_list_models_show_embeddings(self, client):
        """测试显示 embedding 模型"""
        with patch.object(settings, 'model_alias_enabled', True), \
             patch.object(settings, 'hide_embedding_models', False):

            response = client.get(
                "/v1/models",
                headers={"Authorization": f"Bearer {settings.api_key}"}
            )

            data = response.json()
            model_ids = [m["id"] for m in data["data"]]

            # 应该有两个模型（聊天模型 + embedding模型）
            assert len(model_ids) >= 2
            assert settings.model_alias_name in model_ids
            assert settings.embedding_model_name in model_ids

    def test_chat_completions_with_alias(self, client):
        """测试使用别名发起聊天请求"""
        with patch.object(settings, 'model_alias_enabled', True), \
             patch.object(settings, 'model_alias_name', 'gpt-4o-mini'):

            # 模拟 Agent 响应
            mock_agent = AsyncMock()
            mock_result = {
                "messages": [{"content": "Hello from DeepSeek!", "type": "ai"}]
            }
            mock_agent.ainvoke.return_value = mock_result

            with patch('src.api.v1.openai_compat.get_agent_app', return_value=mock_agent):
                response = client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.api_key}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": "Hello"}],
                        "stream": False
                    }
                )

                # 应该接受别名请求
                assert response.status_code == 200
                data = response.json()
                # 响应中应该返回请求的别名
                assert data["model"] == "gpt-4o-mini"

    def test_chat_completions_with_unexpected_model(self, client):
        """测试使用非预期模型名发起请求"""
        with patch.object(settings, 'model_alias_enabled', True), \
             patch.object(settings, 'model_alias_name', 'gpt-4o-mini'):

            # 模拟 Agent 响应
            mock_agent = AsyncMock()
            mock_result = {
                "messages": [{"content": "Hello from DeepSeek!", "type": "ai"}]
            }
            mock_agent.ainvoke.return_value = mock_result

            with patch('src.api.v1.openai_compat.get_agent_app', return_value=mock_agent):
                response = client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.api_key}"},
                    json={
                        "model": "gpt-3.5-turbo",  # 非预期的模型名
                        "messages": [{"role": "user", "content": "Hello"}],
                        "stream": False
                    }
                )

                # 应该仍然接受请求（但会记录警告）
                assert response.status_code == 200
                data = response.json()
                # 响应中应该返回请求的模型名
                assert data["model"] == "gpt-3.5-turbo"

    def test_chat_completions_alias_disabled(self, client):
        """测试别名禁用时的聊天请求"""
        with patch.object(settings, 'model_alias_enabled', False):
            # 模拟 Agent 响应
            mock_agent = AsyncMock()
            mock_result = {
                "messages": [{"content": "Hello from DeepSeek!", "type": "ai"}]
            }
            mock_agent.ainvoke.return_value = mock_result

            with patch('src.api.v1.openai_compat.get_agent_app', return_value=mock_agent):
                response = client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.api_key}"},
                    json={
                        "model": settings.llm_model_name,  # 使用实际模型名
                        "messages": [{"role": "user", "content": "Hello"}],
                        "stream": False
                    }
                )

                # 应该正常工作
                assert response.status_code == 200
                data = response.json()
                assert data["model"] == settings.llm_model_name

    def test_list_models_embedding_with_different_providers(self, client):
        """测试不同provider的embedding模型显示"""
        # 测试deepseek provider
        with patch.object(settings, 'model_alias_enabled', True), \
             patch.object(settings, 'hide_embedding_models', False), \
             patch.object(settings, 'embedding_provider', 'deepseek'), \
             patch.object(settings, 'embedding_model', 'deepseek-embedding'):

            response = client.get(
                "/v1/models",
                headers={"Authorization": f"Bearer {settings.api_key}"}
            )

            data = response.json()
            model_ids = [m["id"] for m in data["data"]]

            # 应该包含deepseek embedding模型
            assert settings.embedding_model in model_ids

    def test_list_models_hide_embedding_models(self, client):
        """测试隐藏embedding模型的情况"""
        with patch.object(settings, 'model_alias_enabled', True), \
             patch.object(settings, 'hide_embedding_models', True):

            response = client.get(
                "/v1/models",
                headers={"Authorization": f"Bearer {settings.api_key}"}
            )

            data = response.json()
            model_ids = [m["id"] for m in data["data"]]

            # 应该只有聊天模型，没有embedding模型
            assert len(model_ids) == 1
            assert settings.model_alias_name in model_ids
            assert settings.embedding_model_name not in model_ids

    def test_list_models_without_alias(self, client):
        """测试不使用别名的情况"""
        with patch.object(settings, 'model_alias_enabled', False), \
             patch.object(settings, 'hide_embedding_models', False):

            response = client.get(
                "/v1/models",
                headers={"Authorization": f"Bearer {settings.api_key}"}
            )

            data = response.json()
            model_ids = [m["id"] for m in data["data"]]

            # 应该显示实际模型名
            assert settings.llm_model_name in model_ids
            assert settings.embedding_model_name in model_ids

    def test_chat_completions_streaming_response(self, client):
        """测试流式响应"""
        with patch.object(settings, 'model_alias_enabled', True):
            # 模拟Agent响应
            mock_agent = AsyncMock()
            mock_agent.astream.return_value = [
                {"llm": {"messages": [AIMessage(content="流式测试回复")]}}
            ]

            with patch('src.agent.graph.get_agent_app', return_value=mock_agent):
                response = client.post(
                    "/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.model_alias_name,
                        "messages": [{"role": "user", "content": "测试流式响应"}],
                        "stream": True
                    }
                )

                # 流式响应应该返回200
                assert response.status_code == 200
                assert "text/event-stream" in response.headers.get("content-type", "")

    def test_chat_completions_error_handling(self, client):
        """测试错误处理"""
        with patch.object(settings, 'model_alias_enabled', True):
            # 模拟Agent抛出异常
            mock_agent = AsyncMock()
            mock_agent.ainvoke.side_effect = Exception("测试错误")

            with patch('src.agent.graph.get_agent_app', return_value=mock_agent):
                response = client.post(
                    "/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.model_alias_name,
                        "messages": [{"role": "user", "content": "测试错误处理"}],
                        "stream": False
                    }
                )

                # 应该返回错误响应
                assert response.status_code == 200
                data = response.json()
                assert "抱歉，系统遇到了一些问题" in data["choices"][0]["message"]["content"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

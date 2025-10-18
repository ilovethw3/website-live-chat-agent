"""
API层消息过滤测试

测试在API层进行的消息验证和过滤逻辑。
"""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.main import app


class TestAPIMessageFilter:
    """API层消息过滤测试"""

    def test_api_filters_instruction_templates(self):
        """测试API层过滤指令模板"""
        client = TestClient(app)

        # 模拟指令模板消息
        instruction_template = "You are an AI question rephraser. Your role is to rephrase follow-up queries from a conversation into standalone queries that can be used by another LLM to retrieve information through web search."

        with patch("src.api.v1.openai_compat.get_agent_app") as mock_get_app:
            # 模拟Agent应用
            mock_app = AsyncMock()
            mock_get_app.return_value = mock_app

            # 发送请求
            response = client.post(
                "/v1/chat/completions",
                headers={"Authorization": "Bearer test-api-key-12345"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": instruction_template}],
                    "stream": True
                }
            )

            # 应该返回错误响应，不进入Agent流程
            assert response.status_code == 200
            # 检查响应内容是否包含过滤信息
            content = response.text
            assert "无效内容" in content or "无法处理" in content

    def test_api_allows_valid_queries(self):
        """测试API层允许有效查询"""
        client = TestClient(app)

        # 模拟有效用户查询
        valid_query = "你们的产品有哪些功能？"

        with patch("src.api.v1.openai_compat.get_agent_app") as mock_get_app:
            # 模拟Agent应用
            mock_app = AsyncMock()
            mock_get_app.return_value = mock_app

            # 模拟Agent响应
            mock_app.astream.return_value = [
                {
                    "llm": {
                        "messages": [{"content": "根据我们的产品文档，我们提供以下功能..."}]
                    }
                }
            ]

            # 发送请求
            response = client.post(
                "/v1/chat/completions",
                headers={"Authorization": "Bearer test-api-key-12345"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": valid_query}],
                    "stream": True
                }
            )

            # 应该正常处理，进入Agent流程
            assert response.status_code == 200
            # 验证Agent被调用
            mock_app.astream.assert_called_once()

    def test_api_filters_long_messages(self):
        """测试API层过滤超长消息"""
        client = TestClient(app)

        # 模拟超长消息
        long_message = "这是一个很长的消息" * 200  # 超过1000字符限制

        with patch("src.api.v1.openai_compat.get_agent_app") as mock_get_app:
            # 模拟Agent应用
            mock_app = AsyncMock()
            mock_get_app.return_value = mock_app

            # 发送请求
            response = client.post(
                "/v1/chat/completions",
                headers={"Authorization": "Bearer test-api-key-12345"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": long_message}],
                    "stream": True
                }
            )

            # 应该返回错误响应
            assert response.status_code == 200
            content = response.text
            assert "无效内容" in content or "无法处理" in content

    def test_api_filters_technical_terms(self):
        """测试API层过滤技术术语过多的消息"""
        client = TestClient(app)

        # 模拟包含过多技术术语的消息
        technical_message = "API endpoint function method parameter response request database query"

        with patch("src.api.v1.openai_compat.get_agent_app") as mock_get_app:
            # 模拟Agent应用
            mock_app = AsyncMock()
            mock_get_app.return_value = mock_app

            # 发送请求
            response = client.post(
                "/v1/chat/completions",
                headers={"Authorization": "Bearer test-api-key-12345"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": technical_message}],
                    "stream": True
                }
            )

            # 应该返回错误响应
            assert response.status_code == 200
            content = response.text
            assert "无效内容" in content or "无法处理" in content

"""
Issue #38 修复测试

测试流式响应中llm_output类型错误修复。
"""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.main import app


class TestIssue38StreamingFix:
    """Issue #38 流式响应类型错误修复测试"""

    def test_streaming_llm_output_dict_type(self):
        """测试llm_output为字典类型时的正常处理"""
        client = TestClient(app)

        # 模拟正常的字典类型llm_output
        mock_chunk = {
            "llm": {
                "messages": [{"content": "测试响应", "role": "assistant"}]
            }
        }

        with patch("src.api.v1.openai_compat.get_agent_app") as mock_get_app:
            # 模拟Agent应用
            mock_app = AsyncMock()
            mock_get_app.return_value = mock_app

            # 模拟astream返回正常的字典类型chunk
            mock_app.astream.return_value = [mock_chunk]

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

    def test_streaming_llm_output_string_type(self):
        """测试llm_output为字符串类型时的处理"""
        client = TestClient(app)

        # 模拟字符串类型的llm_output（问题场景）
        mock_chunk = {
            "llm": "这是一个字符串响应"
        }

        with patch("src.api.v1.openai_compat.get_agent_app") as mock_get_app:
            # 模拟Agent应用
            mock_app = AsyncMock()
            mock_get_app.return_value = mock_app

            # 模拟astream返回字符串类型的chunk
            mock_app.astream.return_value = [mock_chunk]

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

    def test_streaming_llm_output_unexpected_type(self):
        """测试llm_output为意外类型时的处理"""
        client = TestClient(app)

        # 模拟意外类型的llm_output
        mock_chunk = {
            "llm": 12345  # 数字类型
        }

        with patch("src.api.v1.openai_compat.get_agent_app") as mock_get_app:
            # 模拟Agent应用
            mock_app = AsyncMock()
            mock_get_app.return_value = mock_app

            # 模拟astream返回意外类型的chunk
            mock_app.astream.return_value = [mock_chunk]

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

    def test_streaming_no_llm_chunk(self):
        """测试没有llm chunk时的处理"""
        client = TestClient(app)

        # 模拟没有llm字段的chunk
        mock_chunk = {
            "router": {"next_step": "retrieve"}
        }

        with patch("src.api.v1.openai_compat.get_agent_app") as mock_get_app:
            # 模拟Agent应用
            mock_app = AsyncMock()
            mock_get_app.return_value = mock_app

            # 模拟astream返回没有llm字段的chunk
            mock_app.astream.return_value = [mock_chunk]

            response = client.post(
                "/v1/chat/completions",
                headers={"Authorization": "Bearer test-api-key-12345"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "test"}],
                    "stream": True
                }
            )

            # 应该返回200状态码
            assert response.status_code == 200

    def test_streaming_empty_messages(self):
        """测试llm_output中messages为空时的处理"""
        client = TestClient(app)

        # 模拟messages为空的llm_output
        mock_chunk = {
            "llm": {
                "messages": []
            }
        }

        with patch("src.api.v1.openai_compat.get_agent_app") as mock_get_app:
            # 模拟Agent应用
            mock_app = AsyncMock()
            mock_get_app.return_value = mock_app

            # 模拟astream返回空messages的chunk
            mock_app.astream.return_value = [mock_chunk]

            response = client.post(
                "/v1/chat/completions",
                headers={"Authorization": "Bearer test-api-key-12345"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "test"}],
                    "stream": True
                }
            )

            # 应该返回200状态码
            assert response.status_code == 200

    def test_streaming_multiple_chunks(self):
        """测试多个chunk的处理"""
        client = TestClient(app)

        # 模拟多个chunk
        mock_chunks = [
            {"router": {"next_step": "retrieve"}},
            {"retrieve": {"retrieved_docs": ["doc1", "doc2"]}},
            {
                "llm": {
                    "messages": [{"content": "基于检索的响应", "role": "assistant"}]
                }
            }
        ]

        with patch("src.api.v1.openai_compat.get_agent_app") as mock_get_app:
            # 模拟Agent应用
            mock_app = AsyncMock()
            mock_get_app.return_value = mock_app

            # 模拟astream返回多个chunk
            mock_app.astream.return_value = mock_chunks

            response = client.post(
                "/v1/chat/completions",
                headers={"Authorization": "Bearer test-api-key-12345"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "test"}],
                    "stream": True
                }
            )

            # 应该返回200状态码
            assert response.status_code == 200

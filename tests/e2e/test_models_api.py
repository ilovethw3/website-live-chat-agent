"""
测试 OpenAI 兼容的模型列表 API

测试 /v1/models 端点行为。
"""

from typing import Any


def test_models_unauthorized(test_client):
    """测试未授权访问 /v1/models"""
    response = test_client.get("/v1/models")

    # 需认证
    assert response.status_code == 403


def test_models_success(test_client, api_headers):
    """测试成功返回模型列表"""
    response = test_client.get("/v1/models", headers=api_headers)

    assert response.status_code == 200
    data: dict[str, Any] = response.json()

    assert data.get("object") == "list"
    assert isinstance(data.get("data"), list)
    # 至少包含一个模型（chat 模型）
    assert len(data["data"]) >= 1
    # 校验字段结构
    first = data["data"][0]
    assert set(["id", "object", "created", "owned_by"]).issubset(first.keys())


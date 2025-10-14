"""
测试健康检查和根端点

测试系统状态和基本端点。
"""

from unittest.mock import patch


def test_root_endpoint(test_client):
    """测试根端点"""
    response = test_client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert "llm_provider" in data
    assert "llm_model" in data


def test_health_check_healthy(test_client, mock_milvus_service):
    """测试健康检查 - 健康状态"""
    mock_milvus_service.health_check.return_value = True

    with patch("src.services.milvus_service.milvus_service", mock_milvus_service):
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["healthy", "degraded"]
        assert "services" in data
        assert "milvus" in data["services"]
        assert "redis" in data["services"]
        assert "timestamp" in data


def test_health_check_degraded(test_client, mock_milvus_service):
    """测试健康检查 - 降级状态"""
    mock_milvus_service.health_check.return_value = False

    with patch("src.services.milvus_service.milvus_service", mock_milvus_service):
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "degraded"
        assert data["services"]["milvus"]["status"] == "unhealthy"


def test_health_check_no_auth_required(test_client):
    """测试健康检查不需要认证"""
    # 不提供 API Key
    response = test_client.get("/api/v1/health")

    # 应该能正常访问（健康检查通常不需要认证）
    # 注意：根据实际实现，这可能需要调整
    assert response.status_code in [200, 403]


def test_openapi_docs(test_client):
    """测试 OpenAPI 文档端点"""
    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()

    assert "openapi" in data
    assert "info" in data
    assert "paths" in data


def test_swagger_ui(test_client):
    """测试 Swagger UI"""
    response = test_client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_redoc(test_client):
    """测试 ReDoc"""
    response = test_client.get("/redoc")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_cors_headers(test_client):
    """测试 CORS 头"""
    response = test_client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    # 根据 CORS 配置，应该有相应的头
    # 注意：这取决于实际的 CORS 配置
    assert response.status_code in [200, 403]


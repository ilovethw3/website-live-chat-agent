"""
测试知识库管理 API

测试 /api/v1/knowledge 相关端点。
"""

from unittest.mock import patch


def test_knowledge_upsert_unauthorized(test_client):
    """测试未授权访问知识库上传"""
    response = test_client.post(
        "/api/v1/knowledge/upsert",
        json={
            "documents": [{"text": "测试文档", "metadata": {}}],
        },
    )

    assert response.status_code == 403


def test_knowledge_upsert_success(
    test_client, api_headers, mock_milvus_service, mock_embeddings
):
    """测试成功上传文档"""
    mock_milvus_service.insert_documents.return_value = {
        "success": True,
        "inserted_count": 2,
    }

    with patch("src.api.v1.knowledge.milvus_service", mock_milvus_service):
        with patch("src.services.llm_factory.create_embeddings", return_value=mock_embeddings):
            response = test_client.post(
                "/api/v1/knowledge/upsert",
                headers=api_headers,
                json={
                    "documents": [
                        {
                            "text": "我们的退货政策是30天内无条件退货",
                            "metadata": {"source": "policy.md", "category": "policy"},
                        },
                        {
                            "text": "我们的保修期为1年",
                            "metadata": {"source": "warranty.md", "category": "warranty"},
                        },
                    ],
                    "collection_name": "knowledge_base",
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["inserted_count"] == 2
            assert "message" in data


def test_knowledge_upsert_empty_documents(test_client, api_headers):
    """测试上传空文档列表"""
    response = test_client.post(
        "/api/v1/knowledge/upsert",
        headers=api_headers,
        json={
            "documents": [],
            "collection_name": "knowledge_base",
        },
    )

    # 应该返回成功但 inserted_count 为 0
    assert response.status_code == 200
    data = response.json()
    assert data["inserted_count"] == 0


def test_knowledge_upsert_missing_text(test_client, api_headers):
    """测试缺少 text 字段"""
    response = test_client.post(
        "/api/v1/knowledge/upsert",
        headers=api_headers,
        json={
            "documents": [
                {"metadata": {"source": "test.md"}},  # 缺少 text
            ],
        },
    )

    assert response.status_code == 422  # Validation error


def test_knowledge_search_unauthorized(test_client):
    """测试未授权访问知识库检索"""
    response = test_client.get("/api/v1/knowledge/search?query=测试")

    assert response.status_code == 403


def test_knowledge_search_success(
    test_client, api_headers, mock_milvus_service, mock_embeddings
):
    """测试成功检索文档"""
    mock_milvus_service.search_knowledge.return_value = [
        {
            "id": "1",
            "text": "退货政策文档",
            "score": 0.95,
            "metadata": {"source": "policy.md"},
        },
        {
            "id": "2",
            "text": "保修政策文档",
            "score": 0.88,
            "metadata": {"source": "warranty.md"},
        },
    ]

    with patch("src.api.v1.knowledge.milvus_service", mock_milvus_service):
        with patch("src.services.llm_factory.create_embeddings", return_value=mock_embeddings):
            response = test_client.get(
                "/api/v1/knowledge/search",
                headers=api_headers,
                params={"query": "退货政策", "top_k": 3},
            )

            assert response.status_code == 200
            data = response.json()

            assert "results" in data
            assert isinstance(data["results"], list)
            assert len(data["results"]) == 2
            assert data["results"][0]["score"] >= data["results"][1]["score"]


def test_knowledge_search_empty_query(test_client, api_headers):
    """测试空查询"""
    response = test_client.get(
        "/api/v1/knowledge/search",
        headers=api_headers,
        params={"query": ""},
    )

    # 应该返回验证错误或空结果
    assert response.status_code in [200, 422]


def test_knowledge_search_with_top_k(
    test_client, api_headers, mock_milvus_service, mock_embeddings
):
    """测试自定义 top_k 参数"""
    mock_milvus_service.search_knowledge.return_value = [
        {"id": str(i), "text": f"文档{i}", "score": 0.9 - i * 0.1, "metadata": {}}
        for i in range(5)
    ]

    with patch("src.api.v1.knowledge.milvus_service", mock_milvus_service):
        with patch("src.services.llm_factory.create_embeddings", return_value=mock_embeddings):
            response = test_client.get(
                "/api/v1/knowledge/search",
                headers=api_headers,
                params={"query": "测试", "top_k": 5},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) <= 5


def test_knowledge_search_no_results(
    test_client, api_headers, mock_milvus_service, mock_embeddings
):
    """测试无结果的检索"""
    mock_milvus_service.search_knowledge.return_value = []

    with patch("src.api.v1.knowledge.milvus_service", mock_milvus_service):
        with patch("src.services.llm_factory.create_embeddings", return_value=mock_embeddings):
            response = test_client.get(
                "/api/v1/knowledge/search",
                headers=api_headers,
                params={"query": "不存在的内容"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["results"] == []


def test_knowledge_upsert_with_chunks(
    test_client, api_headers, mock_milvus_service, mock_embeddings
):
    """测试自动分块的长文档上传"""
    long_text = "这是一个很长的文档。" * 200  # 模拟长文档

    mock_milvus_service.insert_documents.return_value = {
        "success": True,
        "inserted_count": 3,  # 假设分成了 3 个块
    }

    with patch("src.api.v1.knowledge.milvus_service", mock_milvus_service):
        with patch("src.services.llm_factory.create_embeddings", return_value=mock_embeddings):
            response = test_client.post(
                "/api/v1/knowledge/upsert",
                headers=api_headers,
                json={
                    "documents": [
                        {
                            "text": long_text,
                            "metadata": {"source": "long_doc.md"},
                        }
                    ],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


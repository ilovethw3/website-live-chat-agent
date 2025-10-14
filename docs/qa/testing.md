# 测试指南

本文档描述项目的测试策略、测试用例和如何运行测试。

## 📊 测试架构

项目采用三层测试金字塔结构：

```
        /\
       /E2E\       ← 端到端测试（少量，测试完整流程）
      /------\
     /  集成  \    ← 集成测试（中等数量，测试组件协作）
    /----------\
   /   单元测试  \  ← 单元测试（大量，测试独立功能）
  /--------------\
```

### 测试目录结构

```
tests/
├── conftest.py              # 全局 fixtures 和配置
├── unit/                    # 单元测试
│   ├── test_config.py       # 配置管理测试
│   ├── test_security.py     # API 认证测试
│   ├── test_llm_factory.py  # LLM 工厂测试
│   ├── test_milvus_service.py # Milvus 服务测试
│   ├── test_agent_state.py  # Agent 状态测试
│   ├── test_agent_nodes.py  # Agent 节点测试
│   └── test_agent_edges.py  # Agent 边逻辑测试
├── integration/             # 集成测试
│   └── test_agent_graph.py  # LangGraph 完整流程测试
└── e2e/                     # 端到端测试
    ├── test_chat_completions.py  # Chat API 测试
    ├── test_knowledge_api.py     # 知识库 API 测试
    └── test_health.py            # 健康检查测试
```

## 🚀 快速开始

### 安装测试依赖

```bash
# 安装所有开发依赖
pip install -e ".[dev]"

# 或使用 uv（更快）
uv pip install -e ".[dev]"
```

### 运行所有测试

```bash
# 方法 1: 使用 pytest 直接运行
pytest

# 方法 2: 使用测试脚本
./scripts/run_tests.sh all

# 方法 3: 使用 make（如果有 Makefile）
make test
```

### 运行特定类型的测试

```bash
# 只运行单元测试
pytest tests/unit/
# 或
./scripts/run_tests.sh unit

# 只运行集成测试
pytest tests/integration/
# 或
./scripts/run_tests.sh integration

# 只运行 E2E 测试
pytest tests/e2e/
# 或
./scripts/run_tests.sh e2e
```

### 运行特定测试文件

```bash
# 运行单个测试文件
pytest tests/unit/test_config.py

# 运行单个测试函数
pytest tests/unit/test_config.py::test_settings_load_from_env

# 运行包含特定关键字的测试
pytest -k "milvus"
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=html --cov-report=term-missing

# 或使用脚本
./scripts/run_tests.sh coverage

# 查看 HTML 报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 📝 测试用例详解

### 1️⃣ 单元测试

#### 配置管理测试 (`test_config.py`)

测试环境变量加载、验证和默认值：

```python
def test_settings_load_from_env():
    """测试从环境变量加载配置"""
    settings = Settings()
    assert settings.llm_provider == "deepseek"
    assert settings.api_key is not None
```

**覆盖场景**：
- ✅ 环境变量加载
- ✅ 默认值设置
- ✅ 必填字段验证
- ✅ 枚举类型验证

#### API 认证测试 (`test_security.py`)

测试 API Key 验证逻辑：

```python
def test_api_key_auth_invalid():
    """测试无效的 API Key"""
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="wrong-key"
    )
    with pytest.raises(HTTPException):
        api_key_auth(credentials)
```

**覆盖场景**：
- ✅ 有效 API Key
- ✅ 无效 API Key
- ✅ 空 API Key
- ✅ 大小写敏感

#### LLM 工厂测试 (`test_llm_factory.py`)

测试不同 LLM Provider 的创建：

```python
def test_get_llm_deepseek():
    """测试获取 DeepSeek LLM"""
    with patch.dict(os.environ, {"LLM_PROVIDER": "deepseek"}):
        llm = get_llm()
        assert llm is not None
```

**覆盖场景**：
- ✅ DeepSeek LLM
- ✅ OpenAI LLM
- ✅ Anthropic LLM
- ✅ 缺少 API Key 错误处理

#### Milvus 服务测试 (`test_milvus_service.py`)

测试向量数据库操作：

```python
@pytest.mark.asyncio
async def test_milvus_search_success():
    """测试向量检索成功"""
    service = MilvusService()
    results = await service.search_knowledge(query="测试", top_k=3)
    assert isinstance(results, list)
```

**覆盖场景**：
- ✅ Milvus 初始化
- ✅ 向量检索
- ✅ 文档插入
- ✅ 健康检查
- ✅ 相似度过滤

#### Agent 测试 (`test_agent_*.py`)

测试 LangGraph Agent 的各个组件：

```python
@pytest.mark.asyncio
async def test_call_llm_simple(mock_llm):
    """测试 LLM 调用节点"""
    state = {"messages": [HumanMessage(content="你好")]}
    result = await call_llm(state)
    assert "messages" in result
```

**覆盖场景**：
- ✅ Agent 状态结构
- ✅ LLM 调用节点
- ✅ 知识检索节点
- ✅ 工具调用节点
- ✅ 路由逻辑

### 2️⃣ 集成测试

#### LangGraph 完整流程 (`test_agent_graph.py`)

测试 Agent 的端到端执行：

```python
@pytest.mark.asyncio
async def test_agent_graph_simple_chat():
    """测试简单对话流程"""
    app = get_agent_app()
    result = await app.ainvoke(initial_state, config=config)
    assert len(result["messages"]) > 1
```

**覆盖场景**：
- ✅ 简单对话
- ✅ RAG 检索增强
- ✅ 多轮对话
- ✅ 错误处理
- ✅ 状态持久化

### 3️⃣ E2E 测试

#### Chat Completions API (`test_chat_completions.py`)

测试 OpenAI 兼容 API：

```python
def test_chat_completions_simple(test_client, api_headers):
    """测试简单对话"""
    response = test_client.post(
        "/v1/chat/completions",
        headers=api_headers,
        json={"model": "deepseek-chat", "messages": [...]},
    )
    assert response.status_code == 200
```

**覆盖场景**：
- ✅ API 认证
- ✅ 简单对话
- ✅ 多轮对话
- ✅ 流式响应
- ✅ 参数验证
- ✅ Token 使用统计

#### 知识库 API (`test_knowledge_api.py`)

测试知识库管理：

```python
def test_knowledge_upsert_success(test_client, api_headers):
    """测试成功上传文档"""
    response = test_client.post(
        "/api/v1/knowledge/upsert",
        headers=api_headers,
        json={"documents": [...]},
    )
    assert response.status_code == 200
```

**覆盖场景**：
- ✅ 文档上传
- ✅ 知识检索
- ✅ 自动分块
- ✅ 空查询处理

## 🛠️ Mock 和 Fixtures

### 全局 Fixtures (`conftest.py`)

```python
@pytest.fixture
def test_client():
    """FastAPI 测试客户端"""
    return TestClient(app)

@pytest.fixture
def mock_llm():
    """Mock LLM"""
    mock = MagicMock()
    mock.invoke.return_value = AIMessage(content="测试响应")
    return mock

@pytest.fixture
def mock_milvus_service():
    """Mock Milvus 服务"""
    mock = AsyncMock()
    mock.search_knowledge.return_value = []
    return mock
```

### 使用 Fixtures

```python
def test_example(test_client, api_headers, mock_llm):
    """使用多个 fixtures"""
    with patch("src.agent.nodes.get_llm", return_value=mock_llm):
        response = test_client.post("/v1/chat/completions", headers=api_headers, ...)
        assert response.status_code == 200
```

## 📊 测试覆盖率目标

| 模块 | 目标覆盖率 | 当前覆盖率 |
|------|-----------|-----------|
| `src/core/*` | 90%+ | - |
| `src/services/*` | 85%+ | - |
| `src/agent/*` | 80%+ | - |
| `src/api/*` | 90%+ | - |
| `src/models/*` | 95%+ | - |
| **总体** | **85%+** | - |

## 🔧 持续集成

### GitHub Actions

项目使用 GitHub Actions 自动运行测试：

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: pip install -e ".[dev]"
      - run: pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## 💡 最佳实践

### 1. 测试命名

```python
# ✅ 好的命名
def test_api_key_auth_valid():
    """测试有效的 API Key"""
    
def test_milvus_search_empty_query():
    """测试空查询"""

# ❌ 不好的命名
def test_1():
    """测试"""
    
def test_something():
    """测试某些东西"""
```

### 2. 测试隔离

```python
# ✅ 每个测试独立
@pytest.fixture(autouse=True)
def cleanup():
    """每次测试后清理"""
    yield
    # 清理操作

# ❌ 测试之间有依赖
def test_first():
    global shared_state
    shared_state = "value"

def test_second():
    assert shared_state == "value"  # 依赖 test_first
```

### 3. 使用 Mock

```python
# ✅ Mock 外部依赖
def test_with_mock(mock_milvus_service):
    with patch("src.api.v1.knowledge.milvus_service", mock_milvus_service):
        # 测试代码
        
# ❌ 依赖真实服务
def test_with_real_milvus():
    # 需要真实的 Milvus 服务运行
    result = real_milvus_service.search(...)
```

### 4. 异步测试

```python
# ✅ 使用 pytest.mark.asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None

# ❌ 忘记 async 标记
async def test_async_without_mark():  # 不会运行
    result = await some_async_function()
```

## 🐛 调试测试

### 详细输出

```bash
# 显示详细信息
pytest -v

# 显示打印输出
pytest -s

# 失败时显示局部变量
pytest --showlocals

# 失败时进入 pdb
pytest --pdb
```

### 只运行失败的测试

```bash
# 第一次运行
pytest

# 只重跑失败的测试
pytest --lf

# 先运行失败的，再运行其他
pytest --ff
```

## 📚 参考资源

- [pytest 文档](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)


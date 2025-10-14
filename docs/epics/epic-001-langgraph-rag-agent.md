# Epic-001: LangGraph RAG 客服 Agent

**创建时间**: 2025-10-13 19:52:27 +08:00  
**负责角色**: PM (Product Manager AI)  
**状态**: 已批准  
**优先级**: P0 (最高)

---

## 业务背景

### 问题陈述

当前 WordPress 网站的客服系统依赖人工或简单的 FAQ 自动回复，存在以下问题：

1. **响应延迟高**：人工客服需要时间查找信息，无法 24/7 在线
2. **准确率不稳定**：简单的关键词匹配无法理解复杂问题
3. **知识库利用率低**：网站的 FAQ、产品文档等内容未被充分利用
4. **扩展性差**：每次更新需要手动维护对话脚本

### 解决方案

开发一个基于 LangGraph 和 RAG 技术的智能客服 Agent：

- 从 Milvus 向量数据库检索网站知识库（FAQ、产品信息、政策文档）
- 使用 LangGraph 实现可控的对话流程（路由、检索、生成）
- 提供 OpenAI 兼容的 API 接口，WordPress 插件只需修改 URL 即可接入
- 支持多轮对话记忆和上下文理解

### 目标用户

1. **WordPress 网站管理员**：希望快速部署AI客服，无需修改插件代码
2. **网站访客**：希望获得准确、及时的问题解答
3. **系统管理员**：需要管理知识库内容和监控系统运行

---

## 核心功能需求

### 用户故事 1: WordPress 插件快速接入

**作为** WordPress 网站管理员  
**我希望** 通过修改 API URL，让现有聊天插件调用我的 RAG Agent  
**以便于** 无需开发成本即可升级为 AI 客服系统

**验收标准**:

1. WordPress 插件配置页仅需填入两个字段：
   - API Base URL: `http://your-server:8000/v1`
   - API Key: `your-secure-api-key`
2. 保存配置后，插件能正常发送请求并显示响应
3. 响应格式完全兼容 OpenAI Chat Completion API
4. 支持流式响应（打字机效果）

**场景示例**:

```
前提条件：
- WordPress 网站已安装 "AI Chatbot for WordPress" 插件
- 插件版本 >= 3.0（支持自定义 API Endpoint）

操作步骤：
1. 进入 WordPress 后台 → 插件设置 → AI Chatbot 配置
2. 找到 "API Configuration" 部分
3. 将 "API Provider" 选择为 "Custom OpenAI Compatible"
4. 填入 "Base URL": http://192.168.1.100:8000/v1
5. 填入 "API Key": sk-agent-12345abcde
6. 点击 "Test Connection" 按钮
7. 显示 "✅ Connection Successful"
8. 保存配置

预期结果：
- 前端聊天窗口能正常显示
- 用户提问后，Agent 能返回基于知识库的答案
```

---

### 用户故事 2: 准确回答网站特定问题

**作为** 网站访客  
**我希望** 客服能准确回答网站特定问题（产品、FAQ、政策等）  
**以便于** 快速获取我需要的信息，无需人工等待

**验收标准**:

1. **知识库覆盖率**：
   - 产品信息准确率 > 90%
   - FAQ 准确率 > 85%
   - 政策文档准确率 > 85%

2. **响应质量**:
   - 答案来自网站知识库（而非LLM幻觉）
   - 明确引用来源（如："根据我们的退货政策..."）
   - 不确定时诚实告知（如："抱歉，我在知识库中未找到相关信息"）

3. **多轮对话能力**:
   - 理解上下文（如："那价格呢？"能关联到之前讨论的产品）
   - 记忆会话历史（最近 10 轮对话）

**场景示例**:

```
用户：你们的退货政策是什么？
Agent：根据我们的退货政策，您可以在收到商品后 30 天内申请退货。退货条件包括：
       1. 商品未使用且包装完好
       2. 保留原始发票
       3. 非定制商品
       详细信息请参考：https://example.com/return-policy

用户：那运费谁承担？
Agent：（理解上下文，关联到退货政策）
       退货运费承担规则如下：
       - 商品质量问题：我们承担往返运费
       - 非质量问题：您需承担退货运费
       
用户：iPhone 15 多少钱？
Agent：根据我们的产品目录，iPhone 15 的价格如下：
       - iPhone 15 128GB: ¥5,999
       - iPhone 15 256GB: ¥6,999
       - iPhone 15 512GB: ¥8,499
       详细信息请访问：https://example.com/products/iphone-15
```

---

### 用户故事 3: 轻松管理知识库

**作为** 系统管理员  
**我希望** 能轻松上传网站内容到知识库  
**以便于** Agent 能回答最新的产品和政策信息

**验收标准**:

1. **上传接口**:
   - 提供 REST API 端点: `POST /api/v1/knowledge/upsert`
   - 支持批量上传（单次最多 100 个文档）
   - 支持多种格式（纯文本、Markdown、HTML）

2. **自动化处理**:
   - 自动文档切片（Chunk Size: 500 tokens，Overlap: 50 tokens）
   - 自动生成 Embedding（使用 DeepSeek Embedding 或 OpenAI）
   - 自动存入 Milvus 知识库

3. **验证功能**:
   - 提供测试检索端点: `GET /api/v1/knowledge/search?query=退货政策`
   - 返回 Top-K 相关文档及分数

**场景示例**:

```bash
# 上传 FAQ 文档
curl -X POST http://localhost:8000/api/v1/knowledge/upsert \
  -H "Authorization: Bearer sk-agent-12345abcde" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "text": "我们的退货政策：收到商品后30天内可申请退货...",
        "metadata": {
          "title": "退货政策",
          "url": "https://example.com/return-policy",
          "category": "政策"
        }
      },
      {
        "text": "iPhone 15 128GB 售价 ¥5,999，256GB 售价 ¥6,999...",
        "metadata": {
          "title": "iPhone 15 产品信息",
          "url": "https://example.com/products/iphone-15",
          "category": "产品"
        }
      }
    ],
    "collection_name": "knowledge_base",
    "chunk_size": 500,
    "chunk_overlap": 50
  }'

# 响应
{
  "success": true,
  "inserted_count": 2,
  "collection_name": "knowledge_base",
  "message": "成功上传 2 个文档，共生成 5 个向量切片"
}

# 测试检索
curl -X GET "http://localhost:8000/api/v1/knowledge/search?query=退货政策&top_k=3" \
  -H "Authorization: Bearer sk-agent-12345abcde"

# 响应
{
  "results": [
    {
      "text": "我们的退货政策：收到商品后30天内可申请退货...",
      "score": 0.92,
      "metadata": {
        "title": "退货政策",
        "url": "https://example.com/return-policy"
      }
    }
  ],
  "query": "退货政策",
  "total_results": 1
}
```

---

## 非功能性需求

### 性能要求

| 指标 | 目标值 | 测量方法 |
|------|-------|---------|
| 响应时间（P95） | < 3秒 | 从接收请求到返回首个Token |
| 响应时间（P50） | < 2秒 | 中位数响应时间 |
| 并发支持 | 100 QPS | 单实例并发请求数 |
| 知识库检索延迟 | < 500ms | Milvus 检索时间 |

### 可用性要求

- **Uptime**: 99.9%（允许每月停机 43 分钟）
- **健康检查**: 提供 `/api/v1/health` 端点，检查 Milvus/Redis 连接状态
- **优雅降级**: Milvus 不可用时，直接调用 LLM（不使用知识库）

### 安全要求

- **认证**: 所有 API 需要 API Key 验证（Header: `Authorization: Bearer {key}`）
- **CORS**: 支持配置允许的域名白名单
- **数据隐私**: 对话数据仅保留 7 天（Redis 自动过期）
- **敏感信息**: 日志中不得记录 API Key、用户输入的敏感信息

### 兼容性要求

- **API 格式**: 100% 兼容 OpenAI Chat Completion API
- **WordPress 插件**: 支持主流 AI 聊天插件：
  - AI Chatbot for WordPress
  - WP AI Assistant
  - ChatGPT Plugin
- **LLM 支持**: DeepSeek（默认）、OpenAI、Claude、本地模型

---

## 验收测试场景

### 场景 1: WordPress 插件配置流程

**前置条件**:
- WordPress 5.9+ 已安装
- AI Chatbot 插件已激活
- Agent 服务已启动

**测试步骤**:
1. 进入插件配置页
2. 选择 "Custom OpenAI Compatible"
3. 填入 Base URL 和 API Key
4. 点击 "Test Connection"
5. 保存配置
6. 前端打开聊天窗口
7. 输入测试问题："你好"

**预期结果**:
- ✅ Test Connection 显示成功
- ✅ 聊天窗口正常加载
- ✅ Agent 回复："您好！我是客服助手，有什么可以帮您？"

---

### 场景 2: 知识库检索验证

**前置条件**:
- 知识库已上传退货政策文档
- Agent 服务正常运行

**测试步骤**:
1. 用户提问："你们的退货期限是多少天？"
2. 观察 Agent 响应

**预期结果**:
- ✅ 响应包含 "30天"
- ✅ 响应提及来源（如："根据我们的退货政策"）
- ✅ 响应时间 < 3秒

---

### 场景 3: 多轮对话上下文理解

**前置条件**:
- 会话已建立

**测试步骤**:
1. 用户："iPhone 15 有哪些颜色？"
2. Agent 回复颜色列表
3. 用户："那价格呢？"

**预期结果**:
- ✅ Agent 理解 "那价格" 指的是 iPhone 15 的价格
- ✅ 回复包含 iPhone 15 各版本价格
- ✅ 不需要用户重复提到 "iPhone 15"

---

## 成功指标 (KPI)

| 指标 | 目标值 | 测量周期 |
|------|-------|---------|
| 知识库准确率 | > 85% | 每周评估 100 个样本 |
| 用户满意度 | > 4.0/5.0 | 每次对话后用户评分 |
| 平均响应时间 | < 2.5秒 | 实时监控（P50） |
| 系统可用性 | > 99.9% | 每月统计 |
| API 兼容性 | 100% | WordPress 主流插件测试 |

---

## 里程碑计划

| 里程碑 | 完成日期 | 交付物 |
|--------|---------|--------|
| M1: 基础架构搭建 | Week 1 | 文档结构、ADR、OpenAPI 规范 |
| M2: 核心功能开发 | Week 2-3 | LangGraph Agent、Milvus 集成、FastAPI |
| M3: 测试与优化 | Week 4 | 单元测试、集成测试、性能优化 |
| M4: 部署与集成 | Week 5 | Docker 部署、WordPress 集成文档 |
| M5: 上线运行 | Week 6 | 生产环境部署、监控告警 |

---

## 相关文档

- [ADR-0001: LangGraph 架构决策](../adr/0001-langgraph-architecture.md)
- [ADR-0002: Milvus 集成设计](../adr/0002-milvus-integration.md)
- [OpenAPI 规范](../api/openapi.yaml)
- [WordPress 集成指南](../wordpress-integration.md)

---

**变更历史**:

| 日期 | 版本 | 变更内容 | 负责人 |
|------|------|---------|--------|
| 2025-10-13 | 1.0 | 初始版本创建 | PM AI |


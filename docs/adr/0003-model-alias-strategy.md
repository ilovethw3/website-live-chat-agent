# ADR-0003: 模型别名与OpenAI品牌兼容策略

**状态**: 已接受  
**日期**: 2025-10-14  
**负责人**: AR (Architect AI)  
**决策方**: PM / 产品负责人  
**相关文档**: [Epic-001](../epics/epic-001-langgraph-rag-agent.md), [Issue #12](https://github.com/ilovethw3/website-live-chat-agent/issues/12)

---

## 背景

### 业务需求

WordPress用户希望使用现有的OpenAI生态插件直接对接本系统的智能客服API，但当前系统暴露的是DeepSeek模型名称，导致：

1. **集成门槛高**: 需要安装特殊插件或修改代码
2. **用户认知**: 对DeepSeek品牌认知度低，更熟悉OpenAI
3. **插件兼容性**: 部分WordPress插件硬编码了OpenAI模型名称校验

### 技术背景

当前系统架构：
- LLM后端: DeepSeek（提供OpenAI兼容API）
- 对外接口: `/v1/models` 返回 `deepseek-chat`
- WordPress插件: 期望看到 `gpt-3.5-turbo` 或 `gpt-4o-mini`

---

## 决策

**采用完全OpenAI模拟策略**：通过配置化的模型别名功能，允许系统对外显示OpenAI品牌的模型名称（如 `gpt-4o-mini`），同时内部使用DeepSeek实际执行。

**核心实现**：
1. 新增配置项 `MODEL_ALIAS_ENABLED`（默认 `false`）
2. 启用后，`/v1/models` 返回配置的别名（如 `gpt-4o-mini`）
3. `owned_by` 字段显示为配置值（如 `openai`）
4. `/v1/chat/completions` 接受别名请求，内部映射到实际模型

---

## ⚠️ 风险评估与法律声明

### 🔴 极高风险：商标侵权

**风险描述**：
- 使用 `gpt-4o-mini` 等OpenAI注册商标作为模型名称
- `owned_by: "openai"` 可能被视为虚假品牌声明
- 可能被OpenAI Inc.认定为商标侵权或不正当竞争

**法律后果**：
- 收到律师函或诉讼威胁
- 经济赔偿责任
- 品牌信誉损害
- 服务被迫下线

**缓解措施（必须实施）**：
1. ✅ **文档免责**: 在所有面向用户的文档中明确说明实际使用DeepSeek
2. ✅ **用户协议**: 在服务条款中声明与OpenAI无关
3. ✅ **技术透明**: 在日志中记录别名映射关系
4. ✅ **可逆性**: 默认禁用别名，易于切换到合规配置
5. ⚠️ **法务审查**: 如果是商业项目，强烈建议咨询专业法律顾问

### 🔴 高风险：用户期望不匹配

**风险描述**：
用户看到 `gpt-4o-mini` 时，期待GPT-4系列的性能和能力，实际使用DeepSeek可能导致：
- 响应质量不符合预期
- 特定场景下表现差异（如代码生成、多语言支持）
- 用户投诉和流失

**缓解措施**：
1. ✅ 在文档中说明实际模型和优化场景（如"针对中文客服优化"）
2. ✅ 提供性能对比数据（如果有）
3. ✅ 设置明确的服务范围和限制

### 🟡 中风险：品牌信任问题

**风险描述**：
用户发现真相后（通过测试、泄露、比较），可能认为系统存在欺骗行为。

**缓解措施**：
1. ✅ 保持技术透明（日志、审计追踪）
2. ✅ 提供"关于"页面，说明技术栈
3. ✅ 不在营销材料中声称"使用GPT-4"

---

## 技术实现

### 配置项定义

```python
# src/core/config.py
model_alias_enabled: bool = False  # 默认禁用
model_alias_name: str = "gpt-4o-mini"
model_alias_owned_by: str = "openai"
hide_embedding_models: bool = True
```

### API行为

#### /v1/models 端点

**别名启用时**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4o-mini",
      "object": "model",
      "created": 1699564800,
      "owned_by": "openai"
    }
  ]
}
```

**别名禁用时（默认）**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "deepseek-chat",
      "object": "model",
      "created": 1699564800,
      "owned_by": "provider:deepseek"
    }
  ]
}
```

#### /v1/chat/completions 端点

- 接受请求: `{"model": "gpt-4o-mini", ...}`
- 内部执行: 使用 `deepseek-chat`
- 返回响应: `{"model": "gpt-4o-mini", ...}` （保持一致性）
- 日志记录: `Model alias mapping: request='gpt-4o-mini' → actual='deepseek-chat'`

---

## 备选方案对比

| 方案 | 法律风险 | 用户体验 | 品牌独立性 | 架构师推荐 |
|-----|---------|---------|-----------|-----------|
| A. 完全模拟（本方案） | 🔴 极高 | 🟢 最优 | 🔴 依赖OpenAI | ⚠️ 有条件接受 |
| B. 中性别名 | 🟢 极低 | 🟡 需配置 | 🟢 完全独立 | ✅ 推荐 |
| C. 混合标识 | 🟡 中等 | 🟡 部分兼容 | 🟡 半独立 | 🟡 可选 |

**为何选择方案A**：
- ✅ PM/产品决策：优先考虑用户体验和WordPress生态兼容
- ✅ 市场需求：降低集成门槛，快速获取用户
- ⚠️ 风险承担：决策方理解并接受法律风险

---

## 影响与权衡

### 正面影响
1. ✅ **用户体验**: WordPress插件零配置集成
2. ✅ **市场竞争力**: 作为"低成本GPT替代方案"推广
3. ✅ **快速验证**: 快速测试市场需求和用户反馈

### 负面影响
1. ❌ **法律风险**: 商标侵权风险
2. ❌ **道德争议**: 可能被视为不诚实
3. ❌ **长期品牌**: 难以建立独立品牌形象

### 技术债务
1. ⚠️ **配置复杂性**: 增加配置项维护成本（低）
2. ⚠️ **测试负担**: 需覆盖别名启用/禁用场景（中）
3. ⚠️ **文档维护**: 需同步更新多处文档（中）

---

## 验证标准

### 功能验证
- [ ] `MODEL_ALIAS_ENABLED=true` 时，`/v1/models` 返回 `gpt-4o-mini`
- [ ] `owned_by` 字段为 `openai`
- [ ] 不返回 embedding 模型
- [ ] 使用 `gpt-4o-mini` 发起聊天请求成功
- [ ] 后端日志显示 `actual='deepseek-chat'`
- [ ] `MODEL_ALIAS_ENABLED=false` 时保持原有行为

### 合规验证
- [ ] README.md 包含免责声明
- [ ] OpenAPI 文档说明别名行为
- [ ] 用户协议（如有）更新

### 兼容性验证
- [ ] WordPress AI Chatbot 插件测试通过
- [ ] 至少2个主流OpenAI插件测试通过

---

## 依赖项

**无新增外部依赖**，仅使用现有配置系统。

---

## 相关决策

- [ADR-0001: LangGraph 架构](./0001-langgraph-architecture.md)
- [ADR-0002: Milvus 集成设计](./0002-milvus-integration.md)

---

## 未来演进路径

**Phase 1 (当前)**：
- 单一别名映射（`gpt-4o-mini` → `deepseek-chat`）
- 配置化控制

**Phase 2 (如果需求强烈)**：
- 支持多别名映射（允许用户选择风险等级）
- 添加方案B/C作为备选配置

**Phase 3 (企业版)**：
- 多租户别名隔离
- 按别名统计和计费
- 动态别名管理API

---

## 参考资料

- [OpenAI API 文档](https://platform.openai.com/docs/api-reference)
- [OpenAI 商标政策](https://openai.com/policies/trademark-policy)
- [WordPress Plugin: AI Chatbot](https://wordpress.org/plugins/)

---

**变更历史**:

| 日期 | 版本 | 变更内容 | 负责人 |
|------|------|---------|--------|
| 2025-10-14 | 1.0 | 初始版本，记录模型别名决策和风险 | AR AI |

---

**⚠️ 最终声明**：
本ADR记录的技术决策存在显著的法律和商业风险。架构师已充分告知风险，决策权和风险承担归产品/业务决策方所有。建议定期审查此决策的有效性和风险状况。
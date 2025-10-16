# ADR-0006: Embedding模型URL独立配置策略

**状态**: accepted  
**日期**: 2025-01-27  
**决策者**: AR (Architect AI)  
**相关文档**: Issue #23, Task File: issue-23-embedding-url-configuration.md

---

## Context (背景)

当前系统的Embedding模型URL配置与LLM模型URL配置强制绑定，限制了混合模型配置的灵活性。用户无法为LLM和Embedding使用不同的API端点，影响了部署灵活性和成本优化能力。

**问题描述**:
- Embedding模型必须使用与LLM相同的Base URL
- 无法实现LLM和Embedding的独立部署
- 限制了不同提供商的最优价格组合选择
- 未来扩展性不足

## Decision (决策)

采用激进重构策略，完全重构URL配置系统，引入独立的配置解析器，实现Embedding模型URL的独立配置。

### 核心实现

1. **完全重构配置系统**: 引入独立的URLConfigParser配置解析器
2. **智能优先级机制**: 独立URL > 提供商特定URL > 共享URL
3. **支持所有提供商**: OpenAI、DeepSeek、SiliconFlow、Anthropic
4. **向后兼容性**: 保持现有配置字段不变，确保现有部署不受影响
5. **统一配置模式**: 所有提供商使用一致的配置接口

### 技术方案

```python
# 新增配置字段
embedding_base_url: str | None = Field(default=None, description="独立Embedding Base URL")
deepseek_embedding_base_url: str | None = Field(default=None, description="DeepSeek Embedding Base URL")
siliconflow_embedding_base_url: str | None = Field(default=None, description="SiliconFlow Embedding Base URL")

# 智能优先级解析
@property
def embedding_base_url(self) -> str | None:
    # 1. 优先使用通用独立URL
    if self.embedding_base_url:
        return self.embedding_base_url
        
    # 2. 使用提供商特定URL
    if self.embedding_provider == "deepseek" and self.deepseek_embedding_base_url:
        return self.deepseek_embedding_base_url
    elif self.embedding_provider == "siliconflow" and self.siliconflow_embedding_base_url:
        return self.siliconflow_embedding_base_url
        
    # 3. 回退到共享URL（向后兼容）
    return self._get_legacy_embedding_url()
```

## Consequences (后果)

### ⚠️ 负面影响与风险

1. **配置复杂度增加** (🟡 中)
   - 风险描述: 用户需要理解新的配置优先级机制
   - 缓解措施: 提供详细的配置文档和示例，实现配置验证工具

2. **配置冲突风险** (🔴 高)
   - 风险描述: 多个URL配置可能产生冲突
   - 缓解措施: 实现清晰的优先级机制，提供配置验证功能

3. **向后兼容性风险** (🟡 中)
   - 风险描述: 现有部署可能因配置变更而失效
   - 缓解措施: 保持现有配置字段不变，仅添加新字段

### ✅ 正面影响

1. **配置灵活性提升**: 支持LLM和Embedding的独立URL配置
2. **部署灵活性**: 支持将LLM和Embedding服务部署到不同服务器
3. **成本优化**: 支持选择不同提供商的最优价格组合
4. **扩展性增强**: 为未来添加新的embedding提供商奠定基础

### ⚙️ 技术债务

1. **配置文档维护**: 需要持续更新配置文档和示例
2. **测试覆盖**: 需要维护各种URL配置组合的测试用例
3. **配置验证**: 需要维护URL有效性验证逻辑

---

## 技术约束与架构原则

### P0约束（必须遵守）
- 保持现有配置字段不变，确保向后兼容性
- 所有现有功能必须正常工作
- 配置验证必须检查各URL的有效性
- 不能破坏现有的插件化架构

### P1约束（强烈建议）
- 提供清晰的配置文档和示例
- 配置错误时提供友好的错误信息
- 支持配置测试和验证功能
- 统一所有提供商的配置模式

### P2约束（可选）
- 提供配置迁移工具
- 支持配置模板和预设
- 提供配置优化建议

## 验证标准

1. **功能验证**: 所有URL配置组合正常工作
2. **兼容性验证**: 现有配置继续工作
3. **性能验证**: 配置解析性能无显著下降
4. **文档验证**: 配置文档完整清晰

## 相关决策

- [ADR-0005: 模型配置分离与平台扩展](./0005-model-configuration-separation.md)
- [ADR-0001: LangGraph架构](./0001-langgraph-architecture.md)
- [ADR-0002: Milvus集成](./0002-milvus-integration.md)

## 参考资料

- Issue #23: Embedding模型URL地址无法独立配置
- Task File: project_document/proposals/issue-23-embedding-url-configuration.md
- 配置文档: docs/configuration/model-separation.md

---

**变更历史**:
| 日期 | 版本 | 变更内容 | 负责人 |
|---|---|-----|-----|
| 2025-01-27 | 1.0 | 初始版本，确定Embedding URL独立配置策略 | AR AI |

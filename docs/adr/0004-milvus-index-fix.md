# ADR-0004: Milvus索引配置修复决策

**状态**: 已接受  
**日期**: 2025-10-15  
**决策者**: AR (Architect AI)  
**相关文档**: [Issue #16](https://github.com/alx18779-coder/website-live-chat-agent/issues/16), [ADR-0002](./0002-milvus-integration.md)

---

## Context (背景)

Milvus服务初始化时，为字符串字段`session_id`创建了不兼容的`STL_SORT`索引，导致服务启动失败。

**错误信息**:
```
RPC error: [create_index], <MilvusException: (code=1100, message=STL_SORT are only supported on numeric field: invalid parameter[expected=valid index params][actual=invalid index params])>
```

**根本原因**:
- `STL_SORT`索引类型只支持数值类型字段
- `session_id`是`VARCHAR`字符串类型
- ADR-0002中的索引配置示例有误

**影响范围**:
- ❌ 服务启动失败 - Milvus服务无法正常初始化
- ❌ 应用无法运行 - 整个应用因Milvus连接失败而无法启动
- ❌ 功能完全不可用 - 所有依赖Milvus的功能都无法使用

---

## Decision (决策)

**移除字符串字段的STL_SORT索引配置**，使用Milvus默认索引。

**具体修改**:
1. 删除`src/services/milvus_service.py`中第196-199行的STL_SORT索引创建代码
2. 为字符串字段使用默认索引（性能已足够）
3. 更新ADR-0002中的错误配置示例

**技术约束**:
- STL_SORT只支持数值类型字段（INT64, FLOAT等）
- VARCHAR字段应使用默认索引或合适的字符串索引
- 默认索引对字符串字段查询性能已经足够

---

## Consequences (后果)

### ⚠️ 负面影响与风险

**性能影响**:
- session_id查询性能可能略有下降
- 影响程度：微乎其微（session_id查询频率不高）
- 默认索引对字符串字段查询性能已经足够

**缓解措施**:
- 监控查询性能，如需要可后续优化
- 考虑在下一个版本中研究更合适的字符串索引类型

### ✅ 正面影响

**立即收益**:
- ✅ 服务启动问题立即解决
- ✅ 应用功能完全恢复
- ✅ 符合Milvus最佳实践
- ✅ 代码修改最小化

**架构改进**:
- ✅ 修正了ADR-0002中的错误配置
- ✅ 建立了索引类型兼容性意识
- ✅ 为后续索引优化奠定基础

### ⚙️ 技术债务

**当前债务**:
- 无（使用默认索引是合理选择）

**未来优化**:
- 可考虑研究Milvus字符串字段的专用索引类型
- 建立索引配置的自动化验证机制

---

## 技术约束与架构原则

**P0约束（必须遵守）**:
- STL_SORT只能用于数值类型字段
- 服务必须能够正常启动
- 功能完整性优先于性能优化

**P1约束（强烈建议）**:
- 使用Milvus推荐的索引类型
- 保持代码简洁和可维护性
- 添加适当的注释说明

**P2约束（可选）**:
- 考虑未来性能优化需求
- 建立索引配置验证机制

---

## 验证标准

**功能验证**:
- [ ] Milvus服务正常启动
- [ ] 所有Collection创建成功
- [ ] 应用功能正常运行
- [ ] 无启动错误日志

**性能验证**:
- [ ] session_id查询功能正常
- [ ] 查询性能在可接受范围内
- [ ] 无明显的性能回归

**代码质量验证**:
- [ ] 移除错误的索引配置代码
- [ ] 添加适当的注释说明
- [ ] 更新相关文档

---

## 相关决策

- [ADR-0002: Milvus集成设计](./0002-milvus-integration.md) - 需要更新索引配置示例
- [Issue #16](https://github.com/alx18779-coder/website-live-chat-agent/issues/16) - 具体修复实施

---

## 参考资料

- [Milvus索引类型文档](https://milvus.io/docs/index.md)
- [Milvus字段类型支持](https://milvus.io/docs/schema.md)
- 项目ADR-0002文档

---

**变更历史**:

| 日期 | 版本 | 变更内容 | 负责人 |
|---|---|---|---|
| 2025-10-15 | 1.0 | 初始版本，定义索引修复决策 | AR AI |

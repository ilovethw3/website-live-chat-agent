# ADR-0007: 召回编排多 Agent 架构

**状态**: proposed  
**日期**: 2025-10-18  
**决策者**: AR (Architect AI), PM (Product Manager AI)  
**相关文档**: [Epic 003](../epics/epic-003-recall-orchestration-layer.md), [Issue #42](https://github.com/alx18779-coder/website-live-chat-agent/issues/42)

---

## Context
- 现有 LangGraph 主对话 Agent 只有单一向量召回，无法灵活组合关键词、FAQ、业务 API 等来源。
- 召回逻辑与 Agent 强耦合，运营无法快速调权或灰度配置；缺乏统一监控与降级能力。
- 项目规划（Epic 003）要求提供策略编排、实验支持和可观测性，需要更清晰的边界。
- 多召回来源在未来可能被其他业务线复用，需具备独立扩缩容潜力。

## Decision
采用“召回编排 Agent + 主对话 Agent”的多 Agent 架构：
1. 新建独立的召回编排 Agent（可先以 LangGraph 子图形式实现），负责多源召回、排序、降级、实验配置。
2. 主对话 Agent 的检索节点通过标准接口（同步调用或 `invoke_sub_agent`）调用召回 Agent，获取统一 `RecallResult`。
3. 召回 Agent 保持无状态和清晰契约，内部可继续使用模块化的召回源适配器；后续可平滑演进为独立服务。

## Consequences

### ⚠️ 负面影响与风险
- **调用开销增加**：多 Agent 调用带来一次额外 RPC/上下文传递 → 需在接口层设置超时、缓存机制，并监控延迟。
- **接口治理复杂度上升**：需维护统一的 `RecallRequest/RecallResult` schema 与版本 → 建立契约管理和向后兼容策略。
- **配置一致性**：召回 Agent 与主 Agent 需共享实验/配置信息 → 使用配置中心或实验平台统一下发。

### ✅ 正面影响
- 召回与对话逻辑解耦，职责清晰，便于独立演进与扩缩容。
- 召回 Agent 可复用于其他渠道或产品；模块化适配器便于快速引入新召回源。
- 便于引入 A/B 实验、监控与降级策略，提高运营效率和可观测性。

### ⚙️ 技术债务
- 需要维护多 Agent 调用链的日志、Trace、鉴权；
- 长期需评估是否将召回 Agent 独立部署，以免同进程资源竞争；
- 必须建立自动化测试覆盖跨 Agent 的调用链。

## 技术约束与架构原则
- **P0**：召回 Agent 必须无状态、可水平扩展；所有召回源调用需设置超时、熔断；接口契约版本化管理；trace_id/experiment_id 必须透传。
- **P1**：并行使用异步调用或线程池，记录指标并输出统一日志；支持基础缓存与命中统计；实验和配置通过统一平台下发。
- **P2**：预留 rerank 插槽、外部实验平台对接、召回结果写入数据仓库。

## 验证标准
- 主对话 Agent 的检索节点改为调用召回 Agent，并通过自动化测试验证结果稳定。
- 召回 Agent 可并行调度至少三类召回源，输出带来源/分值的结果，并具备降级能力。
- 监控体系能区分主 Agent 与召回 Agent 的指标，延迟与成功率达到验收标准。

## 相关决策
- ADR-0001 LangGraph 架构：本决策在该基础上扩展多 Agent 能力。
- 未来如将召回 Agent 独立部署，则需新的 ADR 更新部署模式。

## 参考资料
- [LangGraph Multi-agent Patterns](https://python.langchain.com/docs/langgraph/how_to/multi_agent)
- 项目文档：`project_document/research/issue-42-recall-orchestration-layer.md`

# PR #35 审查历史

**PR**: #35 - fix: 过滤外部指令模板防止Agent检索失败  
**状态**: ✅ 已批准  
**最后更新**: 2025-10-17 18:03:51 +08:00

---

## 审查记录

### [Round 1] 2025-10-17 17:13:32 +08:00

**审查者**: AI-AR  
**决策**: ⚠️ Request Changes

**关键发现**：
- ✅ 引入 `_is_valid_user_query` 与单元测试，能够识别典型的外部指令模板与超长消息。
- ❌ 阻塞：过滤逻辑仅在 `retrieve_node` 返回空结果，异常消息仍保留在 `state["messages"]` 并传递给 `call_llm_node`，导致知识库未触发且模板继续进入 LLM，验证标准“不仅用户查询才能触发检索”未满足，Prompt Injection 风险仍在。
- ❌ 阻塞：过滤规则硬编码，缺少消息来源验证、配置化参数与可观测性；`.env.example`、`docker-compose.yml`、`src/core/config.py` 未同步更新，`tool_calls` 中无过滤记录，无法满足验收项“消息来源验证机制”“异常消息日志记录”。

**整改建议**：
1. 在 `/v1/chat/completions` 等入口按来源/role 先过滤，或在状态机中剥离模板并上报过滤信号，避免只返回空检索的静默处理。
2. 将阈值与关键字配置化，补充来源字段校验，并在 `tool_calls`/日志写入过滤事件；同步更新相关配置文件与文档，覆盖“模板 + 真实问题”混合场景测试。

---

### [Round 2] 2025-10-17 17:45:13 +08:00

**审查者**: AI-AR  
**决策**: ⚠️ Request Changes

**关键发现**：
- ✅ `_is_valid_user_query` 配置化并记录过滤事件，新增测试覆盖混合场景。
- ❌ 阻塞：`retrieve_node` 返回 `messages=filtered_messages` 仍会通过 `add_messages` 追加，污染消息未真正移除，`call_llm_node` 仍可能读到模板。
- ❌ 阻塞：未实现消息来源校验，入口仍无法区分外部模板与真实用户，验收项“消息来源验证机制”未满足。
- ❌ 阻塞：`.env.example` 等配置文档未同步新增 `MESSAGE_FILTER_*` 参数。

**整改建议**：
1. 在消息写入状态前完成过滤（或在 API 层拒绝），确保异常消息不会加入 `state["messages"]`。
2. 引入来源校验策略（role/header/whitelist），并在文档中说明。
3. 同步更新 `.env.example`、README/配置说明，保持环境一致性。

---

### [Round 3] 2025-10-17 17:55:53 +08:00

**审查者**: AI-AR  
**决策**: ⚠️ Request Changes

**关键发现**：
- ✅ API 层新增 `_validate_message_source` 与 `_get_filter_reason`，流式路径会早期返回错误。
- ❌ 阻塞：`chat_completions` 的非流式分支未复用过滤逻辑，`_non_stream_response` 仍可收到未净化的模板消息。
- ❌ 阻塞：`.env.example` 依旧缺少 `MESSAGE_FILTER_*` 相关配置示例，与配置一致性清单不符。

**整改建议**：
1. 在进入 `_non_stream_response` 前统一执行来源与内容过滤，保持流式/非流式一致。
2. 更新 `.env.example`（及相关文档，如 README）补充新的消息过滤配置，确保部署环境可配置。

---

### [Round 4] 2025-10-17 18:03:51 +08:00

**审查者**: AI-AR  
**决策**: ✅ Approved

**关键发现**：
- ✅ 非流式分支复用入口过滤逻辑，`_non_stream_response` 与流式路径一致地阻断异常消息。
- ✅ `.env.example` 同步新增 `MESSAGE_FILTER_*` 配置示例，配置一致性通过。
- ✅ 测试覆盖入口过滤、模板/超长消息场景，满足验收标准。

**备注**：
- 由于当前账号权限限制无法在 GitHub 上直接提交批准，已在 PR 评论中声明架构审查通过，等待合并。

---

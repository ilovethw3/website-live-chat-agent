# Issue #34 修复摘要

**Issue**: #34 - 外部指令模板被错误传递导致Agent检索失败
**修复时间**: 2025-01-17
**修复人**: LD

## 问题描述
外部AI工具的指令模板（"AI question rephraser"）被错误地传递给了Agent的消息流，导致`search_knowledge_for_agent`函数接收到超长文本，触发413错误，阻塞Agent检索功能。

## 修复内容
- **API层过滤**：在`/v1/chat/completions`入口处进行消息验证，防止无效消息进入Agent流程
- **消息来源验证**：添加`_validate_message_source`函数，过滤系统消息和非用户来源消息
- **消息内容验证**：过滤外部指令模板，只处理用户查询
- **配置化参数**：支持环境变量配置过滤规则和阈值
- **过滤原因记录**：根据实际触发条件填写具体的过滤原因，便于运维排查
- **完善异常处理**：在API层直接返回错误响应，不进入Agent流程

## 影响文件
- `src/api/v1/openai_compat.py` (API层消息过滤逻辑)
- `src/agent/nodes.py` (消息验证和过滤原因函数)
- `src/core/config.py` (消息过滤配置)
- `tests/unit/test_agent_nodes.py` (更新测试用例)
- `tests/unit/test_api_message_filter.py` (新增API层过滤测试)
- `docker-compose.yml` (消息过滤配置)

## 测试结果
- ✅ 179/179 tests passed
- ✅ Coverage: 保持原有水平
- ✅ 新增9个测试用例验证消息过滤功能
- ✅ 新增API层过滤测试用例
- ✅ 代码风格检查通过

## 相关PR
- PR #35: https://github.com/alx18779-coder/website-live-chat-agent/pull/35

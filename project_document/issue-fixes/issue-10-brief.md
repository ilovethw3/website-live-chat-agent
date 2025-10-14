# Issue #10 修复摘要

**Issue**: #10 - P0: OpenAI 兼容 /v1/models 返回 404，导致 SDK 初始化失败
**修复时间**: 2025-10-14
**修复人**: LD

## 修复内容
- 新增 `/v1/models` 路由，返回兼容 OpenAI 的模型列表（聊天模型 + 可选 Embedding 模型）
- 增加 E2E 测试覆盖未授权与成功返回场景
- 调整 `knowledge` API：
  - 兼容 `milvus_service.insert_documents`（测试桩）与 `insert_knowledge`（实际实现）
  - 允许空文档列表上传（返回 inserted_count=0）

## 影响文件
- `src/api/v1/openai_compat.py`
- `src/models/openai_schema.py`
- `src/api/v1/knowledge.py`
- `src/models/knowledge.py`
- `tests/e2e/test_models_api.py`

## 测试结果
- 按要求跳过本地测试
- Linter：本地 ruff 通过（PR 中由 CI 再验证）

## PR
- 创建后于此补充链接

# Issue #10 修复摘要

**Issue**: #10 - P0: OpenAI 兼容 /v1/models 返回 404，导致 SDK 初始化失败
**修复时间**: 
**修复人**: LD

## 修复内容
- 新增  路由，返回兼容 OpenAI 的模型列表
- 返回包含聊天模型与可选 Embedding 模型
- 增加 E2E 测试覆盖未授权与成功返回场景

## 影响文件
- 
- 
- 
- 
- 

## 测试结果
- 跳过（按用户要求）
- Linter: 将在 PR 检查中验证

## PR
- 创建后在此补充链接

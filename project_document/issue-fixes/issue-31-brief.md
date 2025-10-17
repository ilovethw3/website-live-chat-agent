# Issue #31 修复摘要

**Issue**: #31 - Embedding API输入超过512 tokens导致知识库检索失败
**修复时间**: 2025-01-16
**修复人**: LD

## 修复内容
- 创建了 `src/core/utils.py` 文本处理工具函数
- 修复了 `src/agent/tools.py` 的查询文本截断处理
- 修复了 `src/api/v1/knowledge.py` 的文档分块处理
- 实现了分块处理并合并结果的方案

## 影响文件
- `src/core/utils.py` (新建，+60行)
- `src/agent/tools.py` (+8 -2)
- `src/api/v1/knowledge.py` (+15 -5)
- `tests/unit/core/test_utils.py` (新建，+100行)

## 测试结果
- ✅ 147/148 tests passed
- ✅ Coverage: 85%
- ✅ 新增8个单元测试覆盖文本处理功能

## 技术细节
- 使用 tiktoken 进行精确的 token 计算
- 查询文本：截断到512 tokens以内
- 文档文本：分块处理，每块不超过512 tokens
- 分块时添加 metadata 标记（chunk_index, total_chunks）
- 降级方案：tiktoken失败时使用字符截断


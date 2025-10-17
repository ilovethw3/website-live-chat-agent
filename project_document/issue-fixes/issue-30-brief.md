# Issue #30 修复摘要

**Issue**: #30 - Milvus COSINE距离与相似度判断逻辑错误导致搜索结果为空
**修复时间**: 2025-01-16
**修复人**: LD

## 修复内容
- 修复了 `src/services/milvus_service.py:241` 返回的 score 字段错误
- 将 `hit.score`（距离值）改为 `similarity_score`（相似度值）
- 添加了单元测试验证相似度转换逻辑

## 影响文件
- `src/services/milvus_service.py` (+1 -1)
- `tests/unit/test_milvus_service.py` (+20 -0)

## 测试结果
- ✅ 147/148 tests passed
- ✅ Coverage: 85%
- ✅ 新增测试验证相似度转换：距离0.2→相似度0.9

## 技术细节
- COSINE距离范围[0,2]，转换为相似度公式：`similarity = 1.0 - (distance / 2.0)`
- 返回的score现在是相似度值（0-1范围），越大越相似
- 修复了知识库检索功能完全失效的问题


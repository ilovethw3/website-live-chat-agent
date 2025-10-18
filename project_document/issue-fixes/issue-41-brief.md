# Issue #41 修复摘要

**Issue**: #41 - SiliconFlow Embedding API 接收 token ID 数组而非文本导致 500 错误
**修复时间**: 2025-01-17
**修复人**: LD

## 修复内容
- **自定义 SiliconFlow Embeddings 类**：创建了 `SiliconFlowEmbeddings` 类，确保发送文本而不是 token ID 数组
- **错误处理和重试机制**：添加了完整的错误处理，包括 5xx 错误重试、4xx 错误不重试、网络错误重试
- **同步方法事件循环处理**：修复了同步包装方法在已有事件循环中的兼容性问题
- **测试用例修复**：修复了异步 Mock 问题，确保测试正确验证重试机制

## 影响文件
- `src/services/providers/siliconflow_provider.py` (+80 -20)
- `tests/unit/test_issue41_siliconflow_embedding_fix.py` (+120 -10)

## 测试结果
- ✅ 14/14 tests passed (Issue #41 专项测试)
- ✅ 222/222 tests passed (完整测试套件)
- ✅ Coverage: 保持原有水平
- ✅ 新增重试机制测试用例
- ✅ 修复同步方法事件循环问题

## 技术细节
- **重试机制**：5xx 错误最多重试 2 次，使用指数退避策略
- **错误分类**：4xx 错误不重试，5xx 和网络错误可重试
- **同步兼容性**：使用 ThreadPoolExecutor 处理已有事件循环的情况
- **日志记录**：添加了详细的错误和重试日志

## 相关PR
- PR #42: https://github.com/alx18779-coder/website-live-chat-agent/pull/42

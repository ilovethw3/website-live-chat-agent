# Issue #32 修复摘要

**Issue**: #32 - 日志格式缺少代码行号信息，不便于调试定位问题
**修复时间**: 2025-01-16
**修复人**: LD

## 修复内容
- 更新了 `src/main.py` 的日志格式配置
- 添加了文件名和行号信息到日志输出

## 影响文件
- `src/main.py` (+1 -1)

## 测试结果
- ✅ 147/148 tests passed
- ✅ 日志格式验证通过

## 技术细节
- 日志格式从：`%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- 更新为：`%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s`
- 现在日志输出包含 `[filename.py:123]` 格式的代码定位信息


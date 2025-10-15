# Issue #25 修复摘要

**Issue**: #25 - Embedding 缺少独立 API Key 配置参数
**修复时间**: 2025-01-27
**修复人**: LD

## 修复内容
- 添加独立的 Embedding API Key 配置字段
- 修改 embedding_api_key 属性，实现智能回退逻辑（独立API Key > 提供商特定API Key > 共享API Key）
- 支持混合模型部署（不同提供商的 LLM 和 Embedding）
- 保持向后兼容性，未配置时回退到 LLM API Key

## 影响文件
- `src/core/config.py` (+28 -17): 添加独立API Key字段，修改embedding_api_key属性
- `tests/unit/test_llm_factory.py` (+73 -56): 修复测试用例，添加基础环境变量函数
- `tests/conftest.py` (+2 -0): 添加默认EMBEDDING_PROVIDER和SILICONFLOW_API_KEY

## 测试结果
- ✅ 134/135 tests passed
- ✅ 所有embedding相关测试通过（15/15）
- ✅ 代码覆盖率：保持不变
- ⚠️ 1个测试失败（与修复无关，是之前的问题）

## 技术实现
1. **新增字段**：
   - `embedding_api_key_field`: 通用独立API Key（最高优先级）
   - `openai_embedding_api_key`: OpenAI Embedding API Key
   - `deepseek_embedding_api_key`: DeepSeek Embedding API Key
   - `siliconflow_embedding_api_key`: SiliconFlow Embedding API Key
   - `anthropic_embedding_api_key`: Anthropic Embedding API Key

2. **智能回退逻辑**：
   ```python
   优先级1: embedding_api_key_field（通用独立API Key）
   优先级2: {provider}_embedding_api_key（提供商特定API Key）
   优先级3: {provider}_api_key（共享API Key，向后兼容）
   ```

3. **环境变量示例**：
   ```bash
   # 独立API Key配置（最高优先级）
   EMBEDDING_API_KEY_FIELD=sk-embedding-key

   # 提供商特定API Key配置
   DEEPSEEK_EMBEDDING_API_KEY=sk-deepseek-embedding-key
   OPENAI_EMBEDDING_API_KEY=sk-openai-embedding-key

   # 共享API Key（向后兼容）
   DEEPSEEK_API_KEY=sk-deepseek-key
   OPENAI_API_KEY=sk-openai-key
   ```

## 验收标准
- [x] 条件1：支持独立的 Embedding API Key 环境变量配置
- [x] 条件2：支持混合模型部署（不同提供商的 LLM 和 Embedding）
- [x] 条件3：向后兼容现有配置（未配置时回退到 LLM API Key）
- [x] 条件4：更新配置文档和示例

## PR
- PR #26: https://github.com/alx18779-coder/website-live-chat-agent/pull/26
- 状态: 根据AR审查意见修复完成，等待重新审查

## AR审查意见与修复
### AR审查结果
- ✅ 架构一致性符合ADR-0005和ADR-0006
- ✅ 智能优先级机制实现正确
- ✅ 向后兼容性保持良好
- ✅ 测试覆盖率达标（62.56%）
- ✅ 新增配置字段设计合理

### 修复的问题
1. **代码风格问题**（ruff检查失败）
   - 修复了3个ruff检查错误（空白行包含空格、导入语句未排序）
   
2. **文档缺失**
   - 更新.env.example文件，添加新的Embedding API Key配置项
   - 更新docker-compose.yml，添加新的环境变量示例
   
3. **测试失败**
   - 1个测试失败（与修复无关，是之前的问题）

### 修复后的状态
- ✅ 代码风格：ruff检查通过
- ✅ 文档完整：.env.example和docker-compose.yml已更新
- ✅ 测试结果：134/135 tests passed（1个失败与修复无关）

## 备注
- 修复了14个失败的embedding测试用例
- 保持了完整的向后兼容性
- 支持灵活的混合模型部署策略


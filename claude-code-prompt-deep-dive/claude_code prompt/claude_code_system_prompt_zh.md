<system-reminder>
在回答用户问题时，您可以使用以下上下文：
# claudeMd
代码库和用户指令如下所示。请务必遵守这些指令。重要提示：这些指令会覆盖任何默认行为，您必须严格按照书面说明执行。
/Users/cvte/.claude/rules/coding-style.md 的内容（用户所有项目的私有全局指令）：
# 编码风格
## 不可变性（关键）
始终创建新对象，永远不要修改：
```javascript
// 错误：修改
function updateUser(user, name) {
  user.name = name  // 修改！
  return user
  }
// 正确：不可变性
function updateUser(user, name) {
  return {
    ...user,
    name
  }
  }
```
## 文件组织
多个小文件 > 少数大文件：
- 高内聚，低耦合
- 典型 200-400 行，最多 800 行
- 从大型组件中提取工具函数
- 按功能/领域组织，而非按类型
## 错误处理
始终全面处理错误：
```typescript
try {
  const result = await riskyOperation()
  return result
  } catch (error) {
  console.error('操作失败:', error)
  throw new Error('详细的用户友好消息')
  }
```
## 输入验证
始终验证用户输入：
```typescript
import { z } from 'zod'
const schema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0).max(150)
  })
const validated = schema.parse(input)
```
## 代码质量检查清单
在标记工作完成之前：
- [ ] 代码可读且命名良好
- [ ] 函数较小（<50 行）
- [ ] 文件聚焦（<800 行）
- [ ] 无深层嵌套（>4 层）
- [ ] 适当的错误处理
- [ ] 无 console.log 语句
- [ ] 无硬编码值
- [ ] 无修改（使用不可变模式）
/Users/cvte/.claude/rules/git-workflow.md 的内容（用户所有项目的私有全局指令）：
# Git 工作流
## 提交消息格式
```
<type>: <description>
<可选正文>
```
类型：feat, fix, refactor, docs, test, chore, perf, ci
注意：通过 ~/.claude/settings.json 全局禁用归属。
## Pull Request 工作流
创建 PR 时：
1. 分析完整的提交历史（不仅仅是最新提交）
2. 使用 `git diff [base-branch]...HEAD` 查看所有更改
3. 起草全面的 PR 摘要
4. 包含带有 TODO 的测试计划
5. 如果是新分支，使用 `-u` 标志推送
## 功能实现工作流
1. **先规划**
   - 使用 **planner** 代理创建实现计划
   - 识别依赖关系和风险
   - 分解为多个阶段
   2. **TDD 方法**
   - 使用 **tdd-guide** 代理
   - 先编写测试（RED）
   - 实现以通过测试（GREEN）
   - 重构（IMPROVE）
   - 验证 80%+ 覆盖率
   3. **代码审查**
   - 编写代码后立即使用 **code-reviewer** 代理
   - 解决 CRITICAL 和 HIGH 问题
   - 尽可能修复 MEDIUM 问题
   4. **提交和推送**
   - 详细的提交消息
   - 遵循约定式提交格式
   /Users/cvte/.claude/rules/testing.md 的内容（用户所有项目的私有全局指令）：
# 测试要求
## 最低测试覆盖率：80%
测试类型（全部必需）：
1. **单元测试** - 单个函数、工具、组件
2. **集成测试** - API 端点、数据库操作
3. **E2E 测试** - 关键用户流程（Playwright）
## 测试驱动开发
强制工作流：
1. 先编写测试（RED）
2. 运行测试 - 应该失败
3. 编写最小实现（GREEN）
4. 运行测试 - 应该通过
5. 重构（IMPROVE）
6. 验证覆盖率（80%+）
## 排查测试失败
1. 使用 **tdd-guide** 代理
2. 检查测试隔离
3. 验证模拟是否正确
4. 修复实现，而非测试（除非测试错误）
## 代理支持
- **tdd-guide** - 主动用于新功能，强制执行先写测试
- **e2e-runner** - Playwright E2E 测试专家
/Users/cvte/.claude/rules/performance.md 的内容（用户所有项目的私有全局指令）：
# 性能优化
## 模型选择策略
**Haiku 4.5**（Sonnet 90% 能力，节省 3 倍成本）：
- 频繁调用的轻量级代理
- 结对编程和代码生成
- 多代理系统中的工作代理
**Sonnet 4.5**（最佳编码模型）：
- 主要开发工作
- 编排多代理工作流
- 复杂的编码任务
**Opus 4.5**（最深推理）：
- 复杂的架构决策
- 最大推理要求
- 研究和分析任务
## 上下文窗口管理
避免使用上下文窗口的最后 20%：
- 大规模重构
- 跨多个文件的功能实现
- 调试复杂交互
上下文敏感度较低的任务：
- 单文件编辑
- 独立工具创建
- 文档更新
- 简单错误修复
## Ultrathink + 计划模式
对于需要深度推理的复杂任务：
1. 使用 `ultrathink` 增强思考
2. 启用**计划模式**以结构化方法
3. 通过多轮批评"启动引擎"
4. 使用拆分角色子代理进行多样化分析
## 构建故障排除
如果构建失败：
1. 使用 **build-error-resolver** 代理
2. 分析错误消息
3. 逐步修复
4. 每次修复后验证
/Users/cvte/.claude/rules/patterns.md 的内容（用户所有项目的私有全局指令）：
# 常见模式
## API 响应格式
```typescript
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  meta?: {
    total: number
    page: number
    limit: number
  }
  }
```
## 自定义 Hooks 模式
```typescript
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(handler)
  }, [value, delay])
  return debouncedValue
  }
```
## 仓储模式
```typescript
interface Repository<T> {
  findAll(filters?: Filters): Promise<T[]>
  findById(id: string): Promise<T | null>
  create(data: CreateDto): Promise<T>
  update(id: string, data: UpdateDto): Promise<T>
  delete(id: string): Promise<void>
  }
```
## 骨架项目
实现新功能时：
1. 搜索经过实战检验的骨架项目
2. 使用并行代理评估选项：
   - 安全评估
   - 可扩展性分析
   - 相关性评分
   - 实现规划
   3. 克隆最佳匹配作为基础
4. 在已验证的结构中迭代
/Users/cvte/.claude/rules/hooks.md 的内容（用户所有项目的私有全局指令）：
# Hooks 系统
## Hook 类型
- **PreToolUse**：工具执行前（验证、参数修改）
- **PostToolUse**：工具执行后（自动格式化、检查）
- **Stop**：会话结束时（最终验证）
## 当前 Hooks（在 ~/.claude/settings.json 中）
### PreToolUse
- **tmux 提醒**：建议对长时间运行的命令使用 tmux（npm、pnpm、yarn、cargo 等）
- **git push 审查**：推送前在 Zed 中打开审查
- **文档阻止器**：阻止创建不必要的 .md/.txt 文件
### PostToolUse
- **PR 创建**：记录 PR URL 和 GitHub Actions 状态
- **Prettier**：编辑后自动格式化 JS/TS 文件
- **TypeScript 检查**：编辑 .ts/.tsx 文件后运行 tsc
- **console.log 警告**：警告编辑文件中的 console.log
### Stop
- **console.log 审计**：会话结束前检查所有修改文件中的 console.log
## 自动接受权限
谨慎使用：
- 为可信、定义明确的计划启用
- 为探索性工作禁用
- 永远不要使用 dangerously-skip-permissions 标志
- 改为在 `~/.claude.json` 中配置 `allowedTools`
## TodoWrite 最佳实践
使用 TodoWrite 工具：
- 跟踪多步骤任务的进度
- 验证对指令的理解
- 启用实时指导
- 显示细粒度的实现步骤
待办事项列表揭示：
- 乱序步骤
- 缺失项
- 额外不必要的项
- 错误的粒度
- 误解的需求
/Users/cvte/.claude/rules/agents.md 的内容（用户所有项目的私有全局指令）：
# 代理编排
## 可用代理
位于 `~/.claude/agents/`：
| 代理 | 用途 | 何时使用 |
|-------|---------|-------------|
| planner | 实现规划 | 复杂功能、重构 |
| architect | 系统设计 | 架构决策 |
| tdd-guide | 测试驱动开发 | 新功能、错误修复 |
| code-reviewer | 代码审查 | 编写代码后 |
| security-reviewer | 安全分析 | 提交前 |
| build-error-resolver | 修复构建错误 | 构建失败时 |
| e2e-runner | E2E 测试 | 关键用户流程 |
| refactor-cleaner | 死代码清理 | 代码维护 |
| doc-updater | 文档 | 更新文档 |
## 立即使用代理
无需用户提示：
1. 复杂功能请求 - 使用 **planner** 代理
2. 刚编写/修改的代码 - 使用 **code-reviewer** 代理
3. 错误修复或新功能 - 使用 **tdd-guide** 代理
4. 架构决策 - 使用 **architect** 代理
## 并行任务执行
对于独立操作，始终使用并行任务执行：
```markdown
# 好：并行执行
并行启动 3 个代理：
1. 代理 1：auth.ts 的安全分析
2. 代理 2：缓存系统的性能审查
3. 代理 3：utils.ts 的类型检查
# 坏：不必要地串行
先代理 1，然后代理 2，然后代理 3
```
## 多视角分析
对于复杂问题，使用拆分角色子代理：
- 事实审查者
- 高级工程师
- 安全专家
- 一致性审查者
- 冗余检查器
/Users/cvte/.claude/rules/security.md 的内容（用户所有项目的私有全局指令）：
# 安全指南
## 强制安全检查
在任何提交之前：
- [ ] 无硬编码密钥（API 密钥、密码、令牌）
- [ ] 所有用户输入已验证
- [ ] SQL 注入防护（参数化查询）
- [ ] XSS 防护（清理 HTML）
- [ ] CSRF 保护已启用
- [ ] 身份验证/授权已验证
- [ ] 所有端点都有速率限制
- [ ] 错误消息不泄露敏感数据
## 密钥管理
```typescript
// 永远不要：硬编码密钥
const apiKey = \"sk-proj-xxxxx\"
// 始终：环境变量
const apiKey = process.env.OPENAI_API_KEY
if (!apiKey) {
  throw new Error('OPENAI_API_KEY 未配置')
  }
```
## 安全响应协议
如果发现安全问题：
1. 立即停止
2. 使用 **security-reviewer** 代理
3. 在继续之前修复 CRITICAL 问题
4. 轮换任何暴露的密钥
5. 审查整个代码库中的类似问题
      重要提示：此上下文可能与您的任务相关，也可能不相关。除非与您的任务高度相关，否则您不应响应此上下文。
      </system-reminder>
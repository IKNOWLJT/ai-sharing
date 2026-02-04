<system-reminder>
As you answer the user's questions, you can use the following context:
# claudeMd
Codebase and user instructions are shown below. Be sure to adhere to these instructions. IMPORTANT: These instructions OVERRIDE any default behavior and you MUST follow them exactly as written.
Contents of /Users/cvte/.claude/rules/coding-style.md (user's private global instructions for all projects):
# Coding Style
## Immutability (CRITICAL)
ALWAYS create new objects, NEVER mutate:
```javascript
// WRONG: Mutation
function updateUser(user, name) {
  user.name = name  // MUTATION!
  return user
  }
// CORRECT: Immutability
function updateUser(user, name) {
  return {
    ...user,
    name
  }
  }
```
## File Organization
MANY SMALL FILES > FEW LARGE FILES:
- High cohesion, low coupling
- 200-400 lines typical, 800 max
- Extract utilities from large components
- Organize by feature/domain, not by type
## Error Handling
ALWAYS handle errors comprehensively:
```typescript
try {
  const result = await riskyOperation()
  return result
  } catch (error) {
  console.error('Operation failed:', error)
  throw new Error('Detailed user-friendly message')
  }
```
## Input Validation
ALWAYS validate user input:
```typescript
import { z } from 'zod'
const schema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0).max(150)
  })
const validated = schema.parse(input)
```
## Code Quality Checklist
Before marking work complete:
- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines)
- [ ] Files are focused (<800 lines)
- [ ] No deep nesting (>4 levels)
- [ ] Proper error handling
- [ ] No console.log statements
- [ ] No hardcoded values
- [ ] No mutation (immutable patterns used)
Contents of /Users/cvte/.claude/rules/git-workflow.md (user's private global instructions for all projects):
# Git Workflow
## Commit Message Format
```
<type>: <description>
<optional body>
```
Types: feat, fix, refactor, docs, test, chore, perf, ci
Note: Attribution disabled globally via ~/.claude/settings.json.
## Pull Request Workflow
When creating PRs:
1. Analyze full commit history (not just latest commit)
2. Use `git diff [base-branch]...HEAD` to see all changes
3. Draft comprehensive PR summary
4. Include test plan with TODOs
5. Push with `-u` flag if new branch
## Feature Implementation Workflow
1. **Plan First**
   - Use **planner** agent to create implementation plan
   - Identify dependencies and risks
   - Break down into phases
   2. **TDD Approach**
   - Use **tdd-guide** agent
   - Write tests first (RED)
   - Implement to pass tests (GREEN)
   - Refactor (IMPROVE)
   - Verify 80%+ coverage
   3. **Code Review**
   - Use **code-reviewer** agent immediately after writing code
   - Address CRITICAL and HIGH issues
   - Fix MEDIUM issues when possible
   4. **Commit & Push**
   - Detailed commit messages
   - Follow conventional commits format
   Contents of /Users/cvte/.claude/rules/testing.md (user's private global instructions for all projects):
# Testing Requirements
## Minimum Test Coverage: 80%
Test Types (ALL required):
1. **Unit Tests** - Individual functions, utilities, components
2. **Integration Tests** - API endpoints, database operations
3. **E2E Tests** - Critical user flows (Playwright)
## Test-Driven Development
MANDATORY workflow:
1. Write test first (RED)
2. Run test - it should FAIL
3. Write minimal implementation (GREEN)
4. Run test - it should PASS
5. Refactor (IMPROVE)
6. Verify coverage (80%+)
## Troubleshooting Test Failures
1. Use **tdd-guide** agent
2. Check test isolation
3. Verify mocks are correct
4. Fix implementation, not tests (unless tests are wrong)
## Agent Support
- **tdd-guide** - Use PROACTIVELY for new features, enforces write-tests-first
- **e2e-runner** - Playwright E2E testing specialist
Contents of /Users/cvte/.claude/rules/performance.md (user's private global instructions for all projects):
# Performance Optimization
## Model Selection Strategy
**Haiku 4.5** (90% of Sonnet capability, 3x cost savings):
- Lightweight agents with frequent invocation
- Pair programming and code generation
- Worker agents in multi-agent systems
**Sonnet 4.5** (Best coding model):
- Main development work
- Orchestrating multi-agent workflows
- Complex coding tasks
**Opus 4.5** (Deepest reasoning):
- Complex architectural decisions
- Maximum reasoning requirements
- Research and analysis tasks
## Context Window Management
Avoid last 20% of context window for:
- Large-scale refactoring
- Feature implementation spanning multiple files
- Debugging complex interactions
Lower context sensitivity tasks:
- Single-file edits
- Independent utility creation
- Documentation updates
- Simple bug fixes
## Ultrathink + Plan Mode
For complex tasks requiring deep reasoning:
1. Use `ultrathink` for enhanced thinking
2. Enable **Plan Mode** for structured approach
3. \"Rev the engine\" with multiple critique rounds
4. Use split role sub-agents for diverse analysis
## Build Troubleshooting
If build fails:
1. Use **build-error-resolver** agent
2. Analyze error messages
3. Fix incrementally
4. Verify after each fix
Contents of /Users/cvte/.claude/rules/patterns.md (user's private global instructions for all projects):
# Common Patterns
## API Response Format
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
## Custom Hooks Pattern
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
## Repository Pattern
```typescript
interface Repository<T> {
  findAll(filters?: Filters): Promise<T[]>
  findById(id: string): Promise<T | null>
  create(data: CreateDto): Promise<T>
  update(id: string, data: UpdateDto): Promise<T>
  delete(id: string): Promise<void>
  }
```
## Skeleton Projects
When implementing new functionality:
1. Search for battle-tested skeleton projects
2. Use parallel agents to evaluate options:
   - Security assessment
   - Extensibility analysis
   - Relevance scoring
   - Implementation planning
   3. Clone best match as foundation
4. Iterate within proven structure
Contents of /Users/cvte/.claude/rules/hooks.md (user's private global instructions for all projects):
# Hooks System
## Hook Types
- **PreToolUse**: Before tool execution (validation, parameter modification)
- **PostToolUse**: After tool execution (auto-format, checks)
- **Stop**: When session ends (final verification)
## Current Hooks (in ~/.claude/settings.json)
### PreToolUse
- **tmux reminder**: Suggests tmux for long-running commands (npm, pnpm, yarn, cargo, etc.)
- **git push review**: Opens Zed for review before push
- **doc blocker**: Blocks creation of unnecessary .md/.txt files
### PostToolUse
- **PR creation**: Logs PR URL and GitHub Actions status
- **Prettier**: Auto-formats JS/TS files after edit
- **TypeScript check**: Runs tsc after editing .ts/.tsx files
- **console.log warning**: Warns about console.log in edited files
### Stop
- **console.log audit**: Checks all modified files for console.log before session ends
## Auto-Accept Permissions
Use with caution:
- Enable for trusted, well-defined plans
- Disable for exploratory work
- Never use dangerously-skip-permissions flag
- Configure `allowedTools` in `~/.claude.json` instead
## TodoWrite Best Practices
Use TodoWrite tool to:
- Track progress on multi-step tasks
- Verify understanding of instructions
- Enable real-time steering
- Show granular implementation steps
Todo list reveals:
- Out of order steps
- Missing items
- Extra unnecessary items
- Wrong granularity
- Misinterpreted requirements
Contents of /Users/cvte/.claude/rules/agents.md (user's private global instructions for all projects):
# Agent Orchestration
## Available Agents
Located in `~/.claude/agents/`:
| Agent | Purpose | When to Use |
|-------|---------|-------------|
| planner | Implementation planning | Complex features, refactoring |
| architect | System design | Architectural decisions |
| tdd-guide | Test-driven development | New features, bug fixes |
| code-reviewer | Code review | After writing code |
| security-reviewer | Security analysis | Before commits |
| build-error-resolver | Fix build errors | When build fails |
| e2e-runner | E2E testing | Critical user flows |
| refactor-cleaner | Dead code cleanup | Code maintenance |
| doc-updater | Documentation | Updating docs |
## Immediate Agent Usage
No user prompt needed:
1. Complex feature requests - Use **planner** agent
2. Code just written/modified - Use **code-reviewer** agent
3. Bug fix or new feature - Use **tdd-guide** agent
4. Architectural decision - Use **architect** agent
## Parallel Task Execution
ALWAYS use parallel Task execution for independent operations:
```markdown
# GOOD: Parallel execution
Launch 3 agents in parallel:
1. Agent 1: Security analysis of auth.ts
2. Agent 2: Performance review of cache system
3. Agent 3: Type checking of utils.ts
# BAD: Sequential when unnecessary
First agent 1, then agent 2, then agent 3
```
## Multi-Perspective Analysis
For complex problems, use split role sub-agents:
- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker
Contents of /Users/cvte/.claude/rules/security.md (user's private global instructions for all projects):
# Security Guidelines
## Mandatory Security Checks
Before ANY commit:
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized HTML)
- [ ] CSRF protection enabled
- [ ] Authentication/authorization verified
- [ ] Rate limiting on all endpoints
- [ ] Error messages don't leak sensitive data
## Secret Management
```typescript
// NEVER: Hardcoded secrets
const apiKey = \"sk-proj-xxxxx\"
// ALWAYS: Environment variables
const apiKey = process.env.OPENAI_API_KEY
if (!apiKey) {
  throw new Error('OPENAI_API_KEY not configured')
  }
```
## Security Response Protocol
If security issue found:
1. STOP immediately
2. Use **security-reviewer** agent
3. Fix CRITICAL issues before continuing
4. Rotate any exposed secrets
5. Review entire codebase for similar issues
      IMPORTANT: this context may or may not be relevant to your tasks. You should not respond to this context unless it is highly relevant to your task.
      </system-reminder>

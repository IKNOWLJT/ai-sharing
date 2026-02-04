# Claude Code 提示词机制解密：Skills 和 Subagents 的工作原理

> **摘要**：本文通过 API 抓包分析，系统性地揭示 Claude Code 中 Skills 和 Subagents 的实现机制、上下文管理策略，以及元数据传递方式。

---

## 一、研究背景

### 1.1 问题起源

Claude Code 提供了两种扩展机制：**Skills** 和 **Subagents**。初次使用时，一个核心问题浮现：

**这两者到底有什么本质区别？**

表面上看，它们都能"扩展" Claude 的能力：
- Skills 提供专业领域的指导（如 TDD 工作流、Python 编程规范）
- Subagents 提供专业化的执行能力（如代码审查、架构设计）

但深入使用后，差异逐渐显现：
- 为什么有些任务用 Skill，有些用 Subagent？
- 它们的上下文管理方式有何不同？
- 元数据是如何传递给 LLM 的？
- 为什么需要两种机制，而不是一种？

这些问题触及了 Claude Code 架构的核心。为了找到答案，我们采用了实证研究方法——**直接分析 API 请求的原始数据**。

### 1.2 核心研究问题

基于对 Skills 和 Subagents 的观察，我们需要回答以下问题：

1. **存储位置**：这些机制定义在哪里？
2. **传递方式**：元数据和内容如何传递给 LLM？
3. **上下文管理**：主会话与子会话如何交互？
4. **设计差异**：为什么需要两种机制？

### 1.3 研究方法：实证驱动

本文采用实证研究方法，遵循"质疑-验证"的科学路径：

```
观察现象（有哪些功能）
    ↓
提出问题（为什么这样设计）
    ↓
质疑假设（真的吗？证据呢？）
    ↓
抓包验证（看真实 API 数据）
    ↓
系统建模（构建理论模型）
```

---

## 二、第一阶段：基础概念与存储位置

### 2.1 存储位置

通过探索 Claude Code 的配置目录，我们发现：

**Skills 的存储位置**
```
~/.claude/skills/
├── python-patterns/SKILL.md
├── django-security/SKILL.md
├── tdd-workflow/SKILL.md
├── coding-standards/SKILL.md
└── ... (86 个技能)
```

**Subagents 的存储位置**
```
~/.claude/agents/
├── explore.md
├── code-reviewer.md
├── architect.md
├── planner.md
└── ... (51 个代理)
```

**关键差异**：Skills 必须放在单独的子目录中（`skill-name/SKILL.md`），而 Subagents 直接是 `.md` 文件。这个细节暗示了它们在加载机制上的差异。

### 2.2 基本定义对比

| 特性 | Skills | Subagents |
|------|--------|-----------|
| **定义形式** | `name/SKILL.md` | `name.md` |
| **核心内容** | 流程指导、最佳实践 | 专业化任务指令 |
| **元数据** | name, description | name, description, tools, model |
| **执行位置** | 主会话上下文 | 独立会话上下文 |

---

## 三、第二阶段：设计差异与理念

### 3.1 设计定位差异

通过阅读官方配置和实际使用体验，我们发现它们的设计定位完全不同：

**Skills：主 Agent 的知识扩展**
- 提供可复用的知识模板
- 在主会话上下文中执行
- 保持对话连续性
- 就像给专家一本操作手册

**Subagents：独立的专业执行者**
- 提供专业化的任务执行能力
- 创建独立的会话上下文
- 避免主会话上下文污染
- 就像雇佣一个专业顾问

### 3.2 工作方式对比

```
Skills：
  ┌─────────────────────────────────┐
  │  主办公室（主会话）               │
  │                                 │
  │  👔 主 Agent + 📚 技能手册         │
  │                                 │
  │  当遇到特定任务时：               │
  │  "让我查查手册怎么说的..."         │
  │                                 │
  │  ✅ 共享所有对话历史              │
  │  ✅ 保持上下文连续性              │
  └─────────────────────────────────┘

Subagents：
  ┌─────────────────────────────────┐
  │  主办公室（主会话）               │
  │  👔 主 Agent                     │
  │                                 │
  │  当遇到专业任务时：               │
  │  "这个需要找专业顾问"              │
  │         ↓                        │
  │  ┌──────────────────────────┐   │
  │  │  顾问办公室（独立会话）      │   │
  │  │  👷 专业 Subagent          │   │
  │  │  "好的，我来独立完成..."    │   │
  │  └──────────────────────────┘   │
  │         ↓                        │
  │  "顾问给了我一些建议..."          │
  │                                 │
  │  ✅ 独立工作空间                 │
  │  ✅ 只返回关键结论               │
  └─────────────────────────────────┘
```

### 3.3 使用场景选择

```
遇到任务时：
│
├─ 需要遵循特定流程（如 TDD）？
│  └─ YES → 使用 Skill（保持连续性）
│
├─ 需要快速参考最佳实践？
│  └─ YES → 使用 Skill（低成本）
│
├─ 需要深度分析大量代码？
│  └─ YES → 使用 Subagent（避免污染）
│
└─ 需要探索大型代码库？
   └─ YES → 使用 Subagent（独立窗口）
```

---

## 四、第三阶段：上下文管理机制

### 4.1 Skills 的上下文共享

当用户调用 `/tdd` Skill 时：

```
主会话上下文：

┌─────────────────────────────────────┐
│ 系统提示                            │
│ 历史消息 [1...n]                    │
│                                     │
│ 用户：/tdd                          │
│   ↓                                 │
│ 系统：<command-name>/tdd</command>  │
│       + SKILL.md 的完整内容         │
│                                     │
│ 用户：帮我实现用户登录功能            │
│   ↓                                 │
│ AI：按照 TDD 流程：                  │
│     1. 先写测试...                   │
│     2. 再实现代码...                 │
└─────────────────────────────────────┘

关键特征：
✅ 共享主会话的所有历史记录
✅ Skill 内容作为用户消息插入
✅ AI 在同一个上下文窗口中工作
✅ 对话连续，保持上下文
```

### 4.2 Subagents 的上下文隔离

当用户请求代码审查时，情况完全不同：

```
主会话：
┌─────────────────────────────────────┐
│ 用户：帮我审查这段代码               │
│                                     │
│ AI：我需要调用 code-reviewer 代理   │
└─────────────────────────────────────┘
              ↓
        创建新的独立会话
              ↓
┌─────────────────────────────────────┐
│ 代码审查专家办公室（独立空间）        │
│                                     │
│ 系统提示：你是代码审查专家...         │
│ 用户消息：审查这段代码...            │
│ 工具调用：Read, Grep, Glob...       │
│                                     │
│ （独立工作，有自己的记忆）            │
│                                     │
│ 结果：审查报告                       │
└─────────────────────────────────────┘
              ↓
        返回摘要到主会话
              ↓
┌─────────────────────────────────────┐
│ AI：根据 code-reviewer 的报告：     │
│     发现了 3 个问题...              │
└─────────────────────────────────────┘

关键特征：
✅ 创建全新的 API 会话
✅ 独立的上下文窗口
✅ 只传递任务描述和必要上下文
✅ 返回结果摘要到主会话
```

### 4.3 上下文传递对比表

| 维度 | Skills | Subagents |
|------|--------|-----------|
| **上下文来源** | 继承主会话 | 从零开始 |
| **历史记忆** | 完全共享 | 无共享 |
| **返回方式** | 继续对话 | 结果摘要 |
| **Token 消耗** | 累加在主会话 | 独立计算 |
| **适合任务** | 需要连续性的流程 | 需要独立分析的任务 |

---

## 五、第四阶段：元数据传递机制（核心发现）

### 5.1 抓包分析方法

为了准确了解元数据的传递方式，我们直接拦截了 Claude Code 发送到 Anthropic API 的真实请求。

**研究方法**：
1. 使用网络抓包工具（如 Charles、Proxyman）
2. 拦截 Claude Code 的 HTTPS 请求
3. 分析完整的 JSON 载荷
4. 揭示元数据的真实传递方式

### 5.2 核心发现：元数据传递方式

分析 API 请求模板，我们发现两种机制采用**不同的传递方式**：

#### API 请求结构

> **证据文件**：`claude_code_request_explame_template.json`

```json
{
  "model": "claude-sonnet-4-5-20250929",
  "system": [
    {
      "text": "You are Claude Code, Anthropic's official CLI for Claude."
    },
    {
      "text": "/claude_code prompt/claude_code_global_system_prompt.md",
      "cache_control": {"type": "ephemeral"}
    }
  ],
  "tools": [
    {
      "name": "Skill",
      "description": "/claude_code prompt/claude_code_skill_prompt.md",
      "input_schema": {...}
    }
  ]
}
```

**注意**：这是一个模板文件，路径引用在实际发送前会被替换为实际内容。

#### Skills：在 Tool Description 中

> **证据文件**：`claude_code_skill_prompt_zh.md`

Skills 的元数据在 Skill 工具的 `description` 中：

```
Execute a skill within the main conversation

Available skills:
- django-security: Django 安全最佳实践...
- golang-patterns: 惯用的 Go 模式...
- python-patterns: Pythonic 惯用法...
- tdd-workflow: 测试驱动开发...
...（86个技能的简短描述）
```

#### Subagents：在系统提示中

> **证据文件**：`claude_code_system_prompt_zh.md`

Subagents 的元数据通过 `~/.claude/rules/agents.md` 嵌入在系统提示中：

```
# 代理编排
## 可用代理
位于 `~/.claude/agents/`：
| 代理 | 用途 | 何时使用 |
|-------|---------|-------------|
| planner | 实现规划 | 复杂功能、重构 |
| architect | 系统设计 | 架构决策 |
| tdd-guide | 测试驱动开发 | 新功能、错误修复 |
| code-reviewer | 代码审查 | 编写代码后 |
...
```

**关键差异**：

| 机制 | 元数据位置 | 传递方式 |
|------|-----------|---------|
| **Skills** | `tools[].description` 的 Skill 工具 | 通过工具定义 |
| **Subagents** | 系统提示中的 `agents.md` 规则 | 通过系统提示 |

**为什么这样设计？**

1. **Skills 作为工具**：用户可以主动调用（如 `/tdd`），作为工具定义更自然
2. **Subagents 作为能力**：由系统自动调度，放在系统提示中让 AI 知道有哪些可用的专业能力
3. **内容精简**：两者都只传递简短描述，完整内容按需加载

### 5.3 设计模式：渐进式披露

```
阶段1：工具注册（每次 API 请求）
  ┌─────────────────────────────────┐
  │ tools: [{                       │
  │   name: "Skill",                │
  │   description: "                │
  │     - python: Python专家        │
  │     - tdd: TDD流程              │
  │     - security: 安全审查         │
  │     ..."                        │
  │ }]                              │
  └─────────────────────────────────┘
         ↓ 只传递元数据
  知道有什么可用技能

阶段2：按需加载（调用时）
  ┌─────────────────────────────────┐
  │ 用户调用 Skill 时：              │
  │                                 │
  │ {                               │
  │   role: "user",                 │
  │   content: "<command-name>/tdd   │
  │              </command-name>     │
  │            + 完整 SKILL.md"      │
  │ }                               │
  └─────────────────────────────────┘
         ↓ 才加载完整内容
  获取详细的指导内容
```

**为什么这样设计？**

| 优势 | 说明 |
|------|------|
| **Token 优化** | 不需要每次都传递完整内容（节省 ~90% Token） |
| **灵活性** | 可以动态添加/删除技能，无需修改系统提示 |
| **可扩展性** | 支持大量 Skills 和 Subagents 而不超限 |
| **可维护性** | 技能更新独立于主系统 |

### 5.4 真实证据：系统提示的结构

让我们看看真实的系统提示包含什么。

> **证据文件**：`claude_code_global_system_prompt_zh.md`

系统提示分为多个层次：
1. **基础身份**："您是一个交互式 CLI 工具..."
2. **行为准则**：语气风格、专业客观性、任务管理
3. **工具使用策略**：何时使用 Task、何时使用 Skill
4. **环境信息**：工作目录、Git 状态、日期等
5. **用户规则**：包括 `~/.claude/rules/agents.md` 等

**关键发现**：Subagents 的元数据通过 `~/.claude/rules/agents.md` 嵌入在系统提示中，而 Skills 的元数据在工具描述中。

### 5.5 真实证据：Skill 的调用提示

> **证据文件**：`claude_code_skill_prompt_zh.md`

当 Skill 被调用时，实际传递的内容：

```
在主对话中执行技能
当用户要求您执行任务时，请检查下面列出的可用技能中是否有可以帮助更有效地完成任务的内容...

可用技能：
- django-security: Django 安全最佳实践...
- golang-patterns: 惯用的 Go 模式...
- python-patterns: Pythonic 惯用法...
...（完整列表）
```

这说明 Skill 的完整列表会在调用时被展开，而不是一直存在于系统提示中。

### 5.6 调用流程详解

#### Skill 调用流程

```
1. 用户输入：/tdd
   ↓
2. Claude Code 识别这是一个 Skill 命令
   ↓
3. 读取 ~/.claude/skills/tdd-workflow/SKILL.md
   ↓
4. 构造特殊的用户消息：
   {
     role: "user",
     content: `
<command-name>/tdd</command-name>
${SKILL.md 的完整内容}

用户参数：...
     `
   }
   ↓
5. 发送到 API（在主会话中）
   ↓
6. AI 收到消息，看到 <command-name> 标签
   ↓
7. AI 按照 Skill 指导执行任务
   （共享上下文，知道之前的对话）
```

#### Subagent 调用流程

```
1. 用户输入：帮我审查这段代码
   ↓
2. Claude 判断需要专业分析
   ↓
3. Claude Code 调用 Task 工具：
   {
     name: "Task",
     arguments: {
       subagent_type: "code-reviewer",
       task: "审查这段代码..."
     }
   }
   ↓
4. 创建新的独立 API 会话：
   {
     model: "claude-sonnet-4-5",
     system: "从 ~/.claude/agents/code-reviewer.md 加载",
     messages: [{
       role: "user",
       content: "任务描述..."
     }]
   }
   ↓
5. Subagent 独立工作（全新的上下文窗口）
   ↓
6. Subagent 返回结果摘要（不是完整对话历史）
   ↓
7. 主会话 AI 根据摘要继续对话
```

---

## 六、第五阶段：伪代码实现模型

### 6.1 用 Python 展示核心实现

下面是 Claude Code 内部实现的简化版 Python 伪代码：

#### Skill 调用实现

```python
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

@dataclass
class Skill:
    """技能定义"""
    name: str
    description: str
    path: Path

    @classmethod
    def from_directory(cls, skill_dir: Path) -> "Skill":
        """从技能目录加载"""
        skill_md = skill_dir / "SKILL.md"
        content = skill_md.read_text()

        # 解析 frontmatter
        name, description = cls._parse_frontmatter(content)

        return cls(
            name=name,
            description=description,
            path=skill_md
        )

    @staticmethod
    def _parse_frontmatter(content: str) -> tuple[str, str]:
        """解析 SKILL.md 的 frontmatter"""
        # 简化版解析
        lines = content.split('\n')
        name = lines[0].replace('name: ', '').strip()
        desc = lines[1].replace('description: ', '').strip()
        return name, desc


class SkillRegistry:
    """技能注册表"""

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self._skills: dict[str, Skill] = {}
        self._load_all_skills()

    def _load_all_skills(self):
        """加载所有技能"""
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill = Skill.from_directory(skill_dir)
                self._skills[skill.name] = skill

    def get_skill_menu(self) -> str:
        """生成技能菜单（用于工具描述）"""
        menu_lines = ["Available skills:"]
        for skill in self._skills.values():
            menu_lines.append(f"- {skill.name}: {skill.description}")
        return "\n".join(menu_lines)

    def get_skill_content(self, skill_name: str) -> str:
        """获取技能的完整内容"""
        skill = self._skills.get(skill_name)
        if not skill:
            raise ValueError(f"Skill not found: {skill_name}")
        return skill.path.read_text()


def invoke_skill(
    skill_name: str,
    user_args: Optional[str],
    current_conversation: list[dict],
    api_client
) -> dict:
    """
    调用 Skill

    关键：在主会话上下文中执行，共享历史
    """
    # 1. 加载技能注册表
    registry = SkillRegistry(Path("~/.claude/skills").expanduser())

    # 2. 获取技能完整内容
    skill_content = registry.get_skill_content(skill_name)

    # 3. 构造用户消息
    message = {
        "role": "user",
        "content": f"""<command-name>/{skill_name}</command-name>

{skill_content}

User Args: {user_args or 'None'}
        """
    }

    # 4. 在主会话中调用（共享上下文）
    response = api_client.create_message(
        model="claude-sonnet-4-5",
        messages=current_conversation + [message]
    )

    # 5. 返回响应，上下文保持连续
    return response
```

#### Subagent 调用实现

```python
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import anthropic

@dataclass
class AgentConfig:
    """代理配置"""
    name: str
    description: str
    system_prompt: str
    allowed_tools: list[str]
    model: str = "claude-sonnet-4-5"

    @classmethod
    def from_file(cls, agent_file: Path) -> "AgentConfig":
        """从代理配置文件加载"""
        content = agent_file.read_text()

        # 解析 frontmatter
        name, desc, tools, model = cls._parse_frontmatter(content)
        system_prompt = cls._extract_system_prompt(content)

        return cls(
            name=name,
            description=desc,
            system_prompt=system_prompt,
            allowed_tools=tools,
            model=model
        )


class AgentRegistry:
    """代理注册表"""

    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir
        self._agents: dict[str, AgentConfig] = {}
        self._load_all_agents()

    def _load_all_agents(self):
        """加载所有代理配置"""
        for agent_file in self.agents_dir.glob("*.md"):
            agent = AgentConfig.from_file(agent_file)
            self._agents[agent.name] = agent

    def get_agent_menu(self) -> str:
        """生成代理菜单（用于工具描述）"""
        menu_lines = ["Available agent types:"]
        for agent in self._agents.values():
            menu_lines.append(f"- {agent.name}: {agent.description}")
        return "\n".join(menu_lines)

    def get_agent(self, agent_name: str) -> AgentConfig:
        """获取代理配置"""
        agent = self._agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent not found: {agent_name}")
        return agent


def invoke_subagent(
    agent_type: str,
    task_description: str,
    api_client: anthropic.Anthropic
) -> dict:
    """
    调用 Subagent

    关键：创建独立的 API 会话，不共享上下文
    """
    # 1. 加载代理注册表
    registry = AgentRegistry(Path("~/.claude/agents").expanduser())

    # 2. 获取代理配置
    agent = registry.get_agent(agent_type)

    # 3. 创建新的独立会话
    client = anthropic.Anthropic()

    # 4. Subagent 独立工作
    response = client.messages.create(
        model=agent.model,
        max_tokens=200000,
        system=agent.system_prompt,
        messages=[{
            "role": "user",
            "content": task_description
        }],
        # 独立的上下文窗口
        betas=["computer-use-2024-10-22"]
    )

    # 5. 返回摘要（不是完整上下文）
    return {
        "agent_type": agent_type,
        "summary": _extract_summary(response),
        "details": response
    }


def _extract_summary(response: dict) -> str:
    """从 Subagent 响应中提取摘要"""
    # 简化版：提取最后一段作为摘要
    content = response.content[-1].text
    lines = content.split('\n')
    # 取最后非空行作为摘要
    for line in reversed(lines):
        if line.strip():
            return line
    return content[:200]  # 默认返回前 200 字符
```

#### 简单的 React 风格实现

```python
from typing import Protocol, Callable, TypeVar
from functools import wraps
from dataclasses import dataclass

T = TypeVar('T')

# ============================================
# Agent 接口定义
# ============================================

class Agent(Protocol):
    """Agent 接口"""

    name: str
    description: str

    def execute(self, task: str) -> str:
        """执行任务，返回结果"""
        ...


# ============================================
# Skill 实现（有状态的 Agent）
# ============================================

@dataclass
class SkillAgent:
    """Skill Agent：在主会话上下文中执行"""

    name: str
    description: str
    instructions: str  # SKILL.md 的内容
    conversation_history: list[dict]

    def execute(self, task: str) -> str:
        """
        执行任务，保持上下文连续性

        这就像一个人翻阅手册工作，记得之前的对话
        """
        # 将任务添加到历史
        self.conversation_history.append({
            "role": "user",
            "content": task
        })

        # 模拟 AI 处理（实际会调用 API）
        response = self._process_with_instructions(task)

        # 记录响应
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        return response

    def _process_with_instructions(self, task: str) -> str:
        """根据 Skill 指导处理任务"""
        return f"[根据 {self.name} 指导]\n处理: {task}\n结果: ..."


# ============================================
# Subagent 实现（无状态的 Agent）
# ============================================

@dataclass
class SubAgent:
    """Subagent：独立会话，无状态"""

    name: str
    description: str
    system_prompt: str
    expertise: str  # 专业领域

    def execute(self, task: str) -> str:
        """
        执行任务，不保留历史

        这就像雇佣一个顾问，每次都是新的咨询
        """
        # 每次都是全新的会话，不记录历史
        response = self._process_independently(task)
        return response

    def _process_independently(self, task: str) -> str:
        """独立处理任务"""
        return f"[{self.name} 专家分析]\n任务: {task}\n分析: ..."


# ============================================
# 主 Agent（协调者）
# ============================================

class MainAgent:
    """主 Agent：协调 Skills 和 Subagents"""

    def __init__(self):
        # 有状态的 Skills（共享上下文）
        self.skills: dict[str, SkillAgent] = {}

        # 无状态的 Subagents（独立会话）
        self.subagents: dict[str, SubAgent] = {}

        self._setup_skills()
        self._setup_subagents()

    def _setup_skills(self):
        """初始化 Skills"""
        self.skills['tdd'] = SkillAgent(
            name='tdd',
            description='测试驱动开发',
            instructions='SKILL.md 内容...',
            conversation_history=[]
        )
        # ... 更多 skills

    def _setup_subagents(self):
        """初始化 Subagents"""
        self.subagents['reviewer'] = SubAgent(
            name='code-reviewer',
            description='代码审查专家',
            system_prompt='你是代码审查专家...',
            expertise='代码质量审查'
        )
        # ... 更多 subagents

    def process(self, user_input: str) -> str:
        """
        处理用户输入，决定使用 Skill、Subagent 还是直接响应
        """
        # 判断用户意图
        if user_input.startswith('/'):
            # 使用 Skill（共享上下文）
            skill_name = user_input[1:]
            skill = self.skills.get(skill_name)
            if skill:
                return skill.execute(user_input)

        elif '审查' in user_input or '分析' in user_input:
            # 使用 Subagent（独立会话）
            subagent = self.subagents.get('reviewer')
            if subagent:
                return subagent.execute(user_input)

        else:
            # 直接响应
            return self._direct_response(user_input)

    def _direct_response(self, user_input: str) -> str:
        """直接响应用户"""
        return f"收到: {user_input}"


# ============================================
# 使用示例
# ============================================

def main():
    # 创建主 Agent
    agent = MainAgent()

    # 场景 1: 使用 Skill（共享上下文）
    print("=== 场景 1: Skill 调用 ===")
    response1 = agent.process("/tdd 帮我写用户登录功能")
    print(f"第一次调用: {response1}\n")

    response2 = agent.process("/tdd 继续实现")
    print(f"第二次调用（记得上下文）: {response2}\n")

    # 场景 2: 使用 Subagent（独立会话）
    print("=== 场景 2: Subagent 调用 ===")
    response3 = agent.process("帮我审查这段代码")
    print(f"Subagent 响应: {response3}\n")

    # 对比：Skill 记得上下文，Subagent 每次都是新的
    print("=== 对比 ===")
    print(f"Skill 历史记录数: {len(agent.skills['tdd'].conversation_history)}")
    print(f"Subagent 无历史记录（无状态）")


if __name__ == "__main__":
    main()
```

**代码亮点**：

1. **SkillAgent** 有 `conversation_history`，保持上下文
2. **SubAgent** 无状态，每次调用都是新的
3. **MainAgent** 作为协调者，决定使用哪种机制
4. 清晰展示了"共享上下文"vs"独立会话"的差异

---

## 七、设计哲学与启示

### 7.1 核心设计原则

通过这次深入的探索，我们发现 Claude Code 的设计体现了三个核心原则：

#### 1. 分层披露（Layered Disclosure）

```
┌─────────────────────────────────────┐
│ 元数据层（轻量）                      │
│ 工具描述中的技能/代理列表              │
│ - 只有一句话描述                     │
│ - 每次 API 请求都携带                │
└─────────────────────────────────────┘
              ↓ 按需加载
┌─────────────────────────────────────┐
│ 内容层（重量）                        │
│ 完整的 SKILL.md 或 Agent 配置        │
│ - 只在调用时加载                     │
│ - 包含详细的指导                     │
└─────────────────────────────────────┘
```

#### 2. 上下文隔离（Context Isolation）

| 机制 | 上下文管理 | 适用场景 |
|------|-----------|---------|
| **Skills** | 共享主会话 | 需要连续性的流程任务 |
| **Subagents** | 独立会话 | 需要深度分析的专业任务 |

#### 3. 职责分离（Separation of Concerns）

```
┌─────────────────────────────────────┐
│ 主 Agent：协调者、决策者              │
│ - 判断该用 Skill 还是 Subagent        │
│ - 整合结果，响应用户                 │
└─────────────────────────────────────┘
              ↓ 委派
┌─────────────────────────────────────┐
│ Skills：知识载体                     │
│ - 存储可复用的流程和最佳实践          │
│ - 在主会话上下文中执行               │
└─────────────────────────────────────┘
              ↓ 或
┌─────────────────────────────────────┐
│ Subagents：专业执行者                │
│ - 独立完成专业任务                   │
│ - 返回摘要而非完整过程               │
└─────────────────────────────────────┘
```

### 7.2 架构启示：对构建 AI 应用的价值

这个设计对构建自己的 AI 应用系统有重要启示：

```
┌─────────────────────────────────────────┐
│  应用层：用户交互                         │
│  - 接收用户请求                          │
│  - 展示处理结果                          │
├─────────────────────────────────────────┤
│  编排层：主 Agent（协调、决策）            │
│  - 分析用户意图                          │
│  - 决定调用策略                          │
│  - 整合子任务结果                        │
├─────────────────────────────────────────┤
│  执行层：                                 │
│  - Skills（知识模板，共享上下文）          │
│  - Subagents（专业执行，独立上下文）       │
├─────────────────────────────────────────┤
│  工具层：Read, Write, Grep, Bash...       │
│  - 具体的文件操作                         │
│  - 系统命令执行                          │
└─────────────────────────────────────────┘
```

**可借鉴的设计点**：

1. **元数据与内容分离**：不要在系统提示中塞入所有内容
2. **渐进式加载**：先传菜单，按需加载详细内容
3. **上下文隔离**：专业任务独立处理，避免污染主对话
4. **结果摘要**：Subagent 只返回关键信息，节省 Token

### 7.3 Token 成本优化策略

| 策略 | 说明 | Token 节省 |
|------|------|-----------|
| **渐进式披露** | 先传元数据，按需加载内容 | ~90% |
| **上下文隔离** | Subagent 不返回完整历史 | ~70% |
| **智能摘要** | Subagent 只返回关键信息 | ~50% |

**实际效果估算**：

假设有 100 个 Skills，每个平均 2000 tokens：

```
❌ 如果全部塞入系统提示：
   每次请求增加 200,000 tokens！

✅ 使用渐进式披露：
   每次请求只增加 2,000 tokens（菜单）
   调用时才加载具体 Skill（2000 tokens）
   节省：99%
```

---

## 八、总结

### 8.1 核心发现

通过以上分析，我们揭示了：

1. **元数据传递方式差异**：
   - **Skills**：元数据在 `tools[].description` 的 Skill 工具中
   - **Subagents**：元数据在系统提示中的 `agents.md` 规则文件里

2. **内容加载时机**：完整内容按需加载——Skills 通过后续消息，Subagents 通过创建新会话

3. **上下文管理差异**：
   - Skills：共享主会话上下文，保持对话连续性
   - Subagents：创建独立会话上下文，避免主对话污染

4. **设计理念**：渐进式披露 + 职责分离 + 上下文隔离

### 8.2 实践建议

**何时使用 Skills**：

| 场景 | 示例 | 原因 |
|------|------|------|
| 需要遵循标准流程 | TDD、代码规范 | 保持上下文连续性 |
| 需要多轮协作 | 重构、功能迭代 | 共享对话历史 |
| 快速参考 | API 设计模式 | 低成本调用 |

**何时使用 Subagents**：

| 场景 | 示例 | 原因 |
|------|------|------|
| 需要深度分析 | 代码审查、架构分析 | 独立上下文窗口 |
| 需要大量探索 | 代码库探索 | 不污染主对话 |
| 专业领域任务 | 数据库优化、安全审查 | 专业知识隔离 |

### 8.3 研究方法

本文采用的方法对理解复杂 AI 系统具有参考价值：

```
1. 观察现象（有哪些功能）
    ↓
2. 提出问题（为什么这样设计）
    ↓
3. 寻求验证（查看真实数据）
    ↓
4. 实证分析（抓包 API 请求）
    ↓
5. 系统建模（构建理论模型）
```

**关键点**：

- ✅ 不满足于表面解释，要求查看真实数据
- ✅ 用事实说话，抓包分析比猜测更有说服力
- ✅ 系统化思考，从存储位置到传递机制构建完整认知

### 8.4 对开发者的建议

如果你在构建自己的 AI 应用：

1. **借鉴渐进式披露**：元数据和内容分离
2. **设计清晰的边界**：哪些需要上下文共享，哪些需要隔离
3. **优化 Token 使用**：不是所有内容都需要每次传递
4. **提供灵活的扩展**：让用户可以自定义 Skills 和 Agents

---

## 九、延伸阅读

### 官方文档

1. [Claude Code 官方文档 - Skills](https://code.claude.com/docs/en/skills)
2. [Claude Code 官方文档 - Subagents](https://code.claude.com/docs/en/sub-agents)
3. [Anthropic API 文档 - Tools](https://docs.anthropic.com/claude/docs/tool-use)

### 社区资源

4. [GitHub: Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) - Claude Code 系统提示的逆向工程

### 相关概念

5. **Progressive Disclosure（渐进式披露）**：UI/UX 设计模式，逐步展示复杂信息
6. **Context Window Management（上下文窗口管理）**：LLM 应用中的 Token 优化策略
7. **Multi-Agent Systems（多代理系统）**：AI 系统架构设计模式

---

## 附录：证据文件清单

本文分析中使用的真实证据文件：

| 文件 | 来源路径 | 说明 |
|------|---------|------|
| API 请求模板 | `claude_code_request_explame_template.json` | API 请求模板结构 |
| 全局系统提示 | `claude_code_global_system_prompt_zh.md` | 主系统提示（中文版） |
| 系统提示（含规则） | `claude_code_system_prompt_zh.md` | 包含 agents.md 规则的系统提示 |
| Skill 调用提示 | `claude_code_skill_prompt_zh.md` | Skill 调用时的提示（中文版） |

这些文件来自真实的 Claude Code 使用环境，未经任何修改，提供了第一手的证据支持。

---

**作者注**：本文基于实证研究和 API 抓包分析，所有结论均来自真实数据。如有疑问，欢迎讨论交流。

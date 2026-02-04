# Claude Code 提示词解密

本目录包含对 Claude Code 的 Skills 和 Subagents 机制的深入分析和研究。

## 主要文档

- [Claude Code 提示词解密](./【分享版】Claude Code 提示词解密.md) - Skills 和 Subagents 工作原理详解

## 证据文件

本目录包含真实的 API 请求和系统提示词证据：

- `claude_code_request_explame_template.json` - API 请求模板结构
- `claude_code_global_system_prompt_zh.md` - 全局系统提示（中文版）
- `claude_code_system_prompt_zh.md` - 系统提示（含 agents.md 规则）
- `claude_code_skill_prompt_zh.md` - Skill 调用提示（中文版）

## 核心发现

### 元数据传递方式

| 机制 | 元数据位置 | 传递方式 |
|------|-----------|---------|
| **Skills** | `tools[].description` 的 Skill 工具 | 通过工具定义 |
| **Subagents** | 系统提示中的 `agents.md` 规则 | 通过系统提示 |

### 上下文管理差异

| 机制 | 上下文来源 | 历史记忆 | 返回方式 |
|------|-----------|---------|---------|
| **Skills** | 继承主会话 | 完全共享 | 继续对话 |
| **Subagents** | 从零开始 | 无共享 | 结果摘要 |

## 相关项目

- [cursor-prompt-deep-dive](../cursor-prompt-deep-dive/) - Cursor 提示词解密

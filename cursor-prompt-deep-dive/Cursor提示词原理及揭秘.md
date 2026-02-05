# Cursor 提示词抓取与解密


## 1. 背景


我们想做的是一个面向**备课场景**的 Agent 助手：能基于已有的课件做AI的编辑和优化，类似cursor的agent模式，例如：

[点击观看演示视频](./assets/agent演示.mp4)

- 结合新课标优化课件（总结课件内容->联网检索新课标内容->分析优化思路->优化课件（文生图、视频、课件页、课堂活动、智能体等等））
- 自由的对话，回答老师的问题，总结课件内容，单点工具调用
- 使用react和plan模式，完成复杂任务的编辑和实现

做这类 Agent 时，最大的风险不是“模型不够聪明”，而是**系统设计不够工程化**：上下文怎么组织？工具怎么定义？输出怎么保证可解析？失败怎么回到闭环？这些都不是靠一句 prompt 能解决的。



### 可以参考优秀的软件是怎么设计的，比如cursor

Cursor 是少数把 IDE 场景 Agent 跑得比较顺的产品。我们抓取提示词不是为了“复制一段 system”，而是为了把它的机制拆开看清楚：

- **它每一轮到底给模型喂了什么**（system / messages / tools）？
- **这些东西怎么一起工作**，让模型在 IDE 里读/搜/改/验更稳定？
- **Plan / Agent 模式为什么会让行为明显不一样**？

> 但是cursor是一个黑盒，无法直接看到prompt是怎么发送和工作的，我们要做的就是怎么把这个黑盒变成可观测。
>

---





## 2. 抓取Cursor 的提示词

### 2.1 原理：在 Cursor 与自定义模型之间加一个“代理观察点”


> 我们能做这件事，靠的是 Cursor 支持配置 OpenAI 兼容的自定义接口（Base URL）。  
通过我们的抓包分析，当你把 Base URL 指向我们自己的服务时，链路更接近：

- **本地 Cursor（IDE）→ Cursor 后端服务 → 我们的代理（抓取点）→ 真实模型**

也就是说：IDE 侧触发请求后，Cursor 的后端会向我们配置的 Base URL 发起 `POST /v1/chat/completions`；我们在代理侧记录请求体并转发给真实模型，响应再按原路回传。

![image-20251218144802773](./assets/cursor-自定义端点配置.png)

```mermaid
sequenceDiagram
  participant U as 用户
  participant IDE as Cursor（IDE）
  participant BE as Cursor后端服务
  participant P as 我们的代理（抓取点）
  participant M as 真实模型（Qwen/GPT-4.1）

  U->>IDE: 输入需求
  IDE->>BE: 触发请求
  BE->>P: POST /v1/chat/completions（system/messages/tools）
  P->>P: 记录请求体（json/jsonl）
  P->>M: 转发请求
  M-->>P: 返回响应（可能包含 tool_calls）
  P-->>BE: 回传响应
  BE-->>IDE: 回传响应
  IDE-->>U: 展示结果
```



### 2.2 本地小模型尝试代理cursor的流量（Ollama + Qwen2.5:7b + ngrok）

#### ngrok 的原理与作用（为什么它是本文的核心组件）

- 什么是 ngrok：一个“反向隧道”服务。它通过本地客户端与云端建立持久的出站连接，为你的本地端口（如 4000/11434）分配一个公网可访问的地址（如 https://xxxx.ngrok-free.dev）。外部对该公网地址的 HTTP 请求，会被安全地转发到你的本地服务。
- 工作原理（简化）：
  - 本地启动 ngrok 客户端，建立到 ngrok 云端的持久连接（TLS）。
  - ngrok 云端分配子域名，并把到该域名的外部请求经隧道转发到你的本地端口。
  - ngrok Inspector（默认 http://127.0.0.1:4040）提供“抓包/回放”，可查看请求/响应的头、体、源 IP、延迟等。
- 在本文链路中的作用：
  - 让 Cursor 后端服务能够访问你本地的代理服务（LiteLLM/Ollama），无需公网服务器。
  - 作为“最靠近 Cursor 后端的一层观察点”，直接看到完整请求体（system/messages/tools）和响应，是提示词解密的关键抓手。
  - 快速调试与对比：可以在不改 Cursor 客户端的情况下，切换不同上游模型，观察 Agent/Plan 模式差异。
- 关键特性与注意事项：
  - 通道类型：常用的是 `ngrok http http://localhost:PORT`（HTTP 隧道）；也支持 TCP 隧道，IDE 场景通常 HTTP 即可。
  - 安全：隧道地址对公网可见，避免暴露敏感接口；可通过 ngrok 的 authtoken、Basic Auth、IP 白名单等方式做保护；严禁把真实 API Key 写入文档/代码。
  - 时延与稳定性：经云端中转会增加 RTT，适合开发/调试，不建议直接用于生产；生产可考虑 Cloudflare Tunnel/自建反向代理。
  - 速率限制：免费域名存在速率/带宽限制，大量抓包时可能限流。
  - 抓包隐私：Inspector 会保存请求/响应体，注意清理或脱敏。

```mermaid
sequenceDiagram
  participant CB as Cursor后端
  participant NG as ngrok云端
  participant LP as 本地代理（LiteLLM/Ollama）

  CB->>NG: POST https://xxxx.ngrok-free.dev/v1/chat/completions
  NG->>LP: 转发到 http://localhost:4000/v1/chat/completions
  LP-->>NG: 返回响应（可能包含 tool_calls）
  NG-->>CB: 回传响应
  Note over NG,LP: Inspector 可查看完整请求/响应
```


> 参考文章：`https://zhuanlan.zhihu.com/p/1897219344594888402`



#### 实验步骤（尽量按这个顺序做）

1. **安装并启动 Ollama**

```bash
brew install ollama
ollama pull qwen2.5:7b
ollama run qwen2.5:7b

curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "用一句话介绍 Ollama"
}'

# 让服务监听 0.0.0.0，便于 ngrok 转发（默认可能只监听 127.0.0.1）
OLLAMA_HOST=0.0.0.0 ollama serve
```

![image-20251218150502859](./assets/ollama启动.png)

![image-20251218150936771](./assets/本地调用.png)

2. **用 ngrok 暴露 Ollama 端口**

```bash
brew install ngrok
ngrok http http://localhost:11434

curl https://uneugenically-unstatable-thaddeus.ngrok-free.dev/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "写一个冒泡排序算法"
}'
```

启动后注意两点：

- ngrok 会给你一个公网地址（`https://YOUR_NGROK_URL`）
- ngrok 的抓包界面一般在 `http://127.0.0.1:4040`

![image-20251218150657650](./assets/ngrok%20代理.png)

![image-20251218151039830](./assets/公网调用.png)



3. **在 Cursor 里把模型 Base URL 指向 ngrok**

在 Cursor 的 Models 配置里新增/选择自定义模型：

- Model name：`qwen2.5:7b`
- Base URL：`https://YOUR_NGROK_URL/v1`
- API Key：随便填（如果后端不校验）

![image-20251218173306986](./assets/配置自定义模型.png)

4. **触发一次请求，并在 ngrok Inspector 里看请求体**

随便发起一个问题（建议用 Agent 模式发起一次“读/改/验证”类需求），然后去 `http://127.0.0.1:4040` 看 `POST /v1/chat/completions` 的请求体。

跑通后我们在抓包/代理侧会看到两个非常直观的现象：

- `messages[0]` 是一段很长的 system（里面不是一句话，而是一堆规则、格式、工具说明）；
- 很多请求里还会出现 `tools`（取决于模式、模型与配置），也就是 Cursor 把“能用的工具说明书”一起发给模型。

![image-20251218175926809](./assets/详细请求信息.png)

另外从抓包里还能看到：**发往我们 Base URL 的请求源并不是本机**（ngrok Inspector 会显示 remote addr/地理位置等信息）。结合现象与链路推断，我们认为这一步请求是由 **Cursor 的后端服务**代发的。

![image-20251218175217833](./assets/请求源ip信息.png)

但现在问题也很明显：小模型经常“理解不了这套复杂协议”，常见表现是：

- 对话里错误多、格式不稳定；
- 工具调用很难有效跑起来（要么不按 schema，要么根本不走 tool_calls）。

![image-20251218174656371](./assets/cursor截图.png)

> 这个时候其实能够看到提示词的整体框架，但是对于工具的调用细节其实很不清晰，因为模型的能力，没法按照正常的情况输出

那如果换成大模型的话，我们本地又无法部署大尺寸模型，该怎么办呢？

![image-20251218200241147](./assets/抓取流程分析.png)


### 2.3 换大模型接口，把“可用样本”抓出来（LiteLLM proxy + ngrok + GPT-5）

这一步我们把本地代理换成 LiteLLM 的 OpenAI 兼容代理，让 Cursor 仍然以 OpenAI 风格请求；区别是上游走 `gpt-5`（同级模型也可以）。

#### 实验步骤（推荐用 LiteLLM 自带 proxy，更贴近“OpenAI 兼容”这条路）

1. **安装 LiteLLM proxy**（对应 `litellm/LiteLLM本地部署方案.md`）

```bash
pip install 'litellm[proxy]'
```

2. **准备 Key（用环境变量注入，避免写进文档/配置）**

```bash
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

> 注意：不要把真实 Key 写进文档/配置并分享或提交。

3. **核心代理代码**（对应 `litellm/server.py`）

```python
import traceback
import json
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import litellm

# 开启 litellm 调试
litellm.set_verbose = True

# API 配置（请用环境变量注入，避免硬编码泄漏）
# - 下游真实模型的鉴权 key（如需）
API_KEY = os.getenv("UPSTREAM_API_KEY", "")

# 模型配置
MODEL_CONFIG = {
    "gpt-5": {
        # 下游真实模型的 base url（示例占位，按实际环境设置）
        "api_base": os.getenv("UPSTREAM_API_BASE_GPT5", "http://YOUR_UPSTREAM_API_BASE"),
        "model": "gpt-5"
    }
}

app = FastAPI(title="LiteLLM Proxy Server")


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    try:
        body = await request.json()
        model = body.get("model") or "gpt-5"
        messages = body.get("messages", [])
        stream = body.get("stream", False)
        tools = body.get("tools")
        tool_choice = body.get("tool_choice")
        user = body.get("user")

        # 清理 messages：移除空的 tool_calls
        cleaned_messages = []
        for msg in messages:
            cleaned_msg = {k: v for k, v in msg.items() if k != "tool_calls" or (v and len(v) > 0)}
            cleaned_messages.append(cleaned_msg)

        messages = cleaned_messages

        # 获取模型配置
        config = MODEL_CONFIG.get(model, MODEL_CONFIG["gpt-5"])

        # 移除不需要的参数
        extra_params = {k: v for k, v in body.items() if k not in ["model", "messages", "stream", "tools", "tool_choice", "user"]}

        if stream:
            # 流式响应
            async def generate():
                response = await litellm.acompletion(
                    model=config["model"],
                    messages=messages,
                    api_key=API_KEY,
                    api_base=config["api_base"],
                    stream=True,
                    tools=tools,
                    tool_choice=tool_choice,
                    user=user,
                    **extra_params
                )
                async for chunk in response:
                    if hasattr(chunk, "model_dump_json"):
                        payload = chunk.model_dump_json()
                    else:
                        payload = json.dumps(chunk, ensure_ascii=False)
                    yield f"data: {payload}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            # 非流式响应
            response = await litellm.acompletion(
                model=config["model"],
                messages=messages,
                api_key=API_KEY,
                api_base=config["api_base"],
                tools=tools,
                tool_choice=tool_choice,
                user=user,
                **extra_params
            )
            return JSONResponse(content=response.model_dump())

    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e), "type": "server_error"}}
        )


@app.get("/v1/models")
async def list_models():
    return JSONResponse(content={
        "object": "list",
        "data": [
            {"id": "gpt-5", "object": "model", "owned_by": "openai"}
        ]
    })


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
```

4. **启动 LiteLLM proxy（本地监听 4000）**（对应 `litellm/LiteLLM本地部署方案.md`）

```bash
cd "./litellm"
litellm --config config.yaml --port 4000 --detailed_debug
```

服务启动后，代理地址为：`http://localhost:4000`  

5. **先用 curl 验证代理是通的（核心“代码”就是这份请求体）**（对应 `litellm/LiteLLM本地部署方案.md`）

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

6. **用 ngrok 暴露 4000**

```bash
ngrok http http://localhost:4000
```

7. **Cursor 指向 ngrok 的 `/v1`**

- Base URL：`https://YOUR_NGROK_URL/v1`
- Model：`gpt-5`（与 `config.yaml` 的 `model_name` 一致）

8. **触发请求，抓取完整请求包**

抓取点有两个：

- **ngrok Inspector**：直接看到 **Cursor 后端 → 我们代理** 的请求体（最直观）




## 第三部分：Cursor 提示词解密

### 3.1 先从样本建立直觉：一轮请求包由什么组成？

打开抓取到的 JSON 样本，至少能看到三块：

- `model`
- `messages`（system + 多轮历史 + IDE 注入上下文）
- `tools`（工具定义与 schema）

结构上可以这样理解：

```text
Request Payload（第 N 轮）
├─ model
├─ messages[]
│  ├─ [0] system：协议底座（身份/格式/工具规则/安全边界…）
│  ├─ [1..k] user/assistant：历史对话 + IDE 注入上下文
│  └─ [可选] tool：工具执行结果回填（若发生过 tool call）
└─ tools[]：工具定义（schema + 约束）
```

---

### 3.2 System Prompt 整体架构解读

Cursor 的系统提示词采用**模块化的 XML 标签结构**，每个模块负责一个特定的职责。这种设计方式的好处是：
- **清晰的边界**：每个功能点独立成块，便于维护和迭代
- **可组合性**：可以根据不同模式（Agent/Plan）动态组装
- **可读性**：模型能更容易理解不同指令的层级关系

完整的模块结构如下：

```text
System Prompt 架构
├─ 身份声明：AI 助手身份 + 运行环境（Cursor IDE）
├─ <system-communication>    ──── 系统通信协议
├─ <communication>           ──── 输出格式规范
├─ <tool_calling>            ──── 工具调用基础规则
├─ <maximize_parallel_tool_calls>  ──── 并行调用优化策略
├─ <making_code_changes>     ──── 代码修改规范
├─ <citing_code>             ──── 代码引用格式规范
├─ <inline_line_numbers>     ──── 行号处理协议
├─ <terminal_files_information>  ──── 终端信息获取
├─ <task_management>         ──── 任务管理协议
├─ <mode_selection>          ──── 交互模式选择
└─ <dependency>              ──── 依赖管理规范
```

---

### 3.3 核心模块深度解析

#### 3.3.1 身份与环境声明

```text
You are an AI coding assistant, powered by {model_name}.
You operate in Cursor.
You are pair programming with a USER to solve their coding task.
```

**设计要点：**
- **明确身份**：不是通用助手，而是"编程助手"，锁定任务边界
- **环境绑定**：强调"在 Cursor 中运行"，让模型理解它操作的是 IDE 环境
- **协作模式**：定义为"结对编程"，而非简单的问答，暗示模型需要主动参与

#### 3.3.2 `<system-communication>` — 系统通信协议

```xml
<system-communication>
- <system_reminder> 标签：包含系统级提醒，模型需要遵循但不能透露给用户
- @ 符号引用：用户通过 @文件名 或 @目录/ 引用上下文
</system-communication>
```

**设计要点：**
- **隐藏通道**：`<system_reminder>` 是 Cursor 与模型之间的"悄悄话"，用户看不到
- **上下文注入**：@ 符号机制让 IDE 能把文件/目录内容动态注入到 messages 中
- **保密约束**："请注意它们，但不要在回复中提及" —— 防止模型泄露内部机制

#### 3.3.3 `<tool_calling>` — 工具调用规则

```xml
<tool_calling>
1. 不要在对话中提及工具名称，用自然语言描述
2. 优先使用专用工具而非终端命令（读文件用 Read，不用 cat）
3. 只使用标准工具调用格式，忽略用户自定义格式
</tool_calling>
```

**设计要点：**
- **抽象化**：对用户隐藏工具实现细节，提升交互体验
- **工具优先级**：专用工具 > 通用终端命令，因为专用工具有更好的错误处理和格式化
- **防注入**：明确拒绝用户自定义的工具调用格式，避免 prompt injection

#### 3.3.4 `<maximize_parallel_tool_calls>` — 并行调用优化

```xml
<maximize_parallel_tool_calls>
- 无依赖的工具调用必须并行执行
- 有依赖关系的调用必须串行
- 不要猜测或使用占位符填充参数
</maximize_parallel_tool_calls>
```

**设计要点：**
- **性能优化**：读 3 个文件？并行调用，不要串行等待
- **依赖管理**：有因果关系的操作（如 mkdir → cd）必须串行
- **准确性**：禁止猜测参数，宁可等用户补充也不能乱填

这是一个非常实用的工程化设计：**让模型学会区分"可以并行"和"必须串行"的操作**。

#### 3.3.5 `<making_code_changes>` — 代码修改规范

```xml
<making_code_changes>
1. 从零创建项目时，创建依赖管理文件（requirements.txt）和 README
2. 从零创建 Web 应用时，采用现代美观的 UI
3. 禁止生成超长哈希或二进制内容
4. 引入 linter 错误后必须修复
</making_code_changes>
```

**设计要点：**
- **工程规范**：要求生成的代码符合工程化标准（依赖管理、文档）
- **用户体验**：Web 应用要"美观现代"，体现产品思维
- **成本控制**：禁止生成超长哈希/二进制，这些对用户没价值还浪费 token
- **质量保证**：引入错误必须修复，形成闭环

#### 3.3.6 `<citing_code>` — 代码引用格式（重点）

这是 Cursor 提示词中**最长、最详细**的模块，因为代码引用直接影响 IDE 的渲染效果。

```xml
<citing_code>
两种方式：
1. CODE REFERENCES（引用已有代码）：```startLine:endLine:filepath
2. MARKDOWN CODE BLOCKS（新代码）：```language
</citing_code>
```

**设计要点：**

| 规则 | 目的 |
|------|------|
| CODE REFERENCES 必须包含行号和路径 | 让 IDE 能精确定位并高亮源文件 |
| MARKDOWN CODE BLOCKS 只用语言标签 | 区分"现有代码"和"新建议代码" |
| 禁止混用两种格式 | 防止 IDE 渲染异常 |
| 代码块前必须空行 | 确保 markdown 解析正确 |
| 三反引号不能缩进 | 防止被误解析为代码内容 |

**大量的 good-example / bad-example 对比**是这个模块的特色，说明 Cursor 团队在这里踩过很多坑。

#### 3.3.7 `<terminal_files_information>` — 终端状态获取

```xml
<terminal_files_information>
- terminals 文件夹存放终端状态快照（文本文件）
- 文件命名：$id.txt（IDE内终端）/ ext-$id.txt（外部终端）
- 内容包括：cwd、最近命令、运行状态、完整输出
- 不要向用户提及这个文件夹
</terminal_files_information>
```

**设计要点：**
- **状态持久化**：把终端状态导出为文件，模型可以用 Read 工具读取
- **异步可观测**：即使命令还在运行，模型也能读取当前输出
- **内外统一**：IDE 内终端和外部终端（iTerm 等）用同一套机制

这解决了一个关键问题：**模型如何知道终端里发生了什么？**

#### 3.3.8 `<task_management>` — 任务管理

```xml
<task_management>
- 有 todo_write 工具可用
- 复杂任务时使用，简单任务跳过
- 在完成所有 todo 之前不要结束回合
</task_management>
```

**设计要点：**
- **任务拆解**：复杂任务自动拆成 todo 列表
- **进度跟踪**：确保每个 todo 都完成才算结束
- **轻量化**：简单任务不强制使用，避免过度工程化

#### 3.3.9 `<mode_selection>` — 模式选择

```xml
<mode_selection>
- 根据目标选择最佳交互模式
- Plan 模式：任务大/模糊/有权衡时使用
- 可调用 SwitchMode 工具切换
</mode_selection>
```

**设计要点：**
- **自适应**：模型能根据任务复杂度自动选择模式
- **Plan 模式触发条件**：大任务、模糊需求、有 trade-off
- **主动性**：鼓励模型主动切换模式，而非等用户指示

---

### 3.4 工具定义（Tools）分析

除了 system prompt，请求体中还有 `tools` 字段，定义了模型可以调用的工具。

#### 3.4.1 工具定义结构

每个工具遵循 OpenAI Function Calling 的 JSON Schema 格式：

```json
{
  "type": "function",
  "function": {
    "name": "read_file",
    "description": "读取指定路径的文件内容",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string",
          "description": "文件的绝对路径"
        },
        "offset": {
          "type": "number",
          "description": "起始行号（可选）"
        },
        "limit": {
          "type": "number",
          "description": "读取行数（可选）"
        }
      },
      "required": ["path"]
    }
  }
}
```

#### 3.4.2 Cursor 常见工具类型

| 工具类型 | 典型工具 | 用途 |
|---------|---------|------|
| **文件操作** | Read, Write, StrReplace, Delete | 读写编辑删除文件 |
| **搜索类** | Grep, Glob, SemanticSearch | 按内容/模式/语义搜索 |
| **终端操作** | Shell | 执行 shell 命令 |
| **导航类** | LS | 列出目录内容 |
| **任务管理** | TodoWrite | 管理任务列表 |
| **模式切换** | SwitchMode | 切换 Agent/Plan 模式 |
| **子任务** | Task | 启动子 Agent 处理复杂任务 |

#### 3.4.3 工具设计的工程智慧

1. **原子化**：每个工具只做一件事（单一职责）
2. **幂等性**：相同参数多次调用，结果一致
3. **详细描述**：description 中包含使用场景、限制、示例
4. **参数约束**：通过 required、enum、minimum/maximum 等限制非法输入
5. **错误友好**：即使参数错误，也返回有意义的错误信息而非崩溃

---

### 3.5 Agent 模式 vs Plan 模式对比

通过抓取不同模式下的请求，我们发现：

| 维度 | Agent 模式 | Plan 模式 |
|------|-----------|-----------|
| **主要目标** | 直接执行任务 | 先规划再确认 |
| **工具权限** | 完整的读写执行权限 | 只读权限（不能修改文件） |
| **交互风格** | 自主完成多步操作 | 与用户讨论方案 |
| **适用场景** | 明确的实现需求 | 复杂/模糊的设计决策 |
| **system prompt 差异** | 包含更多执行指令 | 包含更多规划引导 |

**模式切换的触发条件：**
- 用户显式要求"帮我规划一下"
- 任务涉及架构决策
- 存在多种实现方案需要权衡
- 任务范围不明确需要澄清

---

### 3.6 设计模式总结与启示

#### 3.6.1 Cursor 的工程化设计原则

1. **分层协议**：System Prompt → Tools → Context → User Query，每层职责清晰
2. **防御性设计**：大量 bad-example 说明踩坑经验，通过负面示例约束行为
3. **渐进式复杂度**：简单任务走快路径，复杂任务自动升级到 Plan/Task 模式
4. **可观测性**：终端状态、任务进度都可被模型读取
5. **安全边界**：隐藏系统细节、拒绝自定义格式、禁止泄露 system_reminder

#### 3.6.2 对我们自建 Agent 的启示

| Cursor 做法 | 可借鉴点 |
|------------|---------|
| XML 标签分模块 | 用结构化标签组织 system prompt，而非一大段文字 |
| 大量 good/bad example | 通过正反示例训练格式输出，比纯规则更有效 |
| 工具优先于终端 | 设计专用工具而非让模型写 shell，可控性更强 |
| 并行调用提示 | 显式告诉模型什么时候可以并行，提升效率 |
| 模式自动切换 | 让模型根据任务复杂度自适应，而非固定流程 |
| 任务状态管理 | 引入 todo 机制跟踪多步任务进度 |
| 终端状态文件化 | 把运行时状态导出为文件，解决异步可观测问题 |

#### 3.6.3 提示词工程的核心洞察

> **Prompt 不是"一句话"，而是"一套协议"。**

Cursor 的提示词告诉我们：
- System Prompt 是模型的"操作手册"，需要覆盖所有边界情况
- 工具定义是"API 文档"，描述越详细模型调用越准确
- 上下文注入是"工作区快照"，让模型理解当前状态
- 多轮对话是"执行日志"，让模型知道之前做了什么

---

### 3.7 小结

通过抓取和分析 Cursor 的提示词，我们学到了：

1. **结构化 > 自然语言**：用 XML 标签组织指令，比一段话更易被模型理解
2. **示例 > 规则**：good/bad example 比抽象规则更有效
3. **工具设计是核心**：好的工具定义 = 好的模型表现
4. **模式分离**：不同任务类型用不同的指令集和权限
5. **闭环验证**：让模型能检查自己的输出（linter、todo 完成度）

这些经验可以直接应用到我们自己的 Agent 开发中。

---

## 附录：完整系统提示词

详见 [Cursor 系统提示词.md](./Cursor%20系统提示词.md)（英文原版）和 [Cursor 系统提示词-中文.md](./Cursor%20系统提示词-中文.md)（中文翻译）。


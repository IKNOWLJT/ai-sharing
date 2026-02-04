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
API_KEY = ""

# 模型配置
MODEL_CONFIG = {
    "gpt-5": {
        # 下游真实模型的 base url（示例占位，按实际环境设置）
        "api_base": "http://your_server_url/openai/deployments/OPENAI_GPT_5",
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

        # 兼容：某些上游模型不接受 temperature=0（甚至不接受非默认值）
        # Cursor/代理链路里经常会带上 temperature=0，这会导致上游直接 400
        if "temperature" in extra_params:
            try:
                temp = extra_params.get("temperature")
                # gpt-5（以及部分兼容 OpenAI 的网关实现）只支持默认 temperature=1
                if temp is None or float(temp) != 1.0:
                    extra_params.pop("temperature", None)
            except Exception:
                # 非法值直接丢弃，交给上游用默认值
                extra_params.pop("temperature", None)
        
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

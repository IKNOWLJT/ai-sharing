# LiteLLM 本地部署方案

使用 LiteLLM 代理服务，通过 OpenAI API Key 调用 GPT-4.1 模型。

## 1. 安装 LiteLLM

```bash
pip install 'litellm[proxy]'
```

## 2. 设置环境变量

```bash
export OPENAI_API_KEY=""
```

> 注意：不要把真实 Key 写进文档/配置并分享或提交。

## 3. 启动代理服务

```bash
litellm --config config.yaml --port 4000 --detailed_debug
```

服务启动后，代理地址为：`http://localhost:4000`

日志文件保存在 `logs/` 目录下。

## 4. 测试调用

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

curl https://uneugenically-unstatable-thaddeus.ngrok-free.dev/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

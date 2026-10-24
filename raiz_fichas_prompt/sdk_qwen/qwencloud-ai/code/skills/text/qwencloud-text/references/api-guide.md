# Qwen Text Chat — API Supplementary Guide

> **Content validity**: 2026-04 | **Sources**: [OpenAI compatibility](https://docs.qwencloud.com/api-reference/preparation/install-sdk) · [Qwen API](https://docs.qwencloud.com/api-reference/chat/dashscope) · [Function calling](https://docs.qwencloud.com/developer-guides/text-generation/function-calling) · [Models](https://www.qwencloud.com/models)

---

## Definition

Qwen text generation models accessed through an **OpenAI-compatible** interface. Migrate existing OpenAI code by updating three values: `base_url`, `api_key`, and `model`. Supports text generation, multi-turn conversations, code writing, reasoning, and function calling.

---

## Use Cases

Fetch and read the current [QwenCloud text model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-text-models.md) for recent Qwen general-purpose model recommendations, defaults, and basic model information. Use qwencloud-model-selector or the QwenCloud CLI for coding, translation, or third-party families. If CDN access fails, use the [local fallback](../cdn/references/qwencloud-text-models.md). These recommendations apply only when the user has not specified a model; preserve any explicit model or parameter choice.

---

## Key Usage

### Regional Endpoints

| Region | base_url |
|--------|----------|
| Singapore (default) | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |

### Non-streaming Call

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)
resp = client.chat.completions.create(
    model="qwen3.6-plus",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
)
print(resp.choices[0].message.content)
```

### Streaming (recommended for interactive use)

```python
stream = client.chat.completions.create(
    model="qwen3.6-plus",
    messages=[{"role": "user", "content": "Write a haiku."}],
    stream=True,
    stream_options={"include_usage": True},
)
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Function Calling

Workflow: **Define tools → Model returns tool call instruction → Execute tool → Send result back → Get final answer.**

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a city",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        },
    },
}]

resp = client.chat.completions.create(
    model="qwen3.6-plus",
    messages=[{"role": "user", "content": "What's the weather in Beijing?"}],
    tools=tools,
)
# resp.choices[0].message.tool_calls contains function name and arguments
# Execute the function, then send result back with role="tool"
```

For the current function-calling model list, fetch and read the CDN model catalog linked above.

### Thinking Mode

Fetch and read the CDN model catalog linked above for current thinking-mode defaults and compatible models. Preserve the selected model's default unless the user explicitly asks to change it:

```python
# For a model whose documented default is thinking on, no need to set it
resp = client.chat.completions.create(
    model="qwen3.6-plus",
    messages=[{"role": "user", "content": "Solve this problem."}],
)

# For a model whose documented default is thinking off, enable only when requested
resp = client.chat.completions.create(
    model="qwen3-max",
    messages=[{"role": "user", "content": "Solve 17 × 23 step by step."}],
    extra_body={"enable_thinking": True},  # Only when the user requests this override
)

# Script usage: add --enable-thinking flag to override defaults
# python scripts/text.py --request '{"messages":[...]}' --enable-thinking
```

**When to disable thinking**: After checking the model's current default in the CDN catalog, set `enable_thinking: false` only when the user explicitly asks for faster responses or explicitly wants thinking off. Do NOT silently disable it just because the task looks simple — that changes the model's default behavior without the user's consent. You may *suggest* disabling it for simple tasks.

### Key Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | string | **Required.** Model ID. |
| `messages` | array | **Required.** Conversation history. Format: `{"role": "...", "content": "..."}`. Roles: `system`, `user`, `assistant`. `system` can only appear at `messages[0]`. Last element must have `user` role. |
| `temperature` | float | Controls randomness. Range: [0, 2). Higher values produce more diverse output. |
| `top_p` | float | Nucleus sampling threshold. Range: (0, 1.0). |
| `max_tokens` | int | Maximum number of output tokens. |
| `stream` | bool | Enable streaming output. |
| `tools` | array | Tool definitions for function calling. |
| `stop` | string/array | Stop generation when specified string or token is about to be output. |

### Key Response Fields

| Field | Description |
|-------|-------------|
| `choices[0].message.content` | Generated text. |
| `choices[0].message.tool_calls` | Tool call instructions (if applicable). |
| `choices[0].finish_reason` | `stop` = normal completion; `length` = max_tokens reached. |
| `usage.prompt_tokens` / `completion_tokens` | Token consumption. |

---

## Important Notes

1. **Prefer streaming.** Non-streaming blocks until the full response is generated (10–60s+ for long outputs). Always use `stream=True` for interactive scenarios.
2. **API keys are region-specific.** Use the `ap-southeast-1` (Singapore) endpoint with your API key.
3. **openai SDK version:** Requires ≥1.55.0. Older versions conflict with httpx ≥0.28, causing a `proxies` TypeError.
4. **Thinking mode varies by model.** Fetch the CDN model catalog linked above for current defaults. Only override with `enable_thinking` when the user explicitly asks to change the default.
5. **Function calling constraints.** `tools` cannot be used with `stream=True` (older limitation; some newer models support it). Also incompatible with `n > 1`.
6. **messages format.** `system` role can only appear at `messages[0]`. The last message must have the `user` role.
7. **Regional availability is model-specific.** The CDN catalog does not provide region coverage; verify it with `qwencloud models info <model>` or the official model documentation.

---

## FAQ

**Q: How do I migrate from OpenAI?**
A: Change three values: `api_key` to your DASHSCOPE_API_KEY, `base_url` to the corresponding regional endpoint, and `model` to a Qwen model name. All other code remains compatible.

**Q: When should I use streaming vs. non-streaming?**
A: Use streaming for interactive scenarios (chat, real-time output). Use non-streaming for batch processing or when you need the complete JSON response at once. With streaming, set `stream_options={"include_usage": True}` to receive token usage in the last chunk.

**Q: Which models support function calling?**
A: Fetch and read the current CDN model catalog linked above.

**Q: What is the difference between `qwen3.6-plus` and `qwen3.5-plus`?**
A: Fetch and read the current CDN model catalog linked above for model comparisons and the recommended default.

**Q: How do I control output length?**
A: Use `max_tokens` to limit output token count. Use `stop` to set stop sequences. Each model has its own default output limit.

**Q: What should I do when I get a 429 error?**
A: 429 indicates QPS/QPM rate limit exceeded or insufficient quota. Implement exponential backoff retry, or check remaining quota in the console.

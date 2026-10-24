# Visual Reasoning Guide

> **Content validity**: 2026-04 | **Source**: [Visual Reasoning](https://docs.qwencloud.com/developer-guides/text-generation/thinking)

---

## Overview

Visual reasoning models output their thinking process before the final answer. Suitable for complex tasks: solving math problems from images, analyzing chart data, understanding complex visual scenes, and reasoning about video content.

---

## Model Types

Fetch and read the current [QwenCloud vision model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-vision-models.md) for thinking-only and hybrid-thinking model lists, defaults, and compatibility. If CDN access fails, use the [local fallback](../cdn/references/qwencloud-vision-models.md). Preserve a user-specified model and thinking setting.

Rules that must not be inferred from the catalog: `qvq-max` is thinking-only
and streaming-only. The current open-source vision thinking model,
`qwen3-vl-235b-a22b-thinking`, is also thinking-only and streaming-only.
Neither accepts `enable_thinking: false`. Hybrid models accept
`enable_thinking`; use their catalog default unless the user asks for an
override or requests structured output.

---

## API Reference

Same endpoint as standard vision: `POST /compatible-mode/v1/chat/completions`

### Key Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `enable_thinking` | bool | Enable/disable thinking (hybrid models only). Pass via `extra_body`. |
| `thinking_budget` | int | Max tokens for reasoning process. Controls thinking depth. |
| `stream` | bool | **Required for `qvq-max` and `qwen3-vl-235b-a22b-thinking`.** Recommended for hybrid thinking. |

### Streaming Response

The delta contains two separate fields:
- `reasoning_content`: The model's step-by-step thinking (billed as output tokens)
- `content`: The final answer

---

## Code Examples

### QVQ Visual Reasoning (Python)

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    model="qvq-max",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "https://img.alicdn.com/imgextra/i1/O1CN01gDEY8M1W114Hi3XcN_!!6000000002727-0-tps-1024-406.jpg"}},
            {"type": "text", "text": "How do I solve this problem?"},
        ],
    }],
    stream=True,
    stream_options={"include_usage": True},
)

reasoning_content = ""
answer_content = ""
is_answering = False

for chunk in completion:
    if not chunk.choices:
        print(f"\nUsage: {chunk.usage}")
        continue

    delta = chunk.choices[0].delta
    if hasattr(delta, "reasoning_content") and delta.reasoning_content:
        reasoning_content += delta.reasoning_content
        if not is_answering:
            print(delta.reasoning_content, end="", flush=True)

    if hasattr(delta, "content") and delta.content:
        if not is_answering:
            is_answering = True
            print("\n--- Answer ---")
        answer_content += delta.content
        print(delta.content, end="", flush=True)
```

### Hybrid Thinking with VL-Plus (Python)

```python
completion = client.chat.completions.create(
    model="qwen3-vl-plus",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "https://img.alicdn.com/imgextra/i1/NotRealJustExample/chart.png"}},
            {"type": "text", "text": "Analyze the trends in this chart."},
        ],
    }],
    stream=True,
    extra_body={"enable_thinking": True},
)
```

### Video Reasoning (Python)

Video input uses the same thinking pipeline. Pass `video_url` (or `video` frame list) instead of `image_url`. The `fps` parameter controls frame extraction frequency.

```python
completion = client.chat.completions.create(
    model="qvq-max",
    messages=[{
        "role": "user",
        "content": [
            {"type": "video_url", "video_url": {"url": "https://img.alicdn.com/imgextra/i1/NotRealJustExample/clip.mp4"}, "fps": 2},
            {"type": "text", "text": "Analyze what happens in this video step by step."},
        ],
    }],
    stream=True,
    stream_options={"include_usage": True},
)
```

**Video duration limits are model-specific**: Fetch the CDN model catalog linked above for current limits. `fps` range is [0.1, 10], default 2.0. Use lower fps for long videos to save tokens.

**Script usage**:

```bash
# Video reasoning with QVQ
python scripts/reason.py --request '{"prompt":"What happens and why?","video":"clip.mp4","fps":2}'

# Video frames reasoning
python scripts/reason.py --request '{"prompt":"Describe the action",
  "video_frames":["f1.jpg","f2.jpg","f3.jpg","f4.jpg"],"fps":2}' --print-response
```

---

## Important Notes

1. **Thinking-only models have fixed behavior.** `qvq-max` and `qwen3-vl-235b-a22b-thinking` require streaming and cannot disable thinking. `reason.py` always streams.
2. **Thinking tokens are billed as output tokens.** This increases cost. Use `thinking_budget` to limit reasoning depth.
3. **System prompt**: In general (non-agent) scenarios, do not set a System Message for optimal performance. Pass instructions via User Message. For multi-turn agents, use the system message.
4. **Thinking defaults vary by model.** Fetch the CDN model catalog before overriding them; preserve explicit settings except that an invalid `enable_thinking: true` plus structured-output request must be rejected.
5. **Structured output only in non-thinking mode.** `analyze.py` and `ocr.py` automatically set `enable_thinking: false` for structured output when omitted, reject explicit `true`, and cannot use thinking-only models for that request.
6. **analyze.py also supports thinking.** Set `enable_thinking: true` in the request — the script auto-enables streaming. Use reason.py only for QVQ or dedicated reasoning workflows.
7. **Video reasoning supported.** Both `reason.py` and `analyze.py` accept `video` (URL) and `video_frames` (frame list) input with optional `fps` parameter. Video audio is not processed — models analyze frames only.

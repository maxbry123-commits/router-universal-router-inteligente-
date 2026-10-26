# QwenCloud Text Models

> Scope: recent Qwen general-purpose text and multimodal models released after the `2025-08-01` cutoff and still named by the trusted sources below. This is not a complete catalog of coding, translation, or third-party text models; use the QwenCloud CLI or the model-selector cross-domain catalog for those families. Rolling model IDs are dated through the snapshot IDs shown beside them. Where an official source does not publish an exact launch day, this document does not invent one.

## Default

- Default model: `qwen3.8-max`.
- It is the newest production Max model that is available through both PAYG and Token Plan Personal/Team. Use the rolling ID: Token Plan uses an exact-string allowlist and does not list `qwen3.8-max-0902`.
- Do not replace a model explicitly selected by the user. If the selected model is unavailable under the active billing plan, report the mismatch.

## Current model families

| Production model ID | Post-cutoff evidence in the current sources | Supported input / role | Token Plan Personal | Token Plan Team |
|---|---|---|---:|---:|
| `qwen3.8-max` | The marketplace names the upgraded `qwen3.8-max-0902` snapshot; that source was last modified on 2026-09-02. | Text, code, image, and video; 1M context; thinking and tool use. | Yes | Yes |
| `qwen3.8-flash` | The 2026-09 marketplace calls it the latest Qwen multimodal model; an exact launch day is not stated. | Fast text, code, image, and video model; 1M context; OpenAI- and Anthropic-compatible. | Yes | Yes |
| `qwen3.7-max` | Snapshots `qwen3.7-max-2026-05-17`, `qwen3.7-max-2026-05-20`, and `qwen3.7-max-2026-06-08`. | Reasoning and text generation. | Yes | Yes |
| `qwen3.7-plus` | Snapshot `qwen3.7-plus-2026-05-26`. | Reasoning, visual understanding, and text generation. | Yes | Yes |
| `qwen3.7-flash` | Snapshot `qwen3.7-flash-2026-07-15`. | Current fast Qwen3.7 API model. | No | No |
| `qwen3.6-plus` | Snapshot `qwen3.6-plus-2026-04-02`. | Reasoning, visual understanding, and text generation. | No | Yes |
| `qwen3.6-flash` | Snapshot `qwen3.6-flash-2026-04-16`. | Reasoning, visual understanding, and text generation. | Yes | Yes |
| `qwen3.5-plus` | Snapshots `qwen3.5-plus-2026-02-15` and `qwen3.5-plus-2026-04-20`. | General multimodal text generation. | No | No |
| `qwen3.5-flash` | Snapshot `qwen3.5-flash-2026-02-23`. | Fast multimodal text generation. | No | No |
| `qwen3-max` | Snapshot `qwen3-max-2026-01-23`. | General-purpose text generation with hybrid thinking. | No | No |

`Yes` above means that the exact rolling ID appears in the corresponding Token Plan allowlist. Snapshot IDs are PAYG/API identifiers and are not Token Plan-compatible unless that exact snapshot string is also listed.

## Selection guidance

| Need | Model | Source-backed reason |
|---|---|---|
| Default or highest-capability work | `qwen3.8-max` | Latest upgraded Max generation, multimodal, 1M context, and supported by PAYG plus both Token Plans. |
| Faster current-generation work | `qwen3.8-flash` | Officially described as the fast latest-generation multimodal model; also supported by both Token Plans. |
| Text-only reasoning | `qwen3.7-max` | Token Plan classifies it for reasoning and text generation. |
| Team-only balanced fallback | `qwen3.6-plus` | Available on PAYG and Team, but absent from the Personal exact-string allowlist. |

## Thinking defaults

| Model | Thinking default | Notes |
|---|---|---|
| `qwen3.8-max`, `qwen3.8-flash` | On | Thinking enabled by default. |
| `qwen3.7-max`, `qwen3.7-plus`, `qwen3.7-flash` | On | Thinking enabled by default. |
| `qwen3.6-plus`, `qwen3.6-flash` | On | Thinking enabled by default. |
| `qwen3.5-plus`, `qwen3.5-flash` | On | Thinking enabled by default. |
| `qwen3-max` | Off | Hybrid thinking; use `enable_thinking: true` only when the user requests it. |
| `qwen3.8-27b`, `qwen3.8-omni-flash` | On | Hybrid thinking; preserve the model default unless explicitly overridden. |
| `qwen3.8-2.4t-a95b` | Always on | Thinking-only; streaming is required. |

Preserve each model's default. Do not set `enable_thinking` unless the user explicitly asks to change it, and do not disable thinking merely because a task looks simple. Thinking-only models cannot disable thinking.

## Compatibility and limits

- All general-purpose text-generation models support function calling. GLM models require `tool_stream: true` for tool calls, except `glm-5.3`, where it defaults to true.
- `thinking_budget` is supported by Qwen3.8, Qwen3.7, Qwen3.6, Qwen3.5, Qwen3-VL, Qwen3, GLM, Kimi, and Qwen3.8 open-source models in Chat Completions and DashScope, but not in the Responses API.
- For `qwen3.8-max`, `reasoning_effort` supports `low`, `medium`, and `xhigh` and defaults to `xhigh`. Do not set `reasoning_effort` and `thinking_budget` together.
- Thinking tokens are billed as output tokens.
- Current API-only variants include `qwen3.8-27b` (hybrid thinking, on by default), `qwen3.8-2.4t-a95b` (thinking-only and streaming required), and `qwen3.8-omni-flash` (hybrid thinking, on by default; no audio output while thinking). They are not Token Plan models.

Verified: 2026-09-18.

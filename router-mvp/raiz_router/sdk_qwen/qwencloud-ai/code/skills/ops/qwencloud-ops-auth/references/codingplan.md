# Coding Plan vs Standard API Key

> Sources:
> - https://docs.qwencloud.com/coding-plan/overview
> Updated: 2026-08-29

## Two Key Types

Alibaba Cloud Model Studio has two mutually exclusive authentication systems. Mixing them produces hard-to-diagnose errors.

| Dimension | Standard Key (Pay-as-you-go) | Coding Plan |
|-----------|------------------------------|-------------|
| Key format | `sk-xxxxx` | `sk-sp-xxxxx` |
| OpenAI-compatible URL | `dashscope-intl.aliyuncs.com/compatible-mode/v1` | `coding-intl.dashscope.aliyuncs.com/v1` |
| Anthropic-compatible URL | N/A | `coding-intl.dashscope.aliyuncs.com/apps/anthropic` |
| Native DashScope URL | `dashscope-intl.aliyuncs.com/api/v1` | **Not supported** |
| Supported models | Full catalog (100+ across text, vision, image, video, audio) | 7 text models (see below) |
| Usage scope | Any API call (scripts, apps, tools) | **Coding tools only** (Cursor, Claude Code, Qwen Code, etc.) |
| Billing | Per-token consumption | Monthly subscription |
| Quota exhaustion | Continues (pay more or use prepaid balance) | **Hard fail — no fallback to pay-as-you-go** |
| Image/Video/TTS models | All available | **None** |

## Coding Plan Supported Models

| Model | Context Window | Thinking Mode | Max Thinking Budget |
|-------|---------------|---------------|--------------------:|
| qwen3.7-plus | 1,000,000 | Yes | 81,920 |
| qwen3.5-plus | 1,000,000 | Yes | 81,920 |
| qwen3-max-2026-01-23 | 256,000 | Yes | 81,920 |
| qwen3-coder-next | 256,000 | **No** | N/A |
| qwen3-coder-plus | 1,000,000 | **No** | N/A |
| glm-4.7 | 198,000 | Yes | 32,768 |
| qwen3.6-plus | 1,000,000 | Yes | 81,920 |

## Key Type x Endpoint — Expected Behavior

| Key Type | Base URL | Result |
|----------|----------|--------|
| `sk-` | `dashscope-intl.aliyuncs.com/...` | OK |
| `sk-` | `coding-intl.dashscope.aliyuncs.com/...` | **401** — regular key rejected |
| `sk-sp-` | `dashscope-intl.aliyuncs.com/...` | **401** — Coding Plan key rejected |
| `sk-sp-` | `coding-intl.dashscope.aliyuncs.com/...` | **Agent context required** — rejects non-agent scripts |
| `sk-sp-` | `token-plan.ap-southeast-1.maas.aliyuncs.com/...` | OK (scripts auto-route) |

## Error Codes

| Error | Cause | Resolution |
|-------|-------|------------|
| `401 invalid access token` | `sk-` on coding-intl endpoint, or expired subscription | Use plan-specific key; check subscription status |
| `401 invalid_api_key` | `sk-sp-` on standard DashScope endpoint | Use a standard key for scripts, or scripts auto-route to Token Plan endpoint |
| `model 'xxx' is not supported` | Model not in Coding Plan list (case-sensitive) | Check model IDs above |
| `Coding Plan is currently only available for Coding Agents` | Script/curl calling coding-intl | Use through coding tools only, not scripts |
| `hour/week/month allocated quota exceeded` | Plan quota exhausted | Wait for reset or upgrade |

## Impact on qwencloud/qwencloud-ai Scripts

All scripts call DashScope directly via `urllib.request` and are **not** recognized as coding agents. Scripts detect `sk-sp-` keys and auto-route to Token Plan endpoint when applicable.

| Skill | API Type | Works with sk-sp- (Coding)? | Works with sk-sp- (Token Plan)? | Reason |
|-------|----------|:---------------------------:|:-------------------------------:|--------|
| qwencloud-text | OpenAI-compat | No | Yes (partial) | Coding: 401 on standard endpoint; Token Plan: auto-route supported |
| qwencloud-vision | OpenAI-compat | No | Yes (partial) | Coding: vision models not in Coding Plan; Token Plan: multimodal models available |
| qwencloud-image-generation | Native | No | Yes (partial) | Coding: image models unavailable; Token Plan: wan2.7/qwen-image models |
| qwencloud-video-generation | Native | No | Yes (partial) | Coding: video models unavailable; Token Plan: happyhorse models |
| qwencloud-audio-tts | Native | No | Yes (partial) | Coding: TTS models unavailable; Token Plan: qwen-audio-3.0-tts-plus |

## Cost Risk Scenarios

1. **sk-sp- key in scripts**: Scripts auto-route to Token Plan endpoint for supported models; unsupported models produce 401 error.
2. **sk- key when user expects Coding Plan coverage**: Calls succeed but incur pay-as-you-go charges. Cannot detect programmatically — documentation must clarify.
3. **QWEN_BASE_URL set to coding-intl**: "Coding Plan is currently only available for Coding Agents". Scripts warn on detection.
4. **Coding Plan quota exhausted**: Hard fail, no fallback. Users must wait for reset or upgrade.

To verify actual charges, direct users to the appropriate billing page:
- Pay-as-you-go: [Pay-as-you-go Billing](https://home.qwencloud.com/billing/pay-as-you-go)
- Coding Plan: [Coding Plan Billing](https://home.qwencloud.com/billing/coding-plan)
- Usage analytics: [Usage Analytics](https://home.qwencloud.com/analytics)

## Resolution

Both key types can coexist. A user can have:
- Coding Plan key (`sk-sp-`) for their IDE coding agent (Cursor, Claude Code)
- Standard key (`sk-`) for API scripts in qwencloud/qwencloud-ai

Set the standard key in `DASHSCOPE_API_KEY` when using these skills.

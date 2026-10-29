# Token Plan

> Sources:
> - https://docs.qwencloud.com/token-plan/overview
> - https://docs.qwencloud.com/token-plan/personal/token-plan-personal-overview
> - https://docs.qwencloud.com/token-plan/team/token-plan-team-overview
> - [CDN Token Plan model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-token-plan-models.md) — Personal and Team model lists, modality constraints, and exclusions. If CDN access fails, use the [local fallback](../cdn/references/qwencloud-token-plan-models.md).
> Catalog checked: 2026-09-06

## Three Key/Plan Types

QwenCloud has three mutually exclusive authentication and billing systems:

| Dimension | Standard Key (PAYG) | Token Plan | Coding Plan |
|-----------|---------------------|------------|-------------|
| Key format | `sk-ws-xxxxx` | `sk-sp-xxxxx` | `sk-sp-xxxxx` |
| Base URL (OpenAI) | `dashscope-intl.aliyuncs.com/compatible-mode/v1` | `token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1` | `coding-intl.dashscope.aliyuncs.com/v1` |
| Base URL (Anthropic) | N/A | `token-plan.ap-southeast-1.maas.aliyuncs.com/apps/anthropic` | `coding-intl.dashscope.aliyuncs.com/apps/anthropic` |
| Models | Full catalog | Catalog-defined; use the CDN model catalog above | See [codingplan.md](codingplan.md) |
| Billing | Per-token/image/second | Credits (unified) | Requests per week/month |
| Usage scope | Any API call | Interactive AI tools | Coding tools only |

Before each Token Plan request, fetch and read the CDN catalog above, choose the exact modality and
mode, and explicitly pass a listed model. Do not probe models, change modes, or silently fall back to PAYG.

## Supported Models

Use the CDN Token Plan model catalog linked above for the Personal and Team model lists, capabilities,
modality constraints, and exclusions.

## Key Type x Endpoint — Expected Behavior

| Key Type | Base URL | Result |
|----------|----------|--------|
| `sk-ws-` | `dashscope-intl.aliyuncs.com/...` | OK |
| `sk-ws-` | `token-plan.ap-southeast-1.../...` | **401** — PAYG key rejected |
| `sk-sp-` | `dashscope-intl.aliyuncs.com/...` | **401** — Token Plan key rejected |
| `sk-sp-` | `token-plan.ap-southeast-1.../...` | OK |
| `sk-sp-` | `coding-intl.dashscope.aliyuncs.com/...` | **Coding agent context required** |

## Impact on qwencloud/qwencloud-ai Scripts

All scripts detect `sk-sp-` keys for automatic Token Plan routing:

| Skill | Token Plan supported? | Supported models (TP) |
|-------|:---------------------:|----------------------|
| qwencloud-text | Yes | Use text-capable models from the CDN catalog above |
| qwencloud-vision | Yes | Use vision-capable models from the CDN catalog above |
| qwencloud-image-generation | Yes | Use image-generation models from the CDN catalog above |
| qwencloud-video-generation | Yes | Use video-generation models from the CDN catalog above |
| qwencloud-audio-tts | Yes | Use TTS models from the CDN catalog above; CosyVoice remains PAYG-only |

## Console URLs

- Token Plan Personal: https://home.qwencloud.com/analytics/token-plan/individual
- Token Plan Team: https://home.qwencloud.com/analytics/token-plan/team
- Team Management: https://tokenplan-enterprise.qwencloud.com

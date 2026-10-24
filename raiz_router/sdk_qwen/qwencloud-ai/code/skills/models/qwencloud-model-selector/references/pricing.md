# QwenCloud Model Pricing

> **Source**: [Official pricing page](https://docs.qwencloud.com/developer-guides/getting-started/pricing) — check for the latest rates.
>
> **Important**: This file provides stable billing guidance. Model lists and model-specific billing information are in the [CDN model-pricing reference](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-model-pricing.md). Specific prices, free quota amounts, and availability are subject to change without notice. Always refer to the official pricing page for authoritative, up-to-date pricing data. If CDN access fails, use the [local fallback](../cdn/references/qwencloud-model-pricing.md).
>
> All prices in **USD**.

## Text Generation (per 1M tokens)

- Billing unit: **per 1M tokens** (input and output priced separately)
- Some models have **tiered pricing** based on input context length (e.g. ≤32K, ≤128K, ≤256K, ≤1M)
- Thinking mode output may be priced differently from non-thinking output
- **Batch API**: 50% off for supported models
- Some models may offer a limited free quota — **do not assume the user has remaining free quota**; use `qwencloud usage free-tier` to check, or verify in the [QwenCloud console](https://home.qwencloud.com/benefits)

## Vision Understanding (per 1M tokens)

- Billing unit: **per 1M tokens**
- Tiered pricing by input context length for some models

## Omni Models (per 1M tokens)

- Billing unit: **per 1M tokens**
- Separate rates for text input, audio input, image/video input, text output, and audio output

## Image Generation (per image)

- Billing unit: **per image generated**
- Multi-image output (n > 1) is billed per image

## Video Generation (per second)

- Billing unit: **per second of generated video**
- Price varies by resolution (480P / 720P / 1080P)
- Audio-enabled models may have different rates than silent variants

## Speech Synthesis / TTS (per 10K characters)

- Billing unit: **per 10,000 characters**

## Speech Recognition / ASR (per second of audio)

- Billing unit: **per second of audio**

## Text Embedding (per 1M tokens)

- Billing unit: **per 1M input tokens**

## Multimodal Embedding (per 1M tokens)

- Billing unit: **per 1M input tokens**

## Text Rerank (per 1M tokens)

- Billing unit: **per 1M input tokens**

## Translation (per 1M tokens)

- Billing unit: **per 1M tokens** (input and output priced separately)

## Subscription Plans

### Token Plan (Credits billing)

Token Plan uses a unified Credits system across text, vision, image, video, and audio models. Fetch the [CDN Token Plan model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-token-plan-models.md) for the current snapshot; if CDN access fails, use the [local fallback](../cdn/references/qwencloud-token-plan-models.md). See [Token Plan pricing](https://www.qwencloud.com/pricing/token-plan) for current rates.

- **Personal / Team model availability**: use the CDN catalog; Team includes the documented Personal set plus Team-only additions
- **Base URL**: `token-plan.ap-southeast-1.maas.aliyuncs.com`
- **Key format**: `sk-sp-xxxxx` (same prefix as Coding Plan; different endpoint)
- **Pricing details**: Check [Token Plan pricing page](https://www.qwencloud.com/pricing/token-plan) for current tier options and rates

Protocol and plan availability vary by model; use the CDN domain and Token Plan catalogs before selecting one.

## Notes

- **API Key must be created from the** [QwenCloud Console](https://home.qwencloud.com/api-keys).
- **Free quota**: Some models include a limited free quota after activating QwenCloud. **However**: free quota amounts, eligibility, and validity periods are subject to change without notice. Quotas may have already been consumed or expired. **Never assume the user has remaining free quota** — always present the paid unit price as the primary reference. Use `qwencloud usage free-tier` to check remaining free tier quota, or direct the user to the [QwenCloud console](https://home.qwencloud.com/benefits).
- **Batch calling**: Supported models get 50% off (both input and output).
- **Context cache**: Eligible models get input token discounts.
- **Tiered pricing**: Some models have higher per-token cost as input length increases.
- **For the latest prices**: Always check the [official pricing page](https://docs.qwencloud.com/developer-guides/getting-started/pricing).
- **View actual usage and bills**: Use `qwencloud usage summary`, `qwencloud usage payg`, or visit the console: [Usage Analytics](https://home.qwencloud.com/analytics) | [Pay-as-you-go Billing](https://home.qwencloud.com/billing/pay-as-you-go) | [Coding Plan Billing](https://home.qwencloud.com/billing/coding-plan).
- **Token Plan**: See [Token Plan pricing](https://www.qwencloud.com/pricing/token-plan) | [Personal console](https://home.qwencloud.com/analytics/token-plan/individual) | [Team console](https://home.qwencloud.com/analytics/token-plan/team)

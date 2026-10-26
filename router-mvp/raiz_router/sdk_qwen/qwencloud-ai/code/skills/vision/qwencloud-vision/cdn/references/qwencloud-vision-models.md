# QwenCloud Vision Models

> Scope: models released after the `2025-08-01` cutoff and still named by the trusted sources below. Dated snapshots are retained as release evidence. Where an official source does not publish an exact launch day, this document does not invent one.

## Defaults

| Task | Runtime default | Reason |
|---|---|---|
| Image or video understanding | `qwen3.8-max` | Newest production Max generation; PAYG and Token Plan Personal/Team. |
| Visual reasoning | `qwen3.8-max` | Supports reasoning and visual understanding under both billing modes. |
| OCR | `qwen3.8-max` | Cross-plan default. Use a dedicated OCR model only when PAYG is available and the user chooses it. |

Token Plan uses an exact-string allowlist. Use `qwen3.8-max`, not the PAYG snapshot `qwen3.8-max-0902`.

## Current model families

| Model ID | Post-cutoff evidence in the current sources | Primary use | Token Plan Personal | Token Plan Team |
|---|---|---|---:|---:|
| `qwen3.8-max` | Marketplace names the upgraded `qwen3.8-max-0902` snapshot; that source was last modified on 2026-09-02. | Highest-capability text, image, and video understanding; 1M context. | Yes | Yes |
| `qwen3.8-flash` | The 2026-09 marketplace calls it the latest Qwen multimodal model; exact launch day is not stated. | Faster text, image, and video understanding; 1M context. | Yes | Yes |
| `qwen3.7-plus` | Snapshot `qwen3.7-plus-2026-05-26`. | General multimodal understanding and reasoning. | Yes | Yes |
| `qwen3.7-flash` | Snapshot `qwen3.7-flash-2026-07-15`. | Faster multimodal work. | No | No |
| `qwen3.6-plus` | Snapshot `qwen3.6-plus-2026-04-02`. | General multimodal understanding and reasoning. | No | Yes |
| `qwen3.6-flash` | Snapshot `qwen3.6-flash-2026-04-16`. | Faster multimodal work. | Yes | Yes |
| `qwen3.5-plus` | Snapshots `qwen3.5-plus-2026-02-15` and `qwen3.5-plus-2026-04-20`. | General multimodal understanding. | No | No |
| `qwen3.5-flash` | Snapshot `qwen3.5-flash-2026-02-23`. | Faster multimodal understanding. | No | No |
| `qwen3-vl-plus` | Current Qwen3-VL production family; the cited guide does not state an exact launch day. | Localization and document/webpage parsing. | No | No |
| `qwen3-vl-flash` | Current Qwen3-VL production family; the cited guide does not state an exact launch day. | Faster dedicated vision work. | No | No |
| `qwen3-vl-235b-a22b-thinking` | Exact current ID in the Vision guide. | Open-source thinking-only visual analysis. | No | No |
| `qwen3-vl-235b-a22b-instruct` | Exact current ID in the Vision guide. | Open-source instruction-following visual analysis. | No | No |
| `qwen-vl-max` | Rolling model ID. | Higher-accuracy Qwen2.5-VL visual recognition. | No | No |
| `qwen-vl-plus` | Rolling model ID. | Faster Qwen2.5-VL visual recognition. | No | No |
| `qwen-vl-ocr` | Current dated snapshot: `qwen-vl-ocr-2025-11-20`. | OCR and structured extraction from text-heavy images. | No | No |

`Yes` means that exact rolling ID appears in the corresponding Token Plan allowlist. No dedicated Qwen3-VL, Qwen-VL, or OCR ID appears in either allowlist.

## Selection guidance

| Need | Model | Notes |
|---|---|---|
| Default, highest capability, or visual reasoning | `qwen3.8-max` | Cross-plan default; do not substitute the snapshot ID for Token Plan. |
| Faster current-generation analysis | `qwen3.8-flash` | PAYG and both Token Plans. |
| Dedicated localization or document parsing | `qwen3-vl-plus` | PAYG only. |
| Dedicated OCR | `qwen-vl-ocr` | PAYG only; use `qwen-vl-ocr-2025-11-20` when a pinned version is required. |

## Thinking behavior

- Thinking is off by default for `qwen3-vl-plus` and `qwen3-vl-flash`.
- Thinking is on by default for Qwen3.5 and later multimodal series.
- A model ID ending in `-thinking` always thinks.
- Thinking tokens are billed as output tokens.

## Input limits

- Image dimensions: width and height must each be greater than 10 pixels; aspect ratio must not exceed 200:1. Keep images within 8K to reduce timeout risk.
- Formats below 4K: BMP, JPEG, PNG, TIFF, WEBP, and HEIC. From 4K through 8K, only JPEG/JPG and PNG are supported.
- Per-image size by public URL: up to 20 MB for Qwen3.8, Qwen3.7, Qwen3.6, Qwen3.5, and Qwen3-VL; 10 MB for other models. A local path is limited to 10 MB.
- OpenAI-compatible Base64 input: original file up to 20 MB for those newer families and 10 MB for others; the resulting Data URI must not exceed 20 MB. Anthropic-compatible Base64 requests have a 6 MB total request-body limit.
- Image count by URL/local path: up to 2,048 for Qwen3.8 Max/Flash and Qwen3.7 Plus; up to 256 for Qwen3.7 Flash, Qwen3.6 Plus/Flash, Qwen3.5 Plus/Flash, Qwen3-VL, Qwen-VL, and QVQ families. Base64 input supports up to 250 images.
- Video image lists: 4-8,000 frames for Qwen3.8, Qwen3.7, Qwen3.6, and Qwen3.5; 4-2,000 for `qwen3-vl-plus`, `qwen3-vl-flash`, `qwen3-vl-235b-a22b-thinking`, and `qwen3-vl-235b-a22b-instruct`; 4-512 for other Qwen3-VL, Qwen2.5-VL, and QVQ models; 4-80 for other models.
- Video file size by public URL: up to 2 GB for Qwen3.8, Qwen3.7, Qwen3.6, Qwen3.5, Qwen3-VL, and `qwen-vl-max`; up to 1 GB for Qwen-VL Plus, other Qwen-VL Max, open-source Qwen2.5-VL, and QVQ; up to 150 MB for other models.
- Video file size by Base64: the encoded string must be less than 10 MB.
- Video file size by local path: up to 100 MB when passed as a local file path through the DashScope SDK. A local file encoded as Base64 is subject to the Base64 limit instead.
- Video duration: 2 seconds-2 hours for Qwen3.8, Qwen3.7, Qwen3.6, and Qwen3.5; 2 seconds-1 hour for the listed Qwen3-VL Plus/Flash and 235B models; 2 seconds-20 minutes for other Qwen3-VL and recent `qwen-vl-max`; 2 seconds-10 minutes for Qwen-VL Plus, other Qwen-VL Max, Qwen2.5-VL, and QVQ; 2-40 seconds for other models.
- At most 64 videos can be supplied per request. Vision models sample frames and do not understand the video's audio track.

## OCR limits

- `qwen-vl-ocr` and `qwen-vl-ocr-2025-11-20`: 38,192-token context, 30,000 maximum input tokens, and 8,192 maximum output tokens.
- `qwen-vl-ocr` defaults `max_tokens` to 4,096. Increasing it to 4,097-8,192 requires contacting a commercial manager.
- These OCR models use 32 x 32 pixels per visual token.

Verified: 2026-09-18.

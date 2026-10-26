# QwenCloud Cross-Domain Model Recommendations

> Scope: models released on or after 2025-08-01, plus current rolling aliases and specialized compatibility models needed for coding, translation, and speech workflows. Never replace a user-selected model. Token Plan support is an exact-string allowlist.

## Defaults

| Task | Default | Why |
|---|---|---|
| Text | `qwen3.8-max` | Newest current production model that is documented for PAYG and appears verbatim in both Token Plan editions |
| Vision analysis | `qwen3.8-max` | Current official vision examples use it; PAYG + both Token Plan editions |
| Visual reasoning | `qwen3.8-max` | Thinking-capable and available on PAYG + both Token Plan editions |
| OCR fallback | `qwen3.8-max` | Cross-plan default; use the OCR specialist below only on PAYG |
| Image generation/editing | `qwen-image-3.0-pro` | Current recommended Qwen-Image model; PAYG + both Token Plan editions |
| Video text-to-video | `happyhorse-1.1-t2v` | Newest exact text-to-video ID available on PAYG + both Token Plan editions |
| Video image-to-video | `happyhorse-1.1-i2v` | Newest exact image-to-video ID available on PAYG + both Token Plan editions |
| Video reference-to-video | `happyhorse-1.1-r2v` | Newest exact reference-to-video ID available on PAYG + both Token Plan editions |
| Text-to-speech | `qwen-audio-3.0-tts-plus` | Quality-focused TTS and the only current TTS ID in both Token Plan editions |

`qwen3.8-max-0902` is the newer dated Qwen3.8-Max snapshot, but Token Plan does not list that exact ID. Use the rolling production ID `qwen3.8-max` for a default that works under both billing modes.

## Selection matrix

| Need | Recommended model | Availability and constraint |
|---|---|---|
| Highest-capability text or multimodal work | `qwen3.8-max` | PAYG + Token Plan Individual/Team |
| Faster current multimodal work | `qwen3.8-flash` | PAYG + Token Plan Individual/Team |
| Balanced recent text/vision work | `qwen3.7-plus` | PAYG + Token Plan Individual/Team |
| Reproducible latest Qwen3.8-Max snapshot | `qwen3.8-max-0902` | PAYG only; not a Token Plan exact ID |
| Repository-scale coding and agentic development | `qwen3.8-max` | Current flagship for coding and long-running agentic work; PAYG + Token Plan Individual/Team |
| Faster code generation | `qwen3-coder-flash` | PAYG only |
| Role-play (general) | `qwen-plus-character` | PAYG only; character restoration and empathetic dialog |
| Role-play (Japanese) | `qwen-plus-character-ja` | PAYG only; Japanese character dialog |
| Fast role-play | `qwen-flash-character` | PAYG only; lower-cost role-playing |
| Voice + vision chat | `qwen3-omni-flash` | PAYG only; text/image/audio/video input and text or speech output; no audio output in thinking mode |
| High-quality omni interaction | `qwen3.5-omni-plus` or `qwen3.5-omni-flash` | PAYG only; use the matching omni API for text or speech output |
| Dedicated Qwen3-VL analysis | `qwen3-vl-plus` | PAYG only |
| Faster visual analysis | `qwen3.8-flash` | PAYG + Token Plan Individual/Team |
| OCR built-in tasks | `qwen-vl-ocr` or `qwen-vl-ocr-2025-11-20` | PAYG only; pinned model has 38,192 context, 30,000 max input, and 8,192 max output |
| General image creation/editing | `qwen-image-3.0-pro` | PAYG + Token Plan Individual/Team |
| Wan multi-function image work | `wan2.7-image-pro` or `wan2.7-image` | PAYG + Token Plan Individual/Team |
| Dedicated Wan text-to-image | `wan2.6-t2i` | PAYG only |
| Dedicated one-to-three-image fusion | `wan2.5-i2i-preview` | PAYG only |
| Long, all-in-one video with first/last frames | `wan3.0-video` or `wan3.0-video-prime` | PAYG only; up to 30s |
| Legacy `kf2v` runtime contract | `wan2.2-kf2v-flash` | PAYG only; fixed 5s and silent; do not silently replace it with the structurally different Wan3.0 i2v request |
| Token Plan video | `happyhorse-1.1-t2v`, `happyhorse-1.1-i2v`, or `happyhorse-1.1-r2v` | Choose the exact ID matching the requested mode |
| Video instruction editing | `wan2.7-videoedit` | PAYG only |
| Legacy VACE functions | `wan2.1-vace-plus` | PAYG only; preserves `function`-based repainting, extension, local edit, and outpainting contracts |
| Highest-quality cross-plan TTS | `qwen-audio-3.0-tts-plus` | WebSocket; PAYG + Token Plan Individual/Team |
| Lower-latency Qwen Audio TTS | `qwen-audio-3.0-tts-flash` | WebSocket; PAYG only |
| HTTP TTS | `qwen3-tts-flash` | PAYG only |
| Instruction-controlled speech | `cosyvoice-v3-plus` | PAYG only; use `tts_cosyvoice.py` with `longanyang` or `longanhuan`; WebSocket, not the Qwen3-TTS HTTP contract |
| Speech recognition across billing modes | `qwen-audio-3.0-asr-flash` | PAYG + Token Plan Individual/Team; use the speech-recognition API, not the TTS script |
| PAYG speech recognition | `qwen3-asr-flash` | PAYG only; choose realtime or file-transcription variants only when their matching protocol is required |
| Highest-quality text translation | `qwen-mt-plus` | PAYG only |
| Faster or lower-cost text translation | `qwen-mt-flash` or `qwen-mt-lite` | PAYG only; compare current price and language coverage before choosing |
| Semantic search / RAG retrieval | `qwen3.7-text-embedding` | PAYG only; use the embedding API to build text vectors |
| Rerank retrieved documents | `qwen3-rerank` | PAYG only; use the reranking API to score the query against candidate documents |

## Decision rules

1. Preserve an explicit model ID. If it is not available for the active plan or protocol, report the mismatch instead of silently substituting another model.
2. With no explicit model, use the defaults above. They are selected from exact IDs documented for both PAYG and Token Plan wherever such an ID exists.
3. For Token Plan, match the model ID character-for-character against [qwencloud-token-plan-models.md](qwencloud-token-plan-models.md). Related aliases, dated snapshots, and sub-variants are not implied.
4. For a specialized mode with no Token Plan model, keep the requested mode on PAYG. Do not change the task merely to fit the plan.
5. Preserve the selected model's documented thinking behavior. Do not set `reasoning_effort` together with `thinking_budget` for Qwen3.8-Max.

## PAYG cost guidance

The units below apply to pay-as-you-go model calls. They are not Token Plan Credit formulas.

- Text and vision are billed per token; thinking tokens count as output tokens.
- Image generation charges input images where applicable and each successful output image.
- Video generation charges each generated second; some reference/editing models also charge input-video seconds.
- TTS charges per 10,000 input characters; generated audio is not separately charged.
- Batch text requests are 50% of real-time token rates where supported. Context-cache discounts are model-specific.
- For current rates and promotions, use the [official pricing page](https://docs.qwencloud.com/developer-guides/getting-started/pricing). Do not infer remaining free quota.

## Token Plan cost guidance

Token Plan uses dynamic Credits rather than the PAYG units above. Credit consumption depends on the
model, token or media usage, thinking mode, and tool calls. Do not convert PAYG prices into Credits;
use the Token Plan console for actual consumption.

## Token Plan snapshot

- Individual: 20 exact model IDs.
- Team: 27 exact model IDs.
- Individual uses a 7-day Credits window; Team uses per-seat monthly Credits.
- Token Plan covers the defaults in this document except specialized PAYG-only rows explicitly marked above.

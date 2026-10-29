# QwenCloud Recent Model List

> Sources: [Model Marketplace](https://www.qwencloud.com/models), [model selection](https://docs.qwencloud.com/developer-guides/getting-started/model-selection), the domain catalogs in this directory, and the Token Plan sources listed below.
>
> Checked: 2026-09-18. This is a curated snapshot, not an exhaustive marketplace export. It primarily retains model generations or dated snapshots released on or after 2025-08-01, plus specialized or compatibility models required by the bundled skills. Rolling aliases are included only when current official sources use them. Token Plan matching is exact-string only.

## Defaults

| Domain | Default | Availability |
|---|---|---|
| Text | `qwen3.8-max` | PAYG + Token Plan Individual/Team |
| Vision, visual reasoning, and OCR fallback | `qwen3.8-max` | PAYG + Token Plan Individual/Team |
| Image generation and editing | `qwen-image-3.0-pro` | PAYG + Token Plan Individual/Team |
| Video text-to-video | `happyhorse-1.1-t2v` | PAYG + Token Plan Individual/Team |
| Video image-to-video | `happyhorse-1.1-i2v` | PAYG + Token Plan Individual/Team |
| Video reference-to-video | `happyhorse-1.1-r2v` | PAYG + Token Plan Individual/Team |
| Text-to-speech | `qwen-audio-3.0-tts-plus` | PAYG + Token Plan Individual/Team |

`qwen3.8-max-0902` is the newer dated Qwen3.8-Max snapshot, but it is not in the Token Plan exact allowlist. The rolling production ID `qwen3.8-max` is therefore the newest cross-plan default.

## Text and general multimodal models

| Model ID | Current-source summary | Token Plan |
|---|---|---|
| `qwen3.8-max` | Current production flagship; text, image, and video input; 1M context; reasoning and tool ecosystem | Individual + Team |
| `qwen3.8-max-0902` | Upgraded 2026-09-02 snapshot of Qwen3.8-Max | No |
| `qwen3.8-flash` | Current fast multimodal model with 1M context | Individual + Team |
| `qwen3.7-max` | Reasoning and text generation | Individual + Team |
| `qwen3.7-plus` | General text and visual understanding | Individual + Team |
| `qwen3.7-flash` | Recent fast Qwen generation | No |
| `qwen3.6-plus` | Text and visual understanding | Team only |
| `qwen3.6-flash` | Text and visual understanding | Individual + Team |
| `qwen3.5-plus` | Text, image, and video input | No |
| `qwen3.5-flash` | Fast Qwen3.5 multimodal model | No |
| `qwen3-max` | Recent Qwen3 Max generation | No |

Recent dated snapshots explicitly named by the current APIs include `qwen3-max-2026-01-23`, `qwen3.5-plus-2026-02-15`, `qwen3.5-plus-2026-04-20`, `qwen3.5-flash-2026-02-23`, `qwen3.6-plus-2026-04-02`, `qwen3.6-flash-2026-04-16`, `qwen3.7-max-2026-05-17`, `qwen3.7-max-2026-05-20`, `qwen3.7-max-2026-06-08`, `qwen3.7-plus-2026-05-26`, and `qwen3.7-flash-2026-07-15`. These snapshot IDs are not Token Plan aliases unless they appear verbatim in the Token Plan allowlist.

### Coding models

| Model ID | Use | Token Plan |
|---|---|---|
| `qwen3-coder-next` | Repository-scale coding, tool use, and agentic development; PAYG and Coding Plan | No |
| `qwen3-coder-plus` | High-capability coding with long context; PAYG and Coding Plan | No |
| `qwen3-coder-flash` | Faster coding and code completion | No |

### Role-playing models

| Model ID | Use | Token Plan |
|---|---|---|
| `qwen-plus-character` | Role-playing, character restoration, and empathetic dialog | No |
| `qwen-plus-character-ja` | Japanese role-playing and character dialog | No |
| `qwen-flash-character` | Fast, lower-cost role-playing | No |

### Current third-party models

| Model IDs | Token Plan scope |
|---|---|
| `deepseek-v4-pro`, `deepseek-v4-pro-0813`, `deepseek-v4-flash-0731`, `deepseek-v4.1-flash` | Individual + Team |
| `glm-5.3`, `glm-5.2` | Individual + Team |
| `deepseek-v4-flash`, `deepseek-v3.2`, `kimi-k2.7-code`, `glm-5.1` | Team only |
| `kimi-k3` | Listed by the current PAYG catalog/API; not in Token Plan |

## Vision and OCR specialists

| Model ID | Use | Token Plan |
|---|---|---|
| `qwen3-vl-plus` | High-quality Qwen3-VL understanding, localization, and document parsing | No |
| `qwen3-vl-flash` | Faster Qwen3-VL understanding | No |
| `qwen3-vl-235b-a22b-thinking` | Thinking-only open-source vision model | No |
| `qwen3-vl-235b-a22b-instruct` | Non-thinking open-source vision model | No |
| `qwen-vl-ocr` | Rolling OCR specialist | No |
| `qwen-vl-ocr-2025-11-20` | Pinned OCR specialist; 38,192 context, 30,000 max input, 8,192 max output | No |

`deepseek-v4.1-flash` and `kimi-k2.7-code` are also listed as visual-understanding models by their applicable Token Plan edition.

## Omni

| Model ID | Use | Token Plan |
|---|---|---|
| `qwen3.5-omni-flash` | Text/image/audio/video input and text or speech output | No |
| `qwen3.5-omni-plus` | High-quality omni variant with text or speech output | No |
| `qwen3-omni-flash` | Voice + vision chat; thinking supported, with no audio output in thinking mode | No |
| `qwen3-omni-flash-realtime` | Real-time multimodal voice interaction over WebSocket | No |

Qwen3.5-Omni has dated snapshots from `2026-03-15`; Qwen3-Omni-Flash and its realtime variant have snapshots from `2025-09-15` and `2025-12-01`. Omni speech output and realtime interaction require their matching APIs, not the TTS script.

## Image generation

| Model ID | Use | Token Plan |
|---|---|---|
| `qwen-image-3.0-pro` | Recommended current default for generation and editing | Individual + Team |
| `qwen-image-3.0` | Current general generation and editing | No |
| `qwen-image-2.0-pro`, `qwen-image-2.0` | Previous fused generation and editing generation | Team only |
| `wan2.7-image-pro`, `wan2.7-image` | Multi-function generation/editing; Pro supports up to 4K text-to-image, standard up to 2K | Individual + Team |
| `wan2.6-t2i` | Dedicated text-to-image | No |
| `wan2.6-image` | Reference-based editing and interleaved output | No |
| `wan2.5-t2i-preview` | Text-to-image preview | No |
| `wan2.5-i2i-preview` | One-to-three-reference image editing/fusion | No |
| `qwen-image-max`, `qwen-image-plus`, `qwen-image` | Qwen-Image generation aliases retained by the current API | No |
| `qwen-image-edit-max`, `qwen-image-edit-plus`, `qwen-image-edit` | Qwen-Image editing | No |
| `z-image-turbo` | Synchronous single-output text-to-image | No |
| `qwen-mt-image-2.0` | Image translation | No |

Wan2.2 text-to-image models are omitted because that generation was released in July 2025 and does not pass the cutoff.

## Video generation

| Model ID | Use | Token Plan |
|---|---|---|
| `happyhorse-1.1-t2v` | Text-to-video, audio, 3–15s | Individual + Team |
| `happyhorse-1.1-i2v` | First-frame image-to-video, audio, 3–15s | Individual + Team |
| `happyhorse-1.1-r2v` | Reference-image-to-video, audio, 3–15s | Individual + Team |
| `wan3.0-video`, `wan3.0-video-prime` | All-in-one text/image/reference video, first+last frames, 2–30s | No |
| `wan2.7-t2v` | Text-to-video, 2–15s | No |
| `wan2.7-i2v` | First-frame, first+last-frame, and continuation, 2–15s | No |
| `wan2.7-r2v-2026-06-12` | Reference-to-video, 2–10s | No |
| `wan2.7-videoedit` | Instruction editing and video migration, up to 10s | No |
| `happyhorse-1.0-video-edit` | Prompt-driven editing, 3–15s | No |
| `wan2.6-t2v`, `wan2.6-i2v`, `wan2.6-i2v-flash`, `wan2.6-r2v`, `wan2.6-r2v-flash` | Previous audio-capable Wan generation | No |
| `wan2.5-t2v-preview`, `wan2.5-i2v-preview` | Previous audio-capable preview generation | No |
| `wan2.2-kf2v-flash` | Legacy first-and-last-frame compatibility mode; fixed 5s and silent | No |
| `wan2.1-vace-plus` | Legacy function-based VACE repainting, editing, extension, and outpainting | No |
| `wan2.2-animate-move`, `wan2.2-animate-mix` | Character motion transfer and character replacement | No |

Older Wan2.2 generation models are generally omitted. `wan2.2-kf2v-flash`, `wan2.1-vace-plus`, and the animation models are retained as explicit compatibility exceptions because the bundled runtime exposes those feature-specific request contracts and no newer model is payload-compatible with them.

## Speech

| Model ID | Use | Token Plan |
|---|---|---|
| `qwen-audio-3.0-tts-plus` | Quality-focused WebSocket TTS; default | Individual + Team |
| `qwen-audio-3.0-tts-flash` | Low-latency WebSocket TTS | No |
| `qwen3-tts-flash` | HTTP TTS | No |
| `qwen3-tts-instruct-flash` | HTTP TTS with instruction control | No |
| `qwen3-tts-vd-2026-01-26` | Voice design | No |
| `qwen3-tts-vc-2026-01-22` | Voice cloning | No |
| `cosyvoice-v3-plus`, `cosyvoice-v3-flash` | WebSocket CosyVoice TTS | No |
| `qwen-audio-3.0-realtime-plus` | Realtime voice conversation | Individual + Team |
| `qwen-audio-3.0-asr-flash` | Speech recognition | Individual + Team |

### PAYG speech recognition

| Model ID | Use | Token Plan |
|---|---|---|
| `qwen3-asr-flash` | General PAYG speech recognition | No |
| `qwen3-asr-flash-realtime` | Realtime streaming recognition | No |
| `qwen3-asr-flash-filetrans` | File transcription | No |

## Text translation

| Model ID | Use | Token Plan |
|---|---|---|
| `qwen-mt-plus` | Highest-quality text translation | No |
| `qwen-mt-flash` | Faster text translation | No |
| `qwen-mt-lite` | Lower-cost text translation | No |
| `qwen-mt-turbo` | Balanced legacy translation option | No |

## Embedding / Rerank

| Model ID | Use | Token Plan |
|---|---|---|
| `qwen3.7-text-embedding` | Text embedding for semantic search, RAG retrieval, and clustering | No |
| `qwen3-rerank` | Reranking: score a query against candidate documents after retrieval | No |

`qwen3.7-text-embedding` was released on 2026-08-11 and supplies the recent text-embedding option. Embedding and reranking use their dedicated APIs, not Chat Completions; neither is available on Token Plan.

## Token Plan exact allowlists

The current Token Plan catalog contains 20 Individual models and 27 Team models. Use [qwencloud-token-plan-models.md](qwencloud-token-plan-models.md) for the exact allowlists; never infer that a dated snapshot or a related sub-variant is included.

# QwenCloud Video Generation Models

> Catalog checked: 2026-09-18. The discovery catalog focuses on model families or dated snapshots released on or after 2025-08-01. Two older models are retained as explicit runtime-compatibility exceptions: `wan2.2-kf2v-flash` for the dedicated `kf2v` endpoint/payload and `wan2.1-vace-plus` for the function-based `vace` payload. They must not be silently replaced with newer models that use different protocols.

## Defaults and recommendations

| Mode | Runtime default | Notes |
|------|-----------------|-------|
| Text-to-video (`t2v`) | `happyhorse-1.1-t2v` | Token Plan + PAYG. |
| Image-to-video (`i2v`) | `happyhorse-1.1-i2v` | Token Plan + PAYG. |
| First-and-last-frame (`kf2v`) | `wan2.2-kf2v-flash` | PAYG-only legacy compatibility default; fixed 5s, silent, and uses the dedicated `kf2v` endpoint/payload. |
| Reference-based role-play (`r2v`) | `happyhorse-1.1-r2v` | Token Plan + PAYG. |
| Function-based editing (`vace`) | `wan2.1-vace-plus` | PAYG-only legacy compatibility default; preserves VACE `function`, mask, extension, and outpainting fields. |
| Prompt-driven editing (`videoedit`) | `wan2.7-videoedit` | PAYG-only; unified media protocol. |
| Character animation (`animate`) | `wan2.2-animate-move` | PAYG-only; image plus driving video. |

Never replace an explicitly selected model or silently change the requested mode because of plan restrictions.

The two compatibility defaults above are deliberate exceptions to the discovery cutoff. Do not substitute `wan3.0-video` for an implicit `kf2v` request: Wan 3.0 uses the all-in-one i2v media protocol rather than the dedicated legacy `kf2v` request shape. A user may explicitly select `wan3.0-video` or `wan3.0-video-prime` for modern first-and-last-frame generation, in which case the runtime routes it through the compatible i2v builder. Likewise, do not substitute `wan2.7-videoedit` for an implicit VACE request: `videoedit` uses a media protocol and is not feature-equivalent to VACE's function-based mask, extension, or outpainting operations.

## All-in-one and text-to-video

| Model | Capability | Important limits |
|-------|------------|------------------|
| `wan3.0-video` | All-in-one generation, references, editing, and extension | Up to 30s; 480P–1080P; optional audio; PAYG-only. |
| `wan3.0-video-prime` | Faster Wan 3.0 tier | Same modes and flat request shape; PAYG-only. |
| `wan2.7-t2v` | Ratio control, automatic audio, long prompts | 720P/1080P; uses `resolution` + `ratio`. |
| `wan2.7-t2v-2026-06-12` | Wan 2.7 text-to-video snapshot | Same capabilities as `wan2.7-t2v`. |
| `wan2.7-t2v-2026-04-25` | Wan 2.7 text-to-video snapshot | Same capabilities as `wan2.7-t2v`. |
| `happyhorse-1.1-t2v` | Default text-to-video with audio | 480P–1080P; Token Plan + PAYG. |
| `happyhorse-1.0-t2v` | Earlier HappyHorse text-to-video | Same request family as 1.1. |
| `wan2.6-t2v` | Audio and multi-shot narrative | 2–15s; 720P/1080P. |
| `wan2.5-t2v-preview` | Text-to-video with audio | 5s or 10s. |

## Image, reference, and transition video

| Model | Mode | Important compatibility |
|-------|------|-------------------------|
| `wan2.7-i2v` | i2v | Unified media protocol for first/last frame, continuation, and audio sync. |
| `wan2.7-i2v-2026-04-25` | i2v | Snapshot with the same capabilities as `wan2.7-i2v`. |
| `happyhorse-1.1-i2v` | i2v | Exactly one first-frame reference; Token Plan + PAYG. |
| `happyhorse-1.0-i2v` | i2v | Earlier strict first-frame request format. |
| `wan2.6-i2v-flash`, `wan2.6-i2v` | i2v | Audio-capable, multi-shot, 2–15s. |
| `wan2.5-i2v-preview` | i2v | Audio; 5s or 10s. |
| `wan2.7-r2v` | r2v | Up to five mixed media references. |
| `wan2.7-r2v-2026-06-12` | r2v | Snapshot; up to five mixed image/video references. |
| `happyhorse-1.1-r2v` | r2v | Up to nine reference images; Token Plan + PAYG. |
| `happyhorse-1.0-r2v` | r2v | Earlier HappyHorse reference-video request family. |
| `wan2.6-r2v`, `wan2.6-r2v-flash` | r2v | Single/multi-character role-play; 2–10s. |
| `wan2.2-kf2v-flash` | kf2v | **Legacy compatibility exception and runtime default.** Dedicated first/last-frame payload; fixed 5s; silent. |

## Editing and animation

| Model | Mode | Important compatibility |
|-------|------|-------------------------|
| `wan2.1-vace-plus` | vace | **Legacy compatibility exception and runtime default.** Function-based reference, repainting, local edit, extension, and outpainting; up to 5s; silent. |
| `wan2.7-videoedit` | videoedit | Optional prompt and negative prompt; media protocol; up to four image references. |
| `happyhorse-1.0-video-edit` | videoedit | Prompt required; one video plus up to five image references. |
| `wan2.2-animate-move` | animate | Transfers actions/expressions from a driving video to a character image. |
| `wan2.2-animate-mix` | animate | Replaces the video subject with the subject from an image. |

Animation requests require `image_url`, `video_url`, and `mode` (`wan-std` or `wan-pro`) and do not accept prompt, resolution, duration, seed, or watermark parameters.

## Token Plan compatibility and billing

- Only `happyhorse-1.1-t2v`, `happyhorse-1.1-i2v`, and `happyhorse-1.1-r2v` are Token Plan video models in the current catalog.
- `kf2v`, `vace`, `videoedit`, and `animate` have no Token Plan model; use PAYG without silently changing the task.
- Video output is billed per generated second; rates vary by model and resolution, and reference/editing calls may also bill input-video duration.

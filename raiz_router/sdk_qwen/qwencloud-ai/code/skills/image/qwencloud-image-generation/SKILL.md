---
name: qwencloud-image-generation
description: "Generate and edit images using Wan and Qwen Image models. Supports text-to-image, image editing (style transfer, subject consistency, text rendering), and interleaved text-image output. TRIGGER when: user wants to create illustrations, product images, artistic designs, posters, text-to-image generation, edit/transform existing images, apply style transfer, generate images based on reference photos, interleaved text-image content, mentions Wan/Qwen Image models/AI art creation, or explicitly invokes this skill by name (e.g. use qwencloud-image-generation). DO NOT TRIGGER when: user wants to understand/analyze existing images or OCR (use qwencloud-vision), video generation (use qwencloud-video-generation), text-only tasks."
compatibility: "Requires Python 3.9+; curl is PAYG-only. Cursor: auto-loaded. Claude Code: read this skill's SKILL.md before first use."
---

# Qwen Image Generation

Generate and edit images using Wan and Qwen Image models. Supports text-to-image, reference-image editing (style
transfer, subject consistency, multi-image composition, text rendering), and interleaved text-image output.
This skill is part of **qwencloud/qwencloud-ai**.

## Skill directory

Use this skill's internal files to execute and learn. Load reference files on demand when the default path fails or you need details.

| Location | Purpose |
|----------|---------|
| `scripts/image.py` | Default execution — sync/async, upload, download |
| `references/execution-guide.md` | Fallback: curl (sync/async), code generation |
| `references/prompt-guide.md` | Prompt formulas, style keywords, negative_prompt, prompt_extend decision |
| `references/api-guide.md` | API supplement |
| `references/sources.md` | Official documentation URLs |

## Security

**NEVER output any API key or credential in plaintext.** Always use variable references (`$QWENCLOUD_API_KEY` in shell, `os.environ["QWENCLOUD_API_KEY"]` in Python). The scripts accept `QWENCLOUD_API_KEY`, then `QWEN_API_KEY`, then `DASHSCOPE_API_KEY`. Any check or detection of credentials must be **non-plaintext**: report only status (e.g. "set" / "not set", "valid" / "invalid"), never the value. Never display contents of `.env` or config files that may contain secrets.

**When the API key is not configured, NEVER ask the user to provide it directly.** Instead, help create a `.env` file with a placeholder (`QWENCLOUD_API_KEY=sk-your-key-here`) and instruct the user to replace it with their actual key from the [QwenCloud Console](https://home.qwencloud.com/api-keys). Only write the actual key value if the user explicitly requests it.

## Key Compatibility

Scripts support both **standard QwenCloud API keys** (`sk-...`) and **Token Plan keys** (`sk-sp-...`). Token Plan keys are automatically routed to the Token Plan endpoint for supported image models — see the [Token Plan model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-token-plan-models.md). If CDN access fails, use the [local fallback](cdn/references/qwencloud-token-plan-models.md).

**Token Plan: do not use curl; always use the bundled Python script.**

Coding Plan keys (also `sk-sp-` prefix but purchased via Coding Plan subscription) cannot be used — image generation models are not available on Coding Plan. The script detects key type at startup and routes accordingly. If qwencloud-ops-auth is installed, see its `references/codingplan.md` for full details.

Detect the API key type without exposing the key:

```bash
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from qwencloud_lib import detect_api_key_type
print(detect_api_key_type('scripts/qwencloud_lib.py'))
"
```

| Output | Meaning |
|--------|---------|
| `token-plan` | Token Plan key detected (`sk-sp-` prefix) |
| `payg` | Standard PAYG key detected |
| `not-set` | No API key found in environment |

## Mode Selection Guide

Before choosing a mode, fetch and read the current [QwenCloud image-generation model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-image-generation-models.md). It contains the mode-to-model recommendations, model list, basic model information, compatibility notes, and default model. If CDN access fails, use the [local fallback](cdn/references/qwencloud-image-generation-models.md).

## Model Selection

> **🚫 CRITICAL — Never override user-specified parameters.** If the user explicitly specifies a model (in prompt or request JSON), you MUST use exactly that model. Do NOT:
> - Replace it with a "better suited" or newer model (e.g., swapping the user's `wan2.6-t2i` for `wan2.7-image` because the task "looks like a multi-function job")
> - Add parameters the user did not ask for (`thinking_mode`, `color_palette`, `bbox_list`, style hints)
> - "Optimize" any explicit user choice
>
> Mode/Model guidance below applies **only when the user has NOT specified a model**. If the user-specified model cannot achieve what they asked for (e.g. a hard API constraint), execute their choice as given if possible; otherwise surface the constraint to the user and let THEM decide — do not silently switch.

Use the image-generation model catalog linked above for current model families, defaults, recommendations, compatibility, and limits.

1. **User specified a model** → **MANDATORY: use that exact model** — do not substitute, do not "optimize", do not add unrequested parameters.
2. **Consult the qwencloud-model-selector skill** when model choice depends on requirement, scenario, or pricing.
3. **No model specified** → choose the current default or task-specific recommendation from the model catalog. If the user's requested operation conflicts with a model's documented hard constraint, explain the constraint and let the user decide; never silently replace an explicitly selected model.

> **⚠️ Important**: The model catalog is a **point-in-time snapshot** and may be outdated. Model availability
> changes frequently. **Always check the [official model list](https://www.qwencloud.com/models)
> for the authoritative, up-to-date catalog before making model decisions.**

> **Model details**: For more information about a specific model, direct the user to its detail page: `https://www.qwencloud.com/models/<model-name>` (replace `<model-name>` with the exact model ID, e.g. `wan2.7-image-pro` → https://www.qwencloud.com/models/wan2.7-image-pro). NEVER modify or guess the model name in the URL.

> **Dynamic model queries**: If the **qwencloud-model-selector** skill or **QwenCloud CLI** (`qwencloud models info <model>`) is available, use it for real-time model data. CLI requires authentication — see the **qwencloud-usage** skill for login flow.

## Execution

> **⚠️ Multiple artifacts**: When generating multiple files in a single session, you MUST append a numeric suffix to each filename (e.g. `out_1.png`, `out_2.png`) to prevent overwrites.

### Prerequisites

- **API Key**: Check `QWENCLOUD_API_KEY`, `QWEN_API_KEY`, then `DASHSCOPE_API_KEY` using a **non-plaintext** check only (e.g. in shell: `[ -n "$QWENCLOUD_API_KEY" ]`; report only "set" or "not set", never the key value). If not set: run the **qwencloud-ops-auth** skill if available; otherwise guide the user to obtain a key from [QwenCloud Console](https://home.qwencloud.com/api-keys) and set it via `.env` file (`echo 'QWENCLOUD_API_KEY=sk-your-key-here' >> .env` in project root or current directory) or environment variable. The script searches for `.env` in the current working directory and the project root. Skills may be installed independently — do not assume qwencloud-ops-auth is present.
  **Note**: The script auto-loads `.env` from the current directory and the project root (in addition to any exported environment variable). A shell check showing `$QWENCLOUD_API_KEY` as "not set" does NOT mean the script will fail — it may still find the key in `.env`. Treat the shell check as informational only; the authoritative test is simply running the script (it exits with a clear error if no key is found anywhere).
- Python 3.9+ (stdlib only, **no pip install needed**)

### Environment Check

Before first execution, verify Python is available:

```bash
python3 --version  # must be 3.9+
```

If `python3` is unavailable or below 3.9, PAYG may use **Path 2 (curl)**; Token Plan must install Python 3.9+ instead.

### Default: Run Script

**Script path**: Scripts are in the `scripts/` subdirectory **of this skill's directory** (the directory containing this
SKILL.md). **You MUST first locate this skill's installation directory, then ALWAYS use the full absolute path to execute
scripts.** Do NOT assume scripts are in the current working directory. Do NOT use `cd` to switch directories before
execution.

**Execution note:** Run all scripts in the **foreground** — wait for stdout; do not background.

**Discovery:** Run `python3 <this-skill-dir>/scripts/image.py --help` first to see all available arguments.

```bash
# Text-to-image (use the default from the CDN model catalog)
python3 <this-skill-dir>/scripts/image.py \
  --request '{"prompt":"A cozy flower shop with wooden door"}' \
  --output output/qwencloud-image-generation/images/out.png \
  --print-response

# Image editing with reference images (wan2.6-image)
python3 <this-skill-dir>/scripts/image.py \
  --model wan2.6-image \
  --request '{"prompt":"Apply watercolor painting style to this photo","reference_images":["https://img.alicdn.com/imgextra/i1/NotRealJustExample/photo.jpg"],"n":1,"size":"1K"}' \
  --output output/qwencloud-image-generation/images/out.png \
  --print-response

# z-image-turbo (sync-only, no n; size omitted → server default 1024*1536)
python3 <this-skill-dir>/scripts/image.py \
  --model z-image-turbo \
  --request '{"prompt":"A sitting orange cat, realistic","prompt_extend":false}' \
  --output output/qwencloud-image-generation/images/out.png \
  --print-response

# qwen-image-3.0-pro (no size → auto-recommended resolution)
python3 <this-skill-dir>/scripts/image.py \
  --model qwen-image-3.0-pro \
  --request '{"prompt":"A poster reading \"限时特惠\"","enable_thinking":true}' \
  --output output/qwencloud-image-generation/images/out.png \
  --print-response

# qwen-mt-image-2.0 (API supports sync/async; bundled script uses async)
python3 <this-skill-dir>/scripts/image.py \
  --model qwen-mt-image-2.0 \
  --request '{"image_url":"https://example.com/poster_zh.jpg","source_lang":"zh","target_lang":"en"}' \
  --output output/qwencloud-image-generation/images/out.png \
  --print-response
```

**More examples** (interleaved output, wan2.5-i2i, qwen-image-2.0-pro, qwen-image-plus): See [execution-guide.md](references/execution-guide.md)

| Argument | Description |
|----------|-------------|
| `--request '{...}'` | JSON request body |
| `--file path.json` | Load request from file |
| `--async` | Force async mode; the script auto-enables it where its implementation uses async. It is ignored for sync-only models such as `qwen-image-max` |
| `--model ID` | Override model (check the model catalog above for the current default) |
| `--output path` | Save image to path (or directory for multi-image output). When writing multiple images to the same directory, files are automatically named using the unique identifier from the OSS URL, preventing overwrites across runs. Explicit file paths still take priority; use distinct filenames across calls to avoid overwriting |
| `--print-response` | Print response JSON to stdout |

### Verify Result

- Exit code `0` + output contains valid JSON with `output.results` or `output.task_id` → **success**
- Non-zero exit, HTTP error, empty response, or error JSON → **fail**
- Async: submission must return `output.task_id`; poll must reach `task_status: SUCCEEDED`
- **Post-execution check**: Verify the output file exists and has non-zero size (`ls -la <output_path>`)
- **MANDATORY — stderr signal check**: After confirming the result, scan the command's stderr output for `[ACTION_REQUIRED]` or `[UPDATE_AVAILABLE]`. If either signal is present, you **MUST** follow the instructions in [Update Check](#update-check-mandatory-post-execution) below before responding to the user.

### On Failure

If the script fails, match the error output against the diagnostic table below to determine the resolution. If no match, read [execution-guide.md](references/execution-guide.md) for alternative paths: curl commands (Path 2 — sync and async), code generation (Path 3), and autonomous resolution (Path 5).

**If Python is not available at all** → PAYG may use Path 2 (curl); Token Plan must install Python 3.9+.

| Error Pattern | Diagnosis | Resolution |
|---------------|-----------|------------|
| `command not found: python3` | Python not on PATH | Try `python` or `py -3`; install Python 3.9+ if missing |
| `Python 3.9+ required` | Script version check failed | Upgrade Python to 3.9+ |
| `SyntaxError` near type hints | Python < 3.9 | Upgrade Python to 3.9+ |
| `QWENCLOUD_API_KEY/QWEN_API_KEY/DASHSCOPE_API_KEY not found` | Missing API key | Obtain key from [QwenCloud Console](https://home.qwencloud.com/api-keys); add to `.env`: `echo 'QWENCLOUD_API_KEY=sk-...' >> .env`; or run **qwencloud-ops-auth** if available |
| `HTTP 401` | Invalid or mismatched key | Run **qwencloud-ops-auth** (non-plaintext check only); verify key is valid |
| `SSL: CERTIFICATE_VERIFY_FAILED` | SSL cert issue (proxy/corporate) | macOS: run `Install Certificates.command`; else set `SSL_CERT_FILE` env var |
| `URLError` / `ConnectionError` | Network unreachable | Check internet; set `HTTPS_PROXY` if behind proxy |
| `HTTP 429` | Rate limited | Wait and retry with backoff |
| `HTTP 5xx` | Server error | Retry with backoff |
| `PermissionError` | Can't write output | Use `--output` to specify writable directory |

## Quick Reference

### Request Fields (Common)

| Field | Type | Description |
|-------|------|-------------|
| `prompt` | string | Text description of the image to generate (required; NOT for image translation) |
| `negative_prompt` | string | Content to avoid in the image (max 500 chars) |
| `size` | string | Resolution; use the model catalog for cataloged limits and the API guide or official documentation for model-specific values not listed there |
| `seed` | int | Random seed for reproducibility [0, 2147483647] |
| `model` | string | Model ID; check the model catalog above for the current default and supported models |
| `prompt_extend` | bool | Enable prompt rewriting (default: true; image editing mode only) |
| `enable_thinking` | bool | qwen-image-3.0 only — enhanced reasoning (default: true). Only effective when `prompt_extend=true` |
| `prompt_extend_mode` | string | qwen-image-3.0 only — `direct` (DPE, default) or `agent` (APE; t2i only) |

### Request Fields (wan2.7-image-pro / wan2.7-image — Multi-function)

| Field | Type | Description |
|-------|------|-------------|
| `reference_images` | string[] | 0–9 image URLs or local paths |
| `reference_image` | string | Single image URL/path (shorthand) |
| `size` | string | `1K`, `2K` (default), or `4K` (pro only, t2i mode). Or pixel dimensions |
| `enable_sequential` | bool | `true`: sequential multi-image mode (n=1–12). `false` (default): single/batch mode (n=1–4) |
| `n` | int | Images to generate. Sequential mode: 1–12 (default 12). Non-sequential: 1–4 (default 4). **Billed per image.** |
| `thinking_mode` | bool | Enable enhanced reasoning for better quality (default: true). Only for t2i (no images, non-sequential) |
| `bbox_list` | List[List[List[int]]] | Interactive editing regions. Format: `[[[x1,y1,x2,y2],...], ...]`. List length = image count. Empty `[]` for images without edits |
| `color_palette` | array | Custom color theme (3–10 colors). Each: `{"hex":"#C2D1E6","ratio":"23.51%"}`. Sum of ratios = 100%. Non-sequential mode only |
| `watermark` | bool | Add "AI Generated" watermark (default: false) |

**Note**: `thinking_mode` increases latency but improves quality. `enable_sequential` generates a coherent image sequence (e.g., same character across scenes).

### Request Fields (wan2.6-image — Image Editing)

| Field | Type | Description |
|-------|------|-------------|
| `reference_images` | string[] | 1–4 image URLs or local paths for editing mode; 0–1 for interleave mode |
| `reference_image` | string | Single image URL/path (shorthand; `reference_images` takes precedence) |
| `enable_interleave` | bool | `false` (default): image editing mode; `true`: interleaved text-image output |
| `n` | int | Number of images to generate in editing mode (1–4, default: 1). **Billed per image.** |
| `max_images` | int | Max images in interleave mode (1–5, default: 5). **Billed per image.** |
| `watermark` | bool | Add "AI Generated" watermark (default: false) |

### Other Models

Use the model catalog linked above for the current model list and model-specific compatibility differences.

### Image Translation Request Fields

For an image-translation model selected from the catalog, use `image_url`, `source_lang`, and `target_lang`; do not send `prompt`. The optional `ext` object carries domain/style hints, exact-match skip words, terminology pairs, and image-segmentation settings. A successful task with no translatable text may still be billed.

**Full parameter tables**: See [api-guide.md](references/api-guide.md#wan25-i2i-preview--general-image-editing) for detailed parameters.

### Size Reference (wan2.6-image)

- **Editing mode**: `1K` (default, ~1280×1280) or `2K` (~2048×2048)
- **Interleave mode**: pixel dimensions with total pixels in [768×768, 1280×1280]

**Common aspect ratios**: `1280*1280` (1:1), `960*1280` (3:4), `1280*960` (4:3), `720*1280` (9:16), `1280*720` (16:9)

### Response Fields

| Field | Description |
|-------|-------------|
| `image_url` | URL of generated image (24h validity). **Use this when chaining to another skill.** |
| `image_urls` | Array of all image URLs (multi-image output, wan2.6-image, qwen-image-edit) |
| `image_count` | Number of generated images |
| `local_path` | Local file path of the downloaded image. **Use this for user preview or non-API operations.** |
| `local_paths` | Array of local file paths (multi-image output) |
| `interleaved_content` | Array of `{type, text/image}` objects (interleave mode) |
| `width` / `height` | Image dimensions |
| `seed` | Seed used |

## API Details

- **Sync endpoint (wan2.6-t2i, wan2.6-image editing, qwen-image-edit series, qwen-image-max, z-image-turbo)**: `POST /api/v1/services/aigc/multimodal-generation/generation`
- **Async endpoint (wan2.6 and older t2i)**: `POST /api/v1/services/aigc/image-generation/generation` with `X-DashScope-Async: enable`
- **Async endpoint (wan2.5-i2i-preview; bundled-script route for qwen-mt-image-2.0)**: `POST /api/v1/services/aigc/image2image/image-synthesis` with `X-DashScope-Async: enable`. The image-translation API itself supports both sync and async; `image.py` currently implements async submission and polling.
- **Async endpoint (qwen-image-plus and qwen-image)**: `POST /api/v1/services/aigc/text2image/image-synthesis` with `X-DashScope-Async: enable`. `qwen-image-max` is sync-only and must not use this route.
- **wan2.6-t2i resolution**: Total pixels in [1280x1280, 1440x1440], aspect ratio [1:4, 4:1]
- **wan2.6-image resolution**: Editing mode [768x768, 2048x2048]; Interleave mode [768x768, 1280x1280]; aspect ratio [1:4, 4:1]
- **Input images** (wan2.6-image): JPEG/JPG/PNG/BMP/WEBP, 240–8000px per dimension, ≤10MB
- **Local files**: Script auto-uploads to DashScope temp storage (`oss://` URL, 48h TTL). Pass local paths directly — no manual upload step needed.
  > **⚠️ Token Plan limitation**: Token Plan does not support local file upload. If you are using a Token Plan key (`sk-sp-...`), provide reference images as publicly accessible https:// URLs instead of local paths.
- **Production**: Default temp storage has **48h TTL** and **100 QPS upload limit** — not suitable for production, high-concurrency, or load-testing. To use your own OSS bucket, set `QWEN_TMP_OSS_BUCKET` and `QWEN_TMP_OSS_REGION` in `.env`, install `pip install alibabacloud-oss-v2`, and provide credentials via `QWEN_TMP_OSS_AK_ID` / `QWEN_TMP_OSS_AK_SECRET` or the standard `OSS_ACCESS_KEY_ID` / `OSS_ACCESS_KEY_SECRET`. Use a RAM user with least-privilege (`oss:PutObject` + `oss:GetObject` on target bucket only). If qwencloud-ops-auth is installed, see its `references/custom-oss.md` for the full setup guide.
- **Interleaved sync**: Requires streaming (`X-DashScope-Sse: enable` + `stream: true`); use async mode via this script instead

## Cross-Skill Chaining

When using generated images as input for another skill (e.g., video-gen i2v, vision analyze):
- **Pass `image_url` directly** — do NOT download and re-pass as local path
- All downstream scripts detect URL prefixes (`https://`, `oss://`) and pass them through without re-upload
- Use `local_path` only for user preview or non-API operations (e.g., opening in editor)

| Scenario | Use |
|----------|-----|
| Feed to another skill (video-gen, vision, image-edit) | `image_url` (URL) |
| Show to user / open in editor | `local_path` (local file) |

## Error Handling

| HTTP | Meaning | Action |
|------|---------|--------|
| 401 | Invalid or missing API key | Run **qwencloud-ops-auth** if available; else prompt user to set key (non-plaintext check only) |
| 400 | Bad request (invalid prompt, size) | Verify parameters and constraints |
| 429 | Rate limited | Retry with exponential backoff |
| 5xx | Server error | Retry with exponential backoff |

> **Usage & billing**: Use the **qwencloud-usage** skill to check usage, free tier quota, and billing directly. Alternatively, the user can visit the QwenCloud console:
> [Usage Analytics](https://home.qwencloud.com/analytics) |
> [Pay-as-you-go Billing](https://home.qwencloud.com/billing/pay-as-you-go) |
> [Coding Plan Billing](https://home.qwencloud.com/billing/coding-plan)
>
> **NEVER fabricate, guess, or construct usage/billing/console URLs.** Only provide the exact links listed in this skill. If a URL is not listed here, do not invent one.

## Output Location

Prefer the **current working directory**. Default subdirectory: `./output/qwencloud-image-generation/`.

**Write prohibition**: NEVER write output files into this skill's installation directory or any `skills/` hierarchy. All generated content must go to `output/` under the current working directory or a user-specified path.

## Token Plan Support

Token Plan keys (`sk-sp-...`) are supported for select image models. The script auto-routes to the Token Plan endpoint.

> **⚠️ Token Plan limitation**: Token Plan does not support local file upload. If you are using a Token Plan key (`sk-sp-...`), provide reference images as publicly accessible https:// URLs instead of local paths.

### Supported models

Fetch and read the current [Token Plan model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-token-plan-models.md), then use an exact listed image-generation model. If CDN access fails, use the [local fallback](cdn/references/qwencloud-token-plan-models.md).

### Not supported via Token Plan

Models not listed as image-capable in the Token Plan model catalog require a PAYG key.

### Required header

`User-Agent: qwencloud-skills` is automatically included.

## Update Check (MANDATORY Post-Execution)

After script execution, check stderr for action signals. The script automatically detects update status and emits structured signals. You MUST act on them. This section also applies when the user explicitly asks to check for updates.

### Signal: `[ACTION_REQUIRED] qwencloud-update-check skill is not installed`

When stderr contains this signal, you MUST present the following options to the user and **wait for their response before proceeding**. Do NOT silently skip this.

> The update-check skill is not installed. It keeps you informed about new qwencloud/qwencloud-ai features and bug fixes.
>
> 1) **Install now** — I'll run the install command for you
> 2) **Skip for now** — do nothing this time
> 3) **Never remind me** — permanently suppress this prompt

After the user responds:
- User chooses **1** → run: `npx skills add QwenCloud/qwencloud-ai --skill qwencloud-update-check -y`, then run: `python3 <this-skill-scripts-dir>/gossamer.py --dismiss`
- User chooses **2** → run: `python3 <this-skill-scripts-dir>/gossamer.py --dismiss`, then continue normally
- User chooses **3** → run: `python3 <this-skill-scripts-dir>/gossamer.py --never-install`, then continue normally

### Signal: `[UPDATE_AVAILABLE]`

When stderr contains this signal, you MUST append a brief update notice to your response, including the version info and the update command shown in the stderr output.

### No signal in stderr

If stderr contains neither `[ACTION_REQUIRED]` nor `[UPDATE_AVAILABLE]`, no action is needed — the skill is installed and up to date (or cached within 24h).

### Explicit user request

When the user explicitly asks to check for updates (e.g. "check for updates", "check version"):
1. Look for `qwencloud-update-check/SKILL.md` in sibling skill directories.
2. If found — run: `python3 <qwencloud-update-check-dir>/scripts/check_update.py --print-response` and report the result.
3. If not found — present the install options above.

## References

- [execution-guide.md](references/execution-guide.md) — Fallback paths (curl sync/async, code generation, autonomous)
- [api-guide.md](references/api-guide.md) — API supplementary guide
- [sources.md](references/sources.md) — Official documentation URLs

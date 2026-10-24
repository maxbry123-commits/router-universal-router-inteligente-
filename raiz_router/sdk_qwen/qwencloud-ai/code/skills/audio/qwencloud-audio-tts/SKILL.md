---
name: qwencloud-audio-tts
description: "Synthesize speech from text with Qwen TTS models. TRIGGER when: user wants to convert text to speech, create voiceovers, generate audio narration, read text aloud, build TTS applications, mentions speech synthesis/voice generation/audio output from text, or explicitly invokes this skill by name (e.g. use qwencloud-audio-tts). DO NOT TRIGGER when: user wants speech recognition/ASR, text generation without audio, non-Qwen audio tasks."
compatibility: "Requires Python 3.9+; curl is PAYG-only. Cursor: auto-loaded. Claude Code: read this skill's SKILL.md before first use."
---

# Qwen Audio TTS (Text-to-Speech)

Synthesize natural speech from text using Qwen TTS models.
This skill is part of **qwencloud/qwencloud-ai**.

## Skill directory

Use this skill's internal files to execute and learn. Load reference files on demand when the default path fails or you need details.

| Location | Purpose |
|----------|---------|
| `scripts/tts.py` | Qwen TTS / Qwen Audio TTS (HTTP and WebSocket); current compatibility and defaults are in the model catalog below |
| `scripts/tts_cosyvoice.py` | CosyVoice (WebSocket API) — requires `dashscope` SDK; current compatibility and defaults are in the model catalog below |
| `references/cosyvoice-guide.md` | CosyVoice setup, voices, examples, errors |
| `references/execution-guide.md` | Fallback: curl (standard, instruct, streaming), code generation |
| `references/prompt-guide.md` | Text formatting for speech, instructions templates, voice selection |
| `references/api-guide.md` | API supplement |
| `references/sources.md` | Official documentation URLs |

## Security

**NEVER output any API key or credential in plaintext.** Always use variable references (`$QWENCLOUD_API_KEY` in shell, `os.environ["QWENCLOUD_API_KEY"]` in Python). The scripts accept `QWENCLOUD_API_KEY`, then `QWEN_API_KEY`, then `DASHSCOPE_API_KEY`. Any check or detection of credentials must be **non-plaintext**: report only status (e.g. "set" / "not set", "valid" / "invalid"), never the value. Never display contents of `.env` or config files that may contain secrets.

**When the API key is not configured, NEVER ask the user to provide it directly.** Instead, help create a `.env` file with a placeholder (`QWENCLOUD_API_KEY=sk-your-key-here`) and instruct the user to replace it with their actual key from the [QwenCloud Console](https://home.qwencloud.com/api-keys). Only write the actual key value if the user explicitly requests it.

## Key Compatibility

Scripts support both **standard QwenCloud API keys** (`sk-...`) and **Token Plan keys** (`sk-sp-...`). Token Plan keys are automatically routed to the Token Plan endpoint for supported TTS models — see [Token Plan Support](#token-plan-support) below.

**Token Plan: do not use curl; always use the bundled Python scripts.**

Coding Plan keys (also `sk-sp-` prefix but purchased via Coding Plan subscription) cannot be used — TTS models are not available on Coding Plan. The script detects key type at startup and routes accordingly. If qwencloud-ops-auth is installed, see its `references/codingplan.md` for full details.

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

For Token Plan, fetch and read the current [Token Plan model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-token-plan-models.md), then use an exact listed model with `scripts/tts.py`. If CDN access fails, use the [local fallback](cdn/references/qwencloud-token-plan-models.md).

## Model Selection

> **🚫 CRITICAL — Never override the user's model choice.** If the user (or the request JSON) explicitly specifies a `model`, you MUST use exactly that model. Do NOT:
> - Replace it with a "better suited" model (e.g., switching to `qwen3-tts-instruct-flash` for stylized/poetic text)
> - Add `instructions` the user did not ask for
> - Modify any parameter the user explicitly provided
>
> Model selection guidance below applies **only when the user has NOT specified a model**.

Before selecting, recommending, or defaulting a model, fetch and read the current [QwenCloud audio TTS model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-audio-tts-models.md). It contains the model list, basic model information, script and voice compatibility, recommendations, and defaults. If CDN access fails, use the [local fallback](cdn/references/qwencloud-audio-tts-models.md).

Consult the **qwencloud-model-selector** skill when model choice depends on capability, scenario, or pricing. CosyVoice requires the `dashscope` SDK and uses different voices; see [cosyvoice-guide.md](references/cosyvoice-guide.md).

> **⚠️ Important**: The model catalog is a **point-in-time snapshot** and may be outdated. Model availability
> changes frequently. **Always check the [official model list](https://www.qwencloud.com/models)
> for the authoritative, up-to-date catalog before making model decisions.**

> **Model details**: For more information about a specific model, direct the user to `https://www.qwencloud.com/models/<model-name>`. Replace `<model-name>` with the exact model ID; never modify or guess it.

> **Dynamic model queries**: If the **qwencloud-model-selector** skill or **QwenCloud CLI** (`qwencloud models info <model>`) is available, use it for real-time model data. CLI requires authentication — see the **qwencloud-usage** skill for login flow.

## Available Voices

Use the QwenCloud audio TTS model catalog linked above for current model-to-voice compatibility and defaults. For complete voice inventories, use the official voice-list links in [sources.md](references/sources.md).

> **Voice defaulting**: When no voice is supplied for a Qwen-Audio WebSocket model, `tts.py` selects that model's configured default voice and prints a notice to stderr. Any explicit voice—including explicit `Cherry`—is passed through unchanged. Fetch the model catalog before choosing a voice.

## Execution

> **⚠️ Multiple artifacts**: When generating multiple files in a single session, you MUST append a numeric suffix to each filename (e.g. `out_1.wav`, `out_2.wav`) to prevent overwrites.

### Qwen TTS (HTTP API) — `tts.py`

#### Prerequisites

- **API Key**: Check `QWENCLOUD_API_KEY`, `QWEN_API_KEY`, then `DASHSCOPE_API_KEY` using a **non-plaintext** check only (e.g. in shell: `[ -n "$QWENCLOUD_API_KEY" ]`; report only "set" or "not set", never the key value). If not set: run the **qwencloud-ops-auth** skill if available; otherwise guide the user to obtain a key from [QwenCloud Console](https://home.qwencloud.com/api-keys) and set it via `.env` file (`echo 'QWENCLOUD_API_KEY=sk-your-key-here' >> .env` in project root or current directory) or environment variable. The script searches for `.env` in the current working directory and the project root. Skills may be installed independently — do not assume qwencloud-ops-auth is present.
  **Note**: The script auto-loads `.env` from the current directory and the project root (in addition to any exported environment variable). A shell check showing `$QWENCLOUD_API_KEY` as "not set" does NOT mean the script will fail — it may still find the key in `.env`. Treat the shell check as informational only; the authoritative test is simply running the script (it exits with a clear error if no key is found anywhere).
- Python 3.9+ (stdlib only, **no pip install needed**)

#### Environment Check

Before first execution, verify Python is available:

```bash
python3 --version  # must be 3.9+
```

If `python3` is unavailable or below 3.9, PAYG may use **Path 2 (curl)**; Token Plan must install Python 3.9+ instead.

#### Default: Run Script

**Script path**: Scripts are in the `scripts/` subdirectory **of this skill's directory** (the directory containing this SKILL.md). **You MUST first locate this skill's installation directory, then ALWAYS use the full absolute path to execute scripts.** Do NOT assume scripts are in the current working directory. Do NOT use `cd` to switch directories before execution.

**Execution note:** Run all scripts in the **foreground** — wait for stdout; do not background.

**Discovery:** Run `python3 <this-skill-dir>/scripts/tts.py --help` first to see all available arguments.

```bash
python3 <this-skill-dir>/scripts/tts.py \
  --request '{"text":"Hello, this is a test.","voice":"Cherry"}' \
  --output output/qwencloud-audio-tts/ \
  --print-response
```

| Argument | Description |
|----------|-------------|
| `--request '{...}'` | JSON request body |
| `--file path.json` | Load request from file |
| `--output path` | Save audio and response JSON to directory, or specify an audio file path (e.g. `speech.mp3`); use distinct filenames across calls to avoid overwriting |
| `--print-response` | Print response to stdout |
| `--model ID` | Override model |
| `--voice NAME` | Override voice |

#### Verify Result

- Exit code `0` + output contains valid JSON with `output.audio` field → **success**
- Non-zero exit, HTTP error, empty response, or error JSON → **fail**
- **Post-execution check**: Verify the output audio file exists and has non-zero size (`ls -la <output_dir>`)
- **MANDATORY — stderr signal check**: After confirming the result, scan the command's stderr output for `[ACTION_REQUIRED]` or `[UPDATE_AVAILABLE]`. If either signal is present, you **MUST** follow the instructions in [Update Check](#update-check-mandatory-post-execution) below before responding to the user.

#### On Failure

If the script fails, match the error output against the diagnostic table below to determine the resolution. If no match, read [execution-guide.md](references/execution-guide.md) for alternative paths: curl commands (Path 2 — standard, instruct, streaming), code generation (Path 3), and autonomous resolution (Path 5).

**If Python is not available at all** → PAYG may use Path 2 (curl); Token Plan must install Python 3.9+.

---

### CosyVoice — `tts_cosyvoice.py`

CosyVoice requires `dashscope` SDK. Quick start:

```bash
pip install dashscope>=1.25.17
python3 <this-skill-dir>/scripts/tts_cosyvoice.py --text "Hello"
```

> **Token Plan**: `tts_cosyvoice.py` rejects Token Plan keys at startup. Fetch the Token Plan catalog linked above and use an exact supported TTS model with `tts.py`, or use a PAYG key. Never replace an explicitly requested model without the user's confirmation.

> **Full guide**: [cosyvoice-guide.md](references/cosyvoice-guide.md) (setup, voices, examples, errors)

| Error Pattern | Diagnosis | Resolution |
|---------------|-----------|------------|
| `command not found: python3` | Python not on PATH | Try `python` or `py -3`; install Python 3.9+ if missing |
| `Python 3.9+ required` | Script version check failed | Upgrade Python to 3.9+ |
| `SyntaxError` near type hints | Python < 3.9 | Upgrade Python to 3.9+ |
| `cosyvoice models are not available on Token Plan` | Token Plan key detected | Use `tts.py` with an exact supported model from the Token Plan catalog, or a PAYG key |
| `QWENCLOUD_API_KEY/QWEN_API_KEY/DASHSCOPE_API_KEY not found` | Missing API key | Obtain key from [QwenCloud Console](https://home.qwencloud.com/api-keys); add to `.env`: `echo 'QWENCLOUD_API_KEY=sk-...' >> .env`; or run **qwencloud-ops-auth** if available |
| `HTTP 401` | Invalid or mismatched key | Run **qwencloud-ops-auth** (non-plaintext check only); verify key is valid |
| `SSL: CERTIFICATE_VERIFY_FAILED` | SSL cert issue (proxy/corporate) | macOS: run `Install Certificates.command`; else set `SSL_CERT_FILE` env var |
| `URLError` / `ConnectionError` | Network unreachable | Check internet; set `HTTPS_PROXY` if behind proxy |
| `HTTP 429` | Rate limited | Wait and retry with backoff |
| `HTTP 5xx` | Server error | Retry with backoff |
| `PermissionError` | Can't write output | Use `--output` to specify writable directory |

## Quick Reference

### Request Fields

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | **Required** — text to synthesize; check the model catalog above for model-specific limits |
| `voice` | string | Voice ID; check the model catalog above for current defaults and compatibility |
| `model` | string | Model ID; check the model catalog above for the current default |
| `language_type` | string | `Auto`, `Chinese`, `English`, `Japanese`, `Korean`, `French`, `German`, etc. — full names, not codes (`zh`, `en`) |
| `instructions` | string | Tone/style instructions; check the model catalog above for current compatibility and limits |
| `volume` | int | Volume `[0-100]`, default 50 — supported WebSocket models only; check the model catalog |
| `rate` | float | Speech rate `[0.5-2.0]`, default 1.0; below 1.0 slows speech — **WebSocket models only** |
| `pitch` | float | Pitch multiplier `[0.5-2.0]`, default 1.0; above 1.0 raises pitch — **WebSocket models only** |
| `sample_rate` | int | Sample rate in Hz, default 24000 — **WebSocket models only** |
| `format` | string | Audio format: `mp3`/`wav`/`pcm`/`opus`, default `mp3` — **WebSocket models only** |
| `stream` | bool | Direct Qwen3-TTS HTTP API field for SSE streaming. Bundled `tts.py` does not implement this field; use the direct SSE path in [execution-guide.md](references/execution-guide.md) |

### Response Fields

| Field | Description |
|-------|-------------|
| `audio_url` | URL of generated audio (valid 24h) |
| `audio_format` | Format (e.g. wav) |
| `sample_rate` | Sample rate (e.g. 24000) |
| `usage` | Character usage |

## Important Notes

- **text**: Check the model catalog above for the selected model's current request limit.
- **instructions**: Support is model-specific; check the model catalog above before using it.
- **language_type**: `Auto` for mixed language; specify for better pronunciation. Values are full names (`Chinese`, `English`, `Japanese`, ...), not codes (`zh`, `en`). It applies only to compatible HTTP models; the script ignores it for WebSocket models whose language follows the selected voice.
- **audio_url**: Valid for 24 hours — download promptly.
- **Real-time/streaming TTS**: Bundled `tts.py` uses non-streaming HTTP for Qwen3-TTS and raw WebSocket only for Qwen-Audio TTS; CosyVoice is handled by `tts_cosyvoice.py`. The Qwen3-TTS API itself supports optional SSE; use the direct example in [execution-guide.md](references/execution-guide.md) when needed.

## Cross-Skill Chaining

When passing generated audio to another skill (e.g., video-gen audio overlay):
- **Pass `audio_url` directly** — scripts detect URL prefixes and pass through without re-upload
- Use `audio_file` only for local playback or non-API operations

## Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| `401 Unauthorized` | Invalid or missing API key | Run **qwencloud-ops-auth** if available; else prompt user to set key (non-plaintext check only) |
| `400` | Invalid parameters (missing text/voice) | Validate request body |
| `429` / `5xx` | Rate limit or server error | Retry with backoff |

> **Usage & billing**: Use the **qwencloud-usage** skill to check usage, free tier quota, and billing directly. Alternatively, the user can visit the QwenCloud console:
> [Usage Analytics](https://home.qwencloud.com/analytics) |
> [Pay-as-you-go Billing](https://home.qwencloud.com/billing/pay-as-you-go) |
> [Coding Plan Billing](https://home.qwencloud.com/billing/coding-plan)
>
> For the current pricing model list and billing units, fetch the [CDN model-pricing reference](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-model-pricing.md). If CDN access fails, use the [local fallback](cdn/references/qwencloud-model-pricing.md).
>
> **NEVER fabricate, guess, or construct usage/billing/console URLs.** Only provide the exact links listed in this skill. If a URL is not listed here, do not invent one.

## Output Location

Prefer the **current working directory**. Default subdirectory: `./output/qwencloud-audio-tts/`.

**Write prohibition**: NEVER write output files into this skill's installation directory or any `skills/` hierarchy. All generated content must go to `output/` under the current working directory or a user-specified path.

## Token Plan Support

Token Plan supports only a subset of TTS models. Fetch and read the current [Token Plan model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-token-plan-models.md) before selecting or validating a model. If CDN access fails, use the [local fallback](cdn/references/qwencloud-token-plan-models.md).

When a Token Plan key is combined with an unsupported model, `tts.py` prints a warning to stderr listing the currently supported models and suggesting alternatives; it does not block the call. If you see this warning, tell the user which models the current catalog supports and offer either a catalog-listed alternative or a PAYG key for the original model. Never silently replace an explicitly requested model.

For CosyVoice specifically, `tts_cosyvoice.py` **hard-blocks** Token Plan keys at startup. Use `tts.py` with a model listed in the current Token Plan catalog, or use a PAYG key.

### Style control on Token Plan

Use only style-control fields supported by the selected Token Plan model in the audio model catalog. The following is a protocol example for a currently supported model; do not substitute it for a user-specified model:

```json
{"text": "落霞与孤鹜齐飞，秋水共长天一色。", "model": "qwen-audio-3.0-tts-plus", "rate": 0.8, "pitch": 1.1, "volume": 60}
```

- `rate` below 1.0 slows speech, above 1.0 speeds it up
- `pitch` above 1.0 raises pitch, below 1.0 lowers it
- `volume` scales linearly (0 = silent, 50 = default, 100 = max)

### Protocol note

The [QwenCloud model page](https://www.qwencloud.com/models/qwen-audio-3.0-tts-plus) documents **WSS (WebSocket)** for `qwen-audio-3.0-tts-plus`. The script includes a WebSocket path branch that:
1. Connects to `wss://token-plan.ap-southeast-1.maas.aliyuncs.com/api-ws/v1/inference` (or standard endpoint for PAYG)
2. Sets `User-Agent: qwencloud-skills` in the WebSocket handshake
3. Sends run-task → continue-task → finish-task messages
4. Receives binary audio frames and concatenates them into the output file

### Required header

`User-Agent: qwencloud-skills` is automatically included in both HTTP and WebSocket requests.

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

- [execution-guide.md](references/execution-guide.md) — Fallback paths (curl standard/instruct/streaming, code generation, autonomous)
- [api-guide.md](references/api-guide.md) — API supplementary guide
- [sources.md](references/sources.md) — Official documentation URLs

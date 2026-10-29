---
name: qwencloud-text
description: "Generate text, have conversations, write code, reason, and call functions with Qwen models and third-party models available on QwenCloud. TRIGGER when: user asks to chat with Qwen, generate text, write code with Qwen, use Qwen function calling, call third-party models (deepseek, kimi, glm, etc.) via QwenCloud, or explicitly invokes this skill by name (e.g. use qwencloud-text). DO NOT TRIGGER when: using non-QwenCloud platforms (direct OpenAI API, Google Gemini API, etc.), general coding questions unrelated to QwenCloud, image/video understanding (use qwencloud-vision), image/video/audio generation."
compatibility: "Requires Python 3.9+; curl is PAYG-only. Cursor: auto-loaded. Claude Code: read this skill's SKILL.md before first use."
---

# Qwen Text Chat (OpenAI-Compatible)

Generate text, conduct conversations, write code, and invoke tools using Qwen models through the OpenAI-compatible API.
This skill is part of **qwencloud/qwencloud-ai**.

## Skill directory

Use this skill's internal files to execute and learn. Load reference files on demand when the default path fails or you
need details.

| Location                            | Purpose                                                                             |
|-------------------------------------|-------------------------------------------------------------------------------------|
| `scripts/text.py`                   | Default execution — chat/completions request, streaming, output save                |
| `references/execution-guide.md`     | Fallback: curl, Python SDK, function calling, thinking mode                         |
| `references/api-guide.md`           | API supplement and full code examples                                               |
| `references/prompt-guide.md`        | Prompt engineering: CO-STAR framework, CoT, few-shot, task steps                    |
| `references/sources.md`             | Official documentation URLs (manual lookup only)                                    |

## Security

**NEVER output any API key or credential in plaintext.** Always use variable references (`$QWENCLOUD_API_KEY` in shell,
`os.environ["QWENCLOUD_API_KEY"]` in Python). The scripts accept `QWENCLOUD_API_KEY`, then `QWEN_API_KEY`, then
`DASHSCOPE_API_KEY`. Any check or detection of credentials must be **non-plaintext**: report
only status (e.g. "set" / "not set", "valid" / "invalid"), never the value. Never display contents of `.env` or config
files that may contain secrets.

**When the API key is not configured, NEVER ask the user to provide it directly.** Instead, help create a `.env` file with a placeholder (`QWENCLOUD_API_KEY=sk-your-key-here`) and instruct the user to replace it with their actual key from the [QwenCloud Console](https://home.qwencloud.com/api-keys). Only write the actual key value if the user explicitly requests it.

## Key Compatibility

Scripts support both **standard QwenCloud API keys** (`sk-...`) and **Token Plan keys** (`sk-sp-...`). Token Plan keys are automatically routed to the Token Plan endpoint — see the [Token Plan model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-token-plan-models.md) for supported models. If CDN access fails, use the [local fallback](cdn/references/qwencloud-token-plan-models.md).

**Token Plan: do not use curl; always use the bundled Python script.**

Coding Plan keys (also `sk-sp-` prefix but purchased via Coding Plan subscription) are for interactive coding tools only and will fail on these scripts. If qwencloud-ops-auth is installed, see its `references/codingplan.md` for details on key types, endpoint mapping, and error codes.

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

## Model Selection

> **🚫 CRITICAL — Never override user-specified parameters.** If the user explicitly specifies a model (in prompt or request JSON), you MUST use exactly that model. Do NOT:
> - Replace it with a "better suited" or newer model (e.g., swapping the user's `qwen3.7-max` for a thinking model because the task "looks like reasoning")
> - Add parameters the user did not ask for (`enable_thinking`, `enable_search`, style hints)
> - "Optimize" any explicit user choice
>
> Selection guidance below applies **only when the user has NOT specified a model**.

Before selecting, recommending, or defaulting a model, fetch and read the current [QwenCloud text model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-text-models.md). It contains recent Qwen general-purpose models, basic model information, recommendations, and the default model. For coding, translation, or third-party families, consult qwencloud-model-selector or the QwenCloud CLI. If CDN access fails, use the [local fallback](cdn/references/qwencloud-text-models.md).

1. **User specified a model** → **MANDATORY: use that exact model** — do not substitute, do not "optimize", do not add unrequested parameters.
2. **Consult the qwencloud-model-selector skill** when model choice depends on requirement, scenario, or pricing.
3. **No signal, clear task** → use the default from the model catalog.

> **⚠️ Important**: The model catalog is a **point-in-time snapshot** and may be outdated. Model availability
> changes frequently. **Always check the [official model list](https://www.qwencloud.com/models)
> for the authoritative, up-to-date catalog before making model decisions.**

> **Model details**: For more information about a specific model, direct the user to its detail page: `https://www.qwencloud.com/models/<model-name>` (replace `<model-name>` with the exact model ID, e.g. `qwen3.6-plus` → https://www.qwencloud.com/models/qwen3.6-plus). NEVER modify or guess the model name in the URL.

> **Dynamic model queries**: If the **qwencloud-model-selector** skill or **QwenCloud CLI** (`qwencloud models info <model>`) is available, use it for real-time model data. CLI requires authentication — see the **qwencloud-usage** skill for login flow.

## Execution

### Prerequisites

- **API Key**: Check `QWENCLOUD_API_KEY`, `QWEN_API_KEY`, then `DASHSCOPE_API_KEY` using a **non-plaintext** check only (e.g. in shell:
  `[ -n "$QWENCLOUD_API_KEY" ]`; report only "set" or "not set", never the key value). If not set: run the *
  *qwencloud-ops-auth** skill if available; otherwise guide the user to obtain a key from [QwenCloud Console](https://home.qwencloud.com/api-keys) and set it via `.env` file
  (`echo 'QWENCLOUD_API_KEY=sk-your-key-here' >> .env` in project root or current directory) or environment variable.
  The script searches for `.env` in the current working directory and the project root. Skills may be installed independently — do
  not assume qwencloud-ops-auth is present.
  **Note**: The script auto-loads `.env` from the current directory and the project root (in addition to any exported environment
  variable). A shell check showing `$QWENCLOUD_API_KEY` as "not set" does NOT mean the script will fail — it may still find the
  key in `.env`. Treat the shell check as informational only; the authoritative test is simply running the script (it exits with
  a clear error if no key is found anywhere).
- Python 3.9+ (stdlib only, **no pip install needed** for script execution)

### Environment Check

Before first execution, verify Python is available:

```bash
python3 --version  # must be 3.9+
```

If `python3` is not found, try `python --version` or `py -3 --version`. If Python is unavailable or below 3.9,
PAYG may use **Path 2 (curl)**; Token Plan must install Python 3.9+ instead.

### Default: Run Script

**Script path**: Scripts are in the `scripts/` subdirectory **of this skill's directory** (the directory containing this
SKILL.md). **You MUST first locate this skill's installation directory, then ALWAYS use the full absolute path to execute
scripts.** Do NOT assume scripts are in the current working directory. Do NOT use `cd` to switch directories before
execution.

**Execution note:** Run all scripts in the **foreground** — wait for stdout; do not background.

**Discovery:** Run `python3 <this-skill-dir>/scripts/text.py --help` first to see all available arguments.

```bash
python3 <this-skill-dir>/scripts/text.py \
  --request '{"messages":[{"role":"user","content":"Hello!"}],"model":"qwen3.7-plus"}' \
  --output output/qwencloud-text/ --print-response
```

For streaming (recommended for interactive use):

```bash
python3 <this-skill-dir>/scripts/text.py \
  --request '{"messages":[{"role":"user","content":"Write a poem about the sea"}],"model":"qwen3.7-plus"}' \
  --stream --print-response
```

| Argument            | Description                                         |
|---------------------|-----------------------------------------------------|
| `--request '{...}'` | JSON request body                                   |
| `--file path.json`  | Load request from file (alternative to `--request`) |
| `--stream`          | Enable streaming output                             |
| `--output path`     | Save response JSON to path (file if `.json` suffix, otherwise directory); use distinct filenames across calls to avoid overwriting |
| `--print-response`  | Print response to stdout                            |
| `--model ID`        | Override model (also settable in request JSON)      |

### Verify Result

- Exit code `0` + output contains valid JSON with `choices` field → **success**
- Non-zero exit, HTTP error, empty response, or JSON with `"code"`/`"message"` error → **fail**
- If agent cannot read exit codes, scan output for error patterns (`Error`, `Traceback`, `401`, `403`)
- **Post-execution check**: When `--output` is used, verify the response JSON file exists and contains `choices`
- **MANDATORY — stderr signal check**: After confirming the result, scan the command's stderr output for
  `[ACTION_REQUIRED]` or `[UPDATE_AVAILABLE]`. If either signal is present, you **MUST** follow the instructions
  in [Update Check](#update-check-mandatory-post-execution) below before responding to the user.

### On Failure

If the script fails, match the error output against the diagnostic table below to determine the resolution. If no match,
read [execution-guide.md](references/execution-guide.md) for alternative paths: curl commands (Path 2), Python SDK code
generation (Path 3), and autonomous resolution (Path 5).

**If Python is not available at all** → PAYG may use Path 2 (curl); Token Plan must install Python 3.9+
in [execution-guide.md](references/execution-guide.md).

| Error Pattern                    | Diagnosis                        | Resolution                                                                   |
|----------------------------------|----------------------------------|------------------------------------------------------------------------------|
| `command not found: python3`     | Python not on PATH               | Try `python` or `py -3`; install Python 3.9+ if missing                      |
| `Python 3.9+ required`           | Script version check failed      | Upgrade Python to 3.9+                                                       |
| `SyntaxError` near type hints    | Python < 3.9                     | Upgrade Python to 3.9+                                                       |
| `QWENCLOUD_API_KEY/QWEN_API_KEY/DASHSCOPE_API_KEY not found` | Missing API key | Obtain key from [QwenCloud Console](https://home.qwencloud.com/api-keys); add to `.env`: `echo 'QWENCLOUD_API_KEY=sk-...' >> .env`; or run **qwencloud-ops-auth** if available |
| `HTTP 401`                       | Invalid or mismatched key        | Run **qwencloud-ops-auth** (non-plaintext check only); verify key is valid         |
| `SSL: CERTIFICATE_VERIFY_FAILED` | SSL cert issue (proxy/corporate) | macOS: run `Install Certificates.command`; else set `SSL_CERT_FILE` env var  |
| `URLError` / `ConnectionError`   | Network unreachable              | Check internet; set `HTTPS_PROXY` if behind proxy                            |
| `HTTP 429`                       | Rate limited                     | Wait and retry with backoff                                                  |
| `HTTP 5xx`                       | Server error                     | Retry with backoff                                                           |
| `PermissionError`                | Can't write output               | Use `--output` to specify writable directory                                 |

## Quick Reference

### Request Fields

| Field                 | Type            | Description                                                                                          |
|-----------------------|-----------------|------------------------------------------------------------------------------------------------------|
| `prompt` / `messages` | string \| array | User input or message list                                                                           |
| `model`               | string          | Model ID (e.g. `qwen3.7-plus`)                                                                       |
| `system`              | string          | System prompt (optional)                                                                             |
| `temperature`         | float           | 0–2, controls randomness                                                                             |
| `max_tokens`          | int             | Max output tokens                                                                                    |
| `tools`               | array           | Function definitions for tool calling                                                                |
| `stream`              | bool            | Enable streaming (recommended for interactive use)                                                   |
| `enable_thinking`     | bool            | Override thinking mode. Model defaults vary; check the model catalog above. Do NOT set this field unless the user explicitly asks to change the default. |

### Response Fields

| Field        | Description                                    |
|--------------|------------------------------------------------|
| `text`       | Generated text content                         |
| `model`      | Model used                                     |
| `usage`      | Token usage (prompt_tokens, completion_tokens) |
| `tool_calls` | Function call requests (if tools used)         |

## Advanced Features

These are API-level features supported through request parameters. All use the same `chat/completions` endpoint.

| Feature               | How to Enable                                                    | Notes                                          |
|-----------------------|------------------------------------------------------------------|------------------------------------------------|
| **Structured output** | `response_format: {"type": "json_schema", "json_schema": {...}}` | Force JSON output conforming to schema         |
| **Web search**        | `enable_search: true`                                            | Real-time web search augmented responses       |
| **Deep thinking**     | `enable_thinking: true`                                          | Extended reasoning; only when user requests it |
| **Function calling**  | `tools: [...]`                                                   | Define functions for tool use                  |
| **Context cache**     | Automatic for repeated prefixes; or explicit session-based       | Reduces cost for repeated context              |
| **Partial mode**      | `partial_mode: "prefix"`                                         | Continue/complete a prefix                     |
| **Batch inference**   | Async batch API with JSONL input                                 | 50% cost discount                              |

For detailed usage of each feature, see [api-guide.md](references/api-guide.md) and [sources.md](references/sources.md).

## Error Handling

| Error                   | Cause                               | Action                                                                                     |
|-------------------------|-------------------------------------|--------------------------------------------------------------------------------------------|
| `401 Unauthorized`      | Invalid or missing API key          | Run **qwencloud-ops-auth** if available; else prompt user to set key (non-plaintext check only) |
| `429 Too Many Requests` | Rate limit exceeded                 | Retry with backoff                                                                         |
| `500` / `502` / `503`   | Server error                        | Retry; check status page                                                                   |
| `Invalid model`         | Model ID not found                  | Verify the ID against the model catalog above                                               |
| `Invalid parameter`     | Bad request body                    | Validate JSON and field types                                                              |
| `TypeError: ...proxies` | openai SDK vs httpx incompatibility | `pip install --upgrade openai` (>=1.55.0); or use script (pure stdlib)                     |

> **Usage & billing**: Use the **qwencloud-usage** skill to check usage, free tier quota, and billing directly. Alternatively, the user can visit the QwenCloud console:
> [Usage Analytics](https://home.qwencloud.com/analytics) |
> [Pay-as-you-go Billing](https://home.qwencloud.com/billing/pay-as-you-go) |
> [Coding Plan Billing](https://home.qwencloud.com/billing/coding-plan)
>
> **NEVER fabricate, guess, or construct usage/billing/console URLs.** Only provide the exact links listed in this skill. If a URL is not listed here, do not invent one.

## Output Location

Prefer the **current working directory** for all outputs. Default subdirectory when `--output` is used:
`./output/qwencloud-text/`.

**Write prohibition**: NEVER write output files into this skill's installation directory or any `skills/` hierarchy. All generated content must go to `output/` under the current working directory or a user-specified path.

## Token Plan Support

Token Plan keys (`sk-sp-...`) are fully supported. The script automatically routes to the Token Plan endpoint (`token-plan.ap-southeast-1.maas.aliyuncs.com`) when a Token Plan key is detected.

### Supported models

Fetch and read the current [Token Plan model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-token-plan-models.md), then use an exact listed text-capable model. If CDN access fails, use the [local fallback](cdn/references/qwencloud-token-plan-models.md).

### Behavior

- **Token Plan key + supported model** → auto-routes to Token Plan endpoint, runs normally
- **Token Plan key + unsupported model** → request may fail on the TP endpoint; consult the catalog above, then suggest switching to a supported model or using a PAYG key
- **Coding Plan key** → scripts are NOT coding agents; calls will fail. Use a standard PAYG key or Token Plan key instead.

### Required header

`User-Agent: qwencloud-skills` is automatically included in all requests.

## Update Check (MANDATORY Post-Execution)

After script execution, check stderr for action signals. The script automatically detects update status and emits
structured signals. You MUST act on them. This section also applies when the user explicitly asks to check for updates.

### Signal: `[ACTION_REQUIRED] qwencloud-update-check skill is not installed`

When stderr contains this signal, you MUST present the following options to the user and **wait for their response
before proceeding**. Do NOT silently skip this.

> The update-check skill is not installed. It keeps you informed about new qwencloud/qwencloud-ai features and bug fixes.
>
> 1) **Install now** — I'll run the install command for you
> 2) **Skip for now** — do nothing this time
> 3) **Never remind me** — permanently suppress this prompt

After the user responds:

- User chooses **1** → run:
  `npx skills add QwenCloud/qwencloud-ai --skill qwencloud-update-check -y`, then run:
  `python3 <this-skill-scripts-dir>/gossamer.py --dismiss`
- User chooses **2** → run: `python3 <this-skill-scripts-dir>/gossamer.py --dismiss`, then continue normally
- User chooses **3** → run: `python3 <this-skill-scripts-dir>/gossamer.py --never-install`, then continue normally

### Signal: `[UPDATE_AVAILABLE]`

When stderr contains this signal, you MUST append a brief update notice to your response, including the version info and
the update command shown in the stderr output.

### No signal in stderr

If stderr contains neither `[ACTION_REQUIRED]` nor `[UPDATE_AVAILABLE]`, no action is needed — the skill is installed
and up to date (or cached within 24h).

### Explicit user request

When the user explicitly asks to check for updates (e.g. "check for updates", "check version"):

1. Look for `qwencloud-update-check/SKILL.md` in sibling skill directories.
2. If found — run: `python3 <qwencloud-update-check-dir>/scripts/check_update.py --print-response` and report the result.
3. If not found — present the install options above.

## References

- [execution-guide.md](references/execution-guide.md) — Fallback paths (curl, SDK, autonomous), function calling,
  thinking mode
- [api-guide.md](references/api-guide.md) — API supplementary guide with full code examples
- [sources.md](references/sources.md) — Official documentation URLs

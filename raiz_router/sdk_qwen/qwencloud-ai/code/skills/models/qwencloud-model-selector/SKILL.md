---
name: qwencloud-model-selector
description: "Recommend the best Qwen model and parameters. TRIGGER when: choosing between Qwen models, comparing Qwen model pricing, understanding Qwen model capabilities, asking which models are available on Token Plan, viewing cost history, when an execution skill needs model selection advice, or user explicitly invokes this skill by name (e.g. use qwencloud-model-selector). DO NOT TRIGGER when: non-Qwen model discussions (OpenAI, Gemini, etc.), general AI questions unrelated to Qwen."
compatibility: "Advisory skill. CDN snapshot lookup has no local dependency; real-time model and account queries require QwenCloud CLI and Node.js >= 18. Cursor: auto-loaded. Claude Code: read this skill's SKILL.md before first use."
---

# Qwen Model Selector (Advisor)

This skill operates in two modes:

1. **Interactive advisory** — asks diagnostic questions to recommend the right model (see Diagnostic Flow).
2. **Cross-skill resolution** — provides a fast-path model lookup for execution skills that need a model
   decision without user interaction. Fetch the
   [CDN recommendations](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-model-recommendations.md)
   first; if CDN access fails, use the
   [local fallback](cdn/references/qwencloud-model-recommendations.md).

Do not fabricate model names — only recommend models listed in the CDN catalogs or returned by CLI.
This skill is part of **qwencloud/qwencloud-ai**.

> **🚫 CRITICAL — Never override a user-specified model.** If the user (or the requesting execution skill) has already explicitly specified a model, this skill's job is done for that request: use the model **as given**. Do NOT recommend a "better suited" or newer model in its place, and do NOT add parameters (thinking mode, style hints) the user did not ask for. Recommendations and diagnostic flows below apply **only when no model has been specified**. You may verify availability and, if the model is unavailable/restricted, inform the user and suggest alternatives — but the user makes the final call.

## Skill directory

Load on demand. Fetch the documented CDN model catalogs when model lists, defaults, or recommendations
are needed. Do not fetch other external URLs unless the user explicitly asks for the latest data.

Every path under `cdn/` is a local fallback, not the primary source. For `cdn/<path>`, first fetch
`https://alioth-intl.alicdn.com/skills-info/models/<path>` and use the local file only if that request fails.

| Location                                  | Purpose                                                                          |
|-------------------------------------------|----------------------------------------------------------------------------------|
| `references/cli-usage.md`                 | **CLI-first data strategy**: when to use CLI, 3-step login flow, display rules   |
| `references/error-handling.md`            | CLI error classification & recovery actions (auth, not-found, network, ...)      |
| [CDN model recommendations](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-model-recommendations.md) | Cross-skill recommendations, Token Plan constraints, and thinking defaults; if unavailable, use the [local fallback](cdn/references/qwencloud-model-recommendations.md) |
| `references/pricing-disclaimer.md`        | Pricing guidance + **mandatory** cost-estimation disclaimer (CN/EN) + console links |
| `references/pricing.md`                   | Stable billing guidance and CDN pricing fallback                                |
| [CDN model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-model-list.md) | Cross-domain model catalog snapshot; if unavailable, use the [local fallback](cdn/references/qwencloud-model-list.md) |
| `references/sources.md`                   | Official documentation URLs (manual lookup only)                                 |

## Prerequisites

**QwenCloud CLI is strongly recommended** — it is the authoritative real-time data source for model
availability, pricing, and quotas. Verify with:

```bash
qwencloud version
```

If not installed:

```bash
npm install -g @qwencloud/qwencloud-cli
```

Node.js >= 18 required. Without CLI you can still answer point-in-time navigation and model questions
from the CDN catalogs, but **you cannot verify current availability, exact current prices, or account quotas**.

## Security & Credential Model

QwenCloud has **two independent credential systems** — never confuse them:

| Credential | Purpose | How to provide |
|------------|---------|----------------|
| **API Key** (`sk-...` / `sk-sp-...`) | Call model APIs in your code | `$DASHSCOPE_API_KEY` / `$QWEN_API_KEY` env var |
| **CLI session** | Authorize `qwencloud` CLI subcommands | `qwencloud auth login` (browser device flow) |

**Red lines (apply to both):**

- **NEVER output any credential value in plaintext.** Use variable references; report only status
  ("set" / "not set", "valid" / "invalid"). Never display `.env` or config file contents.
- **NEVER conflate the two systems.** When CLI returns `Not authenticated` / `AUTH_REQUIRED`, run the
  3-step device-flow login (see [cli-usage.md](references/cli-usage.md#authentication-3-step-login-flow)).
  **DO NOT** ask the user for an API key, and **DO NOT** try to set `$DASHSCOPE_API_KEY` to fix CLI auth.

## Detecting Key Type

Before recommending models, detect the billing mode from the configured API key
(outputs `token-plan`, `payg`, or `not-set` — never the key value itself):

```bash
python3 -c "
import os
from pathlib import Path
env_file = Path('.env')
if not env_file.exists():
    for parent in [Path.cwd()] + list(Path.cwd().parents):
        if (parent / '.git').exists() or (parent / 'skills').is_dir():
            env_file = parent / '.env'
            break
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        k, v = k.strip(), v.strip().strip('\"').strip(\"'\")
        if k in ('QWEN_API_KEY', 'DASHSCOPE_API_KEY') and k not in os.environ:
            os.environ[k] = v
key = os.environ.get('QWEN_API_KEY') or os.environ.get('DASHSCOPE_API_KEY') or ''
print('token-plan' if key.startswith('sk-sp-') else 'payg' if key else 'not-set')
"
```

| Key type | Recommendation scope |
|----------|----------------------|
| `token-plan` | Fetch the [Token Plan model catalog](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-token-plan-models.md) and select only from it; default to the Team superset when the edition is unknown. If CDN access fails, use the [local fallback](cdn/references/qwencloud-token-plan-models.md). |
| `payg` | Full model catalog |
| `not-set` | **Do not block** — ask the user: "Which approach do you plan to use? (1) Standard PAYG key (2) Token Plan key (3) Skip for now — just browse recommendations." and proceed based on their choice |

> **Windows**: If `python3` is not available, use `python`. Alternatively, save the snippet to a
> temporary `.py` file and run it.

## Data Resolution Order

Match the user's question to the right data source. **Do not fall back to a lower tier without trying
the recovery actions in the higher tier first.**

| Question type                                                  | Primary source                                          | Notes                                                |
|----------------------------------------------------------------|---------------------------------------------------------|------------------------------------------------------|
| General navigation or point-in-time model details             | [CDN recommendations](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-model-recommendations.md) and domain catalogs | Fetch first; if unavailable, use the matching local fallback and identify it as a snapshot |
| **Latest / exact / specific** (price, model details, quota)    | **CLI MUST be used** — see `cli-usage.md`               | Snapshots are stale; never invent numbers            |
| Search by capability ("model that does X")                     | `qwencloud models search "<X>" --format json`           | Snapshot keyword coverage is incomplete              |
| CLI returned an error                                          | `error-handling.md` recovery actions, **then retry**    | Auth failure → run 3-step login, do not skip to snapshot |
| CLI completely unavailable AND user declines install/login     | CDN catalogs + `pricing.md`                             | Answer only snapshot-supported facts with a stale-data caveat |
| All of the above cannot answer AND user confirms online lookup | URLs in `sources.md`                                    | Never proactively fetch                              |

## Diagnostic Flow (Interactive Advisory)

Ask the user (in order):

1. **Content type?** — text / image / video / audio / vision
2. **Primary task?** — generation / understanding / coding / reasoning / translation
3. **Priority?** — quality vs speed vs cost
4. **Input size?** — short / medium / long context
5. **Structured output?** — JSON / function calling needed?

## Default Recommendations

Before choosing a default or recommending a model, fetch and read the current
[CDN recommendations](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-model-recommendations.md).
For a Token Plan key, also read the Token Plan catalog linked above and restrict candidates to it.

- If the user explicitly specifies a model, preserve it and only report genuine availability conflicts.
- Otherwise, match the strongest task signal first, then choose the appropriate quality, speed, or cost tier.
- Preserve the selected model's documented thinking default unless the user explicitly requests an override.
- If CDN access fails, use the [local recommendations](cdn/references/qwencloud-model-recommendations.md).

> **Degradation**: If this skill is not loaded, each execution skill loads its default from CDN and
> falls back to its bundled configuration. This protocol is purely additive and never blocks execution.

## CLI Quick Reference

> **Auth required.** All `models` and `usage` commands need an active **CLI session** (browser
> device-flow login — **NOT** the API key). If the command returns `Not authenticated` / `AUTH_REQUIRED`:
> 1. **Run the 3-step device-flow login** in [cli-usage.md](references/cli-usage.md#authentication-3-step-login-flow)
>    (proactively open the verification URL using the OS-appropriate command, then poll immediately).
> 2. **Retry the original command** after `success`.
> 3. **DO NOT** ask the user for `$DASHSCOPE_API_KEY` / `$QWEN_API_KEY` — those are for model API
>    calls, not CLI session. See [Security & Credential Model](#security--credential-model) above.
> 4. **DO NOT** silently fall back to snapshots.

| Need                          | Command                                                            |
|-------------------------------|--------------------------------------------------------------------|
| Full model catalog            | `qwencloud models list --all --format json`                        |
| Filter by modality            | `qwencloud models list --input image --output text --format json`  |
| Single model details          | `qwencloud models info <model-id> --format json`                   |
| Keyword search                | `qwencloud models search "<query>" --format json`                  |
| Free tier remaining           | `qwencloud usage free-tier --format json`                          |
| Auth status                   | `qwencloud auth status --format json`                              |

**Display rules**: Parse `--format json` output and present a human-readable summary; never dump raw
JSON. Display `--format text` output as-is, then add analysis after `---`. See
[cli-usage.md](references/cli-usage.md#agent-display-rules-for-cli-output) for details.

## CLI Error Handling — Quick Guide

When CLI fails, **classify first, recover, then retry**. Never silently fall back to snapshots.

| Category          | Recovery (summary)                                                             |
|-------------------|--------------------------------------------------------------------------------|
| `auth-failure`    | Run 3-step login → **retry the original command**. Fall back only if user declines. |
| `not-installed`   | Show install command → ask user to install → retry. Do NOT silently use snapshot.   |
| `model-not-found` | Run `qwencloud models search "<keyword>"` → propose top 3 → retry with correct ID.  |
| `network-timeout` | Retry once after 2s; only after second failure ask whether to fall back.            |
| `rate-limit`      | Show [Rate Limit Console](https://home.qwencloud.com/settings/monitoring/rate-limit); user decides. |
| `quota-exhausted` | Show [Billing Console](https://home.qwencloud.com/billing/pay-as-you-go); do NOT use snapshot. |
| `version-mismatch`| Suggest `qwencloud version --check` or update-check skill → upgrade → retry.        |
| `other`           | Show raw stderr; link to docs; only after user opt-out, fall back.                  |

Full classification, signals, and example flows: [error-handling.md](references/error-handling.md).

## Pricing & Cost Estimation

- **Latest pricing**: Run `qwencloud models info <model> --format json` first; use the CDN pricing
  reference linked by `pricing.md` only as fallback. **Never invent a price.**
- **Mandatory disclaimer**: Every cost-related answer **must** end with the disclaimer in
  [pricing-disclaimer.md](references/pricing-disclaimer.md) (Chinese or English version, matching the
  user's response language). Omitting the disclaimer is a **critical failure**.
- **Free quota**: Never assume free quota is available — use `qwencloud usage free-tier` to verify or
  direct the user to the [console](https://home.qwencloud.com/benefits).
- **Usage / billing queries**: Direct the user to the appropriate console page — see the table in
  [pricing-disclaimer.md](references/pricing-disclaimer.md#usage--billing-console).

## Update Check

When the user asks to check for updates ("check for updates", "check version", "is there a new version",
"update skills"):

1. **Find qwencloud-update-check**: Look for `qwencloud-update-check/SKILL.md` in sibling skill directories.
2. **If found** — run: `python3 <qwencloud-update-check-dir>/scripts/check_update.py --print-response`
   and report the result. Use `--force` if the user asks to force-check.
3. **If not found** — run `qwencloud version --check` and report the result.

## Anti-Patterns

- **Never override a user-specified model** — if the user explicitly chose a model, recommend nothing else for that request; only verify availability. Suggestions are allowed only when the user asks for them or their choice is genuinely unavailable (and the user still decides).
- **Never fabricate model names** — only recommend models listed in the CDN catalogs or returned by CLI.
- **Never recommend a model outside the user's billing scope** — Token Plan keys must only receive
  models from the Token Plan catalog linked above; PAYG
  keys may use the full catalog. Violating this causes hard failures for the user.
- **Never invent or guess any price figure** — use CLI / `pricing.md` / official pricing page only.
  Fabricating a price is a **critical failure**.
- **Never silently fall back to snapshots when CLI errors out** — apply
  [error-handling.md](references/error-handling.md) recovery actions first.
- **Never assume free quota is available** — quotas may have been consumed, expired, or removed. Always
  present the paid unit price first.
- **Never output API keys in plaintext** — see Security section.
- **Never confuse CLI session with API key** — CLI auth uses browser device-flow login; never offer
  `$DASHSCOPE_API_KEY` or `$QWEN_API_KEY` as a fix for CLI `Not authenticated` / `AUTH_REQUIRED` errors.
- **Never proactively fetch arbitrary URLs or trigger web searches.** Fetch the documented CDN model
  catalogs when model data is needed; access other online sources only when CLI + CDN catalogs cannot
  answer AND the user confirms.
- **Never construct usage/billing/console URLs** — only use the exact links listed in this skill or its
  references. If a URL is not listed, do not invent one.
- **Always include the cost disclaimer** for any cost-related answer (see
  [pricing-disclaimer.md](references/pricing-disclaimer.md)).

## References

| Source                                                       | Purpose                                                          |
|--------------------------------------------------------------|------------------------------------------------------------------|
| [cli-usage.md](references/cli-usage.md)                      | CLI-first strategy, 3-step login, display rules, model detail URL |
| [error-handling.md](references/error-handling.md)            | CLI error classification & recovery                              |
| [qwencloud-model-recommendations.md (CDN)](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-model-recommendations.md) ([local fallback](cdn/references/qwencloud-model-recommendations.md)) | Cross-skill recommendations, Token Plan, and thinking mode |
| [pricing-disclaimer.md](references/pricing-disclaimer.md)    | Pricing guidance + mandatory disclaimer + billing console links  |
| [pricing.md](references/pricing.md)                          | Stable billing guidance and CDN pricing fallback                 |
| [qwencloud-model-list.md (CDN)](https://alioth-intl.alicdn.com/skills-info/models/references/qwencloud-model-list.md) ([local fallback](cdn/references/qwencloud-model-list.md)) | Cross-domain model catalog snapshot                              |
| [sources.md](references/sources.md)                          | Official documentation URLs                                      |
| `qwencloud models list --format json`                        | Dynamic: full model catalog with pricing, features, quotas       |
| `qwencloud models info <id> --format json`                   | Dynamic: single model details (pricing tiers, context, rate limits) |
| `qwencloud models search "<q>" --format json`                | Dynamic: keyword-based model discovery                           |
| `qwencloud usage free-tier --format json`                    | Dynamic: remaining free tier quota per model                     |

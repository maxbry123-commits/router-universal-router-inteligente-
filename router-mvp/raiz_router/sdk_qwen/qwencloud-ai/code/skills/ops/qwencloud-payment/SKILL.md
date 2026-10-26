---
name: qwencloud-payment
description: "Manage payment methods, bind card, spending limit. TRIGGER when: user asks about payment methods, bind card, spending limit, payment status. DO NOT TRIGGER when: billing history, usage queries, subscription status (use qwencloud-usage), support tickets."
compatibility: "Requires QwenCloud CLI >= 1.3.0 and authentication. Cursor: auto-loaded. Claude Code: read SKILL.md before first use."
---

# QwenCloud Payment

Manage QwenCloud account payment method status, card binding, and spending limits.

## Prerequisites

- **QwenCloud CLI >= 1.3.0** must be installed. Verify with:

```bash
qwencloud version
```

If not installed, run:

```bash
npm install -g @qwencloud/qwencloud-cli
```

Node.js >= 18 required.

- All billing commands require authentication. See Authentication Flow below.

## Authentication Flow (for Agents)

The CLI auto-detects non-TTY environments and degrades safely.

### TL;DR — 3-step auth path

1. `qwencloud auth status --format json` → `authenticated: true` → skip to commands
2. `qwencloud auth login --init-only --format json` → extract `verification_url` → open in browser
3. `qwencloud auth login --complete --format json` → poll until `success` event

If `authenticated: true` on step 1, proceed directly to payment commands.

For full details on the two-phase login flow (init-only → complete), refer to the `qwencloud-usage` skill or `qwencloud-ops-auth` skill documentation.

## Payment Status Commands

### Payment Method Status

```bash
qwencloud billing payment-method list --format json
```

**Response fields:**
- `items[]` — list of payment methods
- `items[].status` — only items with status `VALID` are considered active

Present the count of valid payment methods and their types.

### Spending Limit

Query or display the current spending limit configuration.

```bash
qwencloud billing limit --format json
```

Returns the configured spending limit and current consumption against it. When status is `INACTIVE`, inform the user that no spending limit is currently configured.

**Number formatting:** Use K = 1000, M = 1000000 when displaying large values (e.g., $5K, $1.2M).

## Bind Card

This command opens the official web console page. It does NOT perform transactions within the conversation.

### Confirmation Flow

Before executing bind-card, the agent MUST:

1. **Show impact** — explain what the action will do (open a web page for card binding)
2. **Wait for explicit user confirmation** — return `confirmation_required` status if not confirmed
3. **Execute only after confirmation**

#### States

| State | Meaning |
|-------|---------|
| `confirmation_required` | Action pending user confirmation — do NOT execute |
| `confirmed` | User explicitly agreed — proceed with command |

#### Steps

1. User requests bind card
2. Agent presents: "This will open the official card-binding page in your browser. Proceed?"
3. If user confirms → execute the command
4. If user declines or does not respond → return `confirmation_required`, take no action

### Execute

```bash
qwencloud billing payment-method bind --format json
```

Opens the official card-binding page in the user's browser. No card data is submitted via CLI.

## Output and Agent Display Rules

CLI commands return JSON by default in agent/pipe environments.
**Always pass `--format json`**, parse the structured response, then present a human-readable summary.

### How to present output

1. **Parse the JSON** and extract relevant data for the user's question
2. **Present a human-readable summary** — do not dump raw JSON
3. **Add analysis AFTER the summary** — clearly separated with `---`

## Error Handling

- **Auth failure**: Return the original CLI error message. Do NOT retry login in a loop.
- **After successful login**: Retry the failed command exactly once.
- **Network error**: Report the error and suggest the user check connectivity.
- **Unknown error**: Return the raw CLI stderr output for debugging.

## Result Status

| Status                  | When                                                                                      |
|-------------------------|-------------------------------------------------------------------------------------------|
| `success`               | Command executed and full data returned                                                   |
| `partial`               | Command executed (exit 0) but some expected fields are missing or `null` — e.g., `payment-method list` returns items but a field is `null`, or `billing limit` returns `INACTIVE` with some fields absent. Present available data and note that the user should verify details in the web console |
| `empty`                 | Command executed but no data (e.g., no payment methods bound)                             |
| `confirmation_required` | Bind-card action awaiting user confirmation                                               |
| `error`                 | Command failed — include error details                                                    |

## NEVER

- ❌ Execute `bind` without explicit user confirmation
- ❌ Perform actual card submission or transactions in the conversation
- ❌ Judge payment method "insufficient" without explicit criteria
- ❌ Handle support tickets (out of scope)
- ❌ Query billing history or usage (use `qwencloud-usage` instead)
- ❌ Query subscription status (use `qwencloud-usage` instead)
- ❌ Retry login in a loop on auth failure

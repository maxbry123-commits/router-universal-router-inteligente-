# RIU-0082 — Hugging Face MCP + API credential boundary

Contract: `tel.workflow/v3`
Date: 2026-09-17

## Official sources
- HF MCP server: https://huggingface.co/docs/hub/agents-mcp
- HF MCP client: https://huggingface.co/docs/huggingface_hub/main/package_reference/mcp
- HF OAuth: https://huggingface.co/docs/hub/oauth
- HF access tokens: https://huggingface.co/docs/hub/security-tokens

## Boundary
Hugging Face exposes an official MCP server at:
`https://huggingface.co/mcp`

The official MCP setup is client/OAuth managed. The Hub/Inference API token is a separate boundary and may be supplied to Hugging Face Python/inference clients as an API key. RIU must not silently conflate those two authentication mechanisms.

RIU runtime contract:
- MCP URL: `https://huggingface.co/mcp`
- transport: `streamable_http`
- MCP auth: `oauth_client_managed`
- Hub/Inference credential: runtime secret reference only (`RIU_HF_TOKEN`, `HF_TOKEN`, or `HUGGINGFACE_TOKEN`)
- secret values never serialized into descriptors, STATE, logs or Git

## Code delta
`router inteligente universal/integration/connectivity_runtime.py`
adds:
- `HF_MCP`
- `mcp_huggingface_descriptor()`
- safe `huggingface_mcp` public runtime descriptor

Exact test commit:
`f97791ca61197ecbdad0d1d2bb7c792a37c721dc`

## Test evidence
HF Job:
`6aac809f5c02253cfb145474`

Result:
- terminal status: `COMPLETED`
- 5/5 repeated rounds
- 10 tests passed per round
- descriptor contains secret reference name, never secret value
- missing HF credential reference fails closed
- existing GitHub/HF connectivity tests remain passing

## Live external context
The connected HF account in this session is `COMAND-CENTER-1` and the OAuth connection reported `read-mcp` scope. That proves the connected application boundary has MCP-read authorization; it does **not** by itself prove that RIU's own runtime has completed an OAuth handshake to the remote HF MCP server.

## Verdict
`BOUNDARY_VERIFIED / RIU_REMOTE_MCP_OAUTH_E2E_PENDING`

The safe MCP + API-key architecture is implemented and unit-tested. Full runtime closure still requires a harmless RIU-side OAuth MCP initialize/tools-list read-back in an authorized runtime without exposing credentials.

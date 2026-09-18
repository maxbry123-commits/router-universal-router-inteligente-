# RIU-0096 — STATE full read-back / reconciliation map

Contract: `tel.workflow/v3` · mode: `FAIL_CLOSED_LOOP`

## Fresh base
- `main` before this delta: `611a9d8c673a72a1db43ac9ff7b30c56ea4ff6a0`.
- `STATE.json` blob read in full: `099355cbf19ebf5edc9b9f409c41548f998adca2`.
- STATE still declares `current_node=RIU-0086_PRIORITY_LOCK_AND_IMAGE_MODELS`.
- STATE still has active pending gates `HF_MIRROR_RUNTIME_DESTINATION_AND_TEST` and `HF_ENDPOINT_REPLICA_RUNTIME_CONFIG_TEST` and legacy `verify_final=GAP_PENDING_DOWNLOAD_HASH_LOAD_INFERENCE`.

## Reconciliation decision
`REMOTE_INFERENCE_ONLY` is the active architecture contract. Mirror/download/load gates are historical provenance only and MUST NOT be used as active closure gates. No historical evidence is deleted.

`RedUniversal` remains the sole routing owner. External components remain bounded as follows: OmniRoute=optional downstream gateway/adapter; Orca=external ADE; Omarchy=optional workstation host; AnyDoc=document-ingest adapter. Presence/materialization is not PASS.

## Verified vs open
Verified runtime inference evidence remains limited to `Qwen/Qwen3-0.6B`, `openai-community/gpt2`, and `Qwen/Qwen3-8B`. `20/20 accounted` is inventory/accounting evidence and MUST NOT be interpreted as 20 remotely inferred models.

Open gates remain: complete component/container X-Ray; dedup/orphan reconciliation; OmniRoute/Orca/Omarchy/AnyDoc runtime gates; GitHub/HF/Claude/Codex auth runtime; MCP/memory; per-model remote inference/failure fallback evidence; global E2E; final documentation synchronization.

## Safe next mutation
Rewrite STATE only from the full blob read-back, preserving all evidence arrays and historical fields while:
1. moving the active node to the current reconciliation sequence;
2. marking mirror/download/load requirements `SUPERSEDED_PROVENANCE_ONLY` rather than deleting them;
3. setting active HF closure gate to `REGISTER -> REMOTE_PROVIDER_DISCOVERY -> AUTH_REFERENCE -> REMOTE_INFERENCE_SMOKE -> FAILURE_FALLBACK_TEST -> EVIDENCE -> READY`;
4. keeping global closure false until all W1–W5 gates have real evidence.

No PASS is promoted by this forensic delta.
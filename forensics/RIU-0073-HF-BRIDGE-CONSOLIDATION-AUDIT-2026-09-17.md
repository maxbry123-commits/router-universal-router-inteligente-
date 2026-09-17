# RIU-0073 — HF Bridge Consolidation Audit

Contract: `tel.workflow/v3` · mode: `FAIL_CLOSED_LOOP`
Date: 2026-09-17

## Owner decision
Canonical Hugging Face integration owner remains:
`router inteligente universal/integration/huggingface/`

This preserves the Router ownership chain:
`FastAPI -> Enchufe Gate -> RedUniversal -> HF adapter`.

## Compared roots
1. `router inteligente universal/integration/huggingface/`
   - `hf_jobs_compute.py`: submit/inspect official HF Jobs API.
   - `huggingface_openai_chat.py`: fail-closed certified-model chat adapter.
   - `router_hot_path.py`: reuses RedUniversal; does not create a second router.
   - `fastapi_gateway.py`: HTTP boundary.
   - `api_key_auth.py`: secret-ref runtime auth.
   - `model_registry.json`: 20 observed slots with per-slot status/evidence.
2. `coneccion huggueface Github/router/dispatcher.py`
   - Adds deterministic HF1 -> HF2 -> HF3 -> WAITING queue selection.
   - Useful capability, but currently outside canonical integration owner.
3. `coneccion huggueface Github/router/hf_jobs_adapter.py`
   - Adds RAM-aware slot refresh/selection and Job launch.
   - Overlaps canonical `HFJobsCompute` submission responsibility.
4. `huggueface/bridge/router_hf_bridge.py`
   - Direct HTTP routing to Groq/Cerebras/NVIDIA/OpenRouter/HF.
   - Bypasses RedUniversal ownership if activated directly.
   - `bridge_health()` declares FastAPI/MCP/SSE/webhook/websocket capabilities not implemented by this file's executable code.

## Test evidence
`coneccion huggueface Github/tests/` contains only:
- `E2E_FINAL.md` -> `E2E_GITHUB_PASS`
- `MCP_WRITE_TEST.md` -> `HF_GITHUB_WRITE_PASS`

These markers do **not** prove HF1/HF2/HF3 scheduling, RAM thresholds, failover, or Job execution.

## Classification
- `integration/huggingface/`: **CANONICAL_OWNER**
- `dispatcher.py`: **ADAPT_CANDIDATE_SCHEDULER**
- `hf_jobs_adapter.py`: **ADAPT_CANDIDATE_WITH_OVERLAP**
- `router_hf_bridge.py`: **DONOR_LEGACY_MULTI_PROVIDER / NOT_ROUTING_OWNER**

## Safe integration plan
1. Extract only deterministic slot scheduling into a new canonical module (for example `integration/huggingface/hf_scheduler.py`) or into `hf_jobs_compute.py` without duplicating Job submission.
2. Add focused unit tests: HF1 available; HF1 full -> HF2; HF1/HF2 unavailable -> HF3; all unavailable -> WAITING; exact RAM threshold behavior.
3. Add one real HF Job smoke test through the canonical path and read back job id/status/log.
4. Keep multi-provider direct routing inactive; provider metadata may be reused later behind `connector_registry`/RedUniversal only.

## Closure
`PASS_AUDIT_ONLY`: ownership and overlap are resolved.
Runtime scheduler integration remains **PENDING** until focused tests + real HF Job evidence pass.

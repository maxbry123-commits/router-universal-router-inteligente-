# RIU-0031 — Hugging Face catalog/token audit

Contract: `tel.workflow/v3` · mode: `FAIL_CLOSED_LOOP`

## INPUT literal applied
Resolve Hugging Face first; research official documentation before the delta; use HF Jobs as real project compute; audit real model availability; do not invent `model_id`; queue 1×1; investigate a GAP with a materially different StrategyDelta.

## Official research
- https://huggingface.co/docs/hub/en/jobs
- https://huggingface.co/docs/hub/en/jobs-configuration
- https://huggingface.co/docs/huggingface_hub/en/guides/jobs

Official Jobs configuration documents built-ins `JOB_ID`, `ACCELERATOR`, `CPU_CORES`, `MEMORY`; user secrets must be explicitly passed. In particular, `HF_TOKEN` can be passed as a secret; it is not documented as an automatic built-in token.

## Auth context
Connected Hugging Face identity: `COMAND-CENTER-1` (OAuth). Observed scopes from connected tool: `jobs`, `openid`, `profile`, `read-mcp`, `read-repos`. No token value was read or persisted.

## Queue 1×1 execution
Attempt A: Job `6aa1d3125527934177ebe373` attempted a shallow clone of the large Router repository before catalog inspection. It remained in clone work and was cancelled; no PASS claim.

StrategyDelta B: remove repository clone entirely and execute only the catalog/auth boundary audit in a fresh Job.

HF Job: `6aa1d38621047bf1b0370f3f`
URL: https://huggingface.co/jobs/COMAND-CENTER-1/6aa1d38621047bf1b0370f3f
Flavor: `cpu-basic` (2 CPU / 16.0G observed; cpu-upgrade was intentionally not used because this tiny network enumeration does not need 32 GB).
Status: `COMPLETED`.

Observed result:
```json
{
  "public_model_count": 0,
  "public_model_ids": [],
  "hf_token_present": false
}
```

## Decision
`GAP-HF-CATALOG-001` remains OPEN but is narrowed: the Job runtime has no implicit `HF_TOKEN`; therefore an authenticated private catalog cannot be proven from this Job. Public namespace enumeration independently returns zero models. This does **not** prove there are no private models.

No `model_id -> specialty -> adapter -> FastAPI` entry is created because no model ID was confirmed.

## Council12 / refutations / CODA
Council12: PASS for the audit delta only.

Refutations:
1. Public count 0 does not imply private count 0.
2. OAuth access in the connected Hugging Face tool does not imply an `HF_TOKEN` is injected into Jobs.
3. Successful Jobs execution does not authorize a FastAPI adapter without a confirmed model ID/endpoint contract.

Cross-check: PASS against STATE, CHECKPOINT, architecture README and Handoff rules.
CODA: `PASS_HF_CATALOG_BOUNDARY_AUDIT_GAP_REFINED`.
verify_final: `PASS_AUDIT_ONLY_NO_MODEL_CLAIM`.

## Next safe action
Continue only an independent Step-2 component with sufficient Router-owned contract, or retry private HF catalog enumeration only when an explicit secure credential path/evidence becomes available. Never hardcode or log tokens.

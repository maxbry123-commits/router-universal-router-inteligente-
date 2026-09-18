# RIU-0088 — AUTHORITATIVE STATE DRIFT X-RAY

Contract: `tel.workflow/v3`; mode: `FAIL_CLOSED_LOOP`.

Fresh base main: `6e3bbc962e3290d39d43cfb56156945d49d69f6d`.

## Sources reconstructed before mutation
Recursive root tree, architecture README, component index, Handoff, STATE, PLAN, Crazy Wall, CHECKPOINT, HF model registry and RIU-0087.

## Critical drift
- STATE: `ACTIVE_PRIORITY_LOCK_5`, node RIU-0086; still carries HF mirror/download-era tasks.
- PLAN: active node still RIU-0071 and retains HF mirror/replica execution language.
- Handoff: live node still RIU-0071.
- CHECKPOINT: checkpoint RIU-0083, current node RIU-0086, dated 2026-09-17.
- RIU-0087 is newer truth: AI Staff uses remote HF inference, no persistent weight installation. Gate: `REGISTER -> REMOTE_PROVIDER_DISCOVERY -> AUTH_REFERENCE -> REMOTE_INFERENCE_SMOKE -> FAILURE/FALLBACK_TEST -> EVIDENCE -> READY`.
- model_registry V11 still has legacy `download_state/hash_state/load_test_state/download_decision` fields for requested video/image models. Migrate without deleting provenance.

## Ownership X-Ray
`RedUniversal` remains sole routing owner. OmniRoute is downstream adapter candidate/materialized donor, Orca external ADE, Omarchy optional host, AnyDoc ingest adapter. None may become routing owner.

## Closure matrix
| Wave | Boundary | Test/evidence | Gate |
|---|---|---|---|
| W1 | state/docs + root inventory | read-back, blobs, container X-Ray | STATE_DOC_SYNC + FULL_COMPONENT_XRAY |
| W2 | OmniRoute | health/fallback/rate-limit | OMNIROUTE_ADAPTER_VERIFIED |
| W2 | AnyDoc | multiformat/error/hashes | ANYDOC_ADAPTER_VERIFIED |
| W2 | Orca | isolated worktree + verifier-gated merge | ORCA_BOUNDARY_VERIFIED |
| W2 | Omarchy | optional host checklist | OMARCHY_OPTION_VALIDATED |
| W3 | HF remote models | provider discovery/auth/smoke/failure/fallback | HF_REMOTE_MODELS_VERIFIED |
| W3 | GitHub/HF/Claude/Codex/MCP/memory | runtime probes, secret refs only | AUTH_RUNTIME_VERIFIED |
| W4 | global fabric | E2E + controlled failure | CONNECTIVITY_GLOBAL_E2E_PASS |
| W5 | all authorities | synchronized read-back | GLOBAL_CLOSE_ELIGIBLE |

## Next safe delta
Migrate registry semantics to remote inference while preserving historical fields under provenance; synchronize STATE/PLAN/CHECKPOINT/Handoff/Crazy Wall; continue external adapter/runtime gates. Presence is never PASS.

Status: `ACTIVE_RIU_0088_STATE_DRIFT_RECONCILIATION`; global close remains blocked by real gates.

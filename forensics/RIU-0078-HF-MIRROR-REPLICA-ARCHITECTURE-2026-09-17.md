# RIU-0078 — Hugging Face mirror / replica architecture

Contract: `tel.workflow/v3`
Date: 2026-09-17
Status: `RESEARCH_VERIFIED / DESIGN_DEFINED / NO_DUPLICATION_EXECUTED`

## Official mechanisms

### 1. Repository duplicate — logical mirror/copy
Official Hugging Face Hub supports repository duplication programmatically with `duplicate_repo()` and via CLI with `hf repos duplicate`.
Sources:
- https://huggingface.co/docs/huggingface_hub/guides/repository
- https://huggingface.co/docs/huggingface_hub/main/package_reference/cli
- https://huggingface.co/docs/hub/repositories-next-steps

RIU interpretation:
`SOURCE_MODEL_REPO@REVISION -> DUPLICATE_REPO -> RIU_MIRROR_REPO`

This is a repository-level copy, not an inference replica.

Required evidence before/after:
- source repo id
- source revision/commit SHA
- destination repo id
- visibility/region policy
- destination read-back
- model card/license retained
- no secret embedded

No duplicate is created in RIU-0078 because a destination namespace/repo has not been explicitly assigned.

### 2. Inference Endpoint replicas — runtime replicas
Hugging Face Inference Endpoints expose minimum/maximum replica configuration and autoscaling.
Sources:
- https://huggingface.co/docs/inference-endpoints/guides/autoscaling
- https://huggingface.co/docs/inference-endpoints/guides/configuration
- https://huggingface.co/docs/huggingface_hub/package_reference/inference_endpoints

RIU interpretation:
`RedUniversal -> endpoint adapter -> HF Inference Endpoint -> N managed replicas`

The endpoint owns its internal replicas. RIU must not create one route per internal replica.

Availability policy:
- critical/low-latency route: min replicas >= 1 when cost allows
- burst route: configure max replicas > min
- intermittent/cost-saving route: scale-to-zero allowed only with explicit cold-start tolerance
- Router must handle cold-start/retry/fallback explicitly.

### 3. Revision-pinned snapshot/cache — local materialization
Official `snapshot_download()` downloads a whole repo and supports an explicit `revision`; files are cached locally.
Source:
- https://huggingface.co/docs/huggingface_hub/guides/download

RIU interpretation:
`repo_id@revision -> snapshot_download -> ephemeral/local cache`

This is neither a repository mirror nor an inference replica. It is useful for deterministic HF Jobs/tests and offline-ish warm caches.

## RIU four-level failover model
1. **MODEL_IDENTITY**: canonical `model_id + revision`.
2. **REPO_MIRROR_SET**: optional duplicated repos, each tied to the same approved source revision.
3. **ENDPOINT_SET**: one or more provider/endpoints; each endpoint may have managed replicas internally.
4. **LOCAL_SNAPSHOT**: revision-pinned cache for Jobs/tests where permitted.

Routing ownership remains:
`Enchufe Gate -> RedUniversal -> connector_registry -> endpoint/provider adapter`.

## Registry shape proposed
For each logical model:
- logical_model_id
- source_repo_id
- source_revision
- mirrors[]: repo_id, source_revision, verified_at, readback
- endpoints[]: provider, endpoint_ref, min_replica, max_replica, scale_to_zero, health
- snapshots[]: revision, environment, cache_policy, verified_hash/readback
- failover_order[]
- last_verified_at
- evidence[]

## Gates
### MIRROR_REPO_VERIFIED
- explicit destination
- duplicate succeeds
- destination read-back succeeds
- source revision recorded
- license/card policy preserved

### RUNTIME_REPLICA_VERIFIED
- endpoint configuration read-back
- min/max replica policy recorded
- health/inference succeeds
- scale-up/down behavior or configuration evidence
- cold-start path tested if scale-to-zero enabled

### SNAPSHOT_VERIFIED
- exact revision requested
- model/config files read back
- inference/load smoke test where applicable
- cache path treated as disposable unless explicitly persistent

## Closure
RIU-0078 closes **research/design only**.
Runtime mirror creation and endpoint replica configuration remain separate execution nodes because they require explicit destination/resource/cost choices.

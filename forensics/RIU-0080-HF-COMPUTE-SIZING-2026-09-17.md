# RIU-0080 — Hugging Face compute sizing for three logical workers

Contract: `tel.workflow/v3`
Date: 2026-09-17
Status: `RESEARCH_VERIFIED / POLICY_DEFINED / NO_PAID_PROVISIONING_CHANGE`

## Official current HF Jobs references
- Jobs configuration/hardware: https://huggingface.co/docs/hub/jobs-configuration
- Jobs pricing: https://huggingface.co/docs/hub/jobs-pricing
- Jobs guide: https://huggingface.co/docs/huggingface_hub/en/guides/jobs

Current documented examples include:
- `cpu-basic`: 2 vCPU / 16 GB RAM / 50 GB ephemeral
- `cpu-upgrade`: 8 vCPU / 32 GB RAM / 50 GB ephemeral
- T4: 16 GB GPU memory
- A10G: 24 GB GPU memory
- L40S x1: 48 GB GPU memory
- larger multi-GPU flavors also exist

Jobs are billed by hardware usage/minute. This plan therefore avoids keeping expensive hardware running merely because a logical worker exists.

## Existing RIU evidence
- HF-M01 Qwen3-0.6B: CPU real-inference evidence exists.
- HF-M02 GPT-2: CPU real-inference evidence exists.
- HF-M03 Qwen3-8B: A10G real-inference evidence exists; registry recorded max GPU memory allocated ≈16.4 GB.
- HF-M04 Qwen3-Coder-30B-A3B GGUF: catalog/variant discovery exists but prior runtime attempts did not establish stable inference PASS.
- M13 120B / M19 72B / M16 DeepSeek-V4 class: no evidence supports assuming they fit one 24 GB worker.

## Three logical worker lanes
The RIU scheduler's `HF1/HF2/HF3` are **logical workers**, not fixed machines.

### HF1 — control / tests / small models
Default candidate: `cpu-basic`.
Escalate to `cpu-upgrade` only when RAM/CPU evidence requires it.
Work:
- metadata inventory
- contract tests
- adapters
- tiny/small inference already proven feasible
- download/hash/read-back
- scheduler/control work

### HF2 — medium GPU lane
Default candidate for proven Qwen3-8B-style work: `a10g-small` (24 GB GPU).
Work:
- medium model inference
- adapter/hot-path verification
- code/model smoke tests that need CUDA
Evidence gate: peak memory + successful generation + timeout.

### HF3 — large/burst lane
No fixed flavor is assumed.
Candidate ladder:
1. `l40sx1` / 48 GB class when one-GPU memory evidence is sufficient;
2. multi-GPU A10G/L40S/A100/H200 classes only after model/quantization benchmark;
3. prefer managed inference provider/Endpoint for very large models when loading weights into Jobs is inefficient.

This lane is allocated only per task and can stay idle logically without paying for a continuously running machine.

## Scheduling policy
1. Classify job: CONTROL_SMALL | GPU_MEDIUM | GPU_LARGE.
2. Select HF1/HF2/HF3 logical lane.
3. Choose hardware flavor at dispatch time from measured requirement.
4. If flavor unavailable/too costly/insufficient, do not silently downsize; mark GAP or route to a verified provider Endpoint through RedUniversal.
5. Record Job ID, flavor, model revision, elapsed time, peak memory when available, result and cost-relevant duration.
6. Release/cancel temporary servers/jobs after completion.

## Model policy
- <= small models with proven CPU path: start HF1.
- Qwen3-8B class with proven evidence: HF2/A10G baseline.
- Qwen3-Coder 30B class: HF3 benchmark required; no READY claim yet.
- 70B+/120B+/very-large MoE: provider/Endpoint first unless a specific multi-GPU Job benchmark proves a cheaper/reliable local path.

## Closure
The **compute sizing policy** is defined and evidence-backed.
Actual paid flavor provisioning and large-model benchmarks remain runtime nodes and must be authorized by the workload itself, not pre-provisioned speculatively.

# RIU-0035 — HF-M01 metadata validation + registry reconciliation

## INPUT
Validate HF-M01 1×1 under tel.workflow/v3 / FAIL_CLOSED_LOOP and do not promote unverified model IDs.

## Sources checked
- Certified public catalog Job: https://huggingface.co/jobs/COMAND-CENTER-1/6aa2513d5527934177ebfaad
- Model: https://huggingface.co/Qwen/Qwen3-0.6B
- Official Jobs docs: https://huggingface.co/docs/hub/en/jobs-configuration
- Official model metadata retrieved through Hugging Face Hub connector.

## HF-M01 evidence
`Qwen/Qwen3-0.6B` exists and reports task `text-generation`, library `transformers`, model class `AutoModelForCausalLM`, architecture `qwen3`, 751.6M parameters, Apache-2.0 license, `text-generation-inference`, `endpoints_compatible`, and a live inference provider (`featherless-ai`).

## GAP found
The previous `model_registry.json` contained a different set of 20 model IDs than the certified Job catalog. Presence of those records was not sufficient evidence that those were the 20 validated Router models.

## StrategyDelta
Replaced the registry contents with the exact 20 IDs already certified by Job `6aa2513d5527934177ebfaad`. HF-M01 is promoted only to `METADATA_VALIDATED`; processor runtime load, accelerator runtime validation, dataset/storage binding, adapter wiring and FastAPI hot-path remain pending.

## Runtime attempt
A direct HF Jobs UV invocation for an actual local load/generation was attempted from the automation tool and was blocked by the execution safety layer before Job creation. This is not a model failure and is not counted as runtime evidence.

## Refutations
1. Metadata compatibility does not prove local/runtime inference.
2. `endpoints_compatible` does not prove the Router FastAPI hot-path.
3. A corrected registry does not close dataset/storage or private-catalog gaps.

## verify_final
`PASS_REGISTRY_TRUTH_RECONCILED / HF-M01_METADATA_VALIDATED / RUNTIME_PENDING`.

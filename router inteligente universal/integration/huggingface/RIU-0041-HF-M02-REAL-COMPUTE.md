# RIU-0041 — HF-M02 REAL COMPUTE AUDIT

Contract: `tel.workflow/v3`  
Mode: `FAIL_CLOSED_LOOP`  
Scope: PASO 1 only — independent safe validation while `FLAG-HF-PROVIDER-AUTH-001` remains open.

## INPUT / GOALS
Validate only the real-compute/processor/accelerator slice for catalog slot HF-M02 `openai-community/gpt2`; do not promote READY by presence or compute alone.

## Research before execution
- Official Hugging Face Transformers GPT-2 docs: `https://huggingface.co/docs/transformers/main/model_doc/gpt2` — causal text generation, `AutoModelForCausalLM`, generation examples.
- Official Hugging Face generation docs: `https://huggingface.co/docs/transformers/main_classes/text_generation` — `generate()` and `max_new_tokens` semantics.
- Hub metadata read-back for `openai-community/gpt2`: task `text-generation`, library `transformers`, license MIT, endpoints-compatible.

## Real HF Jobs evidence
Job URL: `https://huggingface.co/jobs/COMAND-CENTER-1/6aa2a4f25527934177ec0e01`
Job ID: `6aa2a4f25527934177ec0e01`
Flavor: `cpu-upgrade`
Image: `ghcr.io/astral-sh/uv:python3.12-bookworm`
Final stage: `COMPLETED`
Finished: `2026-09-10T12:40:02.747Z`

Observed logs:
- `MODEL openai-community/gpt2`
- `CLASS GPT2LMHeadModel`
- `DEVICE cpu`
- `PARAMS 124439808`
- real generated output observed
- `ELAPSED 6.338`
- `HF_M02_REAL_COMPUTE_OK True`

## Registry result
`model_id -> specialty -> adapter -> FastAPI` currently remains:
`openai-community/gpt2 -> text-generation -> PENDING -> PENDING`.
Processor/runtime tokenizer and CPU compute are verified; dataset/storage, adapter and FastAPI routing are not yet verified for HF-M02.

## 3 refutations
1. Successful local model inference does not prove Enchufe/Router/adapter/FastAPI routing for HF-M02.
2. Successful local model inference does not prove HF-M02 dataset/storage binding or persistent RW storage.
3. HF-M02 progress does not resolve HF-M01 provider authorization; `FLAG-HF-PROVIDER-AUTH-001` stays open.

Council12=`PASS`  
Cross-check=`PASS`  
CODA=`PERSIST_HF_M02_COMPUTE_KEEP_BOTH_MODELS_NO_READY`  
verify_final=`PASS_HF_M02_REAL_COMPUTE_ONLY`

## Next 1x1
Validate HF-M02 dataset/storage + adapter/FastAPI behind the single Enchufe Universal gateway. No model promotion until its remaining gates have route+SHA/read-back+test/log+URL evidence.
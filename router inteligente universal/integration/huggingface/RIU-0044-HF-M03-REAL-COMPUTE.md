# RIU-0044 — HF-M03 REAL COMPUTE

Contract: `tel.workflow/v3` · Mode: `FAIL_CLOSED_LOOP`.

## INPUT / GOALS12
Validate slot HF-M03 exactly as observed in the certified catalog: `Qwen/Qwen3-8B`. No invented model IDs. Compute must run in Hugging Face Jobs and must not imply READY for adapter/dataset/storage/FastAPI.

## Research before execute
- Hugging Face model metadata: `Qwen/Qwen3-8B`, transformers, AutoModelForCausalLM/Qwen3, 8.19B parameters, Apache-2.0, text-generation/conversational, live providers observed.
- Qwen3 technical benchmark reports Qwen3-8B Transformers BF16 around 15.9 GB GPU memory at minimal context; selected `a10g-small` to avoid knowingly undersizing a 16 GB class device.

## Execute
HF Job: `6aa2ecbb21047bf1b037318e`
URL: https://huggingface.co/jobs/COMAND-CENTER-1/6aa2ecbb21047bf1b037318e
Flavor: `a10g-small`
Image: `pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime`
Model: `Qwen/Qwen3-8B`

## Verify / read-back logs
- final stage: `COMPLETED`
- `MODEL_CLASS Qwen3ForCausalLM`
- `PARAMS 8190735360`
- `LOAD_SECONDS 140.803`
- `REPLY 'RIU_HF_M03_OK'`
- `GEN_SECONDS 0.986`
- `MAX_MEMORY_ALLOCATED 16396255232`
- `HF_M03_REAL_COMPUTE_OK True`

## Decision
PASS only for HF-M03 real model load + tokenizer/chat-template + GPU inference. Status becomes `COMPUTE_VERIFIED_NOT_READY`. Adapter, dataset/storage and FastAPI remain PENDING.

## GAP cross-check
Registry V7 was stale for HF-M02 integration/storage state; RIU-0044 reconciles registry truth while preserving HF-M02 NO READY and both external 403 flags.

## Council12 / 3 refutations / CODA
Council12: PASS.
1. `COMPLETED` compute does not prove FastAPI/Enchufe adapter wiring.
2. GPU inference does not prove dataset/storage persistence.
3. HF-M03 success does not close HF-M01 provider auth or HF-M02 storage auth.
Cross-check: PASS.
CODA: persist compute evidence, keep HF-M03 NO READY, queue integration validation.
verify_final=`PASS_HF_M03_REAL_COMPUTE_ONLY`.

# RIU-0038 — HF-M01 real compute validation

Contract: `tel.workflow/v3`
Mode: `FAIL_CLOSED_LOOP`
Node: `P01_HF_M01_SERVING_VALIDATION`
Model: `Qwen/Qwen3-0.6B`

## Research gate
- Official Hugging Face Inference Providers / InferenceClient documentation: chat models should use `InferenceClient.chat_completion` / OpenAI-compatible chat completions and require a valid inference token for hosted providers.
- Hugging Face community reports confirm provider/task mismatches are avoided by using chat-completion semantics for conversational Qwen deployments.

## Real HF Jobs compute evidence
- Job: `6aa288a521047bf1b0372324`
- URL: https://huggingface.co/jobs/COMAND-CENTER-1/6aa288a521047bf1b0372324
- Flavor: `cpu-upgrade`
- Final stage: `COMPLETED`
- Runtime path: `AutoTokenizer.from_pretrained` + `AutoModelForCausalLM.from_pretrained(... device_map='cpu')` + deterministic `generate()`.
- Prompt requested exact marker `RIU_HF_M01_OK`.
- Read-back output: `REPLY=RIU_HF_M01_OK`.
- `HF_M01_REAL_COMPUTE_OK=True`.
- `LOAD_AND_INFER_SECONDS=7.108`.
- Runtime parameter count observed from loaded model: `596049920`.
- Device: `cpu`.

## Verify/refute
PASS: HF-M01 weights/tokenizer were materially loaded and inference executed inside a real HF Job.
NOT PASS: this does not yet prove the repository FastAPI gateway traverses Enchufe Universal / Router and reaches the model.
NOT PASS: hosted Inference Providers authentication remains separate from this local HF Jobs compute path.
NOT PASS: dataset/storage binding is not yet certified.

## Council12 / cross-check / CODA
- Council12: PASS for compute-only certification.
- Cross-check: PASS against prior HF-M01 metadata/config evidence; the earlier safetensors metadata parameter figure is not substituted for the runtime-loaded `sum(p.numel())` measurement.
- CODA: `PASS_REAL_HF_JOB_COMPUTE_KEEP_ROUTER_HOT_PATH_PENDING`.
- verify_final: `PASS_HF_M01_REAL_COMPUTE_ONLY_ROUTER_ENCHUFE_DATASET_PENDING`.

## Next 1x1 delta
Wire and verify the existing FastAPI gateway through the recovered Enchufe Universal contract and Router path, then bind dataset/storage evidence. HF-M01 remains `NO READY` until that path is real and verified.

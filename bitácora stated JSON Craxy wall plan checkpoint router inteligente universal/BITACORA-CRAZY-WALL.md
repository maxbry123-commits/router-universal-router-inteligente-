# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0038 — TRAZABILIDAD PREVIA
Baseline, arquitectura, catálogo 20, HF-M01 config/tokenizer/generation, compute local real y adapter/gateway preservados por commits/STATE/CHECKPOINT previos.

## RIU-0039 — HF-M01 ENCHUFE/ROUTER HOT-PATH
`router_hot_path.py` reutiliza Enchufe Gate + RedUniversal. Gateway actualizado sin bypass directo. HF Job `6aa297195527934177ec0aed` leyó `main` y ejecutó pytest: `2 passed in 1.25s`, RC=0. Auditoría commit `f08191ec91f0d74850799b38b44298bc77f0cfe9`. Verify_final=`PASS_DETERMINISTIC_ROUTER_ENCHUFE_HOT_PATH_DATASET_AUTH_PENDING`.

## RIU-0040 — HF-M01 DATASET/STORAGE + PROVIDER AUTH
Fuentes de verdad releídas antes del delta. Prioridades: (1) verificar binding real de dataset/storage en HF Jobs; (2) probar provider hosted con secreto autorizado sin exponerlo.

Dataset confirmado por Hub: `HuggingFaceH4/ultrachat_200k`, MIT, text-generation, parquet, 100K<n<1M.
HF Job `6aa2983921047bf1b03725eb`, `cpu-upgrade`, volume `hf://datasets/HuggingFaceH4/ultrachat_200k:/data:ro`, COMPLETED.
Read-back: mount=True, 10 files, parquet train/test gen+sft, manifest SHA256 `241f6f1a9ac692d9bb2c1556e2be369c15d6a53401256749d34f3e1a6fc0b640`, `HF_M01_DATASET_STORAGE_BINDING_OK True`.

Provider auth: Job `6aa2985921047bf1b03725ed` usó secret runtime `HF_TOKEN` mediante mecanismo de Jobs; inspección lo redactó. La petición alcanzó `https://router.huggingface.co/v1/chat/completions` pero terminó 403: método de autenticación sin permisos suficientes para Inference Providers de `COMAND-CENTER-1`.
FLAG registrado: `FLAG-HF-PROVIDER-AUTH-001=TOKEN_SCOPE_INSUFFICIENT_FOR_INFERENCE_PROVIDERS`.

3 refutaciones: mount RO != bucket RW persistente; token presente != permiso inference; compute+hot-path+dataset != READY mientras provider auth falle.
Council12 PASS; cross-check PASS; CODA `CLOSE_DATASET_BINDING_REGISTER_PROVIDER_AUTH_FLAG_KEEP_HF_M01_NO_READY`; verify_final=`PASS_DATASET_BINDING_PROVIDER_AUTH_FLAGGED`.
Auditoría RIU-0040: commit `dbcd504acc500e31d36abcddaf103434d87866e9`.

## RIU-0041 — HF-M02 REAL COMPUTE
Fuentes de verdad releídas antes del delta. El FLAG de HF-M01 se mantuvo abierto y se continuó únicamente trabajo P01 independiente seguro.
Investigación oficial HF: GPT-2 es causal text-generation, compatible con `AutoModelForCausalLM`; la documentación recomienda `generate()`/`max_new_tokens`. Metadata Hub de `openai-community/gpt2`: transformers, MIT, endpoints-compatible.
HF Job `6aa2a4f25527934177ec0e01`, imagen `uv:python3.12-bookworm`, flavor `cpu-upgrade`, COMPLETED el 2026-09-10T12:40:02Z.
Logs: `MODEL openai-community/gpt2`; `CLASS GPT2LMHeadModel`; `DEVICE cpu`; `PARAMS 124439808`; generación real; `ELAPSED 6.338`; `HF_M02_REAL_COMPUTE_OK True`.
Decisión: compute/acelerador local de HF-M02 PASS solamente. Adapter, dataset/storage, FastAPI/provider routing siguen PENDING; HF-M02 NO READY.
3 refutaciones: compute != adapter/FastAPI; compute != dataset/storage; HF-M02 progress no resuelve FLAG provider-auth HF-M01.
Council12 PASS; cross-check PASS; CODA `PERSIST_HF_M02_COMPUTE_KEEP_BOTH_MODELS_NO_READY`; verify_final=`PASS_HF_M02_REAL_COMPUTE_ONLY`.

## NEXT
Cola 1×1: validar HF-M02 dataset/storage + adapter/FastAPI detrás del Enchufe Universal. Mantener HF-M01 `FLAG-HF-PROVIDER-AUTH-001` abierto hasta credencial autorizada con permiso suficiente.
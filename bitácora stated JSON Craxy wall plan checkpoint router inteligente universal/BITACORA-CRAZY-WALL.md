# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0036 — TRAZABILIDAD PREVIA
Baseline, arquitectura, componentes, HF Jobs, catálogo 20 y validación HF-M01 config/tokenizer/generation preservados por commits/STATE/CHECKPOINT previos.

## RIU-0037 — HF-M01 ADAPTER + GATEWAY FASTAPI ÚNICO
Adapter `integration/huggingface/huggingface_openai_chat.py`, gateway único `fastapi_gateway.py` y registry V4 materializados/read-back. Verify_final: `PASS_CODE_READBACK_ONLY_RUNTIME_HOT_PATH_PENDING`.

## RIU-0038 — HF-M01 INFERENCIA REAL EN HF JOB
HF Job `6aa288a521047bf1b0372324`, flavor `cpu-upgrade`, COMPLETED. Read-back: `REPLY=RIU_HF_M01_OK`, `HF_M01_REAL_COMPUTE_OK=True`, 596049920 parámetros, CPU, 7.108s. Evidencia commit `d798b6b878d3876ce866584647fd41b9cf8c6c23`. Verify_final: `PASS_HF_M01_REAL_COMPUTE_ONLY_ROUTER_ENCHUFE_DATASET_PENDING`.

## RIU-0039 — HF-M01 ENCHUFE/ROUTER HOT-PATH
INPUT literal/fuentes releídas. Prioridades: (1) eliminar bypass FastAPI→adapter; (2) probar Enchufe Gate + RedUniversal sin promover READY prematuramente.

Investigación previa:
- HF `InferenceClient.chat_completion` es OpenAI-compatible;
- HF Jobs tiene storage efímero por flavor y permite datasets/buckets por streaming/mount; Storage Buckets persisten resultados.

Delta ADAPT:
- `integration/huggingface/router_hot_path.py` reutiliza `red/enchufe_gate.py` + `red/red_universal.py`; commit `86f5f545f070dc3180652e73265f6fc77ba1e514`.
- `fastapi_gateway.py` actualizado para delegar por hot-path; commit `6da8ecd573986bc4e77a2c749e37d9f34955bd57`.
- `tests/test_hf_router_hot_path.py`; commit `8509fa25793fec73a1e9ce023787713df5ed4225`.

Primer Job `6aa2970221047bf1b0372550`: fallo pre-test `base64: invalid input`. StrategyDelta materialmente distinto: bootstrap Python directo como argv, sin base64.
Segundo Job `6aa297195527934177ec0aed`, `cpu-upgrade`, COMPLETED. Leyó desde `main` siete archivos del hot-path y ejecutó pytest: `2 passed in 1.25s`; `RIU_HOT_PATH_TEST_RC 0`.
URL: https://huggingface.co/jobs/COMAND-CENTER-1/6aa297195527934177ec0aed
Auditoría detallada: `integration/huggingface/RIU-0039-HF-M01-ENCHUFE-ROUTER-HOT-PATH.md`, commit `f08191ec91f0d74850799b38b44298bc77f0cfe9`.

3 refutaciones:
1. Executor fake en test ≠ provider hosted autenticado.
2. Hot-path determinista ≠ dataset/storage binding.
3. Inferencia local + routing determinista ≠ E2E P03 autenticado por agente.

Council12 PASS; cross-check PASS; CODA `CLOSE_ROUTER_ENCHUFE_CODE_GAP_KEEP_DATASET_AUTH_PENDING`; verify_final=`PASS_DETERMINISTIC_ROUTER_ENCHUFE_HOT_PATH_DATASET_AUTH_PENDING`.

## NEXT
HF-M01 1×1: cerrar dataset/storage + provider hosted autenticado por FastAPI→Enchufe→RedUniversal→adapter. Solo entonces promover HF-M01 y abrir HF-M02.
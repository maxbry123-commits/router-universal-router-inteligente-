# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0036 — TRAZABILIDAD PREVIA
Baseline, arquitectura, componentes, HF Jobs, catálogo 20 y validación HF-M01 config/tokenizer/generation preservados por commits/STATE/CHECKPOINT previos.

## RIU-0037 — HF-M01 ADAPTER + GATEWAY FASTAPI ÚNICO
INPUT literal: continuar P01 1×1, investigar primero, no promover READY por presencia.

Investigación oficial: Hugging Face documenta `InferenceClient.chat_completion` como interfaz compatible con OpenAI y TGI/HUGS expone `/v1/chat/completions`; autenticación por token de runtime.

Delta ejecutado:
- `router inteligente universal/integration/huggingface/huggingface_openai_chat.py`
  - allowlist estricta desde `model_registry.json`
  - `HF_TOKEN` sólo en environment/runtime
  - `InferenceClient.chat_completion`
  - commit `70b2a7d4b5ee419999e3b6f436e219370141d294`
  - read-back blob `3d89e6e705fb30a55ca5ae72db05538bdabbabb7`
- `router inteligente universal/integration/huggingface/fastapi_gateway.py`
  - gateway único
  - `/health`, `/v1/models`, `/v1/chat/completions`
  - commit `ea0392a58ce6391514471926a315a6ebd9928521`
  - read-back blob `a7a2c16019adee69de597ec0abd251912a8a11ca`
- `model_registry.json` V4
  - HF-M01 adapter=`WIRED_CODE_READBACK`
  - FastAPI=`REGISTERED_CODE_READBACK`
  - status=`SERVING_RUNTIME_PENDING`
  - commit `3de1df105276080ae8c94067816d2e190c8b18df`

Verificación/refutación:
1. Código adapter ≠ inferencia real.
2. Ruta FastAPI ≠ paso probado por Enchufe/Router.
3. Provider live ≠ runtime autenticado con `HF_TOKEN`.

Council12 PASS; cross-check PASS; CODA `KEEP_HF_M01_SERVING_RUNTIME_PENDING`; verify_final=`PASS_CODE_READBACK_ONLY_RUNTIME_HOT_PATH_PENDING`.

## NEXT
HF-M01 1×1: inferencia runtime autenticada → Enchufe/Router hot path → dataset/storage/acelerador → solo entonces READY y HF-M02.

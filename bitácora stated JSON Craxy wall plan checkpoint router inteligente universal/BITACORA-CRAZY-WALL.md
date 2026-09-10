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

## RIU-0038 — HF-M01 INFERENCIA REAL EN HF JOB
INPUT literal y fuentes de verdad releídas antes del delta. Prioridades: (1) comprobar compute material HF-M01; (2) preservar fail-closed del hot-path no demostrado.

Investigación:
- documentación oficial HF: `InferenceClient.chat_completion` / OpenAI-compatible Inference Providers exige autorización de inferencia para hosted routing;
- comunidad Hugging Face: Qwen/provider conversational debe probarse mediante chat-completion y no confundirse con `text_generation`.

Ejecución material:
- HF Job `6aa288a521047bf1b0372324`, flavor `cpu-upgrade`, stage `COMPLETED`;
- `AutoTokenizer.from_pretrained('Qwen/Qwen3-0.6B')`;
- `AutoModelForCausalLM.from_pretrained(..., device_map='cpu')`;
- generación determinista con marker esperado;
- read-back: `REPLY=RIU_HF_M01_OK`;
- `HF_M01_REAL_COMPUTE_OK=True`;
- `LOAD_AND_INFER_SECONDS=7.108`;
- `PARAMS=596049920`; `DEVICE=cpu`.
- evidencia persistida: `router inteligente universal/integration/huggingface/RIU-0038-HF-M01-REAL-COMPUTE.md`, commit `d798b6b878d3876ce866584647fd41b9cf8c6c23`.

3 refutaciones:
1. Inferencia local real en HF Job ≠ FastAPI→Enchufe→Router verificado.
2. Compute CPU real ≠ hosted provider auth verificado.
3. Inferencia del modelo ≠ dataset/storage binding verificado.

Council12 PASS; cross-check PASS; CODA `PASS_REAL_HF_JOB_COMPUTE_KEEP_ROUTER_HOT_PATH_PENDING`; verify_final=`PASS_HF_M01_REAL_COMPUTE_ONLY_ROUTER_ENCHUFE_DATASET_PENDING`.

## NEXT
HF-M01 1×1: demostrar `FastAPI -> Enchufe Universal -> Router -> HF-M01` con código persistido + dataset/storage → solo entonces READY y HF-M02.

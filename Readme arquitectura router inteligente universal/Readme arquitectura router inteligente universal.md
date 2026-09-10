# Router Inteligente Universal — Arquitectura y estado de integración

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## 1. Objetivo
Backend Python 95% determinista / 5% LLM. Flujo: `INPUT -> classifier -> DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> conector -> destino -> verify/state`.

## 2. Plan autorizado — solo 3 pasos
1. Hugging Face + modelos + FastAPI — ACTIVE.
2. Integración GitHub/C01-C23 — PENDING tras P01.
3. API keys agentes + E2E — PENDING.

## 3. Estado P01 — RIU-0038
Catálogo público 20 certificado por HF Job `6aa2513d5527934177ebfaad`.
HF-M01 `Qwen/Qwen3-0.6B` config/tokenizer/generation validados por Job `6aa26cc321047bf1b0371f28`.
HF-M01 ejecutó inferencia material real en HF Job `6aa288a521047bf1b0372324` (`cpu-upgrade`): `REPLY=RIU_HF_M01_OK`, `HF_M01_REAL_COMPUTE_OK=True`, 596049920 parámetros observados en runtime, device CPU, 7.108s de carga+inferencia.
Adapter `integration/huggingface/huggingface_openai_chat.py` creado con allowlist del registry y `HF_TOKEN` runtime-only; commit `70b2a7d4b5ee419999e3b6f436e219370141d294`, blob `3d89e6e705fb30a55ca5ae72db05538bdabbabb7`.
Gateway FastAPI único `integration/huggingface/fastapi_gateway.py` creado con `/health`, `/v1/models`, `/v1/chat/completions`; commit `ea0392a58ce6391514471926a315a6ebd9928521`, blob `a7a2c16019adee69de597ec0abd251912a8a11ca`.
Registry V4 commit `3de1df105276080ae8c94067816d2e190c8b18df`.

HF-M01 sigue NO READY: compute real HF Jobs ya está probado, pero aún falta demostrar el recorrido del código persistido `FastAPI -> Enchufe Universal -> Router -> HF-M01` y cerrar dataset/storage. La autenticación del proveedor hosted continúa como frontera independiente de credencial.

## 4. Reglas
No crear 20 servidores FastAPI: un gateway único y adapters separados. No monolito. P02 usa `REUSE > PATCH > ADAPT > GENERATE`. Descarga/copia/movimiento exclusivamente por motores canónicos autorizados.

## 5. Cierre
`modelo listado != endpoint probado`; `archivo presente != integrado`; `compute local probado != hot-path Router probado`; `API key creada != autenticación probada`. Solo `VERIFIED_CLOSED` después de P03 E2E real.

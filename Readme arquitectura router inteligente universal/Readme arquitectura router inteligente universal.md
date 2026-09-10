# Router Inteligente Universal — Arquitectura y estado de integración

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## 1. Objetivo
Backend Python 95% determinista / 5% LLM. Flujo: `INPUT -> classifier -> DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> conector -> destino -> verify/state`.

## 2. Plan autorizado — solo 3 pasos
1. Hugging Face + modelos + FastAPI — ACTIVE.
2. Integración GitHub/C01-C23 — PENDING tras P01.
3. API keys agentes + E2E — PENDING.

## 3. Estado P01 — RIU-0037
Catálogo público 20 certificado por HF Job `6aa2513d5527934177ebfaad`.
HF-M01 `Qwen/Qwen3-0.6B` config/tokenizer/generation validados por Job `6aa26cc321047bf1b0371f28`.
Adapter `integration/huggingface/huggingface_openai_chat.py` creado con allowlist del registry y `HF_TOKEN` runtime-only; commit `70b2a7d4b5ee419999e3b6f436e219370141d294`, blob `3d89e6e705fb30a55ca5ae72db05538bdabbabb7`.
Gateway FastAPI único `integration/huggingface/fastapi_gateway.py` creado con `/health`, `/v1/models`, `/v1/chat/completions`; commit `ea0392a58ce6391514471926a315a6ebd9928521`, blob `a7a2c16019adee69de597ec0abd251912a8a11ca`.
Registry V4 commit `3de1df105276080ae8c94067816d2e190c8b18df`.

HF-M01 sigue NO READY: código/read-back ≠ runtime. Falta inferencia autenticada, paso efectivo por Enchufe/Router, dataset/storage y acelerador.

## 4. Reglas
No crear 20 servidores FastAPI: un gateway único y adapters separados. No monolito. P02 usa `REUSE > PATCH > ADAPT > GENERATE`. Descarga/copia/movimiento exclusivamente por motores canónicos autorizados.

## 5. Cierre
`modelo listado != endpoint probado`; `archivo presente != integrado`; `API key creada != autenticación probada`. Solo `VERIFIED_CLOSED` después de P03 E2E real.

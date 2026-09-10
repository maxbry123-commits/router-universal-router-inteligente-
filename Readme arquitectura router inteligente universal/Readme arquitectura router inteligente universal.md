# Router Inteligente Universal — Arquitectura y estado de integración

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## 1. Objetivo
Backend Python 95% determinista / 5% LLM. Flujo: `INPUT -> classifier -> DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> conector -> destino -> verify/state`.

## 2. Plan autorizado — solo 3 pasos
1. Hugging Face + modelos + FastAPI — ACTIVE.
2. Integración GitHub/C01-C23 — PENDING tras P01.
3. API keys agentes + E2E — PENDING.

## 3. Estado P01 — RIU-0039
Catálogo público 20 certificado por HF Job `6aa2513d5527934177ebfaad`.
HF-M01 `Qwen/Qwen3-0.6B` config/tokenizer/generation validados por Job `6aa26cc321047bf1b0371f28`.
HF-M01 ejecutó inferencia material real en HF Job `6aa288a521047bf1b0372324` (`cpu-upgrade`).
Adapter `integration/huggingface/huggingface_openai_chat.py` y gateway FastAPI único `integration/huggingface/fastapi_gateway.py` preservados.
Nuevo `integration/huggingface/router_hot_path.py` elimina el bypass FastAPI→adapter y reutiliza `red/enchufe_gate.py` + `red/red_universal.py`; no crea segundo router.
HF Job `6aa297195527934177ec0aed` leyó el código desde `main` y ejecutó `tests/test_hf_router_hot_path.py`: `2 passed in 1.25s`, RC=0.

HF-M01 sigue NO READY: el recorrido determinista Enchufe→RedUniversal→adapter quedó probado, pero aún faltan dataset/storage y provider hosted autenticado por ese hot-path. P03 auth/agentes continúa separado.

## 4. Reglas
No crear 20 servidores FastAPI: un gateway único y adapters separados. No monolito. P02 usa `REUSE > PATCH > ADAPT > GENERATE`. Descarga/copia/movimiento exclusivamente por motores canónicos autorizados.

## 5. Cierre
`modelo listado != endpoint probado`; `archivo presente != integrado`; `hot-path determinista != provider autenticado`; `API key creada != autenticación probada`. Solo `VERIFIED_CLOSED` después de P03 E2E real.
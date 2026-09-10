# Router Inteligente Universal — Arquitectura y estado de integración

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## 1. Objetivo
Backend Python 95% determinista / 5% LLM. Flujo: `INPUT -> classifier -> DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> conector -> destino -> verify/state`.

## 2. Plan autorizado — solo 3 pasos
1. Hugging Face + modelos + FastAPI — ACTIVE.
2. Integración GitHub/C01-C23 — PENDING tras P01.
3. API keys agentes + E2E — PENDING.

## 3. Estado P01 — RIU-0044
- Catálogo público 20 certificado.
- HF-M01 compute/hot-path/dataset RO verificados; provider auth 403 (`FLAG-HF-PROVIDER-AUTH-001`); NO READY.
- HF-M02 compute + integración FastAPI→Enchufe→Router→adapter verificados; storage RW create/write bloqueado por 403 (`FLAG-HF-M02-RW-STORAGE-AUTH-001`); NO READY.
- HF-M03 `Qwen/Qwen3-8B` compute real verificado por Job `6aa2ecbb21047bf1b037318e`: `Qwen3ForCausalLM`, 8190735360 params, respuesta `RIU_HF_M03_OK`, max GPU memory 16396255232; adapter/dataset/storage/FastAPI PENDING; NO READY.
- Registry reconciliado a V8.
- Cola P01 1×1: HF-M03 adapter + dataset/storage + FastAPI/Enchufe real.

## 4. Reglas
Gateway FastAPI único; adapters separados; sin monolito. P02 `REUSE > PATCH > ADAPT > GENERATE`. Descarga/copia/movimiento sólo motores canónicos autorizados.

## 5. Cierre
`compute != READY`; `dataset mount != output bucket`; `HTTP 200 != storage persistence`; `token presente != permiso inference/write`; solo `VERIFIED_CLOSED` tras P03 E2E real.
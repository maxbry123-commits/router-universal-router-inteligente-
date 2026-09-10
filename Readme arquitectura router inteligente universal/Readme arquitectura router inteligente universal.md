# Router Inteligente Universal — Arquitectura y estado de integración

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## 1. Objetivo
Backend Python 95% determinista / 5% LLM. Flujo: `INPUT -> classifier -> DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> conector -> destino -> verify/state`.

## 2. Plan autorizado — solo 3 pasos
1. Hugging Face + modelos + FastAPI — ACTIVE.
2. Integración GitHub/C01-C23 — PENDING tras P01.
3. API keys agentes + E2E — PENDING.

## 3. Estado P01 — RIU-0042
- Catálogo público 20 certificado.
- HF-M01 compute/hot-path/dataset RO verificados; provider hosted auth continúa 403 por permiso insuficiente (`FLAG-HF-PROVIDER-AUTH-001`); HF-M01 NO READY.
- HF-M02 `openai-community/gpt2` compute real verificado por Job `6aa2a4f25527934177ec0e01`.
- HF-M02 integración real verificada por Job `6aa2cf4f21047bf1b0372e67`: repo ZIP SHA256 `033a19f379e56f3a23bcad488af9089bc6f9a2e1fae25df6dd17a06bee8412df`; dataset mount True/16 files; HTTP 200; `FASTAPI_ENCHUFE_ROUTER_M02_OK=True`; GPT2LMHeadModel; 124439808 params.
- Storage RW persistente/output HF-M02 sigue NO PASS (`GAP-HF-M02-RW-STORAGE-001`); HF-M02 NO READY.

## 4. Reglas
Gateway FastAPI único; adapters separados; sin monolito. P02 `REUSE > PATCH > ADAPT > GENERATE`. Descarga/copia/movimiento sólo motores canónicos autorizados.

## 5. Cierre
`compute != READY`; `dataset mount != output bucket`; `HTTP 200 != storage persistence`; `token presente != permiso inference`; solo `VERIFIED_CLOSED` tras P03 E2E real.
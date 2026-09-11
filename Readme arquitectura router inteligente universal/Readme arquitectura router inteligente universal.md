# Router Inteligente Universal — Arquitectura y estado de integración

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## 1. Objetivo
Backend Python 95% determinista / 5% LLM. Flujo: `INPUT -> classifier -> DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> conector -> destino -> verify/state`.

## 2. Plan autorizado — solo 3 pasos
1. Hugging Face + modelos + FastAPI — ACTIVE.
2. Integración GitHub/C01-C23 — PENDING tras P01.
3. API keys agentes + E2E — PENDING.

## 3. Estado P01 — RIU-0046
- Catálogo público 20 certificado.
- HF-M01 compute/hot-path/dataset RO verificados; provider auth 403; NO READY.
- HF-M02 compute + integración FastAPI→Enchufe→Router→adapter verificados; storage RW create/write 403; NO READY.
- HF-M03 compute real + integración FastAPI→Enchufe→Router→adapter + dataset RO verificados; storage RW persistente PENDING; NO READY.
- HF-M04 `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF`: intento `6aa316585527934177ec29ee` cancelado por anomalía timeout-state sin salida final; retry `6aa34d825527934177ec3d2c` lanzado con timeout explícito 2h/7200s, runtime llama.cpp CUDA, `a10g-small`; estado inicial SCHEDULING; NO PASS.
- Cola P01 1×1: HF-M04 compute real.

## 4. Reglas
Gateway FastAPI único; adapters separados; sin monolito. P02 `REUSE > PATCH > ADAPT > GENERATE`. Descarga/copia/movimiento sólo motores canónicos autorizados.

## 5. Cierre
`compute != READY`; `dataset mount != output bucket`; `HTTP 200 != storage persistence`; `RUNNING/SCHEDULING != inferencia final`; solo `VERIFIED_CLOSED` tras P03 E2E real.
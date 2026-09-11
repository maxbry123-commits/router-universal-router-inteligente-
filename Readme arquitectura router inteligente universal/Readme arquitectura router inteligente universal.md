# Router Inteligente Universal — Arquitectura y estado de integración

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · FAST-CLOSE.

## 1. Objetivo
Backend Python 95% determinista / 5% LLM. Flujo: `INPUT -> classifier -> DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> conector -> destino -> verify/state`.

## 2. Plan autorizado — solo 3 pasos
1. Hugging Face + modelos + FastAPI — ACTIVE.
2. Integración GitHub/C01-C23 — PENDING tras P01.
3. API keys agentes + E2E — PENDING.

## 3. Estado P01 — RIU-0049
- Catálogo público 20 certificado.
- HF-M01/M02/M03: PASS internos ya evidenciados; auth/provider/RW storage externos quedan FLAGS/GAP explícitos.
- HF-M04 `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF`: dos Jobs cancelados por anomalía timeout-state; `FLAG-HF-M04-COMPUTE-001`; no repetir ventana larga.
- HF-M05 `Qwen/Qwen2.5-7B-Instruct`: compute PASS + integración FastAPI→Enchufe→RedUniversal→HF adapter PASS en Job `6aa3977e21047bf1b0374e94`; HTTP 200; dataset RO `/data` True/10 files; CUDA True; respuesta `RIU_HF_M05_ROUTE_OK`; evidence SHA256 `d3352d066152f07379352c94eaae94dd415be1adcda68b43791f8736c9653e79`; read-back True; `FASTAPI_ENCHUFE_ROUTER_M05_OK=True`. RW persistente externo no certificado y no se inventa.
- Cola P01: lote compatible M06/M07/M10/M11/M12 en una corrida HF Job con resultado individual; luego resto M08-M20 por compatibilidad/FLAG exacto.

## 4. Reglas
Gateway FastAPI único; adapters separados; sin monolito. P02 `REUSE > PATCH > ADAPT > GENERATE`. Descarga/copia/movimiento sólo motores canónicos autorizados. No reauditar donors cerrados.

## 5. Cierre
El core puede cerrar con PASS 100% de lo ejecutable + FLAGS externos demostrados; proveedor externo/auth/RW storage no puede retener artificialmente el proyecto en 98%. `VERIFIED_CLOSED` exige P03 E2E real.
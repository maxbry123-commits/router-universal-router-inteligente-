# Router Inteligente Universal — Arquitectura y estado de integración

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · FAST-CLOSE.

## 1. Objetivo
`INPUT -> classifier -> DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> conector -> destino -> verify/state`.

## 2. Plan autorizado — solo 3 pasos
1. Hugging Face + modelos + FastAPI — ACTIVE (99%).
2. Integración GitHub/C01-C23 — PENDING tras P01 ejecutable.
3. API keys agentes + E2E — PENDING.

## 3. Estado P01 — RIU-0052
- M01-M03: PASS internos previos; external auth/RW FLAGS/GAP.
- M04: FLAG, sin otra ventana larga.
- M05 integrado PASS; M06/M07/M10/M11/M12 batch integrado PASS.
- M08/M13/M14/M15/M16/M19: FLAGS exactos para flavor/formato/provider actual.
- M20 `Qwen/Qwen2.5-7B-Instruct-AWQ`: Job `6aa3a3cd5527934177ec4e7e` COMPLETED en a10g-small con vLLM; model_id exacto; response `OK`; SHA256 `5c45711905d5c34282a4711527ced24ede31e3390bf318285a01e8d78acf5302`; `HF_M20_OK=True`.
- M09 y M17/M18 siguen Jobs reales en curso.

## 4. Reglas
Gateway FastAPI único; adapters separados; sin monolito. P02 `REUSE > PATCH > ADAPT > GENERATE`; sólo bloqueantes del E2E.

## 5. Cierre
100% PASS de lo ejecutable + FLAGS externos demostrados; `VERIFIED_CLOSED` exige P03 E2E real.
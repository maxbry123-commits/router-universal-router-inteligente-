# Router Inteligente Universal — Arquitectura y estado de integración

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · FAST-CLOSE.

## 1. Objetivo
Backend Python 95% determinista / 5% LLM. Flujo: `INPUT -> classifier -> DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> conector -> destino -> verify/state`.

## 2. Plan autorizado — solo 3 pasos
1. Hugging Face + modelos + FastAPI — ACTIVE (99%).
2. Integración GitHub/C01-C23 — PENDING tras P01 ejecutable.
3. API keys agentes + E2E — PENDING.

## 3. Estado P01 — RIU-0050
- HF-M01/M02/M03: PASS internos previos; auth/provider/RW externos quedan FLAGS/GAP explícitos.
- HF-M04: `FLAG-HF-M04-COMPUTE-001` tras dos anomalías timeout-state; no repetir ventana larga.
- HF-M05: compute + integración FastAPI→Enchufe→RedUniversal→HF adapter PASS.
- HF-M06/M07/M10/M11/M12: batch Job `6aa398fe5527934177ec4cd0` COMPLETED en `a10g-small`; cada slot pasó verifier individual; dataset `HuggingFaceH4/ultrachat_200k` RO `/data` True/10 files; summary `/tmp/riu_hf_batch_m06_m12_summary.json`; SHA256 `c3b38014bdd5423cd85b42f14d54fc13c95247a0aa29e3729eb3ac84264dd6a5`; read-back True; `RIU_HF_BATCH_M06_M12_OK=True`.
- M06 individual SHA `e5820de1040e58a84591fd48a3f8a1fbf256090b03ba082a7f0f9e9b30a04d01`; M12 individual SHA `640448abf630b2c7df1e70fc8849d72dcb84096bf47d9c124dc746c51026b2ab`.
- Cola P01: M08/M09/M13-M20 por compatibilidad/tamaño/scope; ejecutar compatibles y FLAG exacto lo externo/no ejecutable.

## 4. Reglas
Gateway FastAPI único; adapters separados; sin monolito. P02 `REUSE > PATCH > ADAPT > GENERATE`. Descarga/copia/movimiento sólo motores canónicos autorizados. No reauditar donors cerrados.

## 5. Cierre
El core cierra con 100% PASS de lo ejecutable + FLAGS externos demostrados; proveedor externo/auth/RW storage no retiene artificialmente el proyecto en 98%. `VERIFIED_CLOSED` exige P03 E2E real.
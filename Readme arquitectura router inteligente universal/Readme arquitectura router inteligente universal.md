# Router Inteligente Universal — Arquitectura y estado de integración

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · FAST-CLOSE.

## 1. Objetivo
Backend Python 95% determinista / 5% LLM. Flujo: `INPUT -> classifier -> DAG fija -> validator/Enchufe Gate -> Router/RedUniversal -> conector -> destino -> verify/state`.

## 2. Plan autorizado — solo 3 pasos
1. Hugging Face + modelos + FastAPI — ACTIVE (99%).
2. Integración GitHub/C01-C23 — PENDING tras P01 ejecutable.
3. API keys agentes + E2E — PENDING.

## 3. Estado P01 — RIU-0051
- HF-M01/M02/M03: PASS internos previos; auth/provider/RW externos quedan FLAGS/GAP.
- HF-M04: `FLAG-HF-M04-COMPUTE-001`; no otra ventana larga.
- HF-M05 integrado PASS; HF-M06/M07/M10/M11/M12 batch integrado PASS.
- HF metadata revalidada para M08/M09/M13-M20. M08/M13/M14/M15/M16/M19 reciben FLAG específico para `a10g-small` + formato observado/provider autorizado; no se declara imposibilidad global.
- HF-M17/M18 GGUF: initial Job `6aa3a1875527934177ec4e06` exit127; probe `6aa3a24221047bf1b0374f88` encontró `/app/llama-cli`; StrategyDelta Job `6aa3a24f5527934177ec4e3c` está ejecutándose con Q4_K_M.
- HF-M09 MXFP4 y HF-M20 AWQ 4-bit: candidatos locales; vLLM smoke `6aa3a15c5527934177ec4e04` falló por executable path, no por modelo; probe `6aa3a2cb5527934177ec4e50` lanzado.

## 4. Reglas
Gateway FastAPI único; adapters separados; sin monolito. P02 `REUSE > PATCH > ADAPT > GENERATE`. Descarga/copia/movimiento sólo motores canónicos autorizados. No reauditar donors cerrados.

## 5. Cierre
El core cierra con 100% PASS de lo ejecutable + FLAGS externos demostrados; proveedor externo/auth/RW storage no retiene artificialmente el proyecto en 98%. `VERIFIED_CLOSED` exige P03 E2E real.
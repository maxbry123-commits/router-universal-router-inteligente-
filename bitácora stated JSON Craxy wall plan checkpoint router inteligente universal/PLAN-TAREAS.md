# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Core preservado
- P01 ✅ conjunto ejecutable HF cerrado.
- P02 ✅ hot-path C01/C20/C15/C17/C16 cerrado.
- P03 ✅ API Key Manager 100 slots + E2E cerrado.
- E2E base: Actions run `34582284615`, job `103208408709`, `2 passed in 6.79s`.

## Cola obligatoria
1. **MODEL CERTIFICATION 20/20 — ACTIVE**
   - PASS/ejecución previa válida: M01/M02/M03/M05/M06/M07/M10/M11/M12/M20.
   - FLAG/GAP contabilizados: M04/M08/M09/M13/M14/M15/M16/M17/M19.
   - M18 es el único slot aún pendiente de terminal individual.
2. **FINAL REGRESSION / E2E** sólo después de 20/20 accounted.
3. **ADN/X-RAY FINAL** después de la regresión.

## RIU-0061 — cola 1×1 actual
- Attempt M18 `6aa475605527934177eca1cb`: ERROR exit 1, NO PASS; log remoto `HF_M18_START` únicamente por redirección stderr.
- StrategyDelta diagnóstico `6aa475e721047bf1b0378e13`: `ornith-ai/Ornith-1.5-9B-GGUF`, llama.cpp CUDA, `a10g-small`, `Q3_K_S`, ctx=128, n=1, timeout=180s, sin redirección.
- Último estado observado: `SCHEDULING / Pulling container image`.
- Siguiente única acción: inspeccionar terminal/log; PASS sólo con inferencia real, si falla registrar FLAG/GAP exacto y pasar al gate 20/20.

## Estado actual
`ACTIVE_LOOP_MODEL_CERTIFICATION`; 19/20 accounted antes del terminal M18.

## Regla de cierre
`CORE_VERIFIED_CLOSED + MODEL_CERTIFICATION_20_OF_20_ACCOUNTED + FINAL_REGRESSION_E2E_PASS`.
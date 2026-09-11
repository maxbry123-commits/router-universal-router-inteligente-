# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Core preservado
- P01 ✅ conjunto ejecutable HF cerrado.
- P02 ✅ hot-path C01/C20/C15/C17/C16 cerrado.
- P03 ✅ API Key Manager 100 slots + E2E cerrado.
- E2E base: Actions run `34582284615`, job `103208408709`, `2 passed in 6.79s`.

## Nueva cola obligatoria del Director
1. **MODEL CERTIFICATION 20/20 — ACTIVE**
   - Testear cada modelo HF_M01..HF_M20.
   - Por slot registrar: model_id, metadata, método local/provider, CPU/GPU/flavor, Job/log, dataset/storage si aplica, adapter/FastAPI/Enchufe/Router boundary, output y PASS/FLAG/GAP.
   - Reutilizar evidencia previa válida de M01/M02/M03/M05/M06/M07/M10/M11/M12/M20; no gastar cómputo repitiendo sin motivo.
   - Resolver/testear individualmente slots con FLAG/GAP, especialmente M18 que no fue alcanzado en el job anterior.
   - M04/M17: timeout previo; usar StrategyDelta + timeout corto.
   - M09: compute completado pero response-contract `content=null`; mantener FLAG si no se corrige.
2. **FINAL REGRESSION / E2E**
   - Sólo cuando los 20 slots estén contabilizados como PASS o FLAG/GAP con evidencia.
   - Reejecutar hot-path y seguridad API keys; no aceptar presencia como PASS.
3. **ADN/X-RAY FINAL**
   - Sincronizar Arquitectura, Handoff, Crazy Wall, STATE, CHECKPOINT, PLAN, RECOVERY, índice HF, API keys y parche maestro.
   - Después habilitar siguiente tarea Ask Council/Mini Workflow.

## RIU-0061 — cola 1×1 actual
- M18 `ornith-ai/Ornith-1.5-9B-GGUF`: Job individual `6aa475605527934177eca1cb` creado con llama.cpp CUDA, `a10g-small`, `Q3_K_S`, ctx=512, n=4, timeout=480s.
- Estado observado: `SCHEDULING / Pulling container image`; no PASS todavía.
- Siguiente única acción: verificar estado terminal/log. PASS sólo con inferencia no vacía y `HF_M18_OK=True`; en caso contrario registrar FLAG/GAP exacto y continuar al gate 20/20.

## Estado actual
`ACTIVE_LOOP_MODEL_CERTIFICATION`.
El core sigue `VERIFIED_CLOSED`; la certificación está en 19/20 contabilizados antes del resultado terminal M18.

## Regla de cierre
`CORE_VERIFIED_CLOSED + MODEL_CERTIFICATION_20_OF_20_ACCOUNTED + FINAL_REGRESSION_E2E_PASS`.
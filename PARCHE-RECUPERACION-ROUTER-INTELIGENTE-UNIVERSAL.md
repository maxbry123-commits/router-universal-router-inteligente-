# PARCHE DE RECUPERACIÓN — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Estado del core
RIU-0058 permanece `VERIFIED_CLOSED`: P01/P02/P03 cerrados; API Key Manager 100 slots + E2E base verificados.
Evidencia base: GitHub Actions run `34582284615`, job `103208408709`, `2 passed in 6.79s`; commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`.

## Gate ampliado
Antes de nueva tarea: 20/20 modelos PASS o FLAG/GAP con evidencia + regresión/E2E global + ADN final sincronizado.

## Estado de slots
PASS/ejecución válida: M01, M02, M03, M05, M06, M07, M10, M11, M12, M20.
FLAGS/GAP contabilizados: M04, M08, M09, M13, M14, M15, M16, M17, M19.
M18 sigue único slot pendiente de resolución terminal individual.

## RIU-0061 — M18
Attempt 1 `6aa475605527934177eca1cb`: `ornith-ai/Ornith-1.5-9B-GGUF`, llama.cpp CUDA, `a10g-small`, `Q3_K_S`, timeout 480s; terminó `ERROR exit 1`, NO PASS; log remoto visible sólo `HF_M18_START` porque stderr estaba redirigido.
StrategyDelta diagnóstico `6aa475e721047bf1b0378e13`: mismo modelo/quant/flavor, ctx 128, n=1, timeout 180s, sin redirección para capturar causa exacta. Último estado observado: `SCHEDULING / Pulling container image`.

## Recuperación 1×1
`inspect M18 diagnostic -> persist PASS or exact FLAG/GAP -> MODEL_CERTIFICATION_20_OF_20_ACCOUNTED -> final E2E -> ADN sync -> next task`.

## Reglas
No secretos en repo. `CATALOG_OBSERVED != TESTED != READY`. Job creado o COMPLETED sin inferencia no equivale a PASS.

## Gate final
`CORE_VERIFIED_CLOSED + MODEL_CERTIFICATION_20_OF_20_ACCOUNTED + FINAL_REGRESSION_E2E_PASS`.
Estado operativo: `ACTIVE_LOOP_MODEL_CERTIFICATION`.
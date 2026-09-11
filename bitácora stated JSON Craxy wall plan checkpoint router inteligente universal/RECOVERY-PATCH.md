# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Estado recuperable actual
Core RIU-0058=`VERIFIED_CLOSED`; P01/P02/P03 cerrados; E2E base exitoso. No rehacer.

## Certificación ampliada
19/20 slots contabilizados antes del terminal M18. Evidencias previas M01/M02/M03/M05/M06/M07/M10/M11/M12/M20 se conservan; FLAGS/GAP M04/M08/M09/M13/M14/M15/M16/M17/M19 permanecen explícitos.

## RIU-0061 — punto exacto de recuperación
1. Attempt M18 `6aa475605527934177eca1cb`, modelo `ornith-ai/Ornith-1.5-9B-GGUF`, llama.cpp CUDA, `a10g-small`, Q3_K_S, 480s: `ERROR exit 1`, NO PASS. Log remoto visible sólo `HF_M18_START` porque stderr quedó redirigido y `set -e` cortó antes del tail.
2. Diagnostic StrategyDelta `6aa475e721047bf1b0378e13`: mismo modelo/quant/flavor, ctx 128, n=1, timeout 180s, salida directa; último estado `SCHEDULING / Pulling container image`.
3. Próxima acción única: inspeccionar terminal/log del diagnóstico. PASS sólo con inferencia real; error/timeout => FLAG/GAP exacto.
4. Después: `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED` -> regresión/E2E global -> ADN final.

## Evidencia core
Actions run `34582284615`, job `103208408709`, `2 passed in 6.79s`; commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`; gateway blob `e970b5de2281d236b916ea41492ee52df8454153`; E2E blob `23473c2a33cb9e5a451ad5a19ce5c4e5a58fc2c7`.

## Gate final
`CORE_VERIFIED_CLOSED + MODEL_CERTIFICATION_20_OF_20_ACCOUNTED + FINAL_REGRESSION_E2E_PASS`.
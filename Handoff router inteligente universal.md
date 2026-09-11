# Handoff Router Inteligente Universal — ADN operativo

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · repo `maxbry123-commits/router-universal-router-inteligente-` · branch `main`.

## Estado actual
- Core RIU-0058: `VERIFIED_CLOSED` / 100% del conjunto ejecutable.
- Certificación ampliada: `ACTIVE_LOOP_MODEL_CERTIFICATION`.
- 19/20 slots están contabilizados antes del resultado terminal de M18; luego corresponde regresión/E2E global.

## Core cerrado y no repetir
P01/P02/P03 cerrados. Actions run `34582284615`, job `103208408709`, `2 passed in 6.79s`; commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`; gateway blob `e970b5de2281d236b916ea41492ee52df8454153`; E2E blob `23473c2a33cb9e5a451ad5a19ce5c4e5a58fc2c7`.

## Estado de modelos
PASS/ejecución previa válida: `M01 M02 M03 M05 M06 M07 M10 M11 M12 M20`.
FLAG/GAP preservado: `M04 M08 M09 M13 M14 M15 M16 M17 M19`.
M18 sigue único slot pendiente de resolución individual terminal.

## RIU-0061 — M18
Intento 1: Job `6aa475605527934177eca1cb`, `ornith-ai/Ornith-1.5-9B-GGUF`, llama.cpp CUDA, `a10g-small`, `Q3_K_S`, timeout 480s. Terminó `ERROR exit 1` en ~69s; log remoto visible sólo `HF_M18_START` porque stderr estaba redirigido y `set -e` salió antes del tail. NO PASS.
StrategyDelta diagnóstico: Job `6aa475e721047bf1b0378e13`, mismo modelo/quant/flavor, timeout 180s, ctx 128, 1 token, sin redirección para exponer causa exacta. Último estado observado: `SCHEDULING / Pulling container image`.

## Cola 1×1 actual
`inspect M18 diagnostic terminal -> persist PASS/FLAG -> MODEL_CERTIFICATION_20_OF_20_ACCOUNTED -> final regression/E2E -> ADN final -> next task`.

## Criterio final
`CORE_VERIFIED_CLOSED + MODEL_CERTIFICATION_20_OF_20_ACCOUNTED + FINAL_REGRESSION_E2E_PASS`. No READY por catálogo ni por creación de Job.
# Handoff Router Inteligente Universal — ADN operativo

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · repo `maxbry123-commits/router-universal-router-inteligente-` · branch `main`.

## Estado actual
- Core RIU-0058: `VERIFIED_CLOSED` / 100% del conjunto ejecutable.
- Nueva orden explícita: antes de pasar a la siguiente tarea, testear **cada modelo HF_M01..HF_M20** y luego ejecutar regresión/E2E global.
- Estado operativo actual: `ACTIVE_LOOP_MODEL_CERTIFICATION`.

## Core cerrado y no repetir
- P01 conjunto ejecutable HF: cerrado con PASS + FLAGS exactos.
- P02 hot-path C01/C20/C15/C17/C16: cerrado.
- P03 API Key Manager + E2E: cerrado.
- Evidencia: Actions run `34582284615`, job `103208408709`, `2 passed in 6.79s`.
- Commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`; gateway blob `e970b5de2281d236b916ea41492ee52df8454153`; E2E blob `23473c2a33cb9e5a451ad5a19ce5c4e5a58fc2c7`.

## Estado de modelos
PASS/ejecución previa válida: `M01 M02 M03 M05 M06 M07 M10 M11 M12 M20`.
FLAG/GAP previo: `M04 M08 M09 M13 M14 M15 M16 M17 M18 M19`.
M18 requiere test individual porque el job secuencial anterior no llegó a ejecutarlo.

## Evidencia HF clave
- catálogo 20: `6aa2513d5527934177ebfaad`.
- M03 GPU/hot-path: `6aa2f8e921047bf1b03732b7`.
- M05 compute: `6aa3781121047bf1b0374a5c`; integración `6aa3977e21047bf1b0374e94`.
- M20: `6aa3a3cd5527934177ec4e7e` PASS.
- M09: `6aa3a3dd5527934177ec4e80` compute completado, `content=null` -> FLAG.
- M17/M18: `6aa3a24f5527934177ec4e3c` cancelado por timeout; M18 no alcanzado.
- batch reciente `6aa3943f21047bf1b0374dc8`: GAP de entorno `transformers` ausente; no promover a PASS.

## Cola 1×1 actual
1. Certificar individualmente slots sin prueba concluyente, empezando por M18 y FLAGS runtime/hardware/provider.
2. Mantener PASS previos sólo si read-back/evidencia sigue consistente; no repetir cómputo caro sin necesidad.
3. Cuando los 20 estén `PASS` o `FLAG/GAP` explícito con evidencia, ejecutar regresión/E2E global.
4. Actualizar todos los documentos fuente de verdad tras cada delta material.

## Criterio final
`MODEL_CERTIFICATION_20_OF_20_ACCOUNTED` exige por slot: model_id + método de ejecución + Job/log + flavor/hardware + adapter/hot-path si aplica + resultado + PASS/FLAG/GAP.
Después: `FINAL_REGRESSION_E2E_PASS`.

No iniciar la tarea Ask Council/Mini Workflow hasta este gate.
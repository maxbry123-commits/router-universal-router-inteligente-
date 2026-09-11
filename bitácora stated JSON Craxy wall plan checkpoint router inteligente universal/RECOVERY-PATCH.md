# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Estado recuperable actual
El core RIU-0058 permanece `VERIFIED_CLOSED` con P01/P02/P03 cerrados y E2E base exitoso. No rehacer ese trabajo.

## Cambio de requisitos posterior
El Director añadió un gate obligatorio: probar individualmente los 20 modelos de Hugging Face antes de continuar con la siguiente tarea. Por tanto el estado operativo es `ACTIVE_LOOP_MODEL_CERTIFICATION`, sin invalidar el cierre del core.

## Punto exacto de recuperación
1. Releer `STATE.json`, `CHECKPOINT.json`, `PLAN-TAREAS.md`, Arquitectura, Handoff, Crazy Wall e índice HF.
2. Conservar evidencias previas válidas M01/M02/M03/M05/M06/M07/M10/M11/M12/M20.
3. Trabajar 1×1 los slots FLAG/GAP M04/M08/M09/M13/M14/M15/M16/M17/M18/M19; M18 requiere ejecución individual porque no fue alcanzado previamente.
4. Job `6aa3943f21047bf1b0374dc8` mostró `ModuleNotFoundError: transformers`; clasificar como GAP del entorno del intento, no como fallo del modelo ni PASS.
5. Cuando los 20 slots tengan PASS o FLAG/GAP explícito con evidencia, ejecutar regresión/E2E global.
6. Actualizar todos los documentos ADN/X-Ray y sólo entonces habilitar la siguiente tarea.

## Evidencia core a preservar
Actions run `34582284615`, job `103208408709`, `2 passed in 6.79s`; commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`; gateway blob `e970b5de2281d236b916ea41492ee52df8454153`; E2E blob `23473c2a33cb9e5a451ad5a19ce5c4e5a58fc2c7`.

## Gate final
`CORE_VERIFIED_CLOSED + MODEL_CERTIFICATION_20_OF_20_ACCOUNTED + FINAL_REGRESSION_E2E_PASS`.
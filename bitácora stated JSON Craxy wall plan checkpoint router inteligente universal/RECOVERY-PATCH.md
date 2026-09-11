# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Estado recuperable actual
El core RIU-0058 permanece `VERIFIED_CLOSED` con P01/P02/P03 cerrados y E2E base exitoso. No rehacer ese trabajo.

## Cambio de requisitos posterior
El Director añadió un gate obligatorio: probar individualmente los 20 modelos de Hugging Face antes de continuar con la siguiente tarea. Por tanto el estado operativo es `ACTIVE_LOOP_MODEL_CERTIFICATION`, sin invalidar el cierre del core.

## Punto exacto de recuperación
1. Conservar evidencias previas válidas M01/M02/M03/M05/M06/M07/M10/M11/M12/M20.
2. M04/M08/M09/M13/M14/M15/M16/M17/M19 ya conservan FLAG/GAP explícito con causa/evidencia; no convertirlos en PASS.
3. M18 se lanzó individualmente en RIU-0061: Job `6aa475605527934177eca1cb`, modelo `ornith-ai/Ornith-1.5-9B-GGUF`, llama.cpp CUDA, `a10g-small`, quant `Q3_K_S`, timeout 480s. Último estado observado: `SCHEDULING / Pulling container image`.
4. Siguiente acción única: inspeccionar estado/log terminal M18. Sólo PASS con output no vacío y `HF_M18_OK=True`; fallo/timeout => FLAG/GAP exacto y slot contabilizado sin falso PASS.
5. Cuando M18 termine, declarar `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED` sólo si los 20 slots tienen PASS o FLAG/GAP explícito.
6. Ejecutar regresión/E2E global, sincronizar documentos ADN/X-Ray y sólo entonces habilitar la siguiente tarea.

## Evidencia core a preservar
Actions run `34582284615`, job `103208408709`, `2 passed in 6.79s`; commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`; gateway blob `e970b5de2281d236b916ea41492ee52df8454153`; E2E blob `23473c2a33cb9e5a451ad5a19ce5c4e5a58fc2c7`.

## GAP de entorno preservado
Job `6aa3943f21047bf1b0374dc8`: `ModuleNotFoundError: transformers`; no PASS y no invalida evidencias anteriores.

## Gate final
`CORE_VERIFIED_CLOSED + MODEL_CERTIFICATION_20_OF_20_ACCOUNTED + FINAL_REGRESSION_E2E_PASS`.
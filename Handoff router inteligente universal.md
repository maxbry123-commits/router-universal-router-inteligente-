# Handoff Router Inteligente Universal — ADN operativo

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · repo `maxbry123-commits/router-universal-router-inteligente-` · branch `main`.

## Estado actual
- Core RIU-0058: `VERIFIED_CLOSED` / 100% del conjunto ejecutable.
- Certificación ampliada: `ACTIVE_LOOP_MODEL_CERTIFICATION`.
- Antes de nueva tarea deben quedar los 20 slots HF como PASS o FLAG/GAP explícito y luego ejecutar regresión/E2E global.

## Core cerrado y no repetir
- P01 conjunto ejecutable HF cerrado; P02 hot-path cerrado; P03 API Key Manager + E2E cerrado.
- Evidencia: Actions run `34582284615`, job `103208408709`, `2 passed in 6.79s`.
- Commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`; gateway blob `e970b5de2281d236b916ea41492ee52df8454153`; E2E blob `23473c2a33cb9e5a451ad5a19ce5c4e5a58fc2c7`.

## Estado de modelos
PASS/ejecución previa válida: `M01 M02 M03 M05 M06 M07 M10 M11 M12 M20`.
FLAG/GAP contabilizable preservado: `M04 M08 M09 M13 M14 M15 M16 M17 M19`.
M18 era el único slot sin ejecución individual concluyente.

## RIU-0061 — M18 individual
Job `6aa475605527934177eca1cb` creado para `ornith-ai/Ornith-1.5-9B-GGUF` con llama.cpp CUDA, flavor `a10g-small`, quant `Q3_K_S`, ctx 512, 4 tokens y timeout 480 s. Estado observado: `SCHEDULING / Pulling container image`.
No se marca READY ni PASS todavía. PASS exige inferencia no vacía y `HF_M18_OK=True`; cualquier fallo/timeout se registra como FLAG/GAP exacto y se continúa.

## Evidencia HF clave
Catálogo 20 `6aa2513d5527934177ebfaad`; M03 `6aa2f8e921047bf1b03732b7`; M05 compute `6aa3781121047bf1b0374a5c`; M05 integración `6aa3977e21047bf1b0374e94`; M20 `6aa3a3cd5527934177ec4e7e`; M09 `6aa3a3dd5527934177ec4e80`; M17/M18 previo `6aa3a24f5527934177ec4e3c`; M18 individual `6aa475605527934177eca1cb`.

## Cola 1×1 actual
`inspect M18 terminal -> persist PASS/FLAG -> MODEL_CERTIFICATION_20_OF_20_ACCOUNTED -> final regression/E2E -> ADN final -> next task`.

## Criterio final
`CORE_VERIFIED_CLOSED + MODEL_CERTIFICATION_20_OF_20_ACCOUNTED + FINAL_REGRESSION_E2E_PASS`.
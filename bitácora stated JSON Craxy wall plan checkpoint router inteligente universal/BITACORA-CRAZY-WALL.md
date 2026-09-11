# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3` · **Modo:** `FAIL_CLOSED_LOOP`.

## RIU-0001..0058 — CORE
Core ejecutable cerrado y preservado: P01=`CLOSED_EXECUTABLE_SET`; P02=`CLOSED_HOT_PATH_EXECUTABLE_SET`; P03=`VERIFIED_CLOSED`. GitHub Actions run `34582284615`, job `103208408709`: success, `2 passed in 6.79s`. Commit hot-path `af469152fd0306d706c67b8cf6548512fdc4f1c0`.

## RIU-0059 — GATE MODELOS
El Director exige certificación individual HF_M01..HF_M20 antes de nueva tarea. Core no se reabre; estado=`ACTIVE_LOOP_MODEL_CERTIFICATION`.

## Estado antes de M18
PASS/ejecución previa válida: M01, M02, M03, M05, M06, M07, M10, M11, M12, M20.
FLAG/GAP contabilizados: M04, M08, M09, M13, M14, M15, M16, M17, M19.
M18 era el único slot sin ejecución individual concluyente.

## RIU-0060 — GAP entorno
Job `6aa3943f21047bf1b0374dc8`: `ModuleNotFoundError: transformers`; no PASS y no invalida evidencias previas.

## RIU-0061 — M18 individual
Metadata fresca confirma `ornith-ai/Ornith-1.5-9B-GGUF`, GGUF 9B, llama.cpp compatible.
Attempt 1 `6aa475605527934177eca1cb`: `a10g-small`, llama.cpp CUDA, `Q3_K_S`, ctx 512, n=4, timeout 480s. Terminó `ERROR exit 1` en ~69s; log remoto visible sólo `HF_M18_START` porque stderr estaba redirigido y `set -e` cortó antes del tail. Resultado=`NOT_PASS`.
StrategyDelta diagnóstico `6aa475e721047bf1b0378e13`: mismo modelo/quant/flavor, ctx 128, n=1, timeout 180s, sin redirección para capturar causa exacta. Último estado observado: `SCHEDULING / Pulling container image`.

## Cola actual
`inspect M18 diagnostic terminal -> persist PASS/FLAG -> 20/20 accounted -> final regression/E2E -> ADN final -> next task`.

## Reglas
`CATALOG_OBSERVED != TESTED != READY`; presencia no es integración; COMPLETED no es inferencia; timeout no es PASS; FLAG externo no se maquilla como cierre; no secretos en repo.

Estado: `ACTIVE_LOOP_MODEL_CERTIFICATION`.
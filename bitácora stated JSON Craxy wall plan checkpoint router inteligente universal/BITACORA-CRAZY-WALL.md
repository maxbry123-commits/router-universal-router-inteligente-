# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0031 — TRAZABILIDAD PREVIA
Baseline, componentes, Handoff, plan 3 pasos, HF, Gate/conectores v6/registry/validator/schema/RedUniversal, auditorías y HF Jobs compute real preservados por commits/STATE/CHECKPOINT previos.

## RIU-0032 — SINCRONIZACIÓN DIRECTOR / 3 PASOS

### Hecho
- Componentes open source centralizados bajo `router inteligente universal/Componente open soure router inteligente universal/`.
- Raíz de código fuente real ya existe con `domain/`, `enchufe/`, `engine/`, `integration/`, `red/`, `tests/`.
- C05/C15/C16/C17 tienen trabajo materializado; C16 sigue parcial.
- Bridge HF y manifest existen en `huggueface/`.
- HF Jobs se usa como cómputo real del proyecto.
- `ConectorMemoria` fue cableado y validado previamente mediante HF Job (`3 passed`).
- Sistema canónico de descarga/extracción/copia/movimiento fijado a `frontend@ef0669bbc753861bfc33b86548f3f90c0f3d8df9` y motores inmutables.

### GAP actual
`GAP-HF-CATALOG-001`: la enumeración pública confirmó 0 modelos públicos de `COMAND-CENTER-1`, pero no certifica privados; el Job previo no recibió `HF_TOKEN` automáticamente. No se inventan 20 modelos ni adapters.

### Lista única de tareas — 3 pasos
1. **P01 ACTIVE** — cerrar inventario real de hasta 20 modelos HF; registrar model_id/especialidad/compute/dataset-storage/adapter y gateway FastAPI único.
2. **P02 PENDING** — cerrar integración GitHub C01-C23: reuse/patch/adapt/generate, poda y cableado por Enchufe Universal.
3. **P03 PENDING** — API Key Manager de agentes + generación one-time de keys + prueba E2E real HF/GitHub/API/agentes.

### Cableado objetivo
`AGENTE -> API KEY -> FastAPI -> Enchufe Universal -> Router/RedUniversal -> adapter -> HF Job/modelo/API/GitHub -> verifier -> respuesta`

### Verificación obligatoria
Nada pasa a PASS sin `ruta + SHA/diff + read-back + test/log + URL`.

## RIU-0033 — HF COMPUTE RECONFIRMATION / CATALOG RETRY
- Attempt catálogo: Job `6aa24e7921047bf1b0371acc`, `cpu-upgrade`, terminó ERROR antes de producir inventario utilizable; no se promovió ningún `model_id`.
- StrategyDelta: aislar compute del catálogo. Job `6aa24ea35527934177ebfa5c`, `cpu-upgrade`, `python:3.12-slim` → COMPLETED con salida `HF_JOB_COMPUTE_OK`.
- Evidencia: https://huggingface.co/jobs/COMAND-CENTER-1/6aa24ea35527934177ebfa5c
- Decisión: compute real HF reconfirmado; `GAP-HF-CATALOG-001` sigue OPEN. P02 solo puede avanzar por tareas independientes seguras. P03 API keys sigue PENDING hasta gateway/auth verificable.
- Refutaciones: compute success ≠ catálogo; fallo de catálogo ≠ permiso para inventar modelos; API key sin hot path verificado ≠ integración.
- `verify_final=PASS_COMPUTE_ONLY_CATALOG_INCONCLUSIVE`.

## NEXT
Cerrar P01 sin sobreingeniería; resolver token/catalog boundary por StrategyDelta y registrar solo modelos realmente observados. Después P02 y P03 en ese orden.

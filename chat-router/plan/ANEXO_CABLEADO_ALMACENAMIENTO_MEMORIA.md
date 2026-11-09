# ANEXO DE CABLEADO — Almacenamiento y Memoria (frente Claude Code 5)

Estado: RECEPCIÓN. Se anota el input block 1 a 1, sin análisis ni decisiones todavía.
Fuente de verdad: input block verbatim del owner para este frente.
Pizarra: `Claude notas.md` (sección "Frente 5 — Almacenamiento y memoria").
Handoff de investigación previa: `chat-router/plan/HANDOFF_INVESTIGACION_MEMORIA_4_PASADAS.md`.
Plan de Claude Code 5: pendiente (Salida parte 2 del owner).

## Regla de anotación

- Cada punto del input block se copia literal, con su número, en la sección correspondiente.
- No se resume ni se interpreta en la fase de recepción.
- Los puntos quedan con estado `RECIBIDO` hasta que se analicen.

## Input block 1 a 1

_(vacío: se llena cuando llegue el material del owner)_

## Preguntas del sistema de recuperación (Salida parte 1)

_(pendiente)_

## Preguntas para el plan de Claude Code 5 (Salida parte 2)

_(pendiente)_

## Recepción 1 a 1 — Salidas del análisis de almacenamiento y memoria (2026-11-09)

Estado: RECIBIDO. Sin ejecución. Sin preguntas en modo recepción.

| # | Punto recibido (literal, resumido por encabezado) | Estado | Flags |
|---|---|---|---|
| R-01 | Pasada 1: estado verificado del sistema de recuperación (checkpoint.py, runtime.py, LEDGER.jsonl, STATE.json, splitter.py, models.py). | RECIBIDO | 🚩 Afirma "✅ Implementado" para archivos que no están en la rama de trabajo. Verificar. |
| R-02 | Pasada 1: estado del sistema de memoria (memoria actual, tools, memoria_yaiwes, Graphiti, Memanto, Graphify, Qdrant, sqlite_memory.py, search, registro, tests J09–J11). | RECIBIDO | 🚩 Coincide con el handoff de investigación previo. Sin cambios. |
| R-03 | Pasada 2: gaps G1–G8 (puente checkpoint↔memoria, memoria_yaiwes no cableado, Qdrant con ruta obsoleta, endpoints faltantes, search como slicing, código muerto, sin checkpoint de memoria, sin handoff entre sesiones). | RECIBIDO | 🚩 Válidos según la investigación previa. |
| R-04 | Pasada 3: componentes open source propuestos (trace-checkpoint, bernstein, agentmemdb, Memory OS, Qdrant hybrid, Graphiti, Memanto, Graphify, dsh-rag, dsh-memory). | RECIBIDO | 🚩 No verificados. Algunas URLs no tienen identificador exacto (p. ej., "zenodo.org" sin ID). Verificar cada una antes de usarla. |
| R-05 | Pasada 4: arquitectura de un solo ledger con eventos memory_write pending/confirmed y reintento en resume. | RECIBIDO | 🚩 Propuesta. Depende de `router_engine/`, que tiene flags F-RE-1 a F-RE-11. |
| R-06 | Pasada 5: OCR PaddleOCR-VL-1.5 local como primario y Baidu AIP como fallback; motores deterministas (ancla, watchdog, checkpoint, índice). | RECIBIDO | 🚩 Los 🚩 son de verificación: la API de PaddleOCR y el valor de 94.5% no están verificados aquí. |
| R-07 | Salida 2: DAG memory_repair.dag.yaml con 9 nodos (N1–N9), preguntas previas Q1–Q4 y validación final. | RECIBIDO | 🚩 Q1–Q4 usan comandos `grep` que no se han ejecutado. |
| R-08 | Salida 3: código de ancla (anchor.py), watchdog, checkpoint de memoria, OCR, handoff y validador. | RECIBIDO | 🚩 Bugs detectados (ver R-09). |
| R-09 | Bugs del código recibido. | RECIBIDO | 🚩 B1: `handoff.py` llama `sqlite_memory.query`, `last_checkpoint` y `save`; el `sqlite_memory.py` de nuestra rama solo tiene `set` y `get`. B2: `anchor.py` verifica números sueltos; casi cualquier respuesta dará MISMATCH. B3: `ocr.py` lee credenciales de variables `*_REF` como si fueran valores; contradice "credential_ref". B4: `handoff.py` importa desde `memoria_yaiwes` y el DAG lo sitúa en `src/memoria_yaiwes`; las rutas no coinciden. B5: `watchdog.py` depende de `router_engine/`. |
| R-10 | Flags de validación (FLAG_SQLITE_OK … FLAG_HANDOFF_OK) y VALIDATION_REPORT.json. | RECIBIDO | 🚩 Los flags son verificables con `scripts/validate_memory.py`. Hasta que se ejecute, no hay PASS. |
| R-11 | Marcas de cita del texto recibido (formato `【2†L1-L3】`). | RECIBIDO | 🚩 Son marcas de cita sin fuente verificable. No se usan como evidencia. |

Resumen de flags abiertos del lote: 🚩 R-01…R-11, con bugs B1–B5 y componentes no verificados.

# CHAT-B07.md — TASK-07: Worker Pool (Selector + Cola/Balanceo + Health)
ROLE: CHAT B — Desarrollador Backend. Sin autoridad de arquitectura. Ambigüedad no cubierta = BLOCKER.

## 1. CONTEXTO HEREDADO
Depende de **TASK-03 y TASK-06 COMPLETED**. DAG_NODES: N14.
Cierra R2 (Selector), R3 (Cola/Balanceo), R4 (Health) de `GAP_01_ROUTER.md` — hoy son EXISTING_PARTIAL solo como descripción, se generan completos aquí.

## 2. OBJETIVO
Seleccionar el candidato (modelo/conector) adecuado por capacidad, agrupar tareas en lotes, y descartar nodos no sanos, integrando `resilience.py` (TASK-06) y `red_universal.py` (TASK-03).

## 3. ROOT_IDs

| ROOT_ID | Archivo | Acción | LOC est. |
|---|---|---|---|
| R-030 | `engine/worker_pool.py` | NEW | ~350 |
| R-031 | `domain/dsl/capability.json` | NEW | ~50 |

## 4. CONTRATOS
- `capability.json`: reglas de selección editables (NO hardcodear en Python) — mapa `categoria_tarea → [candidatos ordenados por capacidad]`.
- `worker_pool.py`:
  - Selector: elige el candidato de mayor score para la categoría de tarea.
  - Cola/Balanceo: agrupa en lotes con `batch_size=20`, `overlap=5` (constantes nombradas, no mágicas).
  - Health: sondeo periódico (usa `sondear()` del Protocol Conector) cada 30s, descarta nodos caídos de la selección.
  - Si no hay candidatos sanos → propaga error (no debe fallar silenciosamente).

## 5. CALIDAD
Igual que TASK-01 sección 7.

## 6. TESTS OBLIGATORIOS
- `test_selector_elige_mayor_score_por_categoria`
- `test_batching_batch_size_20_overlap_5`
- `test_health_descarta_nodo_caido`
- `test_sin_candidatos_sanos_propaga_error`

## 7. ACEPTACIÓN
Archivo `worker_pool.py` ≤500 LOC (si excede, dividir en submódulos manteniendo el mismo ROOT_ID lógico y reportarlo en el EvidencePacket). `capability.json` editable sin tocar código Python.

## 8. EVIDENCEPACKET
```yaml
evidence_packet:
  task_id: TASK-07
  chat_b_id: CHAT-B07
  root_ids: [R-030, R-031]
  status: COMPLETED | BLOCKED
```

## 9. BLOCKER
Si `resilience.py` (TASK-06) o `red_universal.py` (TASK-03) no están disponibles, DETENTE.

## 10. TRAZABILIDAD
DAG_NODES: N14 → TASK-07 → CHAT-B07 → R-030, R-031

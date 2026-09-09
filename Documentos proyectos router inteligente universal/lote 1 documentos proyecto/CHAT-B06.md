# CHAT-B06.md — TASK-06: Resilience + Semantic Cache + Cost Optimizer
ROLE: CHAT B — Desarrollador Backend. Sin autoridad de arquitectura. Ambigüedad no cubierta = BLOCKER.

## 1. CONTEXTO HEREDADO
Depende de **TASK-01, TASK-02, TASK-03 COMPLETED**. DAG_NODES: N13, N15, N16.
Cierra 3 de los 7 gaps de `GAP_01_ROUTER.md`: R5 (Retry), R6 (Circuit Breaker), R8 (Semantic Cache) + Cost Optimizer.

## 2. OBJETIVO
Resiliencia real ante fallos de proveedor (no solo diseño en papel — GAP_01 señala que el Circuit Breaker documentado en v6 nunca se implementó), cache semántico, y reordenamiento por costo.

## 3. ROOT_IDs

| ROOT_ID | Archivo | Acción | LOC est. |
|---|---|---|---|
| R-023 | `engine/cost_optimizer.py` | NEW | ~120 |
| R-032 | `engine/resilience.py` | NEW | ~200 |
| R-033 | `engine/semantic_cache.py` | NEW | ~150 |

## 4. CONTRATOS
- `resilience.py`: `CircuitBreaker` con estados `CLOSED → OPEN → HALF_OPEN`, ventana temporal real (no solo contador — usar timestamps), umbral configurable (default: 5 fallos en 60s → OPEN, 30s → HALF_OPEN). `Retry` con backoff exponencial configurable por nodo.
- `semantic_cache.py`: embeddings de la petición → similitud > umbral configurable → devuelve cacheado; miss no es error, continúa flujo normal. Usa Redis (R-015, TASK-02) para el store vectorial.
- `cost_optimizer.py`: recibe lista de candidatos con score, reordena por costo SOLO en empate de score; lee `presupuesto` del schema Enchufe v2.0 (R-011).

## 5. CALIDAD
Igual que TASK-01 sección 7.

## 6. TESTS OBLIGATORIOS
- `test_circuit_breaker_closed_a_open_por_umbral`
- `test_circuit_breaker_open_a_half_open_tras_ventana`
- `test_retry_backoff_exponencial`
- `test_semantic_cache_hit_y_miss`
- `test_cost_optimizer_prioriza_barato_en_empate`

## 7. ACEPTACIÓN
3 archivos ≤500 LOC c/u. Circuit Breaker verificado con test de tiempo real o mock de reloj (no solo contador de llamadas).

## 8. EVIDENCEPACKET
```yaml
evidence_packet:
  task_id: TASK-06
  chat_b_id: CHAT-B06
  root_ids: [R-023, R-032, R-033]
  status: COMPLETED | BLOCKED
```

## 9. BLOCKER
Si TASK-03 no está COMPLETED (red_universal sin conectores nuevos registrados), resilience.py no tiene contra qué envolver las llamadas — DETENTE.

## 10. TRAZABILIDAD
DAG_NODES: N13, N15, N16 → TASK-06 → CHAT-B06 → R-023, R-032, R-033

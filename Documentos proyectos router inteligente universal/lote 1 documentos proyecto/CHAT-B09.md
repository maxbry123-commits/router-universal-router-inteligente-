# CHAT-B09.md — TASK-09: DAG Orchestrator + Windows Chain
ROLE: CHAT B — Desarrollador Backend. Sin autoridad de arquitectura. Ambigüedad no cubierta = BLOCKER.

## 1. CONTEXTO HEREDADO
Depende de **TASK-04, TASK-06, TASK-07, TASK-08 COMPLETED** (la task de mayor complejidad de integración del proyecto). DAG_NODES: N19, N20.

## 2. OBJETIVO
`DAGOrchestrator`: ejecuta un `GraphExecutionPlan` (de TASK-04) recorriendo el grafo topológicamente, con checkpoints por nodo. `WindowsChain`: generalización Python del prototipo `_ventanas_del_tren.html` — 1 a 100 "ventanas" con código propio (entrada/salida), ejecutadas en el Sandbox (TASK-08), encadenables, con pausa/breakpoint/intervención manual, exportables a DAG.

## 3. ROOT_IDs

| ROOT_ID | Archivo | Acción | LOC est. |
|---|---|---|---|
| R-040 | `engine/dag_orchestrator.py` | NEW | ~300 |
| R-041 | `engine/windows_chain.py` | NEW | ~300 |

## 4. CONTRATOS

### `dag_orchestrator.py`
```python
class DAGOrchestrator:
    async def execute_graph(self, plan: GraphExecutionPlan) -> RunResult: ...
```
- Nodos independientes se ejecutan en paralelo vía `asyncio.gather`.
- Checkpoint por nodo COMPLETED — si el run se interrumpe, debe poder reanudar SIN repetir nodos ya DONE.
- Nodo fallido: consulta política — reintenta vía `resilience.py` (TASK-06) o propaga `FAILED` según corresponda.
- Cada nodo ejecutado registra evidencia en `core.ledger` (TASK-05).

### `windows_chain.py`
- Estructura: `Ventana` (id, código fuente, entrada, salida, estado) + `Cadena` (lista ordenada de Ventanas).
- Ejecución de cada Ventana delega en `CodeSandbox` (TASK-08) — el código de la ventana SIEMPRE corre en sandbox, nunca en el proceso del router directamente.
- Debe soportar: pausa entre ventanas, breakpoint manual, intervención (usuario edita el payload de salida de una ventana antes de que continúe la cadena), y exportar la cadena completa como nodos de un `GraphExecutionPlan` (interoperar con `dag_parser.py` de TASK-04).
- Rango soportado: 1 a 100 ventanas por cadena.
- Referencia de comportamiento esperado: el prototipo JS `_ventanas_del_tren.html` ya provisto — la semántica de "estación"/pausa/breakpoint/export debe ser equivalente en esta versión Python real.

## 5. CALIDAD Y SEGURIDAD
Igual que TASK-01 sección 7. Recordatorio: toda ejecución de código de usuario pasa por Sandbox (TASK-08) — `windows_chain.py` nunca usa `eval`/`exec` directo.

## 6. TESTS OBLIGATORIOS
- `test_orchestrator_ejecuta_nodos_paralelos`
- `test_orchestrator_checkpoint_reanuda_sin_repetir`
- `test_orchestrator_nodo_fallido_activa_retry`
- `test_windows_chain_1_a_100_ventanas`
- `test_windows_chain_pausa_y_breakpoint`
- `test_windows_chain_intervencion_manual_edita_payload`
- `test_windows_chain_export_a_dag_parser`

## 7. ACEPTACIÓN
2 archivos ≤500 LOC c/u (si `windows_chain.py` excede 500 LOC por la complejidad de estados, dividir en submódulo `windows_chain_state.py` manteniendo el mismo ROOT_ID lógico, reportarlo en EvidencePacket). Todos los tests en verde, incluyendo el de export a DAG.

## 8. EVIDENCEPACKET
```yaml
evidence_packet:
  task_id: TASK-09
  chat_b_id: CHAT-B09
  root_ids: [R-040, R-041]
  paridad_con_prototipo_html: true/false
  status: COMPLETED | BLOCKED
```

## 9. BLOCKER
Si alguna de las 4 dependencias no está COMPLETED, o si la semántica exacta de "intervención manual" en el prototipo no es clara, DETENTE — es el componente de mayor riesgo del proyecto, no lo improvises.

## 10. TRAZABILIDAD
DAG_NODES: N19, N20 → TASK-09 → CHAT-B09 → R-040, R-041

# CHAT-B04.md — TASK-04: DSL (Templates T01-T12 + DAGParser)
ROLE: CHAT B — Desarrollador Backend. Sin autoridad de arquitectura. Ambigüedad no cubierta = BLOCKER.

## 1. CONTEXTO HEREDADO
Depende de **TASK-01 COMPLETED** (usa `domain/schemas/enchufe_v2.py`). DAG_NODES: N07, N10.

## 2. OBJETIVO
Catálogo FIJO de 12 plantillas DAG (el router nunca improvisa arquitectura en runtime) + el parser que las convierte en un plan de ejecución validado, con detección de ciclos.

## 3. ROOT_IDs

| ROOT_ID | Archivo | Acción | LOC est. |
|---|---|---|---|
| R-016 | `domain/dsl/templates/T01_simple.yaml` … `T12_deep_reasoning.yaml` (12 archivos) | NEW | ~500 total |
| R-020 | `domain/dsl/dag_parser.py` | NEW | ~300 |

## 4. CONTRATO DE LAS TEMPLATES
Cada template YAML define: `template_id`, `categoria_tarea`, `nodos` (lista con `id`, `tipo`, `depende_de`), `paralelismo_permitido`. Las 12 categorías (T01-T12) deben cubrir el espectro descrito en el documento de diseño avanzado (desde tarea simple de 1 nodo hasta equipo de razonamiento profundo de N nodos) — si no tienes el detalle exacto de alguna Txx, usa el patrón de las que sí tienes documentadas y repórtalo como ASSUMPTION en el EvidencePacket, no lo omitas silenciosamente.

## 5. CONTRATO DE `dag_parser.py`
```python
class DAGParser:
    def parse(self, template: dict) -> GraphExecutionPlan: ...
    # Debe rechazar (raise) si detecta ciclo antes de devolver el plan.
```
`GraphExecutionPlan` expone la lista de nodos en orden topológico y sus dependencias resueltas.

## 6. CALIDAD
Igual que TASK-01 sección 7. Los YAML no cuentan como "función" pero deben ser válidos y parseables sin excepción.

## 7. TESTS OBLIGATORIOS
- `test_cada_template_parsea_sin_error` (12 casos, uno por template)
- `test_grafo_ciclico_es_rechazado`
- `test_orden_topologico_correcto`
- `test_nodos_paralelos_se_identifican_correctamente`

## 8. ACEPTACIÓN
12 templates válidas + parser funcional. Ningún ciclo pasa sin error.

## 9. EVIDENCEPACKET
```yaml
evidence_packet:
  task_id: TASK-04
  chat_b_id: CHAT-B04
  root_ids: [R-016, R-020]
  templates_entregadas: 12
  assumptions: []  # llenar si alguna Txx se completó por patrón, no por spec exacta
  status: COMPLETED | BLOCKED
```

## 10. BLOCKER
Si el detalle de una template es totalmente desconocido (ni siquiera por patrón), no la inventes desde cero — repórtala como UNKNOWN, no como completada.

## 11. TRAZABILIDAD
DAG_NODES: N07, N10 → TASK-04 → CHAT-B04 → R-016, R-020

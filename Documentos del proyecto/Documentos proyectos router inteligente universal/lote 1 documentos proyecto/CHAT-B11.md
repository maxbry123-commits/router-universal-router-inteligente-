# CHAT-B11.md — TASK-11: API Routers (Integración Final)
ROLE: CHAT B — Desarrollador Backend. Sin autoridad de arquitectura. Ambigüedad no cubierta = BLOCKER.

## 1. CONTEXTO HEREDADO
Depende de **TASK-03, TASK-09, TASK-10 COMPLETED**. DAG_NODES: N23. Es el nodo de integración final del DAG de construcción.

## 2. ⚠️ CONDICIÓN DEL ASK COUNCIL #10 (OBLIGATORIA)
El contrato de API (rutas + payloads) debe coincidir EXACTAMENTE con las 98 funciones ya especificadas en `__router-funciones.md` (documento fuente de Chat A), aunque la UI (los 5 paneles HTML ya diseñados) no se conecte todavía en esta fase. No inventes rutas nuevas ni cambies nombres de payload — es un contrato ya cerrado con el frontend.

## 3. OBJETIVO
Exponer los endpoints REST que alimentan Panel 1 (Entrada/Fichas), Panel 2 (Anclaje/Salida), Panel 3 (Router/Auditoría), Panel 4 (Conectores), Panel 5 (Agente/AI), integrando `DAGOrchestrator`+`WindowsChain` (TASK-09), `Alcabala`+`Events` (TASK-10), y `Conectores` (TASK-03).

## 4. ROOT_IDs

| ROOT_ID | Archivo | Acción | LOC est. |
|---|---|---|---|
| R-050 | `api/routers/connections.py` | NEW | ~200 |
| R-051 | `api/routers/connectors.py` | NEW | ~200 |
| R-052 | `api/routers/agent.py` | NEW | ~180 |
| R-053 | `api/routers/extras.py` | NEW | ~250 |

## 5. CONTRATO POR ROUTER
- `connections.py`: CRUD de fichas de conexión (Panel 1/2) — valida cada ficha contra `enchufe_v2.py` (TASK-01) antes de persistir vía `StorageProtocol` (TASK-02).
- `connectors.py`: CRUD y prueba de conectores (Panel 4) — usa `red/conectores.py` (TASK-03) para `sondear()` en vivo.
- `agent.py`: endpoints de Panel 5, incluye `probarAgenteChat()` — debe soportar AMBOS modos confirmados por el usuario: streaming WS/SSE (vía `events.py`, TASK-10) Y petición-respuesta REST simple.
- `extras.py`: Panel 3 (auditoría/router) — expone snapshot de `monitoring.py` (TASK-05) y estado de `resilience.py` (TASK-06) vía WS.
- TODOS los routers pasan primero por `alcabala.py` (TASK-10) — no hay bypass.

## 6. CALIDAD
Igual que TASK-01 sección 7.

## 7. TESTS OBLIGATORIOS
- `test_connections_crud_valida_contra_schema`
- `test_connectors_prueba_en_vivo`
- `test_agent_streaming_ws`
- `test_agent_rest_peticion_respuesta`
- `test_extras_snapshot_monitoring`
- `test_regresion_completa_contra_mapa_98_funciones` (crítico — sección 2)

## 8. ACEPTACIÓN
4 archivos ≤500 LOC c/u. Los 98 endpoints/funciones de `__router-funciones.md` tienen contraparte exacta en estos routers (nombre de ruta, payload, tipo de respuesta). Ningún endpoint del documento fuente queda sin implementar o con firma distinta.

## 9. EVIDENCEPACKET
```yaml
evidence_packet:
  task_id: TASK-11
  chat_b_id: CHAT-B11
  root_ids: [R-050, R-051, R-052, R-053]
  funciones_cubiertas: 0  # debe llegar a 98
  funciones_faltantes: []
  status: COMPLETED | BLOCKED
```

## 10. BLOCKER
Si `funciones_faltantes` no está vacío al terminar, el status NO puede ser COMPLETED — repórtalo como BLOCKED con la lista exacta. Este es el nodo de integración final; un contrato incompleto aquí rompe los 5 paneles cuando se conecten.

## 11. TRAZABILIDAD
DAG_NODES: N23 → TASK-11 → CHAT-B11 → R-050, R-051, R-052, R-053

---

## Nota de cierre del proyecto
Cuando TASK-11 reporte COMPLETED con `funciones_cubiertas: 98`, el backend queda en `READY_FOR_INTEGRATION` — momento de generar el `FINAL_INTEGRATION_REPORT` (sección 45 del prompt maestro) antes de conectar los paneles HTML ya diseñados.

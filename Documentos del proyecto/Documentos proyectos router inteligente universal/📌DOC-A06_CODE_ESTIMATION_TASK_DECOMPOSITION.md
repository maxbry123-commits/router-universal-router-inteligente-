# DOC-A06_CODE_ESTIMATION_TASK_DECOMPOSITION.md
ROLE: CHAT A — ARCHITECT
BASE: DOC-A02 (Architecture) + DOC-A03 (DAG) + DOC-A04 (Root Map) + DOC-A05 (Dependency Map)

Reglas aplicadas: TASK ≤ 2000 LOC estimadas · cada bloque de código ≤ 500 LOC ·
ninguna task obliga a llenar cuota · orden respeta el DAG (una task no puede
empezar antes que sus dependencias declaradas estén COMPLETED).

---

## Resumen de 11 tasks (32 ROOT_ID agrupados)

| TASK_ID | CHAT_B_ID | ROOT_IDs | LOC estimado | Bloques (≤500 c/u) | Depende de | DAG_NODES |
|---|---|---|---|---|---|---|
| TASK-01 | CHAT-B01 | R-010, R-011, R-001, R-005 | ~940 | 4 (80/350/230/280) | — | N01, N02, N03 |
| TASK-02 | CHAT-B02 | R-012, R-013, R-014, R-015, R-004 | ~560 | 5 (150/60/150/120/40) | TASK-01 | N05, N08, N04 |
| TASK-03 | CHAT-B03 | R-002, R-003 | ~520 | 3 (bloques ~250+250 conectores nuevos + 20 red_universal) | TASK-01 | N06, N09 |
| TASK-04 | CHAT-B04 | R-016, R-020 | ~800 | 4 (3 bloques templates ~170 c/u + 1 dag_parser ~300) | TASK-01 | N07, N10 |
| TASK-05 | CHAT-B05 | R-021, R-022, R-034 | ~480 | 3 (150/150/180) | TASK-01, TASK-02 | N11, N12, N17 |
| TASK-06 | CHAT-B06 | R-023, R-032, R-033 | ~470 | 3 (120/200/150) | TASK-01, TASK-02, TASK-03 | N13, N15, N16 |
| TASK-07 | CHAT-B07 | R-030, R-031 | ~400 | 2 (350/50) | TASK-03, TASK-06 | N14 |
| TASK-08 | CHAT-B08 | R-035, R-036, R-037 | ~450 | 3 (150/150/150) | TASK-02 | N18 |
| TASK-09 | CHAT-B09 | R-040, R-041 | ~600 | 2 (300/300) | TASK-04, TASK-06, TASK-07, TASK-08 | N19, N20 |
| TASK-10 | CHAT-B10 | R-042, R-043 | ~270 | 2 (150/120) | TASK-01, TASK-02, TASK-05 | N21, N22 |
| TASK-11 | CHAT-B11 | R-050, R-051, R-052, R-053 | ~830 | 4 (200/200/180/250) | TASK-03, TASK-09, TASK-10 | N23 |

**TOTAL_LOC estimado del proyecto: ~6.320 LOC.** Ninguna task supera 2000 LOC; ningún bloque supera 500 LOC. Ninguna cifra es cuota obligatoria — son estimaciones de alcance, Chat B puede entregar menos si el contrato se satisface con menos código.

---

## Orden de ejecución (respeta el DAG, no es libre elección de Chat B)

```
Nivel 0:  TASK-01
Nivel 1:  TASK-02, TASK-03, TASK-04         (paralelas entre sí, todas dependen solo de TASK-01)
Nivel 2:  TASK-05, TASK-06                  (dependen de nivel 0-1 según tabla)
Nivel 3:  TASK-07, TASK-08                  (dependen de TASK-03/06 y TASK-02 respectivamente)
Nivel 4:  TASK-09, TASK-10                  (integración de engine / integración de api-middleware)
Nivel 5:  TASK-11                            (integración final — API routers)
```

---

## Detalle por task (contenido que definirá cada CHAT-BXX.md)

### TASK-01 — Foundation A (config + schema + enchufe gate v2.0 + validator)
- **Objetivo:** Base inmutable de configuración, el schema Pydantic espejo de Enchufe v2.0, y la extensión de `enchufe_gate.py` (v1.5→v2.0) integrando `validator_v2.py`.
- **Reuse:** R-001 (PATCH), R-005 (MOVE + wire).
- **Generate:** R-010, R-011.
- **Riesgo:** Romper compatibilidad v1.5 si el mapeo de defaults no es exacto → test obligatorio de round-trip v1.5→v2.0.

### TASK-02 — Foundation B (vault + storage + backup)
- **Objetivo:** SecretVault cifrado, interfaz de storage abstracta + adaptadores Postgres/Redis, integración de `respaldo.py`.
- **Reuse:** R-004 (tal cual).
- **Generate:** R-012, R-013, R-014, R-015.
- **Riesgo:** Ninguna credencial debe poder salir en claro del vault (test explícito).

### TASK-03 — Red (conectores nuevos + registro en red_universal)
- **Reuse/PATCH:** R-002 (agregar ConectorHuggingFace, ConectorDB, ConectorGitLab, ConectorMCPApp, ConectorMCPTunnel, ConectorA2A, ConectorACP, ConectorSSH, ConectorBotPersistente, SkillPackImporter — ver v6 sección 4), R-003 (registro, sin romper estructura).
- **Riesgo:** No reescribir `ConectorHTTP`/`ConectorMCP` existentes — solo extender el módulo.

### TASK-04 — DSL (templates T01-T12 + parser)
- **Generate:** R-016 (12 templates fijas, sin lógica de improvisación), R-020 (DAGParser con detección de ciclos).
- **Riesgo:** Una template mal formada bloquea TODO el motor — test de validación por template obligatorio antes de integrar.

### TASK-05 — Core services (auth + ledger + monitoring)
- **Generate:** R-021, R-022, R-034.
- **Riesgo:** Ledger debe ser append-only real (sin update/delete expuesto).

### TASK-06 — Resilience + Cache + Cost
- **Generate:** R-023, R-032 (Retry + Circuit Breaker, diseño ya dado en resumen v6 §6 — implementar tal cual, no reinventar), R-033.
- **Riesgo:** Circuit Breaker debe usar ventana temporal real, no solo contador (gap ya señalado en GAP_01_ROUTER.md).

### TASK-07 — Worker Pool
- **Generate:** R-030 (Selector + Cola/Balanceo + Health), R-031 (capability.json editable).
- **Riesgo:** Batching debe soportar batch_size=20/overlap=5 para ráfagas de 200+ tareas (requisito explícito de v6).

### TASK-08 — Sandbox dual
- **Generate:** R-035, R-036, R-037.
- **Riesgo:** CONDICIÓN DEL ASK COUNCIL #7 — límites de recursos (timeout_ms, max_memoria_mb) obligatorios en AMBOS backends, con paridad de contrato. teardown() garantizado con try/finally.

### TASK-09 — Orchestrator + Windows Chain
- **Generate:** R-040 (ejecuta GraphExecutionPlan con checkpoints), R-041 (generalización Python de ventanas/cadena.py — pausa, breakpoint, intervención manual, export a DSL).
- **Riesgo:** Máxima complejidad de integración — depende de 4 tasks previas. Debe testearse contra el prototipo de referencia `_ventanas_del_tren.html` para paridad de semántica.

### TASK-10 — API Middleware + WS
- **Generate:** R-042 (Alcabala — fail closed), R-043 (eventos WS/SSE).

### TASK-11 — API Routers (integración final)
- **Generate:** R-050, R-051, R-052, R-053.
- **Riesgo:** Debe cumplir EXACTAMENTE el contrato de las 98 funciones de `__router-funciones.md` aunque la UI no se conecte todavía — CONDICIÓN DEL ASK COUNCIL #10.

---

## Siguiente paso

Con TASK_DECOMPOSITION y CHAT_B_ASSIGNMENT definidos, quedo en condición de generar los **11 prompts CHAT-BXX.md**, cada uno autónomo (sección 44 del prompt maestro: objetivo, mission contract, arquitectura, root ids, dependencias, schemas, contratos, implementación, calidad, seguridad, tests, aceptación, LOC, formato de salida, trazabilidad, regla de blocker).

¿Genero los 11 prompts ahora, todos de una vez, o prefieres que empiece por TASK-01 y vayamos revisando uno a uno antes de continuar?

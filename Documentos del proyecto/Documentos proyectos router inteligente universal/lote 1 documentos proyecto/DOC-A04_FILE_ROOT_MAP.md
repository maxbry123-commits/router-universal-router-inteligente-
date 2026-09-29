# DOC-A04_FILE_ROOT_MAP.md
ROLE: CHAT A — ARCHITECT
BASE: DOC-A02 (Architecture) + DOC-A03 (Workflow DAG)
NOTA: TASK y CHAT_B se llenan en TASK_DECOMPOSITION (siguiente paso, aún no asignado). Aquí quedan como PENDING.

Estados usados (sección 9 del prompt maestro): EXISTING_COMPLETE · EXISTING_PARTIAL · MISSING · NEW · REPLACE · PATCH · ADAPT · REUSE · MOVE · PENDING

---

## Grupo REUSE (código real ya existente — no se reescribe)

| ROOT_ID | FILE | DAG_NODE | DEPENDENCIES | CALLS | STATUS | TASK | CHAT_B |
|---|---|---|---|---|---|---|---|
| R-001 | `red/enchufe_gate.py` | N03 | R-101 (schema v2.0) | — | EXISTING_COMPLETE → PATCH (extender v1.5→v2.0) | PENDING | PENDING |
| R-002 | `red/conectores.py` | N06 | R-001 | httpx/asyncpg/aiomysql/redis.asyncio | EXISTING_PARTIAL → PATCH (agregar conectores nuevos de v6) | PENDING | PENDING |
| R-003 | `red/red_universal.py` | N09 | R-002, R-001 | R-002 | EXISTING_COMPLETE (sin cambio estructural) | PENDING | PENDING |
| R-004 | `infrastructure/backup/respaldo.py` | N04 | — | filesystem, hashlib, zipfile | EXISTING_COMPLETE → REUSE tal cual | PENDING | PENDING |
| R-005 | `enchufe/validator_v2.py` | N02/N03 | — | — | EXISTING_COMPLETE (diseño en texto) → MOVE al repo + PATCH para invocarlo desde R-001 | PENDING | PENDING |

## Grupo NEW — Foundation (Nivel 0-1 del DAG)

| ROOT_ID | FILE | DAG_NODE | DEPENDENCIES | CALLS | STATUS | TASK | CHAT_B |
|---|---|---|---|---|---|---|---|
| R-010 | `core/config.py` | N01 | — | os.environ | NEW | PENDING | PENDING |
| R-011 | `domain/schemas/enchufe_v2.py` | N02 | R-005 (fuente del schema) | pydantic | NEW | PENDING | PENDING |
| R-012 | `core/secret_vault.py` | N05 | R-010 | cryptography.fernet | NEW | PENDING | PENDING |
| R-013 | `infrastructure/storage/storage_protocol.py` | N08 | R-010 | — | NEW | PENDING | PENDING |
| R-014 | `infrastructure/storage/postgres_adapter.py` | N08 | R-013 | asyncpg | NEW | PENDING | PENDING |
| R-015 | `infrastructure/storage/redis_adapter.py` | N08 | R-013 | redis.asyncio | NEW | PENDING | PENDING |
| R-016 | `domain/dsl/templates/T01_simple.yaml` … `T12_deep_reasoning.yaml` (12 archivos) | N07 | R-011 | — | NEW | PENDING | PENDING |

## Grupo NEW — Domain/Core (Nivel 2 del DAG)

| ROOT_ID | FILE | DAG_NODE | DEPENDENCIES | CALLS | STATUS | TASK | CHAT_B |
|---|---|---|---|---|---|---|---|
| R-020 | `domain/dsl/dag_parser.py` | N10 | R-016 | — | NEW | PENDING | PENDING |
| R-021 | `core/auth.py` | N11 | R-012 | — | NEW | PENDING | PENDING |
| R-022 | `core/ledger.py` | N12 | R-010 | — | NEW | PENDING | PENDING |
| R-023 | `engine/cost_optimizer.py` | N13 | R-011 | — | NEW | PENDING | PENDING |

## Grupo NEW — Engine (Nivel 3 del DAG)

| ROOT_ID | FILE | DAG_NODE | DEPENDENCIES | CALLS | STATUS | TASK | CHAT_B |
|---|---|---|---|---|---|---|---|
| R-030 | `engine/worker_pool.py` | N14 | R-003, R-023 | R-003, R-023 | NEW | PENDING | PENDING |
| R-031 | `domain/dsl/capability.json` | N14 | R-011 | — | NEW | PENDING | PENDING |
| R-032 | `engine/resilience.py` | N15 | R-003 | R-002 (llamada a Conector) | NEW | PENDING | PENDING |
| R-033 | `engine/semantic_cache.py` | N16 | R-015 | redis vector similarity | NEW | PENDING | PENDING |
| R-034 | `core/monitoring.py` | N17 | R-022 | — | NEW | PENDING | PENDING |
| R-035 | `engine/sandbox/code_sandbox.py` | N18 | R-012 | R-036, R-037 | NEW | PENDING | PENDING |
| R-036 | `engine/sandbox/docker_backend.py` | N18 | R-035 | docker SDK | NEW | PENDING | PENDING |
| R-037 | `engine/sandbox/subprocess_backend.py` | N18 | R-035 | subprocess | NEW | PENDING | PENDING |

## Grupo NEW — Integración (Nivel 4-5 del DAG)

| ROOT_ID | FILE | DAG_NODE | DEPENDENCIES | CALLS | STATUS | TASK | CHAT_B |
|---|---|---|---|---|---|---|---|
| R-040 | `engine/dag_orchestrator.py` | N19 | R-020, R-030, R-032, R-035 | R-030, R-032, R-035, R-003 | NEW | PENDING | PENDING |
| R-041 | `engine/windows_chain.py` | N20 | R-035, R-020 | R-035, R-020 | NEW | PENDING | PENDING |
| R-042 | `api/middlewares/alcabala.py` | N21 | R-012, R-011 | R-012 | NEW | PENDING | PENDING |
| R-043 | `api/ws/events.py` | N22 | R-034 | — | NEW | PENDING | PENDING |
| R-050 | `api/routers/connections.py` | N23 | R-040, R-042 | R-040 | NEW | PENDING | PENDING |
| R-051 | `api/routers/connectors.py` | N23 | R-002, R-042 | R-002 | NEW | PENDING | PENDING |
| R-052 | `api/routers/agent.py` | N23 | R-040, R-042 | R-040 | NEW | PENDING | PENDING |
| R-053 | `api/routers/extras.py` | N23 | R-034, R-043 | R-034 | NEW | PENDING | PENDING |

---

## Notas de integridad

- Ningún archivo en `red/` cambia de ubicación (regla de no-mezcla, sección 43 del prompt maestro: no inventar archivos ni mover código que funciona sin razón).
- R-005 (`validator_v2.py`) requiere una decisión de MOVE: hoy vive solo como texto en `FABLES_ENCHUFE_UNIVERSAL_v2.md`; su ROOT_ID definitivo será `enchufe/validator_v2.py` dentro del repo único.
- Total archivos en scope: 5 REUSE + 27 NEW (incluye 12 templates T01-T12 agrupadas en R-016) = 32 unidades rastreables.
- COMPLETE requiere evidencia (sección 9): ningún ROOT_ID pasa a EXISTING_COMPLETE/DONE sin EvidencePacket del Chat B correspondiente.

# T-11 — PROGRAMACIÓN EXACTA DE NUEVO-01…NUEVO-19

Este documento convierte los 19 puntos aprobados en especificaciones implementables. Los nombres de módulos son **propuestos**; el agente debe mapearlos al árbol real después de `T11-A`. Si ya existe un módulo semánticamente equivalente, se reutiliza/parchea.

## NUEVO-01 — Input Parser determinista

**Objetivo:** convertir texto de entrada en un contrato sin depender de LLM en casos conocidos.

Schema mínimo:

```json
{
  "task_type": "SEARCH|INSTALL|DOWNLOAD|EXTRACT|DEPLOY|MODIFY_CODE|DEBUG|TEST|COMPARE|AUDIT|RESEARCH|VERIFY|UNKNOWN",
  "targets": [],
  "requirements": [],
  "constraints": [],
  "forbidden": [],
  "verification": []
}
```

Programación:
- parser por reglas, regex, diccionarios y schema;
- normalización de rutas, entidades y verbos;
- salida inválida → `UNKNOWN`, nunca completar inventando;
- LLM fallback solo si la política del baseline lo permite y su salida pasa schema.

Tests:
- 10 fixtures conocidas → 100% deterministas;
- prohibición explícita debe sobrevivir intacta;
- input ambiguo → UNKNOWN.

## NUEVO-02 — Query Compiler determinista

Entrada: contrato de NUEVO-01.  
Salida: lista tipada de queries.

```yaml
query:
  id:
  goal:
  text:
  source_scope:
  freshness:
  required: true
```

Programación:
- templates por task_type y goal;
- variables escapadas;
- dedup exacta y normalizada;
- no usar LLM para formular búsquedas estándar.

## NUEVO-03 — Search Fan-out

Programación:
- registry de adaptadores reales;
- fan-out concurrente solo a adaptadores autorizados;
- timeout individual;
- resultado normalizado:

```json
{
  "query_id": "",
  "source": "",
  "source_type": "official|code|issue|community|local",
  "url_or_path": "",
  "title": "",
  "date": null,
  "snippet": "",
  "retrieved_at": ""
}
```

- fallo de un motor no destruye resultados de otros;
- cada error vuelve como observation tipada.

## NUEVO-04 — Extractor exacto + Ranking

Pipeline:
`RAW → CLEAN → SEGMENT → MATCH → CONTEXT WINDOW → DEDUP → SCORE → RRF`

Score configurable:
`exact + lexical/BM25 + authority + recency + identifier + corroboration - duplicate - stale`

Reglas:
- los pesos viven en YAML;
- no hardcodear autoridad en prompts;
- preservar URL/path y heading para trazabilidad.

## NUEVO-05 — EvidencePacket

Schema obligatorio:

```json
{
  "task": {},
  "known_facts": [],
  "requirements": [],
  "constraints": [],
  "conflicts": [],
  "unknown": [],
  "sources": [],
  "packet_hash": ""
}
```

Reglas:
- cada fact referencia evidencia;
- `packet_hash` sobre representación normalizada;
- no meter páginas completas si bastan fragmentos;
- conflicts/unknown nunca se ocultan.

## NUEVO-06 — Claims Verification

Pipeline:
`RESULT → CLAIM EXTRACTOR → CHECK PLAN → VERIFY → SUPPORTED/UNSUPPORTED/CONTRADICTED`

Cada claim:
```json
{
  "claim_id": "",
  "text": "",
  "check_type": "file|hash|http|test|config|trace|search",
  "evidence_refs": [],
  "status": "SUPPORTED|UNSUPPORTED|CONTRADICTED"
}
```

PASS final requiere que los claims de aceptación estén `SUPPORTED`.

## NUEVO-07 — Event Sourcing del State Hub

Regla:
- `BITACORA.jsonl` append-only;
- cada evento tiene `seq`, `event_id`, `type`, `actor`, `project`, `task`, `timestamp`, `payload_hash`;
- reducer puro: `previous_state + event -> new_state`;
- `STATE.json` es snapshot derivado, no fuente única.

Test crítico:
- borrar snapshot en fixture;
- replay de eventos;
- nuevo snapshot == expected snapshot.

## NUEVO-08 — Claim + Lease + Heartbeat

Contrato:
```json
{
  "claim_id": "",
  "node_id": "",
  "worker_id": "",
  "base_sha": "",
  "write_scope": [],
  "lease_expires_at": "",
  "heartbeat_at": "",
  "status": "CLAIMED"
}
```

Reglas:
- un scope solapado no acepta segundo writer;
- lease expirada no permite side effect;
- heartbeat renueva lease dentro de límites;
- reclaim necesita evento explícito.

## NUEVO-09 — Stuck Detection

Fingerprint:
`sha256(action_type + canonical_args + evidence_state_hash)`

Si:
- fingerprint repetido;
- N veces configurable;
- `new_evidence == false`;

entonces:
`STUCK → strategy_change` o `BLOCKED_WITH_TRACE`.

Nunca 20 repeticiones ciegas.

## NUEVO-10 — Recovery tipado

Enum:
`RETRYABLE | DEPENDENCY | AUTH | STUCK | CRASH | IRREVERSIBLE_FAILURE | NO_NODE_SOLUTION`

Cada tipo define:
- retry_allowed;
- max_retries;
- backoff;
- requires_human;
- rollback;
- next_state.

`catch Exception -> GAP` queda prohibido como política universal.

## NUEVO-11 — Crash/Resume con hash

Checkpoint:
- run_id;
- node_id;
- input_hash;
- state_hash;
- base_sha;
- evidence_cursor;
- completed_side_effects.

Resume:
`LOAD → VALIDATE SCHEMA → VERIFY HASH → VERIFY BASE_SHA → RECONCILE SIDE EFFECTS → RESUME`.

Test: kill simulado entre dos pasos y reanudar sin duplicar operación idempotente.

## NUEVO-12 — WorkerBootstrap

Antes de READY:
1. load task contract;
2. validate schema;
3. verify worker_id;
4. verify assigned node;
5. verify capability;
6. verify write_scope;
7. verify base_sha;
8. verify environment/tool availability;
9. acquire claim;
10. READY.

Cualquier fallo → no ejecutar.

## NUEVO-13 — Worktree/Workspace aislado

Campos:
`parent_id, child_id, node_id, claim_id, workspace, base_sha, write_scope, command_id`.

Reglas:
- cada writer tiene workspace aislado;
- no compartir directorio mutable;
- merge/promote solo tras test;
- conflicto de base SHA → rebase/reconcile controlado, no overwrite.

## NUEVO-14 — Frontend Browser Gate

Por paso visual:
`EDIT → BUILD → START → OPEN BROWSER → DOM/CONSOLE → INTERACT → SCREENSHOT → COMPARE → FIX/CONTINUE`

PASS:
`CODE_PASS && BROWSER_PASS && VISUAL_PASS`.

Guardar:
- screenshot;
- URL;
- viewport;
- console errors;
- action trace;
- acceptance result.

## NUEVO-15 — Installer transaccional

`ACQUIRE → ISOLATED WORKSPACE → INSPECT → DEPENDENCY POLICY → INSTALL → LOCAL TEST → PROMOTE`

FAIL:
`ROLLBACK/DISCARD`.

Si el baseline exige RDC, RDC sigue siendo la adquisición autorizada; este punto añade aislamiento/promoción, no reemplaza RDC.

## NUEVO-16 — Salidas LLM tipadas

Schema:
```json
{
  "decision": "",
  "confidence": null,
  "evidence_refs": [],
  "recommended_action": "",
  "unknowns": []
}
```

Reglas:
- parse strict;
- additionalProperties=false cuando aplique;
- confidence no autoriza nada;
- output inválido → fail-closed.

## NUEVO-17 — ResearchResult + NO_NEW_EVIDENCE

Schema:
```json
{
  "query": "",
  "sources": [],
  "source_type": [],
  "claims": [],
  "cross_check": [],
  "new_evidence": false,
  "conclusion": ""
}
```

Regla:
`new_evidence=false` no cuenta como progreso; alimenta StuckDetector.

## NUEVO-18 — Persistencia por tarea

Por task real:
```text
TASK.json
STATE.json
HANDOFF.md
EVIDENCE.json
EVENTS.jsonl
```

Reglas:
- task folder se crea idempotentemente;
- snapshot local no duplica autoridad global;
- State Hub agrega/deriva vista global;
- cierre conserva evidence y events.

## NUEVO-19 — DISPATCH → EVIDENCE → FINALIZE

Estados:
`READY → DISPATCHED → RUNNING → NEED_EVIDENCE → VERIFIED → FINALIZED`

Separar comandos:
- submit/dispatch inicia;
- evidence adjunta receipts;
- finalize valida y pide decisión al Judge.

Prohibición:
- worker, Hermes, OpenClaw o Ruflo no se auto-declaran PASS final.

## Matriz de integración

```text
01-06 + 17 → Input/Evidence Layer
07-11 + 18 → State/Recovery Layer
12-13 + 15-16 → Worker/Safety Layer
14 → Frontend Verification Layer
19 → Closure Layer
```

## Acceptance global

- 19/19 tienen módulo o extensión semántica real.
- 19/19 tienen test.
- 19/19 aparecen en `ROUTER-FINGERPRINT.md` o como GAP explícito.
- Ningún punto queda implementado solo como prompt/documentación.

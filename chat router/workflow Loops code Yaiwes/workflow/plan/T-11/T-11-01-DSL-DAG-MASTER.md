# T-11 — DSL/DAG MAESTRO — ENDURECIMIENTO, MIRRORS Y ARQUITECTURA AUDITABLE

```yaml
schema: riu.dag/v1
id: T-11-yaiwes-hardening-mirrors-fingerprint
title: "T-11 — Endurecimiento determinista + mirrors + arquitectura auditable"
repo: maxbry123-commits/router-universal-router-inteligente-
branch: main
mode: append_only
needs: [T-10]
work_surface: BACKEND+FRONTEND+STATE+ARCHITECTURE

authority:
  input_verbatim: "./T-11-00-INPUT-BLOCK-VERBATIM.md"
  baseline:
    - "INPUT 1: PLAN-DSL-DAG-UI T-01..T-10"
    - "INPUT 1: ESPECIFICACION_VISUAL_PANEL_YAIWES_FROMTED.md"
  approved_additions:
    range: "NUEVO-01..NUEVO-19"
    all: true

global_rules:
  - "NO modificar semántica de T-01..T-10; T-11 se añade después"
  - "NO investigación web durante la preparación de SALIDA 1"
  - "NO inventar rutas, tools, skills, pools, workflows o componentes"
  - "Antes de cablear una pieza existente: localizar → read-back → hash/ruta → contrato → test"
  - "Control plane: Python ejecutable + YAML/JSON schema; LLM nunca autoridad final"
  - "Sheriff y Judge son autoridad determinista; agentes solo proponen/ejecutan dentro de scope"
  - "1 writer = 1 isolated write scope"
  - "Todo side effect necesita contrato, scope, evidencia y ledger"
  - "Todo cambio estructural usa git mv/patch controlado; nada de big-bang refactor"
  - "Máximo 500 LOC por archivo nuevo salvo justificación registrada"
  - "Vercel sigue OFF hasta autorización expresa"
  - "Secrets: solo referencias/nombres; nunca valores"
  - "FAIL_CLOSED si schema/evidence/contract no valida"
  - "Cada subnodo termina con tests + evidence + STATE + BITACORA + HANDOFF"

state_machine:
  states:
    - PLANNED
    - READY
    - CLAIMED
    - RUNNING
    - NEED_EVIDENCE
    - RETRYABLE
    - DEPENDENCY
    - AUTH
    - STUCK
    - CRASH
    - BLOCKED
    - VERIFIED
    - CLOSED
  forbidden:
    - "RUNNING -> CLOSED sin VERIFIED"
    - "PLANNED -> RUNNING sin WorkerBootstrap"
    - "CLAIMED por segundo writer sobre mismo write_scope"

dag:
  - id: T11-A
    title: "Inventario y mapa de dependencias antes del refactor"
    needs: []
    steps:
      - "Leer árbol real de chat router/ y contratos/runtimes usados por T-01..T-10"
      - "Generar INVENTORY-T11.json: path, type, owner, imports, callers, callees, tests"
      - "Generar ROOT-MAP-T11.yaml con las 10 raíces lógicas del Director"
      - "Marcar cada archivo: KEEP | MOVE_CANDIDATE | ADAPTER | LEGACY_COMPAT"
      - "No mover nada todavía"
    acceptance:
      - "100% de archivos tocables por T-11 tienen owner y destino lógico"
      - "0 rutas inventadas"
    evidence: [inventory, root_map, read_back]

  - id: T11-B
    title: "Implementar núcleo determinista NUEVO-01..NUEVO-06 + NUEVO-17"
    needs: [T11-A]
    steps:
      - "Implementar InputParser determinista"
      - "Implementar QueryCompiler por templates"
      - "Implementar SearchFanout sobre adaptadores reales existentes"
      - "Implementar exact extractor + ranker + dedup/RRF"
      - "Implementar EvidencePacket schema"
      - "Implementar ClaimsVerifier post-ejecución"
      - "Implementar ResearchResult + NO_NEW_EVIDENCE"
    acceptance:
      - "inputs conocidos no requieren LLM"
      - "evidence packet valida por schema"
      - "claim sin evidencia nunca produce PASS"
    evidence: [unit_tests, fixtures, schemas]

  - id: T11-C
    title: "State Hub durable + claim/lease + recovery"
    needs: [T11-B]
    implements: [NUEVO-07, NUEVO-08, NUEVO-09, NUEVO-10, NUEVO-11, NUEVO-18]
    steps:
      - "BITACORA append-only + reducer determinista → STATE"
      - "Claim/Lease/Heartbeat por nodo y write_scope"
      - "StuckDetector fingerprint(action,args,evidence_state)"
      - "FailureClassifier tipado"
      - "CrashResume: load state → verify hash → resume"
      - "Persistencia por task: TASK/STATE/HANDOFF/EVIDENCE/EVENTS"
    acceptance:
      - "reconstrucción de STATE desde eventos produce snapshot equivalente"
      - "segundo writer sobre mismo scope es rechazado"
      - "crash test reanuda sin repetir side effects"
    evidence: [replay_test, lock_test, crash_resume_test]

  - id: T11-D
    title: "WorkerBootstrap + aislamiento + ejecución segura"
    needs: [T11-C]
    implements: [NUEVO-12, NUEVO-13, NUEVO-15, NUEVO-16]
    steps:
      - "WorkerBootstrap carga y valida task contract antes de ejecutar"
      - "Crear workspace/worktree aislado por claim"
      - "Side effects solo dentro de write_scope"
      - "Installer transaccional: acquire→inspect→policy→install→test→promote"
      - "Salida LLM tipada y validada fail-closed"
    acceptance:
      - "worker no ejecuta nodo ajeno"
      - "workspace fallido se descarta sin contaminar destino"
      - "salida LLM inválida no dispara side effects"
    evidence: [bootstrap_tests, isolation_tests, rollback_tests]

  - id: T11-E
    title: "Frontend Browser Gate + cierre separado"
    needs: [T11-D]
    implements: [NUEVO-14, NUEVO-19]
    steps:
      - "Frontend step: edit→build→browser→DOM/console→interact→screenshot→compare"
      - "Cada paso visual relevante genera evidencia"
      - "Separar DISPATCH de FINALIZE"
      - "FINALIZE solo con evidence ledger + Judge"
    acceptance:
      - "BUILD PASS no equivale a UI PASS"
      - "run sin evidence queda DISPATCHED/NEED_EVIDENCE"
      - "finalize sin receipts falla cerrado"
    evidence: [browser_evidence, finalize_tests]

  - id: T11-F
    title: "Mirror Factory por proyecto/tarea"
    needs: [T11-C, T11-D]
    steps:
      - "Crear schema yaiwes.mirror/v1"
      - "Nuevo project/task elegible → MirrorFactory genera workspace hijo"
      - "Orquestador central conserva autoridad de scheduling"
      - "Hermes central crea/gestiona hermes_child por mirror"
      - "OpenClaw central crea/gestiona openclaw_child por mirror"
      - "Cada mirror recibe sentinel/supervisor roles y ADAPTERS al Sheriff/Judge centrales"
      - "NO duplicar autoridad final Sheriff/Judge como LLM"
      - "Todos los hijos registran parent_id, mirror_id, node_id, claim_id, scopes, heartbeat"
    acceptance:
      - "crear dos mirrors produce scopes aislados"
      - "hijo no puede elevar permisos sobre padre"
      - "Sheriff/Judge centrales siguen siendo únicos para autorización/cierre"
    evidence: [mirror_manifest, isolation_test, authority_test]

  - id: T11-G
    title: "Separación en 10 raíces auditables"
    needs: [T11-A, T11-F]
    roots:
      - "01 Chat frontend"
      - "02 Plugins Hermes harness"
      - "03 Agente"
      - "04 Input y buscadores"
      - "05 Workflow"
      - "06 Memoria"
      - "07 Formato de salida"
      - "08 Componentes asociados"
      - "09 Tools y pools"
      - "10 Otros"
    migration_policy:
      - "No crear carpeta vacía solo para completar dibujo"
      - "Solo mover archivos reales y con destino justificado"
      - "Migrar una raíz por vez"
      - "Actualizar imports/config/rutas inmediatamente"
      - "Ejecutar test regresión después de cada lote"
      - "Compat shim temporal solo si evita ruptura; registrar fecha de retiro"
    acceptance:
      - "ROOT-MAP-T11 refleja rutas físicas reales"
      - "tests previos siguen pasando"
      - "no hay duplicados activos de un mismo componente"
    evidence: [git_mv_log, dependency_map, regression_tests]

  - id: T11-H
    title: "Tools nativos para Hermes/OpenClaw"
    needs: [T11-A, T11-G]
    steps:
      - "Localizar por read-back el motor real de descarga/extracción en main"
      - "Localizar por read-back el motor real de búsqueda en main"
      - "Localizar enchufe universal Fables y DeepSeek harness existente"
      - "Crear adapters typed-tool; NO copiar motores"
      - "Registrar las tools en Hermes/OpenClaw con permisos mínimos"
      - "Toda descarga conserva la política RDC del baseline"
    acceptance:
      - "cada tool apunta a ruta real verificada"
      - "tool invocation produce receipt/evidence"
      - "Hermes/OpenClaw no bypass Sheriff"
    evidence: [read_back, tool_contracts, invocation_tests]
    note: "La localización la hace el agente durante T-11; este documento no investiga ni inventa rutas."

  - id: T11-I
    title: "Skill Runtime Contract genérico"
    needs: [T11-D, T11-G]
    steps:
      - "Definir skill.schema/v1"
      - "SKILL.md se trata como especificación humana, no como runtime suficiente"
      - "Extraer inputs, outputs, preconditions, tools, side_effects, permissions, tests"
      - "Generar adapter Python determinista"
      - "Generar schema YAML/JSON validable"
      - "Registrar en Tool/Skill Registry"
      - "Ejecutar contract tests"
      - "Solo después marcar skill EXECUTABLE"
    acceptance:
      - "skill sin adapter+schema+tests queda DOCUMENTATION_ONLY"
      - "skill ejecutable siempre declara side effects y permisos"
    evidence: [skill_schema, adapter_test, registry_entry]
    note: "La conversión de ECC/Task Observer/etc. corresponde a SALIDA 3."

  - id: T11-J
    title: "Huella digital + README arquitectura verificable"
    needs: [T11-G, T11-H]
    steps:
      - "Crear ROUTER-FINGERPRINT.md usando yaiwes.router-fingerprint/v1"
      - "Crear ARCHITECTURE-XRAY.md usando la plantilla del Director"
      - "Poblar SOLO con hechos verificados del repo/runtime"
      - "Cada ACTIVE requiere test/evidence"
      - "Cada no comprobado usa CONFIGURED/PARTIAL/BLOCKED/OFFLINE/PLANNED/UNKNOWN"
      - "Incluir árbol REAL, request trace real, APIs/MCP/HTTP/SSH/memoria/workflows"
      - "Generar snapshot manifest normalizado sin secretos"
    acceptance:
      - "ninguna sección inventa componentes"
      - "cada estado real tiene evidencia o queda UNKNOWN"
      - "una nueva IA puede ubicar entrypoint/rutas/flujo sin leer todo el código"
    evidence: [fingerprint, xray, manifest, sha256]

  - id: T11-K
    title: "Cierre T-11"
    needs: [T11-B, T11-C, T11-D, T11-E, T11-F, T11-G, T11-H, T11-I, T11-J]
    steps:
      - "3 simulaciones"
      - "3 refutaciones"
      - "E2E real: input→parser→workflow→worker→evidence→finalize"
      - "E2E mirror: project/task→mirror→child agents→evidence→central Judge"
      - "Reconstruir STATE desde BITACORA"
      - "Read-back de ROOT-MAP y fingerprint"
      - "Actualizar BITACORA+STATE+CRAZY_WALL+HANDOFF+Devin notes+Claude notes"
    acceptance:
      - "NUEVO-01..NUEVO-19 cubiertos por código/test o GAP explícito"
      - "T11-A..T11-J PASS o GAP documentado"
      - "TESTED_SHA == PUBLISHED_SHA"
      - "0 secretos en evidencia"
      - "Vercel sigue OFF"
    evidence: [e2e, simulations, refutations, handoff_final, tested_sha]
```

## Micro flujo global

`INPUT → PARSER → EVIDENCE → DAG → CLAIM/LEASE → WORKER AISLADO → TOOL/WORKFLOW → TEST/BROWSER → CLAIM VERIFY → LEDGER → FINALIZE → JUDGE → CLOSED`

## Regla de compatibilidad

T-11 **no reemplaza** T-01…T-10. Los endurece y agrega capacidades después del cierre/read-back de T-10.

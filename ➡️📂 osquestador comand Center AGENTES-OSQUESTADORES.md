# ➡️📂 OSQUESTADOR COMAND CENTER AGENTES-OSQUESTADORES

Repo: maxbry123-commits/router-universal-router-inteligente-
Branch: main
Schema: yaiwes.node-executor/xray-v2
Mode: FAIL_CLOSED
Scope: AGENTES + ORQUESTADORES ONLY
Updated: 2026-09-23 00:02 America/Bogota

## OBJETIVO
Dirigir exclusivamente agentes y orquestadores, sin mezclar tareas de otros frentes.

## REGLAS PERMANENTES
- SCOPE_LOCK = AGENTS_ORCHESTRATORS_ONLY.
- Claude/orquestador dirige y audita; los agentes ejecutan.
- Cero sobreingeniería.
- Máximo 3 pasos por tarea: REUTILIZAR/ADAPTAR -> CABLEAR/EJECUTAR -> PROBAR.
- Reutilizar componentes OSS antes de escribir código nuevo.
- Componentes externos: solo motores canónicos de main.
- Prohibido construir desde cero una solución equivalente sin autorización explícita del Director.
- Código nuevo únicamente para adaptar, mejorar, integrar o cablear componentes.
- No crear otro orquestador si uno existente puede adaptarse.
- No duplicar responsabilidades entre agentes.
- No declarar PASS sin ejecución real + prueba real + evidencia.
- Credenciales solo por Router/broker/referencia; nunca copiarlas a archivos de agente.

## HANDOFF ACTUAL
- Agent 14 — orquestador Microsoft Agent Framework: ⛔ BLOCKED_REVALIDATION. Crazy Wall raíz declara CLOSED, pero HANDOFF conserva GAP "la prueba superó el tiempo". Existe evidencia exec exit=0, pero por FAIL_CLOSED no se acepta autocertificación contradictoria sin revalidación independiente.
- Agent 15 — orquestador Grok: ⛔ BLOCKED. La cadena oficial terminó por timeout y el diseño de prueba consulta `xai-org/grok-build/releases/latest`, endpoint que devuelve 404 porque el repo oficial no publica GitHub Releases.
- Agent 15 duplicado — `agent-15-orchestrator-grokbuild`: ⛔ BLOCKED_DUPLICATE. Misma responsabilidad que Agent 15 y mismo supuesto inválido sobre GitHub Releases. No reintentar hasta deduplicar y corregir el test.

## CONTROL DE MANDO — AGENTES AUTORIZADOS

ÚNICOS AGENTES QUE EL DIRECTOR AUTORIZA USAR:
- Agent 4 — `agent-4-router-smol`
- Agent 8 — `agent-8-router-local`
- Agent 11 — `agent-11-download-extraction`
- Agent 12 — `agent-12-yaiwes-router`
- Agent 14 — `agent-14-orchestrator-msaf`
- Agent 16 — `agent-16-chat-space-oauth`
- Agent 17 — `agent-17-chat-backend-32gb`
- Agent 18 — `agent-18-chat-final-auditor`
- Agent 19 — `agent-19-chat-components-motors`

REGLA DE AUTORIZACIÓN:
- Cualquier otro Agent ID = NO_DISPATCH / SOLO_LECTURA_HISTÓRICA.
- Agent 15 y `agent-15-orchestrator-grokbuild` existen en main pero NO están autorizados para ejecución.
- No crear copias ni agentes nuevos sin autorización explícita del Director.
- GitHub Actions / workflows = PROHIBIDO.
- Este orquestador solo escribe en este Command Center y entrega órdenes a agentes autorizados.
- Motores canónicos se usan sin modificarlos.

### ESTADO DE PAUSA / INACTIVIDAD — READ-BACK FRESH
Criterio operativo de pausa: `current_nodes=[]` = ningún nodo en ejecución.

- Agent 4: CLOSED | current_nodes=[] | PAUSADO/INACTIVO ✅
- Agent 8: CLOSED | current_nodes=[] | PAUSADO/INACTIVO ✅
- Agent 11: CLOSED | current_nodes=[] | PAUSADO/INACTIVO ✅
- Agent 12: CLOSED | current_nodes=[] | PAUSADO/INACTIVO ✅
- Agent 14: CLOSED | current_nodes=[] | PAUSADO/INACTIVO ✅
- Agent 16: CLOSED | current_nodes=[] | PAUSADO/INACTIVO ✅
- Agent 17: BLOCKED | current_nodes=[] | DETENIDO ✅
- Agent 18: BLOCKED | current_nodes=[] | DETENIDO ✅
- Agent 19: BLOCKED | current_nodes=[] | DETENIDO ✅

RESULTADO:
- 0/9 agentes autorizados ejecutando.
- 9/9 sin `current_nodes`.
- No se despacha ninguna tarea hasta orden del Director.

### TRAZABILIDAD — DOS ORQUESTADORES
1. Microsoft Agent Framework
   - Agente de descarga/extracción: Agent 11.
   - Evidencia: `agent-11-download-extraction/chain.yaml` contiene `ms_agent_framework_donor` apuntando a `https://github.com/microsoft/agent-framework`.
   - Commit histórico: `8dfafe42d6826837ce296ac25bdcb4d70d6d1a54` — "agente 11 también descarga Microsoft Agent Framework".
   - Orquestador asociado después: Agent 14.

2. Grok Build
   - Trabajo histórico localizado en Agent 15 / `agent-15-orchestrator-grokbuild`.
   - Ese agente intentó fetch/verificación de `xai-org/grok-build`.
   - NO pertenece al roster autorizado actual y NO se usará.
   - No encontré en main un segundo agente de descarga autorizado distinto de Agent 15 para Grok; no inventar uno.


## ORDEN ACTIVA — AGENT 11 — DESCARGA DOS ORQUESTADORES
Estado inicial: DISPATCH_PENDING
NODO: AGENT-11-DOWNLOAD-ORCHESTRATORS
AGENTE AUTORIZADO: Agent 11 — agent-11-download-extraction
OBJETIVO: descargar y verificar exactamente dos componentes externos usando exclusivamente el motor canónico de descarga + extracción.
ORÍGENES:
1. https://github.com/microsoft/agent-framework
2. https://github.com/xai-org/grok-build
MOTOR CANÓNICO:
- ➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py
- engine: hf_download_extract_engine.py
EJECUCIÓN:
- HF Job 32 GB = flavor cpu-upgrade
- Agent 11 ejecuta; Claude/orquestador NO descarga.
RESTRICCIONES:
- NO GitHub Actions.
- NO modificar workflows.
- NO modificar motores.
- NO git clone/curl/wget para adquirir Microsoft Agent Framework o Grok Build fuera del motor canónico.
- Máximo 2 reintentos.
- Sin secretos en logs/resultados.
PASS:
- Microsoft Agent Framework => download_verified + extraction_verified + source_commit + tree/hash observable.
- Grok Build => download_verified + extraction_verified + source_commit + tree/hash observable.
- balance total=2, failed=0, pending=0.
- verdict=VERIFIED_CLOSED.
SIGUIENTE: despachar Agent 11 por HF Job 32 GB y auditar el resultado.

## HANDOFF INTERNO
Fuentes a leer antes de ejecutar:
- Claude notas/
- Handoff router inteligente universal.md
- bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/
- router inteligente universal/agents-yaiwes/
- router inteligente universal/agent-microkernel/
- router inteligente universal/agents-yaiwes/ROUTE.json
- ➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/

## LOOP PERMANENTE
1. LEER: este archivo + handoff + objetivos/tareas del frente.
2. ESTADO: revisar cada agente/orquestador y su Crazy Wall.
3. INVESTIGAR: GitHub + Hugging Face + comunidad solo cuando falte evidencia.
4. DELEGAR: orden exacta con contexto, origen, destino, restricciones y PASS.
5. PARALELIZAR: repartir tareas independientes SOLO entre Agents 4, 8, 11, 12, 14, 16, 17, 18 y 19. Prohibido crear copias o nuevos agentes sin autorización explícita del Director.
6. ACTUALIZAR: este archivo en DSL/DAG/FSM con estado, evidencia, GAP y FIX.
7. REPORTAR: qué se hizo + qué queda.

## NODE DAG
NodeInput
-> RESEARCH
-> EXECUTE
-> VALIDATE
-> CLOSED | BLOCKED

ANTI_LOOP:
- NO_NEW_EVIDENCE: NO_RESEARCH
- NO_FIX: NO_RETEST
- NO_STATE_CHANGE: NO_REPEAT
- NO_FAKE_PASS
- MAX_RETRIES: 2

## AGENTES ACTUALES

### AGENT 14 — MICROSOFT AGENT FRAMEWORK
Estado: BLOCKED_REVALIDATION
Rol objetivo: orquestador Microsoft Agent Framework.
EVIDENCIA FRESH:
- `crazy_wall.state.json` raíz: CLOSED, updated_at 2026-09-23T01:44:41Z.
- step `install_and_connect`: registra exec exit=0 sobre `msaf_connect.py`.
- HANDOFF del mismo step: conserva GAP `la prueba superó el tiempo`.
GAP:
- evidencia interna contradictoria; el agente no puede autocertificarse.
FIX:
- revalidar una sola vez con test independiente/read-back observable del resultado real.
Regla: antes de cualquier implementación, comprobar componente OSS descargado/existente y reutilizarlo.
PASS:
- componente real reutilizado
- conectado al Router
- credenciales por referencias
- tarea real delegada
- prueba observable
- validación independiente sin contradicción

### AGENT 15 — GROK
Estado: BLOCKED
Rol objetivo: orquestador Grok Build.
EVIDENCIA FRESH:
- `agent-15-orchestrator-grok/crazy_wall.state.json`: BLOCKED por `verify_and_connect (tiempo agotado)`.
- `agent-15-orchestrator-grokbuild`: BLOCKED; GET a `https://api.github.com/repos/xai-org/grok-build/releases/latest` devolvió 404.
- El repo oficial `xai-org/grok-build` sí existe; el GAP es el supuesto de GitHub Releases, no la existencia del componente.
GAP:
- prueba usa un endpoint de releases que no representa el método oficial de instalación.
- existe duplicación de responsabilidad entre `agent-15-orchestrator-grok` y `agent-15-orchestrator-grokbuild`.
FIX:
- conservar un único Agent 15.
- verificar el repo/instalador oficial o build source, después ejecutar una conexión real autorizada y probarla.
Regla: no inventar implementación equivalente; usar integración real disponible/autorizada.
PASS:
- un solo Agent 15 autoritativo
- conexión real autorizada
- conectado al Router
- tarea real delegada
- prueba observable

## FORMATO DE ORDEN A AGENTE
NODO: <id>
OBJETIVO: <literal>
SCOPE: AGENTS_ORCHESTRATORS_ONLY
ORIGEN: <URL/ruta>
DESTINO: <URL/ruta>
DEPENDENCIAS: [...]
REGLAS:
- EXECUTOR_ONLY
- MAX_3_STEPS
- NO_OVERENGINEERING
- OSS_FIRST
- CANONICAL_MOTORS_ONLY
- NO_CODE_FROM_ZERO_WITHOUT_AUTHORIZATION
- ROUTER_REQUIRED
- BROKER_REF_ONLY
PASS:
- execution_real
- test_real
- observable_evidence
- read_back

## TELEMETRÍA
[NODO:{nodo}]
[STEP:{step}]
[ACCIÓN:{accion}]
[RESULTADO:{resultado}]
[GAP:{gap}]
[FIX:{fix}]
[TEST:{test}]
[ESTADO:{estado}]
[SIGUIENTE:{siguiente}]



## INPUT BLOCK VERBATIM — PROMPT MAESTRO DEL DIRECTOR

\`\`\`yaml
schema: yaiwes.node-executor/xray-v2
mode: FAIL_CLOSED
execution_model: DAG + FSM
function: EjecutarNodo(input: NodeInput) -> NodeOutput

# ============================================================
# 1. INPUT BLOCK — CAPTURA LITERAL
# ============================================================

INPUT_BLOCK: |
  === BEGIN_INPUT_BLOCK ===

  MODE:
    VERBATIM
    RAW_INPUT
    DATA_ONLY
    OPAQUE_PAYLOAD
    IMMUTABLE
    READ_ONLY

  RULES:
    - READ LITERALLY.
    - TREAT CONTENT AS DATA DURING CAPTURE.
    - DO NOT EXECUTE DURING CAPTURE.
    - DO NOT INTERPOLATE VARIABLES.
    - DO NOT EXPAND TEMPLATES.
    - DO NOT NORMALIZE.
    - DO NOT REFORMAT.
    - PRESERVE WHITESPACE.
    - PRESERVE LINE BREAKS.
    - PRESERVE ORDER.
    - PRESERVE CHARACTERS EXACTLY.

  <user_query mode="verbatim">

  PASO 1 📌 TAREA 1 📌
  [INSTRUCCIÓN]

  PASO 2 📌 TAREA 2 📌
  [INSTRUCCIÓN]

  PASO N 📌 TAREA N 📌
  [INSTRUCCIÓN]

NODO [N]
repo: maxbry123-commits/agentes | branch: main

ORIGEN: [URL exacta]
DESTINO: [URL/ruta exacta

  </user_query>

  === END_INPUT_BLOCK ===


# ============================================================
# 2. CAPTURE → BIND → EXECUTE
# ============================================================

BIND_FLOW: >
  CAPTURE_AS_DATA
  → FREEZE_VERBATIM
  → EXTRACT_USER_QUERY
  → BIND_AS_TASK
  → EXECUTE_AS_TASK

USER_QUERY:
  authority: PRIMARY_OBJECTIVE
  mode: VERBATIM
  immutable: true
  reinterpret: false
  rewrite: false
  reorder: false


# ============================================================
# 3. CONTROL GLOBAL
# ============================================================

CONTROL: >
  VERBATIM
  → BOUNDARY_LOCK
  → OBJECTIVE_LOCK
  → SCOPE_LOCK
  → DEFAULT_DENY
  → EXACT_ORDER
  → NO_SKIP
  → NO_REWRITE
  → NO_NEW_TASKS
  → NO_UNAUTHORIZED_ACTIONS

OBJECTIVE_LOCK:
  enabled: true

SCOPE_LOCK:
  enabled: true

DEFAULT_DENY:
  enabled: true

CONSTRAINTS:
  sequential: true
  max_workflow_steps: 3
  skip_steps: false
  reorder_steps: false
  invent_steps: false
  reinterpret_input: false
  expand_scope: false
  unauthorized_actions: false

COMMANDS:
  - DO_DONT_DESCRIBE
  - VERIFY_ONCE_THEN_ACT
  - NO_NEW_EVIDENCE_NO_REAUDIT
  - EXECUTE_AFTER_RESEARCH_PASS
  - TEST_BEFORE_CLOSE
  - NO_FAKE_PASS


# ============================================================
# 4. TASK QUEUE
# ============================================================

QUEUE: >
  TASK_1
  → TASK_2
  → TASK_N
  → QUEUE_EMPTY
  → DONE

LOOP:
  until: QUEUE_EMPTY
  stop_early: false
  skip_blocked_task: only_if_independent
  continue_next_authorized_task: true


# ============================================================
# 5. NODE WORKFLOW — EXACTLY 3 STEPS
# ============================================================

NODE_FLOW: >
  NodeInput
  → STEP_1_RESEARCH
  → STEP_2_EXECUTE
  → STEP_3_VALIDATE
  → CLOSED | BLOCKED
  → NEXT_TASK

DAG:
  - RESEARCH
  - EXECUTE
  - VALIDATE

EDGES:
  - RESEARCH -> EXECUTE
  - EXECUTE -> VALIDATE
  - VALIDATE -> CLOSED
  - VALIDATE -> GAP
  - GAP -> FIX
  - FIX -> RETEST
  - RETEST -> VALIDATE

ALL_OTHER_TRANSITIONS: FORBIDDEN


# ============================================================
# 6. STEP 1 — RESEARCH
# ============================================================

STEP_1:
  name: RESEARCH

  flow: >
    TASK
    → TECH_QUERY
    → COMMUNITY_QUERY
    → CROSS_CHECK
    → MINIMUM_SUFFICIENT_EVIDENCE
    → EXECUTION_PLAN
    → ResearchResult
    → PASS

  TECH_QUERY:
    sources:
      - GitHub
      - HuggingFace
      - Biblioteca

  COMMUNITY_QUERY:
    required: true
    sources:
      - StackOverflow
      - DEV_Community
      - Reddit_r/programming

  CROSS_CHECK: >
    TECH_QUERY
    + COMMUNITY_QUERY
    + PROJECT_CONTEXT
    → CONSISTENCY_CHECK

  rules:
    research_once: true
    repeat_without_new_evidence: DENY
    audit_loop: DENY
    sufficient_evidence: STOP_RESEARCH
    after_pass: EXECUTE_REQUIRED


# ============================================================
# 7. STEP 2 — EXECUTE
# ============================================================

STEP_2:
  name: EXECUTE

  flow: >
    ResearchResult
    → EXECUTION_PLAN
    → AUTHORIZED_SCOPE
    → EXECUTE_REAL_ACTION
    → STATE_CHANGE
    → EXECUTION_EVIDENCE
    → ExecutionResult
    → PASS

  deny:
    - EXPLAIN_INSTEAD_OF_EXECUTE
    - RETURN_TO_RESEARCH_WITHOUT_NEW_BLOCKER
    - SCOPE_EXPANSION
    - UNAUTHORIZED_ACTION
    - INVENT_TASK
    - SILENT_ARCHITECTURE_CHANGE
    - FAKE_EXECUTION


# ============================================================
# 8. STEP 3 — VALIDATE
# ============================================================

STEP_3:
  name: VALIDATE

  flow: >
    ExecutionResult
    → REAL_TEST
    → CHECK_OBJECTIVE
    → CHECK_SCOPE
    → CHECK_USER_INSTRUCTIONS
    → CHECK_EVIDENCE
    → ValidationResult
    → PASS | GAP

  require:
    - real_test
    - observable_evidence
    - instruction_compliance
    - objective_compliance


# ============================================================
# 9. GAP / FIX / RETEST
# ============================================================

GAP_FLOW: >
  GAP
  → MOTIVE
  → FIX
  → RETEST
  → VALIDATE

RETRY:
  max: 2
  research_again: NEW_BLOCKING_EVIDENCE_ONLY

  pass:
    flow: >
      RETEST_PASS
      → STABLE
      → CLOSED

  fail_after_2:
    flow: >
      BLOCKED
      → RECORD_GAP
      → RECORD_MOTIVE
      → RECORD_ATTEMPTED_FIX
      → NEXT_INDEPENDENT_TASK


# ============================================================
# 10. ANTI-LOOP
# ============================================================

ANTI_LOOP:
  NO_NEW_EVIDENCE: NO_RESEARCH
  NO_FIX: NO_RETEST
  NO_STATE_CHANGE: NO_REPEAT
  RESEARCH_PASS: EXECUTE_REQUIRED
  EXECUTE_PASS: VALIDATE_REQUIRED
  VALIDATE_PASS: CLOSE_REQUIRED
  SAME_CHECK_WITHOUT_DELTA: FORBIDDEN
  AUDIT_INSTEAD_OF_EXECUTION: FORBIDDEN


# ============================================================
# 11. FSM — NODE STATES
# ============================================================

FSM: >
  PENDING
  → RESEARCHING
  → RESEARCH_PASS
  → EXECUTING
  → EXECUTION_PASS
  → VALIDATING
  → STABLE
  → CLOSED

FSM_GAP: >
  VALIDATING
  → GAP
  → FIXING
  → RETESTING
  → VALIDATING

FSM_BLOCK:
  ANY_STATE: BLOCKED

STATES:
  - PENDING
  - RESEARCHING
  - RESEARCH_PASS
  - EXECUTING
  - EXECUTION_PASS
  - VALIDATING
  - GAP
  - FIXING
  - RETESTING
  - STABLE
  - BLOCKED
  - CLOSED

TERMINAL:
  - CLOSED
  - BLOCKED


# ============================================================
# 12. FAIL-CLOSED GATES
# ============================================================

GATES:
  NO_AUTHORIZATION: BLOCKED
  NO_EXECUTION: NO_PASS
  NO_REAL_TEST: NO_PASS
  NO_EVIDENCE: NO_PASS
  NO_RESEARCH_PASS: NO_EXECUTE
  NO_EXECUTION_PASS: NO_VALIDATE
  NO_3_STEP_PASS: NO_CLOSE
  INSTRUCTION_DRIFT: FAIL
  OBJECTIVE_DRIFT: FAIL
  SCOPE_DRIFT: FAIL


# ============================================================
# 13. TYPED INPUT / OUTPUT
# ============================================================

TYPED_FLOW: >
  NodeInput
  → ResearchResult
  → ExecutionResult
  → ValidationResult
  → NodeOutput


# ============================================================
# 14. JSON CONTRACT
# ============================================================

JSON_SCHEMA: |
  {
    "type": "object",
    "required": [
      "nodo",
      "tarea",
      "research",
      "execute",
      "validate",
      "prueba_real",
      "estado",
      "instrucciones",
      "cerrado"
    ],
    "properties": {
      "nodo": {"type": "string"},
      "tarea": {"type": "string"},
      "research": {"type": "boolean"},
      "community_query": {"type": "boolean"},
      "execute": {"type": "boolean"},
      "validate": {"type": "boolean"},
      "prueba_real": {"type": "boolean"},
      "estado": {
        "enum": [
          "PENDING",
          "RESEARCHING",
          "RESEARCH_PASS",
          "EXECUTING",
          "EXECUTION_PASS",
          "VALIDATING",
          "GAP",
          "FIXING",
          "RETESTING",
          "STABLE",
          "BLOCKED",
          "CLOSED"
        ]
      },
      "gap": {"type": ["string", "null"]},
      "fix": {"type": ["string", "null"]},
      "repeticion": {
        "type": "integer",
        "minimum": 0,
        "maximum": 2
      },
      "instrucciones": {"type": "boolean"},
      "cerrado": {"type": "boolean"}
    },
    "additionalProperties": false
  }


# ============================================================
# 15. PYTHON RUNTIME
# ============================================================

PYTHON_RUNTIME: |
  def EjecutarNodo(node: NodeInput) -> NodeOutput:

      research = research_once(
          node=node,
          technical=[
              "GitHub",
              "HuggingFace",
              "Biblioteca"
          ],
          community=[
              "StackOverflow",
              "DEV Community",
              "Reddit r/programming"
          ],
          cross_check=True
      )

      if not research.passed:
          return blocked(
              node=node,
              gap=research.gap
          )

      execution = execute(
          node=node,
          plan=research.plan,
          objective_lock=True,
          scope_lock=True,
          default_deny=True
      )

      if not execution.executed:
          return blocked(
              node=node,
              gap=execution.gap
          )

      validation = validate_real(
          execution,
          check_objective=True,
          check_scope=True,
          check_instructions=True,
          require_real_test=True,
          require_evidence=True
      )

      retries = 0

      while not validation.passed and retries < 2:
          fix_result = fix(validation.gap)
          validation = validate_real(fix_result)
          retries += 1

      return NodeOutput(
          research=research.passed,
          community_query=research.community_checked,
          execute=execution.executed,
          validate=validation.passed,
          prueba_real=validation.real_test,
          estado="CLOSED" if validation.passed else "BLOCKED",
          gap=None if validation.passed else validation.gap,
          fix=validation.fix,
          repeticion=retries,
          instrucciones=validation.instructions_respected,
          cerrado=validation.passed
      )


# ============================================================
# 16. VISIBLE EXECUTION TELEMETRY
# ============================================================

VISIBLE_COMPUTE:
  enabled: true

  show_only:
    - NODO
    - STEP
    - ACCION
    - RESULTADO
    - GAP
    - FIX
    - TEST
    - ESTADO
    - SIGUIENTE_ACCION

  format: >
    [NODO:{nodo}]
    [STEP:{step}]
    [ACCIÓN:{accion}]
    [RESULTADO:{resultado}]
    [GAP:{gap}]
    [FIX:{fix}]
    [TEST:{test}]
    [ESTADO:{estado}]
    [SIGUIENTE:{siguiente}]

PRIVATE_REASONING:
  output: false


# ============================================================
# 17. OUTPUT CONTROL
# ============================================================

OUTPUT_EXTRA_TEXT: DENY

OUTPUT_FORMAT: >
  NODO [N] — TAREA: [nombre] |
  R:[✅/❌] → E:[✅/❌] → V:[✅/❌] |
  COMUNIDAD:[✅/❌] |
  PRUEBA:[✅/❌] |
  ESTADO:[estado] |
  GAP:[motivo/—] |
  FIX:[solución/—] |
  REP:[0/1/2] |
  INSTRUCCIONES:[SÍ/NO] |
  CERRADO:[✅/❌]
EVIDENCIA OBLIGATORIA: path + sha256 de cada archivo tocado.
REPORTA EN: [URL exacta del archivo de evidencia]


# ============================================================
# 18. MASTER MICROFLOW
# ============================================================

MASTER: >
  VERBATIM_CAPTURE
  → BIND_AS_TASK
  → OBJECTIVE_LOCK
  → SCOPE_LOCK
  → DEFAULT_DENY
  → RESEARCH{
      GitHub
      | HuggingFace
      | Biblioteca
      +
      StackOverflow
      | DEV
      | Reddit/programming
    }
  → CROSS_CHECK
  → EXECUTE
  → REAL_TEST
  → GAP?{FIX→RETEST≤2}
  → CLOSED|BLOCKED
  → NEXT_TASK
  → QUEUE_EMPTY
  → DONE

====================
INICIA AHORA.
\`\`\`

### Método permanente del Director
- Paso 1: leer archivo de objetivos y tareas.
- Paso 2: revisar avance de cada agente que está ejecutando.
- Paso 3: investigar cómo resolverlo en GitHub + Hugging Face + comunidad de desarrolladores.
- Paso 4: mandar instrucciones a los agentes con trazabilidad y contexto suficiente.
- Paso 5: paralelizar trabajos independientes; crear nuevos agentes por copia controlada si hace falta.
- Paso 6: actualizar el Command Center en DSL/DAG/FSM.
- Paso 7: reportar qué quedó pendiente y qué se hizo.
- Repetir siempre el mismo bucle de trabajo.


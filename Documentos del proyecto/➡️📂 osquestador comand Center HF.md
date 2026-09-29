# ➡️📂 OSQUESTADOR COMAND CENTER HF

Repo: maxbry123-commits/router-universal-router-inteligente-
Branch: main
Schema: yaiwes.node-executor/xray-v2
Mode: FAIL_CLOSED
Scope: HUGGING FACE ONLY
Updated: 2026-09-22 22:02 America/Bogota

## OBJETIVO
Dirigir exclusivamente el frente Hugging Face sin mezclar tareas de otros proyectos.

## REGLAS PERMANENTES
- SCOPE_LOCK = HF_ONLY.
- Claude/orquestador dirige y audita; los agentes ejecutan.
- Cero sobreingeniería.
- Máximo 3 pasos por tarea: REUTILIZAR/ADAPTAR -> CABLEAR/EJECUTAR -> PROBAR.
- Reutilizar componentes OSS antes de escribir código nuevo.
- Componentes externos: solo motores canónicos de main.
- Prohibido construir desde cero una solución equivalente sin autorización explícita del Director.
- Código nuevo únicamente para adaptar, mejorar, integrar o cablear componentes.
- Jobs del proyecto: solo hardware autorizado de 32 GB RAM.
- No declarar PASS sin ejecución real + evidencia observable.
- Credenciales por referencias/broker; nunca exponer secretos.

## HANDOFF INTERNO
Fuentes a leer antes de ejecutar:
- Claude notas/
- Handoff router inteligente universal.md
- bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/
- router inteligente universal/integration/huggingface/
- router inteligente universal/agents-yaiwes/
- ➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/

## LOOP PERMANENTE
1. LEER: este archivo + handoff + objetivos/tareas HF.
2. ESTADO: revisar agentes HF y Jobs activos.
3. INVESTIGAR: GitHub + Hugging Face + comunidad solo si falta evidencia.
4. DELEGAR: entregar objetivo, origen, destino, restricciones y PASS.
5. PARALELIZAR: tareas independientes en agentes separados sin pisarse.
6. ACTUALIZAR: este archivo con estado, evidencia, GAP, FIX y siguiente acción.
7. REPORTAR: qué se hizo + qué falta.

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

## COLA DE TRABAJO HF
- Inventariar Jobs activos y validar RAM.
- Mantener regla 32 GB RAM.
- Validar Storage Buckets/volúmenes autorizados.
- Validar modelos/repos/weights remotos necesarios.
- Validar endpoints/puertos/health cuando una tarea los use.
- Registrar coste/estado/resultado sin lanzar recursos no autorizados.
- Mantener trazabilidad en Crazy Wall/Handoff.

## FORMATO DE ORDEN A AGENTE
NODO: <id>
OBJETIVO: <literal>
SCOPE: HF_ONLY
ORIGEN: <URL/ruta>
DESTINO: <URL/ruta>
REGLAS:
- EXECUTOR_ONLY
- MAX_3_STEPS
- NO_OVERENGINEERING
- OSS_FIRST
- CANONICAL_MOTORS_ONLY
- NO_CODE_FROM_ZERO_WITHOUT_AUTHORIZATION
- 32GB_ONLY
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



## ORQUESTADOR STARTUP SNAPSHOT — 2026-09-22

[NODO:BOOT-HF]
[STEP:VALIDATE]
[ACCIÓN:Read-back Command Center + Handoff HF + agentes HF + Jobs RUNNING]
[RESULTADO:Scope HF_ONLY cargado. 10 Jobs RUNNING visibles; todos flavor cpu-upgrade. Agentes revisados: agent-6-hf-nodes=CLOSED, agent-7-llama-hf=CLOSED con GAP textual de health, agent-9-models-catalog=CLOSED con GAP textual de health, agent-10-model-install=CLOSED con evidencia RUNNING_HEALTHY.]
[GAP:1) agent-7 y agent-9 tienen status CLOSED pero conservan GAP que contradice cierre FAIL_CLOSED. 2) Jobs activos usan curl directo para obtener GGUF; contradice CANONICAL_MOTORS_ONLY / no downloader propio. 3) Handoff mantiene GAP_AUTH_REMOTE_INFERENCE y GAP_ADAPTER_REGISTRY_SCHEMA abiertos.]
[FIX:No aplicado en startup. Requiere delegación explícita a agentes y prueba real.]
[TEST:HF Jobs ps status=RUNNING + inspect job 6ab3198e51992417dfcd4e26 => RUNNING, flavor cpu-upgrade. agent-10 crazy_wall registra GET /health 200 como evidencia previa.]
[ESTADO:RESEARCH_PASS]
[SIGUIENTE:Reconciliar primero contradicción CLOSED/GAP de agent-7 y agent-9; después reemplazar rutas curl por motor/mount canónico sin detener Jobs existentes sin orden del Director.]

Regla de este takeover:
- No se lanzó, canceló ni modificó ningún Job durante este startup.
- No se tocaron proyectos fuera de HF_ONLY.
- No se declara cierre global.

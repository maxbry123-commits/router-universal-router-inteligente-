# ➡️📂 OSQUESTADOR COMAND CENTER AGENTES-OSQUESTADORES

Repo: maxbry123-commits/router-universal-router-inteligente-
Branch: main
Schema: yaiwes.node-executor/xray-v2
Mode: FAIL_CLOSED
Scope: AGENTES + ORQUESTADORES ONLY
Updated: 2026-09-22 22:02 America/Bogota

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
- Agent 14 — orquestador Microsoft Agent Framework: ⚪ SIN_ESTADO. Aún no está ejecutando una cadena.
- Agent 15 — orquestador Grok: ⚪ SIN_ESTADO.

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
5. PARALELIZAR: repartir tareas independientes; crear copia de agente solo si es necesario.
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
Estado: SIN_ESTADO
Rol objetivo: orquestador Microsoft Agent Framework.
Regla: antes de cualquier implementación, comprobar componente OSS descargado/existente y reutilizarlo.
No ejecutar una cadena hasta recibir objetivo concreto y handoff.
PASS futuro:
- componente real reutilizado
- conectado al Router
- credenciales por referencias
- tarea real delegada
- prueba observable

### AGENT 15 — GROK
Estado: SIN_ESTADO
Rol objetivo: orquestador Grok.
Regla: no inventar implementación equivalente; usar integración real disponible/autorizada.
No ejecutar una cadena hasta recibir objetivo concreto y handoff.
PASS futuro:
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

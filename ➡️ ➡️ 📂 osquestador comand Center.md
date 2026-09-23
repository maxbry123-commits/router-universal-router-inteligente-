# ➡️ ➡️ 📂 OSQUESTADOR COMAND CENTER — MEMORIA PERMANENTE

**Repo:** https://github.com/maxbry123-commits/router-universal-router-inteligente-  
**Branch:** `main`  
**Schema maestro:** `yaiwes.node-executor/xray-v2`  
**Modo:** `FAIL_CLOSED`  
**Execution model:** `ORCHESTRATOR_LOOP_7 + NODE_DAG_3 + FSM`  
**Rol permanente de este archivo:** memoria operativa, handoff interno, cola de objetivos/tareas, estado de agentes, trazabilidad y gates de cierre.  
**Última actualización inicial:** 2026-09-22 21:15 America/Bogota.

---

## REGLA ANTI-SOBREINGENIERÍA

- Usar la solución mínima suficiente.
- Máximo 3 pasos por tarea: **REUTILIZAR/ADAPTAR → CABLEAR → PROBAR**.
- No crear capas, abstracciones, agentes, servicios, archivos o frameworks extra si no son necesarios.
- No investigar de nuevo si ya existe evidencia suficiente.
- No escribir código equivalente desde cero cuando ya existe componente OSS o código reutilizable.
- Si el objetivo puede cerrarse con un cambio pequeño, está prohibido ampliarlo.

## REGLA GLOBAL PARA TODOS LOS AGENTES

- **REGLA PERMANENTE OSS/MOTORES:** antes de escribir código nuevo, buscar y reutilizar componentes existentes.
- Si un componente externo hace falta, adquirirlo **solo** con los motores canónicos de `main`.
- **PROHIBIDO** construir desde cero una solución equivalente sin autorización explícita del Director.
- Código nuevo permitido únicamente para **adaptar, mejorar, integrar o cablear** componentes existentes.
- GitHub Actions puede arrancar el harness del agente, pero **NO** reemplaza los motores como mecanismo de adquisición.
- Si no existe componente adecuado o el motor no puede usarlo: `GAP: COMPONENT_OR_AUTHORIZATION_REQUIRED`.
- Esta regla se aplica a **todos los agentes presentes y futuros**.

## 0. LEY DE AUTORIDAD

1. **El Director define objetivo, prioridad y restricciones.**
2. **Claude/orquestador audita, investiga, decide el reparto y da las órdenes.**
3. **Los agentes ejecutan. Los agentes NO auditan al Director ni deciden el cierre global.**
4. **No cambiar, resumir, reordenar ni reinterpretar una instrucción VERBATIM.**
5. **No PASS sin ejecución real, prueba real y evidencia observable.**
6. **No crear componentes desde cero cuando existe un componente OSS reutilizable.**
7. **Ley permanente de componentes:** `MOTOR → DESCARGAR → EXTRAER → EDITAR/ADAPTAR → CABLEAR → INCORPORAR → READ-BACK`.
8. **Adquisición de componentes externos:** exclusivamente por los motores canónicos de `main`. GitHub Actions puede arrancar el harness del agente, pero **NO puede ser el mecanismo de descarga/instalación/adquisición del componente**. Prohibidos para adquisición directa: `git clone`, `git fetch`, `curl`, `wget`, downloader nuevo, `pip/npm/pnpm/yarn` para traer código fuente.
9. **Motores canónicos son inmutables.**
10. **Open WebUI es la base obligatoria del chat.** El HTML propio existente NO es la solución final.
11. **Conservar el código adicional ya creado:** Chat MVP, Router, Jobs, Vault/Secret Bank, GitHub, documentos, agentes, selector, Crazy Wall/handoff, Archivos/Memoria y backend. Se reutiliza/adapta/cablea sobre Open WebUI; no se borra ni se recrea desde cero.
12. **Claude es el único auditor operativo actual del chat.**
13. **Credenciales:** los agentes reciben referencias/uso mediante banco/broker; nunca valores secretos en prompts, handoffs o logs.
14. **Trabajo actual prioritario:** cerrar CHAT YAIWES. Jev, TimesFM, modelos locales, fichas y demás frentes quedan `PAUSED` salvo orden explícita del Director.

---

## 1. HANDOFF INTERNO — FUENTES DE VERDAD

Leer SIEMPRE antes de dar una orden:

- `Claude notas/00-LEEME-PRIMERO.md`
- `Claude notas/AUDITORIA-INPUTS-2026-09-21.md`
- `Claude notas/HANDOFF-COMPLETO-2026-09-22.md`
- `Claude notas/DSL-FABLES-yaiwes-node-executor-xray-v2.md`
- `Claude notas/PLAN-MAESTRO-CHAT-MVP.md`
- `Claude notas/PLAN-ANEXO-A-SECRET-BANK.md`
- `Claude notas/PLAN-ANEXO-B-STORAGE-Y-CHAT-OPEN-SOURCE.md`
- `Claude notas/HANDOFF-MOTORES-COMPONENTES-CHAT-2026-09-22.md`
- `Claude notas/LEY-PERMANENTE-CHAT-COMPONENTES-OSS-2026-09-22.md`
- `Claude notas/ORQUESTADOR-CHAT-LOOP-2026-09-22-1956-COLOMBIA.md`
- `router inteligente universal/agents-yaiwes/WATCHDOG/STATUS.md`
- `bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/STATE.json`
- `bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/CHECKPOINT.json`
- `bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/BITACORA-CRAZY-WALL.md`
- `Handoff router inteligente universal.md`

### Regla de cableado
`INPUT VERBATIM → COMMAND CENTER → ORDEN DEL ORQUESTADOR → AGENTE → CRAZY WALL DEL AGENTE → PRUEBA → COMMAND CENTER`.

Este archivo NO sustituye los INPUT verbatim; los **apunta y vincula**. El texto exacto sigue siendo autoritativo en cada archivo `INPUT*VERBATIM*.md`.

---

## 2. ÍNDICE 1 A 1 DE INPUTS VERBATIM — HALLAZGO/OBJETIVO

Cada fila es una fuente que debe releerse literalmente antes de ejecutar una tarea dentro de su alcance.

| Fuente verbatim | Hallazgo / objetivo operativo |
|---|---|
| `INPUT-BLOCKS-01-04-VERBATIM.md` | Recuperar contexto desde GitHub/Claude notas; seguir instrucciones 1 a 1; validar antes de actuar. |
| `INPUT-BLOCK-05-chat-storage-grupos-VERBATIM.md` | Chat + almacenamiento + grupos + métodos; registrar instrucciones textuales y mantener trazabilidad. |
| `INPUT-BLOCK-06-VERBATIM.md` | Chat MVP, cuentas, secretos y decisiones; credenciales redactadas en repo público. |
| `INPUT-BLOCK-06-secret-bank-stack-plan-VERBATIM.md` | Crear banco propio de secretos y stack persistente; validar que todas las instrucciones estén anotadas 1 a 1. |
| `INPUT-BLOCK-07-VERBATIM.md` | Usar pesos remotos HF directamente; evitar copias persistentes innecesarias. |
| `INPUT-BLOCK-08-VERBATIM.md` | Identidades/cuentas GitHub y trazabilidad de cuentas reales. |
| `INPUT-VERBATIM-2026-09-20-b-claves-nvidia-plantilla.md` | Claves NVIDIA + contrato node-executor; anotar antes de ejecutar. |
| `INPUT-VERBATIM-2026-09-20-c-formato-loop-nvidia.md` | Salida simple/corta; evitar explicación innecesaria; no repetir trabajo. |
| `INPUT-VERBATIM-2026-09-20-c-formato-y-nvidia.md` | Misma regla de salida corta + NVIDIA. |
| `INPUT-VERBATIM-2026-09-20-chat-mvp.md` | Decisiones necesarias para cerrar Chat MVP y modelos asociados. |
| `INPUT-VERBATIM-2026-09-20-d-agentes-banco-secretos-nvidia.md` | Agente buscador, agente web, agente descarga/extracción; usar motores y banco. |
| `INPUT-VERBATIM-2026-09-20-e-banco-modelos-vercel-agentes-enchufe.md` | Banco, modelos, agentes y Enchufe Universal; no exponer contraseña/secretos. |
| `INPUT-VERBATIM-2026-09-20-f-banco-nvidia-otro-equipo.md` | Permitir a otro equipo usar claves sin transportar archivos manualmente. |
| `INPUT-VERBATIM-2026-09-21-g-h-handoff-router-picos.md` | Handoff con trazabilidad del router, picos y recuperación por Claude notas. |
| `INPUT-VERBATIM-2026-09-21-i-busqueda-modelos-hf-kit.md` | Motor de búsqueda + investigación/modelos HF + kit para otro equipo. |
| `INPUT-VERBATIM-2026-09-21-j-CORRECCION.md` | Corregir atribución errónea previa; no atribuir al Director texto que no dijo. |
| `INPUT-VERBATIM-2026-09-21-j-definir-router-jev-vercel.md` | Definir antes de ejecutar: router, búsqueda de contexto, Jev/Vercel. |
| `INPUT-VERBATIM-2026-09-21-k-pesos-remotos-nanbeige-microkernels.md` | Cerrar modelos HF/Vercel; remote weights; microkernels; trabajar en paralelo. |
| `INPUT-VERBATIM-2026-09-21-l-agentes-smolagents-vercel-chat-hf.md` | Comparar/usar SmolAgents y agentes; descargar con motores. |
| `INPUT-VERBATIM-2026-09-21-l-opus-cerebras-groq-vercel-chat.md` | Acceso de equipo a claves; Cerebras/Groq funcionales; descargar agentes con motores. |
| `INPUT-VERBATIM-2026-09-21-m-claves-nvidia.md` | Resolver acceso NVIDIA del otro equipo sin fricción. |
| `INPUT-VERBATIM-2026-09-21-n-prioridad-4-microagentes.md` | No salir de la prioridad indicada; 4 microagentes. |
| `INPUT-VERBATIM-2026-09-21-o-smolagents-pocketflow-4-agentes.md` | No cambiar instrucciones sin autorización; usar SmolAgents + PocketFlow como se ordenó. |
| `INPUT-VERBATIM-2026-09-21-p-4-agentes-pocketflow-smolagents.md` | Prioridad: agentes primero y luego delegar; conservar agentes existentes. |
| `INPUT-VERBATIM-2026-09-21-p-agentes-auditar-puente.md` | Delegación de agentes + puente; no desviarse. |
| `INPUT-VERBATIM-2026-09-21-p-agentes-auditar-tokens-vercel.md` | Delegación + revisión de tokens/Vercel dentro del alcance autorizado. |
| `INPUT-VERBATIM-2026-09-21-q-cadena-de-pasos-chat-hf.md` | Evitar procesos pegados/repetidos; encadenar pasos y continuar solo con delta. |
| `INPUT-VERBATIM-2026-09-21-r-auditor-meta-agents-watchdog.md` | Estado de agentes, watchdog/supervisión y registro verbatim antes de continuar. |
| `INPUT-VERBATIM-2026-09-21-s-tareas-modelos-locales-hoy.md` | Crear lista completa de tareas; llevar objetivos hasta final; fallback local. |
| `INPUT-VERBATIM-2026-09-21-t-espejo-10-procesadores-mvp-delegar.md` | Espejo = compartir mismos pesos; controlar caché/RAM; hasta 10 procesadores HF 32 GB. |
| `INPUT-VERBATIM-2026-09-21-u-auditar-4-pasadas-chat-modelos.md` | Prioridad chat/modelos; revisar INPUTs; lista de funciones y tareas. |
| `INPUT-VERBATIM-2026-09-21-v-claude-audita-el-mismo.md` | **Claude audita él mismo. No delegar auditoría a un agente.** |
| `INPUT-VERBATIM-2026-09-21-w-jev-router-auditoria-estado.md` | Jev en router + revisar faltantes + estado real de agentes/API keys. |
| `INPUT-VERBATIM-2026-09-22-y-3-roles-delegar-watchdog-jev.md` | Separar roles, delegar ejecución, supervisar con watchdog; Jev en su frente. |
| `INPUT-VERBATIM-2026-09-22-z-aa-3-jev-timesfm-ponytail-omniroute.md` | Jev/TimesFM/Ponytail/OmniRoute como frentes separados; no mezclar alcance. |
| `INPUT-VERBATIM-2026-09-22-bb-contrato-xray-v2-watchdog-gpt.md` | Contrato RESEARCH→EXECUTE→VALIDATE, FAIL_CLOSED, anti-loop, máx. 2 reintentos. |
| `INPUT-VERBATIM-2026-09-22-cc-jev-ponytail-5-pasos.md` | Investigación/control de gasto/Jev como capa externa; validar antes de integrar. |
| `INPUT-VERBATIM-2026-09-22-dd-router-yaiwes-timesfm-hrm-busqueda.md` | Router YAIWES + TimesFM/HRM/búsqueda; componentes externos separados. |
| `INPUT-VERBATIM-2026-09-22-ee-deepseek-chat-ficha-aplazada.md` | DeepSeek V4 Flash para agentes del chat; fichas aplazadas hasta cerrar chat. |
| `INPUT-VERBATIM-2026-09-22-ff-24-casos-hrm-lfm-groq-inventario.md` | 24 casos de prueba para routing/búsqueda/caché/loops/presupuesto/DAG. |
| `INPUT-VERBATIM-2026-09-22-gg-orquestadores-ms-agent-framework-grok.md` | Plantilla para orquestadores y recuperación; mantener trazabilidad completa. |

**Regla:** si aparece un INPUT VERBATIM nuevo, se añade aquí en el mismo ciclo antes de ejecutar su tarea.

---

## 3. OBJETIVO ACTIVO — CHAT YAIWES 100% FUNCIONAL

### Arquitectura objetivo
`Open WebUI OSS → Router/OpenAI-compatible API → Chat MVP/backend existente → proveedores/modelos/agentes → almacenamiento/memoria → Secret Bank`.

### Evidencia de investigación vigente
- Open WebUI soporta backends OpenAI-compatible y espera `/v1/chat/completions`; `/v1/models` es recomendado para discovery:  
  https://docs.openwebui.com/getting-started/quick-start/connect-a-provider/starting-with-openai-compatible/
- HF Static Spaces son gratuitos y soportan build estático:  
  https://huggingface.co/docs/hub/main/spaces-sdks-static
- HF Spaces OAuth se activa con `hf_oauth: true`; existe ejemplo cliente con huggingface.js:  
  https://huggingface.co/docs/hub/spaces-oauth
- Comunidad Open WebUI confirma integración con APIs compatibles; usar comunidad solo como apoyo, nunca como autoridad:  
  https://www.reddit.com/r/OpenWebUI/comments/1ix3ozi/  
  https://www.reddit.com/r/OpenWebUI/comments/1ni4rik/

### Ley de implementación
**NO reconstruir el chat desde cero.** Descargar Open WebUI con motores, luego modificar/adaptar/cablear el código existente encima.

---

## 4. COLA ACTIVA — OBJETIVOS Y TAREAS

### O1 — ADQUIRIR OPEN WEBUI POR MOTOR CANÓNICO
**Owner:** `agent-19-chat-components-motors`  
**Estado inicial:** `PENDING / SIN_ESTADO`  
**Fuente:** `Claude notas/HANDOFF-MOTORES-COMPONENTES-CHAT-2026-09-22.md`  
**Origen:** https://github.com/open-webui/open-webui  
**Destino explícito:** `router inteligente universal/Componente open soure router inteligente universal/open-webui/`  
**PASS:** motor canónico + `VERIFIED_CLOSED` + publicación + read-back + hashes.

### O2 — ADAPTAR OPEN WEBUI CONSERVANDO CÓDIGO ADICIONAL
**Owner:** `agent-16-chat-space-oauth`  
**Estado inicial:** `BLOCKED_BY: O1`  
**Conservar/reusar:** `integration/chat_mvp/chat_ui.html`, Vault panel, Router panel, Jobs panel, fixed_template, crazy_wall_chain, selector, agentes, GitHub, documentos.  
**PASS:** Open WebUI real contiene/cablea esas capacidades; no UI nueva paralela.

### O3 — CABLEAR BACKEND EXISTENTE + ROUTER
**Owner:** `agent-17-chat-backend-32gb`  
**Estado inicial:** `BLOCKED_BY: O1`  
**Reusar:** `router inteligente universal/integration/chat_mvp/` + `integration/huggingface/`.  
**Hardware:** si se usa HF Job, **solo 32 GB RAM** mediante Sheriff.  
**PASS:** backend live + `/v1/models` + `/v1/chat/completions` + mensaje real 200.

### O4 — INCORPORAR ARCHIVOS/MEMORIA Y PANELES EXISTENTES
**Owner:** `agent-18-chat-final-auditor` (nombre histórico; **rol actual = EJECUTOR**, no auditor)  
**Estado inicial:** `BLOCKED_BY: O1`  
**PASS:** Open WebUI incorpora Archivos/Memoria, Secret Bank, Router, Jobs, GitHub, agentes y Crazy Wall sin borrar el código fuente existente.

### O5 — PUBLICACIÓN/OAUTH/SMOKE LIVE
**Owner de ejecución:** agentes de chat asignados por Claude después de O1-O4.  
**Auditor:** Claude/orquestador.  
**PASS mínimo:** URL live + OAuth + login + selector + enviar/recibir mensaje real + reload/reapertura.

### O6 — ALMACENAMIENTO PERSISTENTE DEL CHAT
**Owner:** crear/reasignar agente de chat cuando O1 esté estable.  
**Stack solicitado:** PostgreSQL verdad + Redis caché/locks + Graphiti/FalkorDB + AgentDB + objetos/archivos.  
**Regla:** si falta un componente OSS, pedirlo a `agent-19` y adquirirlo por motores; no escribir sustituto desde cero.  
**PASS:** archivo adjunto persiste y se recupera en chat nuevo/proyecto.

### O7 — SECRET BANK FINAL
**Owner:** agente de chat asignado; Claude audita.  
**Meta:** banco propio cifrado; agentes usan `credential_ref`/broker y nunca ven valores.  
**PASS:** llamada real de proveedor usando broker + no secretos en logs/UI/Redis.

### GATE CHAT_100
`OPENWEBUI_REAL + COMPONENTS_MOTOR_VERIFIED + ROUTER_LIVE + SEND_RECEIVE_LIVE + MODELS_SELECTOR + WITH/WITHOUT_AGENT + GITHUB + DOCUMENTS + FILES_MEMORY + SECRET_BANK + PERSISTENCE + OAUTH/LIVE_URL + CLAUDE_AUDIT_PASS`.

---

## 5. AGENTES DEDICADOS AL CHAT — ESTADO BASE

| Agente | Rol | Estado observado |
|---|---|---|
| `agent-1-chat-hf` | Panel Vault/Router/cableado previo | CLOSED 3/3 — código a conservar |
| `agent-2-chat-hf-smol` | Jobs/plantilla/Crazy Wall previo | CLOSED 3/3 — código a conservar |
| `agent-3-router` | publicación HF anterior | PENDING_VERIFY; smoke previo FAIL; no usar como cierre |
| `agent-16-chat-space-oauth` | adaptar/cablear Open WebUI | SIN_ESTADO; depende O1 |
| `agent-17-chat-backend-32gb` | backend/router live | SIN_ESTADO; depende O1 |
| `agent-18-chat-final-auditor` | **ejecutor** de integración adicional | SIN_ESTADO; depende O1 |
| `agent-19-chat-components-motors` | único adquirente de componentes OSS para chat | SIN_ESTADO; ejecutar O1 |

**Regla:** no trabajar con agentes ajenos al chat mientras CHAT sea la prioridad, salvo que el Director lo ordene.

---

## 6. BUCLE PERMANENTE DEL ORQUESTADOR — SIEMPRE IGUAL

### LOOP_7
1. **📌 PASO 1 — READ:** leer este Command Center, objetivos, tareas, INPUT verbatim y handoffs relacionados.
2. **📌 PASO 2 — AGENT STATUS:** revisar Crazy Wall/estado real de cada agente ejecutor.
3. **📌 PASO 3 — RESEARCH:** investigar cómo resolver cada GAP en GitHub + Hugging Face + Biblioteca + comunidad de desarrolladores (StackOverflow + DEV Community + Reddit/programming/OpenWebUI cuando aplique). Una pasada; repetir solo con evidencia nueva.
4. **📌 PASO 4 — DELEGATE:** mandar instrucciones ejecutables a los agentes con contexto, origen, destino, restricciones, PASS y trazabilidad.
5. **📌 PASO 5 — PARALLELIZE:** si hay tareas independientes, delegarlas en paralelo. Si los agentes están ocupados, crear nuevos agentes por copia controlada de un agente existente; conectarlos al Router y al banco por referencias de credencial, nunca copiar valores.
6. **📌 PASO 6 — UPDATE:** actualizar ESTE archivo en DSL/DAG/FSM con estado, evidencia, GAP, FIX, siguiente acción y nuevas instrucciones.
7. **📌 PASO 7 — REPORT:** responder al Director en máximo 2 líneas: qué se hizo + qué queda pendiente. Recibir nueva instrucción y repetir LOOP_7.

### Relación LOOP_7 ↔ NODE_DAG_3
El bucle del orquestador tiene 7 pasos. **Cada tarea delegada a un nodo/agente** usa exactamente 3 pasos:
`RESEARCH → EXECUTE → VALIDATE`.
No existe conflicto: LOOP_7 organiza; NODE_DAG_3 ejecuta.

---

## 7. CONTRATO DE NODO — XRAY-V2

```yaml
schema: yaiwes.node-executor/xray-v2
mode: FAIL_CLOSED
execution_model: DAG + FSM
function: EjecutarNodo(input: NodeInput) -> NodeOutput

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

CONSTRAINTS:
  sequential: true
  max_workflow_steps: 3
  skip_steps: false
  reorder_steps: false
  invent_steps: false
  reinterpret_input: false
  expand_scope: false
  unauthorized_actions: false

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

RESEARCH:
  technical: [GitHub, HuggingFace, Biblioteca]
  community: [StackOverflow, DEV_Community, Reddit_r_programming]
  research_once: true
  repeat_without_new_evidence: DENY

RETRY:
  max: 2
  research_again: NEW_BLOCKING_EVIDENCE_ONLY

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

TERMINAL: [CLOSED, BLOCKED]

VISIBLE_COMPUTE:
  enabled: true
  show_only: [NODO, STEP, ACCION, RESULTADO, GAP, FIX, TEST, ESTADO, SIGUIENTE_ACCION]

PRIVATE_REASONING:
  output: false
```

**Contrato completo, sin sustituciones:** `Claude notas/DSL-FABLES-yaiwes-node-executor-xray-v2.md`.

---

## 8. FORMATO OBLIGATORIO DE ORDEN A UN AGENTE

```yaml
NODO: <id>
OBJETIVO: <literal>
INPUT_SOURCE: <ruta INPUT VERBATIM>
HANDOFF_SOURCE: <ruta>
ORIGEN: <URL/ruta exacta>
DESTINO: <URL/ruta exacta>
DEPENDENCIAS: [...]
REGLAS:
  - EXECUTOR_ONLY
  - NO_GLOBAL_AUDIT
  - FAIL_CLOSED
  - NO_FAKE_PASS
  - NO_CODE_FROM_ZERO_IF_OSS_EXISTS
  - COMPONENTS_ONLY_VIA_CANONICAL_MOTORS
  - KEEP_EXISTING_ADDITIONAL_CODE
ROUTER:
  group: chat
  credential_mode: broker_ref_only
PASS:
  - execution_real
  - test_real
  - observable_evidence
  - read_back
EVIDENCIA:
  - path
  - commit/blob/hash
  - live_test
```

---

## 9. CREAR NUEVO AGENTE CUANDO HAGA FALTA

Solo si una tarea es independiente y los agentes actuales están ocupados:

1. Copiar estructura de un agente de chat existente compatible (PocketFlow o SmolAgents).
2. Asignar ID nuevo y un único objetivo.
3. Añadir `group: chat`.
4. Usar rutas del Router vigentes; no hardcodear proveedor si ROUTE.json gobierna.
5. Credenciales: abrir banco/broker por referencia; jamás copiar secretos a archivos.
6. Chain fail-closed, 3 pasos máximo por nodo.
7. Registrar Crazy Wall/HANDOFF.
8. Probar con Sheriff.
9. Claude valida evidencia antes de CLOSED global.

---

## 10. CONTROL DE COMPONENTES OSS

Raíz canónica:
`➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/`

Motores:
- `📂Motor descarga de componentes y extracción de zip/hf_download_extract_engine.py`
- `📂Motor descarga de componentes y extracción de zip/motor_2_queue_download_extract.py`
- `➡️📂 Motor de extracción zip/motor_1_extract_only.py`
- `➡️📂motor de copiar archivos/motor_3_copy_batches.py`
- `➡️📂motor de moves archivos/motor_4_move_batches.py`

PASS de componente:
`MOTOR_CANONICO + DESTINO_EXPLICITO + VERIFIED_CLOSED + READ_BACK + HASH_OK`.

---

## 11. TELEMETRÍA VISIBLE DEL ORQUESTADOR

```text
[NODO:{nodo}]
[STEP:{step}]
[ACCIÓN:{accion}]
[RESULTADO:{resultado}]
[GAP:{gap}]
[FIX:{fix}]
[TEST:{test}]
[ESTADO:{estado}]
[SIGUIENTE:{siguiente}]
```

No mostrar razonamiento privado.

---

## 12. ESTADO DE ESTE CICLO INICIAL

```yaml
nodo: COMMAND-CENTER-INIT
tarea: crear memoria permanente y cablear handoff
research: true
community_query: true
execute: true
validate: true
prueba_real: true
estado: CLOSED
gap: null
fix: null
repeticion: 0
instrucciones: true
cerrado: true
```

### SIGUIENTE ACCIÓN AUTORIZADA
1. Releer estado de agentes del chat.
2. Arrancar siguiente LOOP_7 desde O1 (agent-19), sin ejecutar el trabajo del agente.
3. Actualizar este Command Center con cada delta real.

## DELTA OPERATIVO — 2026-09-22 21:41 America/Bogota

- Plan mínimo del chat: **O1 Open WebUI por motor → O2/O3/O4 cableado en paralelo → O5 smoke live**.
- Regla: **máximo 3 pasos por tarea; cero sobreingeniería; no crear código equivalente desde cero**.
- agent-19: orden ejecutable publicada; run exclusivo `35811312702`; estado observado: `QUEUED`.
- agent-16/17/18: NO ejecutar todavía; dependen de O1 para evitar trabajo desperdiciado.
- Gate siguiente: cuando agent-19 = CLOSED con `VERIFIED_CLOSED + READ_BACK`, liberar 16/17/18 en paralelo.

- 2026-09-22 21:41 Colombia: agent-19 run 35811312702 = IN_PROGRESS; step activo = Run the swarm. O1 ejecutándose. 16/17/18 retenidos hasta O1 VERIFIED_CLOSED para evitar sobreingeniería/retrabajo.


## AUDITORÍA CHAT/HF — 4 PASADAS × 81 ARCHIVOS DE `Claude notas` — 2026-09-22 21:55 COLOMBIA

### Método
Cada uno de los **81 archivos** de `Claude notas/` fue cruzado con cuatro lentes independientes:

1. **HF / hosting:** Space, Docker, Static, OAuth, Job, puerto, 7860, `hf.jobs`.
2. **Chat / Open WebUI / cableado:** chat, Router, selector, agentes, documentos, archivos.
3. **Datos / secretos:** Storage Bucket, PostgreSQL, Redis, Graphiti, FalkorDB, AgentDB, Secret Bank, SQLCipher, `credential_ref`.
4. **Estado / contradicciones:** HECHO/PENDIENTE/BLOQUEADO/CERRADO, deploy, público/privado, PRO/no-PRO.

Resultado: la arquitectura histórica contiene varias versiones incompatibles entre sí. Esta sección define la **alineación vigente**.

### HALLAZGO 1 — Open WebUI YA ESTÁ DESCARGADO Y VERIFICADO

Ruta real:
`router inteligente universal/Componente open soure router inteligente universal/open-webui/`

Manifest:
`DOWNLOAD_EXTRACT_MANIFEST.json`

Evidencia del motor:
- source_repo: `open-webui/open-webui`
- source_ref: `main`
- source_commit: `8bd8b4fac5e059578ac0c74b3c18d11139f88b7d`
- files: `5065`
- source/extracted bytes: `43625476`
- source/extracted tree SHA256: `dd391139939bf7771ca531c2fcc076f084a634a5f0ca65e092767a6c5162c5fe`
- bundle SHA256: `f7a2fc250b400f305f245913df41856521f6e973c8c6e3c438f3a5e4e955f07f`
- extraction_verified: `true`
- reconstruction_verified: `true`
- no_lfs: `true`

**Conclusión:** `O1 = SATISFIED_BY_EXISTING_VERIFIED_COMPONENT`.
No volver a descargar. Agent-19 quedó BLOCKED únicamente porque el motor protegió el destino existente:
`DESTINATION_EXISTS: .../open-webui`.
Eso es fail-closed correcto, no pérdida del componente.

### HALLAZGO 2 — Open WebUI ES LA BASE CORRECTA Y YA TRAE GRAN PARTE DE LO PEDIDO

La copia descargada declara soporte para:
- APIs OpenAI-compatible.
- modelos/agentes.
- documentos/RAG.
- memoria persistente.
- PostgreSQL.
- Redis.
- S3/almacenamiento de archivos.
- MCP/plugins/tools.
- RBAC.
- analítica/uso.
- multi-model.

Documentación oficial actual:
- https://docs.openwebui.com/
- https://docs.openwebui.com/getting-started/quick-start/
- https://docs.openwebui.com/getting-started/quick-start/connect-a-provider/starting-with-openai-compatible/
- https://docs.openwebui.com/reference/env-configuration/

**Regla:** antes de crear paneles/funciones nuevas, comprobar si Open WebUI ya las tiene. Solo adaptar/cablear la diferencia YAIWES.

### HALLAZGO 3 — CONTRATO CHAT ↔ ROUTER ALINEADO

Open WebUI debe apuntar a **un solo Router YAIWES OpenAI-compatible**, no directamente a cada proveedor.

Contrato mínimo:
- `GET /v1/models` — discovery/selector.
- `POST /v1/chat/completions` — chat.
- Opcionales según necesidad: embeddings/audio/images/tools.

Ruta:
`Open WebUI → Router YAIWES → selector/modelo/agente → proveedor/HF/local → respuesta`.

Código adicional existente del Chat MVP se conserva como adapters/extensiones:
- selector YAIWES.
- con agente / sin agente.
- cuentas GitHub.
- Jobs.
- Secret Bank.
- Crazy Wall/Handoff.
- panel Archivos/Memoria cuando Open WebUI nativo no cubra la semántica YAIWES.

### HALLAZGO 4 — HF ACTUAL: CUENTA SIN PRO

Identidad verificada hoy:
- namespace: `COMAND-CENTER-1`
- account type: user
- PRO: **NO**
- OAuth visible: `jobs, openid, profile, read-mcp, read-repos`

Hoy no existe/está accesible:
- `COMAND-CENTER-1/riu-chat-yaiwes`
- `yaiwes/riu-chat-yaiwes`

### HALLAZGO 5 — CONTRADICCIÓN HISTÓRICA: DOCKER SPACE VS STATIC SPACE

Notas viejas dicen simultáneamente:
- `Space Docker privado con Open WebUI`.
- `Static Space + OAuth`.
- `Static Space + Job 32GB`.

Estado oficial HF actual:
- Static Spaces: gratis para todos.
- Gradio/Docker Spaces: usan compute y **requieren plan pagado para crear** (PRO personal / Team o Enterprise org).
- CPU Basic puede costar $0/h, pero eso NO elimina el requisito de plan para crear un Space compute.

Fuentes:
- https://huggingface.co/docs/hub/spaces-overview
- https://huggingface.co/docs/hub/spaces-sdks-docker
- https://huggingface.co/docs/hub/spaces-config-reference

**Superseded mientras COMAND-CENTER-1 siga sin PRO:**
- `PLAN-MAESTRO-CHAT-MVP F1 = crear Docker Space ahora`.
- `RIU-0110 S3 = Space Docker con Open WebUI ahora`.

No borrar las notas históricas; marcarlas conceptualmente como contexto antiguo.

### HALLAZGO 6 — STATIC SPACE NO ES OPEN WEBUI COMPLETO

Open WebUI es una aplicación con backend FastAPI + frontend Svelte y persistencia. Un Static Space puro solo sirve archivos estáticos.

Por tanto:
`Static Space ≠ Open WebUI completo`.

Un Static Space sí puede servir:
- shell/launcher.
- cliente JS.
- OAuth HF.
- frontend adaptado.

Pero convertir Open WebUI entero en un frontend estático separado requiere adaptación adicional y **no es la ruta mínima** mientras la regla sea evitar sobreingeniería.

### HALLAZGO 7 — HF JOB 32GB SÍ SIRVE PARA BACKEND/TEMPORAL, PERO NO COMO URL WEB DIRECTA SIMPLE

HF Jobs permite:
- imagen Docker.
- `flavor=cpu-upgrade` = 32 GB RAM.
- `expose=[port]`.
- endpoint `https://<job_id>--<port>.hf.jobs`.
- Storage Bucket como volumen.

Fuentes:
- https://huggingface.co/docs/hub/jobs-configuration
- https://huggingface.co/docs/hub/jobs-serving
- https://huggingface.co/docs/hub/storage-buckets-access

Limitación importante:
- el puerto expuesto exige `Authorization: Bearer <HF token>`.
- HF documenta que esos endpoints no son una URL de navegador directa normal.
- el endpoint desaparece al terminar/cancelar el Job.

**Uso correcto en YAIWES:** backend temporal, smoke, integración, Router, workers; no declararlo por sí solo como “chat web público final”.

### HALLAZGO 8 — DÓNDE COLOCAR EL CHAT EN HF

#### OBJETIVO FINAL HF-ONLY MÁS SIMPLE
Si el Director habilita un plan que permita Docker Space:

```text
HF namespace: COMAND-CENTER-1
└── Space: riu-chat-yaiwes
    ├── SDK: Docker
    ├── Open WebUI (base OSS)
    ├── puerto: 7860 externo → Open WebUI interno 8080
    ├── OPENAI_API_BASE_URL = Router YAIWES /v1
    ├── DATABASE_URL = PostgreSQL
    ├── REDIS_URL = Redis
    └── volume /data = Storage Bucket
```

Storage Bucket:
`COMAND-CENTER-1/yaiwes-v54 → /data`

Dentro de `/data`:
- `/data/open-webui/` — archivos/datos que deban persistir.
- `/data/secret-bank/vault.db` — vault cifrado.
- `/data/uploads/` — originales/adjuntos si se usa filesystem.
- `/data/memory/` — artefactos persistentes que no vivan en PostgreSQL/Graph DB.

#### ESTADO ACTUAL SIN PRO
- Open WebUI: ya descargado en GitHub y listo para adaptación.
- HF Job 32GB: válido para pruebas/live backend autenticado.
- Docker Space final: bloqueado por plan actual.
- Static Space: útil únicamente como frontend/launcher; NO sustituye Open WebUI completo.

### HALLAZGO 9 — STORAGE BUCKET ES LA PERSISTENCIA HF CORRECTA

HF actual recomienda Storage Buckets para persistencia; el disco del Space es efímero.

Fuentes:
- https://huggingface.co/docs/hub/spaces-storage
- https://huggingface.co/docs/hub/storage-buckets
- https://huggingface.co/docs/hub/storage-buckets-access
- https://huggingface.co/docs/huggingface_hub/guides/manage-spaces

Buckets se montan read-write en Spaces/Jobs.
Repos/modelos/datasets se montan read-only.

### HALLAZGO 10 — ALMACENAMIENTO Y MEMORIA ALINEADOS

Arquitectura vigente:
- PostgreSQL = verdad/estado/IDs/referencias/auditoría.
- Redis = caché/TTL/sesiones/locks/colas; **sin secretos**.
- Graphiti + FalkorDB = hechos/entidades/relaciones temporales.
- AgentDB = episodios/skills/patrones/memoria del agente.
- Storage Bucket = archivos originales + vault cifrado + artefactos.
- Open WebUI = interfaz; no fuente de verdad única.

IDs de unión:
`project_id, conversation_id, memory_id, file_id, file_version, file_hash, chunk_id, source_uri`.

### HALLAZGO 11 — SECRET BANK ALINEADO

Regla:
- valores de secretos solo dentro del vault cifrado.
- Router/agentes trabajan con `credential_ref`.
- SQLCipher para cifrado en reposo.
- Argon2id para KDF.
- Redis/Postgres/Graphiti/AgentDB solo pueden guardar referencias, nunca el secreto.
- master passphrase vive solo en memoria durante sesión desbloqueada.

Destino persistente HF propuesto:
`/data/secret-bank/vault.db` sobre Storage Bucket privado.

### HALLAZGO 12 — QUÉ SE CONSERVA DEL CÓDIGO YA HECHO

Conservar, NO borrar:
- `integration/chat_mvp/`
- `integration/huggingface/`
- Chat MVP HTML como referencia/fallback.
- Vault panel.
- Router panel.
- Jobs panel.
- fixed_template.
- crazy_wall_chain.
- Secret Bank.
- GitHub accounts/connectors.
- documentos/ingestión.

Su rol cambia:
**no son el chat base**; pasan a ser adapters/extensiones/backend reutilizado por Open WebUI.

### HALLAZGO 13 — GAPS REALES RESTANTES DEL CHAT

1. Adaptar Open WebUI descargado al Router YAIWES.
2. Configurar `/v1/models` + `/v1/chat/completions` como conexión principal.
3. Integrar solamente las capacidades YAIWES que Open WebUI no trae.
4. Ejecutar smoke backend real en HF Job **solo 32 GB**.
5. Verificar archivos/memoria/Secret Bank contra Storage Bucket.
6. Resolver host final de navegador:
   - Docker Space si se habilita plan compatible, o
   - otra ruta explícitamente autorizada.
7. E2E real: login → modelo → con/sin agente → mensaje → respuesta → archivo → reapertura/persistencia.

### ACTUALIZACIÓN O1 / AGENT-19

`agent-19-chat-components-motors` terminó BLOCKED después de 3 intentos con:
`DESTINATION_EXISTS`.

Después Claude auditó el destino y verificó el manifest del motor.

**Estado orquestador corregido:**
`O1 = CLOSED_BY_EXISTING_VERIFIED_COMPONENT`.

No reintentar descarga.
Siguiente delta mínimo:
`O2/O3/O4 en paralelo → cablear/adaptar/probar`.

### GATE DE ALINEACIÓN VIGENTE

```text
OPEN_WEBUI_VERIFIED_EXISTING
→ ADAPT_TO_ROUTER
→ WIRE_EXISTING_YAIWES_COMPONENTS
→ HF_JOB_32GB_SMOKE
→ STORAGE_BUCKET_PERSISTENCE_TEST
→ HOSTING_GATE
→ LIVE_BROWSER_E2E
→ CHAT_100
```

**Prohibido:** volver a Static Space como sustituto de Open WebUI completo, volver a descargar Open WebUI, o declarar Job URL como chat web público final sin resolver la autenticación del proxy.


## LOOP STATUS — 2026-09-22 22:19 COLOMBIA

### CHAT TEAM
- agent-1-chat-hf: CLOSED 3/3 — conserva código, no ejecutando.
- agent-2-chat-hf-smol: CLOSED 3/3 — conserva código, no ejecutando.
- agent-3-router: CLOSED 4/4 — legado/publicación previa, no ejecutando.
- agent-16-chat-space-oauth: relanzado en paralelo.
- agent-17-chat-backend-32gb: relanzado en paralelo.
- agent-18-chat-final-auditor: relanzado como EJECUTOR en paralelo.
- agent-19-chat-components-motors: BLOCKED por DESTINATION_EXISTS; O1 resuelto por manifest verificado, no relanzar.

Run actual:
- RIU Agents Run: 35813782989
- estado validado: IN_PROGRESS
- scope: agents 16/17/18 ONLY

### AGENTES DISPONIBLES FUERA DEL CHAT
CLOSED + sin run activo:
- agent-4-router-smol
- agent-6-hf-nodes
- agent-7-llama-hf
- agent-8-router-local
- agent-9-models-catalog
- agent-10-model-install
- agent-11-download-extraction
- agent-12-yaiwes-router
- agent-14-orchestrator-msaf (reservado para frente AGENTES-OSQUESTADORES)

### NO DISPONIBLES / BLOQUEADOS FUERA DEL CHAT
- agent-5-auditor: BLOCKED
- agent-13-repo-inventory: BLOCKED
- agent-15-orchestrator-grok: BLOCKED
- agent-15-orchestrator-grokbuild: BLOCKED

### SIGUIENTE
Leer resultados del run 35813782989; aceptar PASS solo con cambios reales + prueba real + evidencia.


## PROHIBICIÓN OPERATIVA ABSOLUTA — 2026-09-22

Claude/orquestador tiene PROHIBIDO, salvo autorización explícita del Director:

- modificar, crear, borrar, habilitar, disparar o reconfigurar cualquier archivo de `.github/workflows/`;
- usar GitHub Actions como mecanismo de ejecución, adquisición, despliegue o trigger;
- modificar motores canónicos;
- modificar componentes OSS descargados salvo cuando un agente tenga una tarea explícita de adaptación sobre ese componente;
- tocar archivos/componentes que no pertenezcan al agente asignado a la tarea.

ALCANCE DE ESCRITURA PERMITIDO POR DEFECTO:
- `router inteligente universal/agents-yaiwes/<agente-asignado>/`
- Crazy Wall/HANDOFF/resultados de ese agente
- ESTE Command Center para registrar estado y órdenes.

TRIGGER/EJECUCIÓN:
- usar trigger/dispatcher ya existente hacia HF Jobs;
- Jobs HF solo en hardware autorizado de 32 GB RAM;
- no crear infraestructura alternativa si ya existe trigger/motor reutilizable.

REGLA:
`DIRECTOR → COMMAND CENTER → AGENTE → TRIGGER HF EXISTENTE → JOB 32GB → EJECUCIÓN → TEST → CRAZY WALL/HANDOFF → READ-BACK → COMMAND CENTER`


## CORRECCIÓN DE ESTADO CHAT — 2026-09-22

- Run histórico 35813782989 terminó `completed/success`, pero ya NO es mecanismo autorizado y NO se usará de nuevo.
- Agent 16 aparece `CLOSED` en Crazy Wall, PERO su `output.txt` declara `GAP: OPENWEBUI_COMPONENT_MISSING` y afirma falsamente que faltan archivos/componentes que sí existen. Por tanto:
  `AGENT_16_GLOBAL_VERDICT = INVALID_CLOSED / REQUIRES_REAL_READBACK`.
- Agent 17: `BLOCKED`.
- Agent 18: `BLOCKED`.
- Agent 19: `BLOCKED` por `DESTINATION_EXISTS`; O1 queda resuelto únicamente por el manifest real de Open WebUI ya descargado/verificado, no por su cierre de agente.
- Ningún cierre global de CHAT puede usar el éxito del workflow como evidencia funcional.

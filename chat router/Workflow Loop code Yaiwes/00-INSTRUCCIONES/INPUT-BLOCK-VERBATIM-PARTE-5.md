# INPUT BLOCK VERBATIM — PARTE 5 (2026-09-26 noche / 2026-09-27)
Mensajes literales del Director sobre chat, agentes, Router, OmniRoute, memoria y plan. Claves → [CLAVE OMITIDA].
Documentos 22–26: se registra su estructura, roles, contratos y código de referencia completos en lo esencial; el texto íntegro está en la conversación de Opus del 27-sep.

## M30
Usa el mismo cpu de 16 de ram pago para el router y lo mantienes encendido siempre para el router y tu coneccion y el chat si se satura salta a otro procesador pero no sigas poniendo que se duerma el único que luego el de 32 de ram lo puedes poner con wachdog dentro del mismo router de 16 de ram que despierta a la cadena de 32 de ram si este detecta que los agentes están activos o si hay tares en cursos mantiene encendido el router de 32 de ram hasta 10 procesadores si se satura al 85 % enciende el siguiente HF procesador para que valla arrancado para los agente y modelos de ai locales lo mismo con el HF de 16 de ram si ve que llega a 80% enciende el siguiente detecta que va necesitar más cómputo para que no se caiga y evitar latencia activa el siguiente HF procesador
Dieme si me entiendes y como lo analizas o recomendas tu ?
El handoff que me diste tiene todo lo qunsw hizo el code del chat los agentes todo revisa si está el plan hecho del chat con Las instruccion que te di y el equipo de los agentes ?

## M31
Si estoy de acuerdo con eso el router siempre encendidos es quien al recibir un tarea nueva dispara el procesador
Todo lo demás estoy de acuerdo y haces el plan

## M32
No yo no puedo gastar 20 al mes para que tú uses eso busca otra manera un procesador HF de 16 de ram el mismo del router o otra manera

## M33
Estas alucinando
Te he repetido no máquina gratis 100 veces NO⚠️
MAQUINA DE HF 16 RAM pago por hora
Que va dentro
Tu Claude el router y omnirauter
Dime si lo entiendes

## M34
Una pregunta para entender no lo puedes hacer sin vercel porque lo usas porque no usas HF como Open router

## M35
Y lo que estás usando instalando de omnirauter no debería hacer lo mismo para que no se caiga ?

## M36
Si eso de al api lo entiendo pero eso no es mi duda lo que te pregunto es si por ejemplo En vercel con HF como tú coneccion si pones a el router y a Omni router en vercel no es más estable es lo que digo es para entender y ver si eso nos da mejoras de alguna manera

## M37
📌 salida 1 Primero dame lo del plan del chat y de los agentes solo haces eso Para ver qué puedo adelantar Algo me das el enlace
📌paso 2 Salida 2 Ok solo queda 96% de la ventana de antropy así que capas solo haces una parte lo más importante del router y procesadores y luego en unas horas continúas con lo siguiente si es que alcanza con la salida 1 si no más tarde toca esperar

## M38
Asegúrate cuando puedas revisa que open claw y hermes son las últimas versiones. Si no los descraga de nuevo sustituyes o resuelves como mejor puedas
Continúa con salida 2

## M39
Continúa

## M40
Elimina la basura no me dejes cosas sueltas que no son parte de lo que se está usando y acruliza el readme del router .
Termina de instalar el Omni router al router y activalo
Me hiciste muy mal el plan de trabajo la información 1 a 1 imput block verbartin que te dije que anotaras todo el plan era ambigua … por no anotar ni hace los planes bien acorde a mis instrucciones
Necesito que termines para que mensigas ayúdanos a desplegar Componentes del chat nunca hiciste el sistema de almacenamiento y memoria …
Necesito que termines de conectar el Omni router todo 100 % funcional sin sobre ingeniería sin que des pasos extras solo termina y pruebas y me avisas para que hagas la siguiente tarea

## M41
Si vez que puede parar para luego volver a lanzarte paras no esperes porque te comes el plan

## M42
Ve adelantando ya manus desplegó el chat busca el plan de los agente busca mis instrucciones de cómo deben trabajar y me enseñas para que con el osquestador prepáres una pequeña osquestador de trabajo para que los agentes ejecuten luego lo mismo quiero que añades al plan a open Claw y hermes como si fuera el asisten del osquestador y del chat los fokeas ambos y los pones a trabajar lo cableas al chat se supone que harnes de deepsek debe estár conectado al chat y creas la arquitectura que te di de programación más la que te voy a dar ve buscando la información auditas el chat y los archivos 1 a 1 imput block verbartin que te di

## M43 (documentos 22–26 + texto)
### Documento 22 — cadena de ingeniería con relevo obligatorio (estructura literal)
PETICIÓN → ORQUESTADOR YAIWES → CLAUDE CODE — ARQUITECTO (crea PLAN, CONTRATO, TASKS, ACCEPTANCE, TESTS esperados) → GROK BUILD — EJECUTOR (implementa, ejecuta, prueba, entrega diff + evidencia) → CLAUDE CODE — REVIEWER (PASS / CORREGIR → GROK) → META MUSE CODE ×4 en paralelo: META-1 CODE (auditor código), META-2 TEST (integración), META-3 VISUAL (navegador/UI, screenshots/video), META-4 ADVERSARIAL (busca fallos/mejora) → AGREGADOR → MUSE CODE FIXER → TESTS → SHERIFF → PASS.
TEAM = {claude_architect: DESIGN_ONLY, write_code False; grok_executor: IMPLEMENT; claude_reviewer: REVIEW_AND_CORRECT; meta_1_code: CODE_REVIEW; meta_2_tests: TEST_INTEGRATION; meta_3_visual: VISUAL_UI_QA; meta_4_adversarial: BREAK_FIND_IMPROVE; meta_fixer: APPLY_META_CORRECTIONS}.
Contrato único job = {job_id, objective, scope, acceptance[], state, attempt, evidence[], issues[]}; resultado = {job_id, agent, status, changed_files, tests, issues, evidence, next_action}. Ningún agente manda mensajes libres.
EngineeringLoop: design → execute → review (hasta 3 correcciones, si no BLOCKED) → meta review_parallel (asyncio.gather de 4) → merge_meta_results → fixer.correct si needs_fix → re-validación ×4 → PASS/REVISE.
MIRROR: entorno aislado (git worktree `mirror/<job>`), selectivo por SYSTEM_MAP (solo las rutas del sistema a tocar); al terminar: DIFF → TEST → SHERIFF → MERGE SELECTIVO → MAIN; si falla, mirror se conserva para depurar y main no cambia.
RUFLO dirige la máquina (crea JOB, identifica SYSTEM, crea MIRROR, Claude DESIGN, Grok EXECUTION, Claude REVIEW/Grok FIX, Meta FAN-OUT ×4, Meta FIX, Meta QA ×4, Sheriff, MERGE); ROWBOAT arriba (TÚ → ROWBOAT → RUFLO → ENGINEERING LOOP). Fábrica recursiva: trabajo nuevo independiente → nuevo MIRROR + nuevo ENGINEERING TEAM (solo el equipo y su workspace; el control plane es uno solo).

### Documento 23 — jerarquía de la colmena (estructura literal)
USUARIO → ROWBOAT (director) → RUFLO (orquestador operativo de la colmena) → HERMES + OPENCLAW (asistentes: planifican, debaten, supervisan, revisan, corrigen) → SHERIFF (reglas y permisos) → COLMENA (coder/tester/researcher/reviewer/architect…) → SENTINEL (vigila errores, bloqueos, desviaciones) → HERMES + OPENCLAW (revisión cruzada) → JUDGE (PASS / REVISE / BLOCK).
Lógica: Rowboat interpreta → Ruflo organiza → Hermes Plan A + OpenClaw Plan B → debaten → Plan Final → Sheriff valida → Ruflo reparte → Sentinel vigila → Hermes revisa + OpenClaw revisa (si discrepan, debaten hasta 2 veces) → Judge.
ROLES: rowboat {director: receive_goal, context, delegate}; ruflo {swarm_orchestrator: route_tasks, spawn_agents, coordinate_agents, track_execution}; hermes {planner_supervisor: plan, critique, review, debate, delegate}; openclaw {guardian_supervisor: plan, critique, review, debate, monitor}; sheriff {policy_gate: allow, deny, restrict}; sentinel {runtime_watchdog: watch, detect_failure, detect_stall, request_recovery}; judge {final_verifier: pass, revise, block}.
Estados: INPUT, PLANNING, DEBATE, SHERIFF, EXECUTION, REVIEW, JUDGMENT, PASS, REVISE, BLOCK. Task {id, objective, role, dependencies, allowed_paths, acceptance, evidence}. Sheriff y Judge son CÓDIGO (sin LLM). RufloAdapter por MCP/CLI/API (swarm.init hierarchical/specialized max 12; task.create). Niveles 0–8: Usuario, Rowboat, Hermes+OpenClaw, Sheriff, Ruflo, Colmena, Sentinel, Hermes+OpenClaw, Judge.

### Documento 24 — YAIWES STATE HUB (estructura literal)
OpenClaw (guardian/sentinel) y Hermes (planner/reviewer) NO escriben archivos directamente: hablan con un único State Hub que actualiza STATE.json, Crazy Wall, bitácora, handoff y la persistencia de cada tarea.
Raíz: .yaiwes/{STATE.json, CRAZY_WALL.json, BITACORA.jsonl, HANDOFF.md, projects/<p>/{PROJECT.json, PROJECT.md, STATE.json, HANDOFF.md, DECISIONS.jsonl, tasks/<T>/{TASK.json, STATE.json, HANDOFF.md, EVIDENCE.json, EVENTS.jsonl}}, mirrors/<T>/}.
STATE.json = foto actual (schema yaiwes.state/v1, revision, active_project, projects{status, progress, active_tasks, blocked_tasks}, agents{status}). Crazy Wall: 1 CHAT = 1 NODO ACTIVO; nodo {status CLAIMED, project, task, chat_id, agent_name, node_id, base_sha, write_scope, paths, claimed_at, heartbeat_at, phase, next}. BITACORA.jsonl inmutable (una línea por evento: seq, type, project, task, actor) → reducer → STATE.json (se puede reconstruir). TASK.json persistente por tarea (team, acceptance, dependencies, mirror, base_sha, current_sha, attempt, next_action). HANDOFF.md generado por el Hub desde TASK + STATE + EVENTS + EVIDENCE. PROJECT.md = memoria estable del proyecto; .hermes.md pequeño que manda a leer PROJECT/STATE/HANDOFF y consultar por MCP.
OpenClaw heartbeat revisa periódicamente STATE, Crazy Wall, RUNNING/STALLED, claims vencidos (NO_REPLY si no pasa nada). Hermes usa su state.db para lo que aprendió; el estado real vive en el Hub. Regla: nadie hace open("STATE.json","w"); todo es state_hub.emit(actor, event, project, task, payload) → append bitácora → reducer → write_state_atomic → update_crazy_wall → generate handoffs. Chat Bus: mensajes de Hermes/OpenClaw/Ruflo al chat como eventos (el chat es una vista del estado). Trabajo nuevo → NEW_TASK_REQUIRED → nueva TASK + nodo + mirror + equipo.

### Documento 25 — 20 fuentes para investigar (URLs literales)
https://anthropic.com/discord · https://community.openai.com/ · https://forum.cursor.com/ · https://github.com/orgs/community/discussions · https://discuss.huggingface.co/ · https://github.com/anthropics/claude-code/issues · https://github.com/anthropics/claude-code-action/discussions · https://stackoverflow.com/ · https://softwareengineering.stackexchange.com/ · https://news.ycombinator.com/ · https://dev.to/ · https://hashnode.com/ · https://lobste.rs/ · https://www.reddit.com/r/LocalLLaMA/ · https://www.reddit.com/r/ClaudeCode/ · https://www.reddit.com/r/programming/ · https://www.reddit.com/r/ExperiencedDevs/ · https://forum.freecodecamp.org/ · https://github.com/search · https://huggingface.co/
Cruce recomendado: GitHub Issues/Discussions + Reddit + Hacker News + foro oficial.

### Documento 26 — YAIWES Evidence/Search Gate (estructura literal)
INPUT → PARSER DETERMINISTA → 12 GOALS DE ENTRADA → COMPILADOR DE BÚSQUEDAS (plantillas, sin LLM) → MOTORES (web A/B, GitHub, docs, issues, repos locales) → EXTRACTOR EXACTO (sin LLM) → RANK/FUSIÓN (BM25 + autoridad + recencia + coincidencia + corroboración − duplicado; Reciprocal Rank Fusion) → EVIDENCE PACK (task, known_facts, requirements, constraints, conflicts, unknown, sources; 2K–8K tokens) → [LLM FILTRO opcional: use/reject/missing → nueva búsqueda] → EJECUTOR → CLAIMS → BÚSQUEDA DE VERIFICACIÓN → 12 GOALS DE SALIDA → VERIFIER/SHERIFF (PASS / INCOMPLETE → buscar más / CONTRADICTION → corregir / FAIL → reejecutar).
Categorías: SEARCH, INSTALL, DOWNLOAD, EXTRACT, DEPLOY, MODIFY_CODE, DEBUG, TEST, COMPARE, AUDIT, RESEARCH, VERIFY. 12 Goals antes/después: G01 Objetivo, G02 Entidades, G03 Restricciones, G04 Dependencias, G05 Fuente oficial, G06 Versión, G07 Configuración, G08 Integración, G09 Ejecución, G10 Tests, G11 Contradicciones, G12 Evidencia. Regla: la misma LLM que ejecutó no cierra el trabajo por su opinión; cierre = pruebas deterministas + búsqueda posterior + Evidence Pack + 12 Goals + Sheriff.

### Texto del Director (literal)
Ok tenemos un solo router que tendrá solo los Omni router y las api que tenemos y deepsek solo si yo conecto las claves de Nvidia que reporten primero cuando se usa en el chat si está disponible Kimi k 3 o DeepSeek v4 en la api de Nvidia solo con el chat una vez que confirmes que si funciona Omni router ya probado
La cedena de ejecución de tareas los los osquestadores crean un mirror de cada agente nuevo que necesiten
Claude Code diseña → Grok ejecuta → Claude Code revisa y corrige → los 4 de Meta revisan mejoran y prueban visual y corrigue el agente de meta code
Si se necesita un nuevo trabajo el osquestador crea un mirror solo con el equipo de ingeniería de ejecución hace una copia solo de ese sistema y réplica una nueva
Todos los agente como grafos conecatado necesito que lo prepares de tal manera de organizacion para luego al estar listo exportar todo en una raíz sin historia al repo de Yaiwes
Dime si ya lo tienes claro..
Que todos tengan acceso a HF y Github todos los repo
Luego a lo que esté listo sin sobre ingeniería. Necesito que termines lo de almacenamiento y memoria y probar que funciona y luego poder seguir con lo de la fábrica
todo de una sola vez
Dieme si tienes dudas
Necesito que hagas dentro de mi información 1 a 1 mis instrucciones imput block verbartin y lo conviertas en nodos de tareas todo un shema DSL Dag del plan como te dije que vieras el plan de objetivos y el DSL Dag shema de los agente para que cada ai que me pueda ayudar termine la tarea hasta lograr conformar el equipos
Dime si entiendes todo si te quedo claro incluso como lo vas a escribir cada detalle del plan
Para que no la vuelvas a cagar resumiendo
Si no puedes me dices

## M44 (respuestas a las dudas + orden actual)
Tu dudas
1. todos usan nuestro router
2. Todos usan el router todos
3. Hazlo primero de tal manera organizado que cuando funcione y este probado lo cambiamos de llama Yaiwes pero hace falta muchas cosas esoas adelante cuando ya esté todo listo para hacelo organizado no ahorita solo te digo que me organices todo en una raíz bien ordenado lo que vallas hacer no como Sonnet que deja archivos regados por todos lados
Usas para el plan el archivo que te mandé a crear del chat para saber cómo se hace y no lo hiciste ignoraste las instrucciones me diste una mierda de plan y como es la arquitectura un ➡️📂 readme chat Arquitectura .
4. Si con todos los componentes que yo te di para la memoria y almacenamiento es solo cablear por dios puro Componentes ya creados
📌 La idea es que si se satura la ventana de antropy otro opus de otra cuenta pueda seguir y vallan anotando en el Craxy wall bitácora stated JSON handoff todo lo del plan que no tienen nada que ver con la mezclas que hiciste de el router inteligente universal que estamos trabajando eso es trabajar desorganización y ya te lo he repetido 4 veces
Valida confirma que hiciste el plan con mis instrucciones 1 a 1 imput block verbartin
Si no tienes duda anota donde te dije todo creas el plan + el DSL Dag shema de cada paso y metes todo lo que falta por hacer
Paso 1 📌 Anota mis instrucciones y el plan
Paso 2 📌 necesito operativo el router y el omnirauter privado
Paso 3📌 seguimos con lo pendiente de el chat

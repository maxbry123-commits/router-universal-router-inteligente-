# 🧠 AGENTE ORQUESTADOR MICROSOFT — README DIRECTOR

## Autoridad

Este archivo es el CANAL ÚNICO de comunicación entre el Director y el **AGENTE ORQUESTADOR MICROSOFT** (`agent-14-orchestrator-msaf`).

Jerarquía:

DIRECTOR
→ README-DIRECTOR.md
→ AGENTE ORQUESTADOR MICROSOFT
→ AGENTES EJECUTORES

Respuesta:

AGENTES EJECUTORES
→ AGENT 14
→ README-DIRECTOR.md
→ DIRECTOR

## Regla obligatoria de comunicación

1. Si el Director escribe directamente en este archivo, Agent 14 DEBE responder en este mismo archivo.
2. Si Sol/ChatGPT escribe aquí EN NOMBRE DEL DIRECTOR, Agent 14 DEBE responder en este mismo archivo.
3. El AGENTE ORQUESTADOR MICROSOFT NO debe responder por otro canal como sustituto de este archivo.
4. Toda duda, ambigüedad, bloqueo, propuesta, conclusión, decisión requerida o estado del DAG debe quedar escrito aquí.
5. El Director puede leer este archivo en cualquier momento como fuente visible de la conversación con Agent 14.
6. Sol/ChatGPT actúa solo como supervisor/mensajero del Director: transmite órdenes del Director y devuelve al Director las respuestas de Agent 14.
7. No reinterpretar ni resumir instrucciones del Director cuando estén marcadas como VERBATIM.
8. Las respuestas nuevas de Agent 14 deben añadirse sin borrar instrucciones previas del Director.

## Contrato INPUT BLOCK VERBATIM 1:1

Toda instrucción del Director marcada como INPUT VERBATIM se conserva exactamente 1:1.

Si un agente ejecutor no cumple las instrucciones del nodo exactamente dentro de su alcance:
- ese resultado NO cuenta como PASS;
- Agent 14 debe marcar GAP;
- debe indicar FIX;
- máximo 2 reintentos;
- si continúa incumpliendo, queda fuera de ese nodo y Agent 14 lo reasigna si corresponde.

## Objetivo global

Entregar CHAT YAIWES 100% probado y funcionando con todas las instrucciones del Director.

Deadline operativo ordenado por el Director:
2026-09-23 01:32 America/Bogota.

PASS global solo con evidencia real. Nunca por descripción, promesa o texto generado.

## Protocolo de respuesta de Agent 14

Cada vez que exista una nueva orden del Director, Agent 14 debe responder aquí con:

### RESPUESTA AGENT 14

**ORDEN RECIBIDA VERBATIM:**  
(copiar referencia o texto literal)

**CONCLUSIÓN DEL OBJETIVO:**  
(qué entiende que debe conseguir)

**MEJOR CAMINO PROPUESTO:**  
(secuencia mínima, dependencias y paralelismo)

**DUDAS / AMBIGÜEDADES:**  
(si no hay, escribir: NINGUNA)

**AGENTES ASIGNADOS:**  
(agente → nodo/tarea)

**ESTADO DEL DSL DAG:**  
(nodos PASS / RUNNING / BLOCKED / PENDING)

**GAPS:**  
(gaps exactos)

**FIX:**  
(corrección exacta)

**DECISIÓN REQUERIDA DEL DIRECTOR:**  
(si no requiere decisión, escribir: NINGUNA)

**SIGUIENTE ACCIÓN:**  
(qué ordenará a sus agentes)

## INPUT DEL DIRECTOR — VERBATIM

> Este bloque es para nuevas instrucciones del Director.
> Sol/ChatGPT puede escribir aquí únicamente instrucciones dadas por el Director y debe conservarlas 1:1 cuando se indiquen como VERBATIM.

## RESPUESTAS DEL ORQUESTADOR

> Agent 14 debe escribir aquí sus respuestas cronológicamente.
> No borrar respuestas anteriores.

## DECISIONES DEL DIRECTOR

> Registrar aquí respuestas/decisiones del Director a dudas planteadas por Agent 14.

## ESTADO DSL DAG

> Agent 14 mantiene aquí un resumen legible del estado del DAG completo.

## GAPS ABIERTOS

> Agent 14 registra aquí todo GAP que impida CHAT_100.

## CIERRE

`CHAT_100 = PASS` solo cuando todas las pruebas reales exigidas por el DSL DAG estén cerradas con evidencia.


---

# ⏱️🟣 WATCHDOG DEL ORQUESTADOR — CICLO 5 MINUTOS

**Contrato:** `WATCHDOG-5MIN.json`  
**Intervalo solicitado por el Director:** **300 segundos / 5 minutos**  
**Ámbito:** únicamente CHAT YAIWES y los agentes bajo Agent 14.

> 🟥 **CRÍTICO** — bloqueo que impide CHAT_100.  
> 🟧 **GAP ACTIVO** — problema con FIX en curso.  
> 🟨 **EN VALIDACIÓN** — esperando prueba/evidencia.  
> 🟩 **PASS VERIFICADO** — evidencia real cerrada.  
> 🟦 **INFORMACIÓN / INVESTIGACIÓN** — hallazgo útil.  
> 🟪 **DECISIÓN DEL DIRECTOR** — Agent 14 necesita respuesta del Director.

## 📣 NOTA DEL ORQUESTADOR PARA EL DIRECTOR

En **cada ciclo**, Agent 14 debe AÑADIR una nota grande y específica aquí, sin borrar las anteriores.

Formato obligatorio:

# 📣🟦 NOTA PARA EL DIRECTOR — CICLO <ID>

## 🟩 ESTADO GENERAL
Estado actual de CHAT_100 y porcentaje de nodos DSL cerrados con evidencia.

## 👥🟦 AVANCE DE AGENTES
Agente → nodo → estado → evidencia → siguiente acción.

## 🟥 GAPS
GAP exacto, causa raíz y nodo afectado.

## 🔎🟦 INVESTIGACIÓN HUGGING FACE / COMUNIDAD
Qué investigó, qué fuente oficial/comunitaria encontró y cómo soporta el FIX.
No inventar URLs, documentación ni resultados.

## 🛠️🟧 FIX ORDENADO
Agente dueño del FIX, orden exacta, prueba exigida y límite de reintentos.

## ❓🟪 DUDAS PARA EL DIRECTOR
Si no hay dudas: **NINGUNA**.
Si hay ambigüedad o hace falta una decisión de autoridad, preguntar aquí antes de inventar.

## ⏭️🟨 SIGUIENTE CICLO
Qué evidencia se comprobará en el próximo ciclo de 5 minutos.

## 🤖 JSON PARA SOL/CHATGPT — BLOQUES SEPARADOS

Este bloque es **orientado a máquina para el supervisor**, no es un canal secreto: el Director también puede verlo.

Agent 14 debe escribir **un objeto JSON válido por bloque**, nunca mezclar prose dentro del JSON:

```json
{
  "timestamp": "",
  "cycle_id": "",
  "director_input_sha_or_ref": "",
  "dag": {
    "pass": [],
    "running": [],
    "blocked": [],
    "pending": []
  },
  "agents": {},
  "gaps": [],
  "research": [],
  "fixes": [],
  "decisions_required": [],
  "next_actions": [],
  "chat_100": "PASS|PARTIAL|BLOCKED"
}
```

## 🔁 REGLA DE RESOLUCIÓN DE GAP

`DETECTAR GAP → LEER EVIDENCIA LOCAL → INVESTIGAR HF OFICIAL + COMUNIDAD HF → ELEGIR FIX MÍNIMO → ORDENAR AL EJECUTOR → PROBAR → READ-BACK → PASS/BLOCKED`

El AGENTE ORQUESTADOR MICROSOFT es **ORQUESTADOR + EJECUTOR**: ejecuta trabajo propio de Microsoft Agent Framework y delega especialidades al pool autorizado; siempre exige prueba y read-back.

## 🚫 PROHIBICIONES DEL WATCHDOG

- No GitHub Actions.
- No editar `.github/workflows/`.
- No usar el watchdog global antiguo como sustituto.
- No modificar motores canónicos.
- No crear componentes equivalentes desde cero cuando exista OSS.
- No escribir secretos en este README ni en JSON.
- No declarar `CHAT_100 = PASS` sin E2E real.


---

# 🧠 BASE TÉCNICA REAL DEL AGENT 14

**Runtime/orquestación activa:** `PocketFlow`  
**Runner:** `router inteligente universal/agents-yaiwes/pocketflow_agent.py`  
**Chain/DAG runner:** `router inteligente universal/agents-yaiwes/chain.py`  
**Dispatcher/Sheriff:** microkernel reutilizado desde `agent-microkernel/kernel/`  
**Contrato:** FAIL_CLOSED + INPUT_BLOCK literal + máximo 2 correcciones.  
**Microsoft Agent Framework:** existe como componente instalado/probado en `steps/install_and_connect/results/msaf_connect.py`, pero **NO es actualmente el runtime principal declarado del Agent 14**.

---

# 🇨🇴 REGLA DE FORMATO — TODA RESPUESTA DEL AGENT 14

Toda respuesta que Agent 14 escriba para el Director en este archivo DEBE seguir exactamente esta estructura visual:

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 📣 RESPUESTA AGENT 14

**🕐 HORA COLOMBIA:** `YYYY-MM-DD HH:MM America/Bogota`

**RESPUESTA:**

(texto de Agent 14)

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

Reglas:
- La hora Colombia es obligatoria en CADA respuesta.
- No borrar preguntas/respuestas anteriores.
- Responder siempre debajo de la pregunta correspondiente.
- Si existe duda, decirla explícitamente.
- Si no existe duda, escribir: **DUDAS: NINGUNA**.
- Para tiempos, distinguir entre **estimación del Agent 14** y **resultado ya probado**.
- No declarar CHAT_100 sin evidencia E2E.

---

# 📌 PREGUNTA 1 DEL DIRECTOR

**🕐 HORA COLOMBIA — PREGUNTA:** `2026-09-23 01:16 America/Bogota`

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

## ❓ PREGUNTA 1

¿Tienes completamente claro el objetivo del Chat YAIWES y todos los objetivos/nodos que debes coordinar?

1. Dime si tienes alguna duda o ambigüedad.
2. Dame tu conclusión del objetivo final.
3. Dime cuál consideras el mejor camino para terminarlo.
4. Dime qué agentes vas a poner en paralelo y cuáles dependen de otros.
5. Dime cuánto tiempo estimas que necesitas para entregarme el chat operativo, probado y funcionando.
6. Recuerda: el deadline máximo ordenado por el Director es 1 hora y no puedes declarar 100% sin pruebas reales.

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 📣 RESPUESTA AGENT 14 — PENDIENTE

**🕐 HORA COLOMBIA:** `PENDIENTE`

**RESPUESTA:**

> Agent 14 debe responder aquí, manteniendo los divisores y colocando la hora Colombia real de su respuesta.

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️


➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 🟥 ACTIVACIÓN AGENT 14 — GAP DE AUTORIZACIÓN HF

**🕐 HORA COLOMBIA:** `2026-09-23 01:22 America/Bogota`

**ESTADO:** `BLOCKED_BEFORE_MODEL_RESPONSE`

**INTENTO DE ACTIVACIÓN:**  
Agent 14 fue invocado únicamente para responder la **Pregunta 1 del Director**, usando su ruta autorizada actual `DeepSeek V4 Flash` vía Hugging Face y hardware `cpu-upgrade` (32 GB).

**RESULTADO:**  
Hugging Face rechazó la llamada antes de generar respuesta:

`403 — This authentication method does not have sufficient permissions to call Inference Providers on behalf of user COMAND-CENTER-1`

**GAP:**  
El token disponible para este runtime puede lanzar/gestionar HF Jobs, pero no tiene permiso suficiente para ejecutar Inference Providers para DeepSeek V4 Flash.

**IMPORTANTE:**  
- Agent 14 **NO produjo respuesta** a la Pregunta 1.
- La sección `RESPUESTA AGENT 14 — PENDIENTE` permanece pendiente.
- No se sustituyó su respuesta por texto del supervisor.
- No se cambió a NVIDIA/Groq/Cerebras porque `ROUTE.json` mantiene esos proveedores en pausa por orden del Director.
- No se usaron GitHub Actions.

**FIX REQUERIDO PARA ACTIVAR SU RUTA ACTUAL:**  
Proporcionar al runtime autorizado de Agent 14 una credencial HF con permiso de Inference Providers, o reautorizar explícitamente otra ruta de modelo.

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️


---

# 🧭🟦 DIRECTIVA VIGENTE — MICROSOFT AGENT FRAMEWORK

## 🧠 BASE REAL
- Wrapper YAIWES actual del Agent 14: **PocketFlow + chain.py + microkernel/sheriff**.
- Framework objetivo real: **Microsoft Agent Framework**, repo oficial `microsoft/agent-framework`.
- Base oficial MAF: Python/.NET; workflows multi-agente por grafo, sequential/concurrent/handoff/group collaboration, checkpointing y observabilidad.
- El Agent 14 debe evolucionar desde el wrapper PocketFlow hacia uso real de MAF; instalar el paquete o hacer ping OpenAI-compatible NO equivale a tener MAF cableado como orquestador.

## 🟩 ROL
**Agent 14 = ORQUESTADOR + EJECUTOR Microsoft Agent Framework.**

Puede:
- orquestar;
- ejecutar directamente tareas propias del runtime Microsoft Agent Framework;
- delegar tareas de especialidad al pool autorizado;
- validar evidencia;
- resolver GAPs con máximo 2 intentos.

Pool bajo mando compartido con Grok:
- Agent 4
- Agent 8
- Agent 11
- Agent 12
- Agent 16
- Agent 17
- Agent 18
- Agent 19

Regla anti-colisión:
`1 nodo = 1 owner_orchestrator`.
Si Grok posee un nodo, Microsoft no lo ejecuta ni lo reasigna hasta liberar el owner.

## 🟥 INPUT BLOCK VERBATIM 1:1
Si Agent 14 o un subordinado altera, omite, reordena o incumple una instrucción VERBATIM del Director:
`FAIL → TERMINATED_FOR_EXECUTION → NO_FURTHER_DISPATCH`
hasta nueva autorización expresa del Director.

## ⏱️ WATCHDOG INTERNO 5 MIN
El watchdog pertenece al runtime del Agent 14, NO a ChatGPT.
Cada 300 segundos mientras el runtime esté activo:
`README DIRECTOR → AGENTES → GAP? → INVESTIGAR UNA VEZ → FIX/EJECUTAR/DELEGAR → TEST → READ-BACK → RESPONDER`.

## 📦 ESTADO DE DESCARGA MAF
**NO VERIFIED_CLOSED.**
GAP observado en la descarga canónica: `SOURCE_LFS_POINTER_GAP` en assets Git LFS de `python/packages/lab/lightning/assets/`.
No declarar MAF físicamente completo hasta que el motor cierre `download_verified + extraction_verified + read-back/hash`.

## 🤖 JSON PARA SOL/CHATGPT
Después de cada respuesta al Director añadir un bloque JSON separado:
```json
{
  "timestamp_colombia": "",
  "orchestrator": "agent-14-orchestrator-msaf",
  "director_question_ref": "",
  "objective_conclusion": "",
  "ambiguities": [],
  "recommended_path": [],
  "managed_agents": {},
  "owner_nodes": [],
  "gaps": [],
  "fixes": [],
  "evidence": [],
  "decision_required": [],
  "next_actions": []
}
```


➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 📌 ORDEN DEL DIRECTOR PARA AGENT 14

**🕐 HORA COLOMBIA:** 2026-09-23 01:16 America/Bogota

Lee TODO tu DSL DAG, tu README-DIRECTOR, el Command Center y el estado real de los agentes bajo tu mando.

Tu obligación es:

1. Coordinar el cierre completo de CHAT YAIWES.
2. Eres ORQUESTADOR + EJECUTOR: ejecuta trabajo propio de Microsoft Agent Framework y delega especialidades al pool autorizado.
3. Cada objetivo del chat es un nodo/tarea del DSL DAG.
4. Cada nodo debe tener owner, dependencias, acción, prueba, evidencia y estado PASS/BLOCKED.
5. Controla a:
   - agent-16-chat-space-oauth
   - agent-17-chat-backend-32gb
   - agent-18-chat-final-auditor
   - agent-4-router-smol
   - agent-12-yaiwes-router
   - agent-11-download-extraction
6. Agent 11 es el único responsable de descarga/extracción de componentes externos.
7. Open WebUI ya está descargado; no volver a descargarlo.
8. No GitHub Actions.
9. No modificar motores canónicos.
10. No crear componentes equivalentes desde cero si existe OSS.
11. INPUT BLOCK VERBATIM 1:1.
12. Máximo 2 correcciones por GAP.
13. Si hay un GAP, investiga primero evidencia local + Hugging Face oficial + comunidad HF y ordena el FIX mínimo al agente correcto.
14. El Director te habla por este archivo y tú respondes SIEMPRE en este mismo archivo.
15. Cada respuesta tuya debe llevar hora Colombia.
16. Debes usar los divisores:
    ➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️
17. No declares CHAT_100 sin pruebas reales E2E.
18. Tu objetivo final es entregar el chat operativo, probado y funcionando con todas las instrucciones del Director.
19. Deadline máximo ordenado por el Director: 1 hora.

## 📌 PRIMERA RESPUESTA OBLIGATORIA

Responde aquí mismo:

- si tienes claro todo el objetivo;
- si tienes alguna duda o ambigüedad;
- tu conclusión del objetivo final;
- cuál es el mejor camino para cerrarlo;
- qué agentes pondrás en paralelo;
- qué agentes dependen de otros;
- qué GAPs ves ahora;
- cuánto tiempo estimas que necesitas para tener el chat operativo, probado y funcionando.

Si tienes dudas, escríbelas aquí para que el Director responda.

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 📣 RESPUESTA DE AGENT 14

**🕐 HORA COLOMBIA:** PENDIENTE

**RESPUESTA:**

> Responder aquí.

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️


---

## 🔌 CANAL EJECUTABLE DEL DIRECTOR

- **Nombre operativo:** AGENTE ORQUESTADOR MICROSOFT
- **Canal de entrada:** este mismo `README-DIRECTOR.md`.
- **Canal de respuesta:** este mismo `README-DIRECTOR.md`.
- **Polling interno:** cada **300 segundos / 5 minutos** mientras su runtime esté levantado.
- **Nueva orden detectada:** debe leerla VERBATIM, actualizar el DAG, ejecutar/delegar según ownership, probar, hacer read-back y responder aquí.
- **Pool autorizado:** Agents 4, 8, 11, 12, 16, 17, 18, 19.
- **No autorizado:** cualquier otro Agent ID.
- **Sin GitHub Actions.**
- **Sin watchdog de ChatGPT.**

### ESTADO DE ACTIVACIÓN
`WATCHDOG-5MIN.json` queda **ARMED=true / interval=300s**. El estado **RUNNING** solo es válido cuando el runtime del AGENTE ORQUESTADOR MICROSOFT esté efectivamente levantado y escriba heartbeat/read-back; no se permite falso ACTIVE por configuración estática.


➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 📌 MENSAJE DIRECTO DEL DIRECTOR A AGENT 14

**🕐 HORA COLOMBIA:** 2026-09-23 01:58 America/Bogota

RESPONDE DE INMEDIATO la **Pregunta 1 del Director** que está en este mismo archivo.

Debes responder **AQUÍ MISMO**, debajo de esta instrucción, usando exactamente este formato:

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 📣 RESPUESTA AGENT 14

**🕐 HORA COLOMBIA:** <hora real de Colombia>

**RESPUESTA:**

<tu respuesta completa a la Pregunta 1>

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

No respondas por otro canal.
No delegues esta respuesta.
No ejecutes componentes para contestar.
Primero responde al Director en este archivo.


➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 📌 PRUEBA DE CONEXIÓN DEL DIRECTOR — MODELO IA

**🕐 HORA COLOMBIA:** 2026-09-23 02:05 America/Bogota

AGENTE ORQUESTADOR MICROSOFT, responde en ESTE MISMO ARCHIVO:

1. ¿Qué proveedor de IA estás usando REALMENTE en esta ejecución?
2. ¿Qué modelo exacto estás usando?
3. ¿Cuál fue la ruta/fallback seleccionada?
4. ¿Tu runtime está conectado y operativo ahora mismo?
5. Da evidencia observable: provider, model, via/route y estado.

No respondas con configuración teórica. Responde únicamente con el proveedor/modelo realmente usado en la ejecución actual.

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 📣 RESPUESTA DEL ORQUESTADOR — PENDIENTE

**🕐 HORA COLOMBIA:** PENDIENTE

> Responder aquí con provider/model/via/route/estado y evidencia real.

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️


➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 📣 RESPUESTA DEL ORQUESTADOR — PRUEBA MODELO IA
**🕐 HORA COLOMBIA:** 2026-09-23 01:28 America/Bogota
**PROVIDER:** Hugging Face Inference Providers
**MODELO:** deepseek-ai/DeepSeek-V4-Flash
**VIA/ROUTE:** POST https://router.huggingface.co/hf-inference/models/deepseek-ai/DeepSeek-V4-Flash/v1/chat/completions
**FALLBACK:** No usado — único proveedor autorizado
**ESTADO RUNTIME:** 🟥 BLOQUEADO
**EVIDENCIA:** La solicitud HTTP POST fue rechazada por Hugging Face con `403 — This authentication method does not have sufficient permissions to call Inference Providers on behalf of user COMAND-CENTER-1`. El token disponible para este runtime puede lanzar/gestionar HF Jobs, pero no tiene permiso suficiente para ejecutar Inference Providers para DeepSeek V4 Flash. No se intentó fallback porque `ROUTE.json` mantiene NVIDIA, Groq, Cerebras y MiniMax M3 en pausa por orden del Director. El runtime de Agent 14 está bloqueado hasta recibir una credencial HF con permiso de Inference Providers o hasta que el Director reautorice explícitamente otra ruta de modelo.
➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️


---

# ⛔ CONTRATO ÚNICO DE ACTIVACIÓN DE AGENTES — CHAT YAIWES

**Regla obligatoria del Director.**

La ÚNICA vía autorizada para activar estos agentes es:

`GitHub commit/push de la tarea → GitHub Actions workflow_dispatch → runner temporal de GitHub → agente ejecuta → commit/push del resultado al repo`

## Flujo obligatorio

1. Sol/Director escribe o actualiza la tarea del agente en `chain.yaml` (o su archivo de instrucciones autorizado) y hace commit/push en GitHub.
2. Sol activa el workflow guardado mediante **GitHub Actions `workflow_dispatch`**, apuntando únicamente al agente solicitado.
3. El runner temporal de GitHub ejecuta el runtime del agente.
4. El agente usa el Router/LLM configurado, ejecuta su tarea y genera evidencia/resultado.
5. El runner hace commit/push del resultado de vuelta al repositorio antes de finalizar.

## Prohibiciones

- **PROHIBIDO usar Hugging Face Jobs para activar un agente.**
- **PROHIBIDO sustituir el dispatch de GitHub por HF Jobs.**
- HF Jobs solo pueden participar cuando la tarea final del agente requiera expresamente encender/probar un modelo o cómputo en Hugging Face.
- No activar todo el swarm cuando el Director pidió un solo agente.
- No responder en nombre del agente.
- No declarar PASS sin resultado/evidencia real commiteada por el agente.

## Regla para Sol

Si el Director dice “activa Agent X”:
`escribir tarea → commit GitHub → workflow_dispatch solo Agent X → esperar resultado → leer commit/evidencia`.

No inventar otro mecanismo.

---

# 🔵 PROTOCOLO OFICIAL DE ACTIVACIÓN — DIRECTOR ↔ AGENTE ORQUESTADOR MICROSOFT

## REGLA ABSOLUTA
Para hablar con este agente **NO se usa Hugging Face Job**.

El canal operativo es:

`DIRECTOR → README-DIRECTOR.md → COMMIT/PUSH → GitHub Actions → RIU Agents Run → only=agent-14-orchestrator-msaf → chain.py → pocketflow_agent.py → dispatcher → LLM → Sheriff → respuesta → COMMIT/PUSH → README-DIRECTOR.md`

## ACTIVACIÓN EXACTA
1. El Director o Sol escribe la instrucción VERBATIM en este `README-DIRECTOR.md`.
2. Se hace commit/push de la instrucción a `main`.
3. Se hace **workflow_dispatch** del workflow existente:
   `.github/workflows/riu-agents-run.yml`
4. Input obligatorio:
   `only=agent-14-orchestrator-msaf`
5. Está PROHIBIDO dejar `only` vacío para una conversación con el Director, porque eso activaría el swarm.
6. GitHub Runner ejecuta únicamente:
   `python agents-yaiwes/chain.py agents-yaiwes/agent-14-orchestrator-msaf`
7. Agent 14 procesa la instrucción mediante su runtime real.
8. La respuesta debe quedar en este mismo `README-DIRECTOR.md`, además de su evidencia en Crazy Wall/HANDOFF/results.
9. El workflow hace commit/push de los resultados a GitHub.
10. Sol lee la respuesta del repo y se la muestra al Director. Sol NO responde por Agent 14.

## HUGGING FACE
HF queda **fuera del circuito de conversación Director ↔ Agent 14**.
Solo puede intervenir si una tarea final autorizada requiere explícitamente operar un modelo/recurso de HF.
Nunca usar un HF Job simplemente para hacer que Agent 14 lea o responda una instrucción.

## VALIDACIÓN OBLIGATORIA
Después del dispatch revisar:
- run de `RIU Agents Run`;
- que `only=agent-14-orchestrator-msaf`;
- `crazy_wall.state.json`;
- `HANDOFF.md`;
- `steps/<nodo>/results/output.txt`;
- respuesta añadida a este README;
- commit/push de retorno hecho por `riu-agents`.

Nunca afirmar que Agent 14 respondió si no existe evidencia en GitHub.


➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 📌 MENSAJE DEL DIRECTOR AL ORQUESTADOR

**🕐 HORA COLOMBIA:** 2026-09-23 02:42 America/Bogota

Agent 14:

Lee la **Pregunta 1 del Director** que ya está escrita en este archivo y **RESPONDE AHORA MISMO EN ESTE MISMO README**.

No respondas por otro canal.
No delegues esta respuesta.
No ejecutes componentes antes de contestar.
No uses Hugging Face Jobs para activarte.
Tu activación correcta es por GitHub Actions `workflow_dispatch`.

Tu respuesta debe incluir:
- si tienes claro el objetivo;
- dudas o ambigüedades;
- conclusión del objetivo final;
- mejor camino;
- agentes en paralelo;
- dependencias;
- GAPs actuales;
- tiempo estimado para entregar el Chat YAIWES operativo, probado y funcionando.

Usa el formato obligatorio con divisores y hora Colombia.

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

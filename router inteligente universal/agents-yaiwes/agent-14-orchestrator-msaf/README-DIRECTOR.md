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

# 🤖 AGENTE ORQUESTADOR GROK BUILD — README DIRECTOR

# 🟦 AUTORIDAD
Este archivo es el canal único de comunicación:
`DIRECTOR ↔ AGENTE ORQUESTADOR GROK BUILD` (`agent-15-orchestrator-grok`).

Si el Director escribe aquí directamente, o Sol/ChatGPT escribe exactamente en su nombre, Agent 15 responde SIEMPRE aquí y añade la respuesta sin borrar historial.

# 🧠 BASE TÉCNICA REAL
- Wrapper YAIWES actual: **SmolAgents**.
- Runtime objetivo real: **Grok Build** de `xai-org/grok-build`.
- Grok Build oficial está escrito principalmente en **Rust**.
- Runtime de agente: `crates/codegen/xai-grok-shell`.
- Herramientas: `xai-grok-tools`.
- Workspace/checkpoints: `xai-grok-workspace`.
- Soporta terminal/TUI, headless, ACP, edición de archivos, ejecución, búsqueda, tareas largas, MCP/plugins/hooks.
- El wrapper SmolAgents NO cuenta como Grok Build cableado: el objetivo es usar el runtime real descargado.

# 🟩 ROL
**Agent 15 = ORQUESTADOR + EJECUTOR Grok Build.**

Pool bajo mando compartido:
- Agent 4
- Agent 8
- Agent 11
- Agent 12
- Agent 16
- Agent 17
- Agent 18
- Agent 19

Regla: `1 nodo = 1 owner_orchestrator`.
No tocar un nodo cuyo owner sea Agent 14 hasta que Agent 14 lo libere.

# 🟥 INPUT BLOCK VERBATIM 1:1
Si Agent 15 o un subordinado altera, omite, reordena o incumple una instrucción VERBATIM del Director:
`FAIL → TERMINATED_FOR_EXECUTION → NO_FURTHER_DISPATCH`
hasta nueva autorización explícita.

# ⏱️ WATCHDOG INTERNO — 5 MINUTOS
Este watchdog pertenece al runtime del Agent 15, NO a ChatGPT.

Cada 300 segundos:
`READ README-DIRECTOR → READ AGENTS → GAP? → INVESTIGATE ONCE → FIX/EJECUTE/DELEGATE → TEST → READ-BACK → WRITE RESPONSE`.

Si existe GAP:
1. leer evidencia local;
2. investigar una sola vez Hugging Face oficial + comunidad HF + upstream OSS;
3. elegir FIX mínimo;
4. ejecutar si pertenece al runtime Grok Build o delegar al agente correcto;
5. probar y registrar evidencia.

# 📦 ESTADO DE DESCARGA GROK BUILD
**VERIFIED_CLOSED en la ejecución canónica reportada del motor.**
Evidencia reportada:
- source commit: `07e35a3dfeed2f200d319ef6c893b5ea286d9a51`
- ZIP SHA-256: `0a30eb6bef2482a1a7fbaba883b61562bde7c37ecd22d143eaa9d0288178a014`
- tree SHA-256: `e547e2b616102b5615d86fea7728d2726f16ebfe4889059c3b2a6590272c6ec2`
- files: 4125
- bytes: 77871279

# 🎨 MARCADORES PARA EL DIRECTOR
🟥 BLOQUEO · 🟧 GAP · 🟨 VALIDACIÓN · 🟩 PASS · 🟦 INFO · 🟪 DECISIÓN

# 🇨🇴 FORMATO OBLIGATORIO DE CADA RESPUESTA
➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 📣 RESPUESTA AGENT 15 / GROK BUILD
**🕐 HORA COLOMBIA:** `YYYY-MM-DD HH:MM America/Bogota`

**RESPUESTA:**
(texto)

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 📌 PREGUNTA 1 DEL DIRECTOR
➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

## ❓ PREGUNTA 1
¿Tienes completamente claro el objetivo y todos los nodos que debes coordinar?

1. Dime si existe alguna duda o ambigüedad.
2. Dame tu conclusión del objetivo final.
3. Dime cuál es el mejor camino para terminarlo.
4. Dime qué agentes pondrás en paralelo y cuáles tienen dependencias.
5. Dime tu estimación para tener el resultado operativo, probado y funcionando.
6. No declares 100% sin pruebas reales.

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 📣 RESPUESTA AGENT 15 — PENDIENTE
**🕐 HORA COLOMBIA:** `PENDIENTE`

> Agent 15 debe responder aquí.

➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 🤖 JSON PARA SOL/CHATGPT
Después de cada respuesta humana, añadir un bloque JSON separado:
```json
{
  "timestamp_colombia": "",
  "orchestrator": "agent-15-orchestrator-grok",
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


---

## 🔌 CANAL EJECUTABLE DEL DIRECTOR

- **Nombre operativo:** AGENTE ORQUESTADOR GROK BUILD
- **Canal de entrada:** este mismo `README-DIRECTOR.md`.
- **Canal de respuesta:** este mismo `README-DIRECTOR.md`.
- **Polling interno:** cada **300 segundos / 5 minutos** mientras su runtime esté levantado.
- **Nueva orden detectada:** leer VERBATIM → ownership → ejecutar/delegar → probar → read-back → responder aquí.
- **Pool autorizado:** Agents 4, 8, 11, 12, 16, 17, 18, 19.
- **No autorizado:** cualquier otro Agent ID.
- **Sin GitHub Actions.**
- **Sin watchdog de ChatGPT.**

### ESTADO DE ACTIVACIÓN
`WATCHDOG-5MIN.json` queda **ARMED=true / interval=300s**. Solo se considera **RUNNING** cuando el runtime de Grok Build publique heartbeat/read-back real en este archivo.


➡️➡️➡️➡️➡️➡️➡️➡️➡️➡️

# 📌 PRUEBA DE CONEXIÓN DEL DIRECTOR — MODELO IA

**🕐 HORA COLOMBIA:** 2026-09-23 02:05 America/Bogota

AGENTE ORQUESTADOR GROK BUILD, responde en ESTE MISMO ARCHIVO:

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

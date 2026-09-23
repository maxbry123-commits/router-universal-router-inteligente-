# README DIRECTOR — CANAL OFICIAL CON AGENT 14

## Autoridad

Este archivo es el CANAL ÚNICO de comunicación entre el Director y `agent-14-orchestrator-msaf`.

Jerarquía:

DIRECTOR
→ README-DIRECTOR.md
→ AGENT 14 ORQUESTADOR
→ AGENTES EJECUTORES

Respuesta:

AGENTES EJECUTORES
→ AGENT 14
→ README-DIRECTOR.md
→ DIRECTOR

## Regla obligatoria de comunicación

1. Si el Director escribe directamente en este archivo, Agent 14 DEBE responder en este mismo archivo.
2. Si Sol/ChatGPT escribe aquí EN NOMBRE DEL DIRECTOR, Agent 14 DEBE responder en este mismo archivo.
3. Agent 14 NO debe responder por otro canal como sustituto de este archivo.
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

Agent 14 **NO ejecuta el componente**. Coordina la resolución y obliga al agente correspondiente a ejecutarla/probarla.

## 🚫 PROHIBICIONES DEL WATCHDOG

- No GitHub Actions.
- No editar `.github/workflows/`.
- No usar el watchdog global antiguo como sustituto.
- No modificar motores canónicos.
- No crear componentes equivalentes desde cero cuando exista OSS.
- No escribir secretos en este README ni en JSON.
- No declarar `CHAT_100 = PASS` sin E2E real.

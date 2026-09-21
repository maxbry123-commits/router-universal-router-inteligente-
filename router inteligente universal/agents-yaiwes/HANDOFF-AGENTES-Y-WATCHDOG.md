# HANDOFF — AGENTES Y WATCHDOG (2026-09-21 13:15 UTC)

Público, sin claves. Instrucciones textuales del Director: `Claude notas/INPUT-VERBATIM-2026-09-21-*.md` (la última: `…-r-auditor-meta-agents-watchdog.md`).

## Cómo se opera (una sola vía)
1. Claude edita el DSL DAG de un agente (`<agente>/chain.yaml`) o la ruta central de modelos (`ROUTE.json`).
2. Despacha el workflow [`RIU Agents Run`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/actions/workflows/riu-agents-run.yml) (retoma solo los pasos pendientes).
3. Los agentes ejecutan, el Sheriff valida, y cada uno anota en `<agente>/crazy_wall.state.json`, `HANDOFF.md` y `steps/<paso>/results/`.
4. El [`RIU Watchdog`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/actions/workflows/riu-watchdog.yml) corre cada hora: escribe [`WATCHDOG/STATUS.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/WATCHDOG/STATUS.md), relanza a los pendientes (máx. 3 veces sin avance) y avisa a Claude.

## Agentes: dónde se les instruye / dónde responden
| Agente | Rol / marco | Instrucciones (DSL DAG) | Respuesta (estado) |
|---|---|---|---|
| 1 | chat · PocketFlow | [chain.yaml](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-1-chat-hf/chain.yaml) | [crazy_wall](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-1-chat-hf/crazy_wall.state.json) |
| 2 | chat · SmolAgents | [chain.yaml](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-2-chat-hf-smol/chain.yaml) | [crazy_wall](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-2-chat-hf-smol/crazy_wall.state.json) |
| 3 | HF (chat sin PRO) · PocketFlow | [chain.yaml](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-3-router/chain.yaml) | [crazy_wall](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-3-router/crazy_wall.state.json) |
| 4 | HF (modelos por pesos remotos) · SmolAgents | [chain.yaml](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-4-router-smol/chain.yaml) | [crazy_wall](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-4-router-smol/crazy_wall.state.json) |
| 5 | AUDITOR / checklist · SmolAgents (copia) | [chain.yaml](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-5-auditor/chain.yaml) | `agent-5-auditor/AUDIT-CHECKLIST.md` (cuando termine) |
README de cada uno (nombres del Director) en esta carpeta: `📂 readme agente 1 🧑‍🔧📶🛜.md`, `📂 readme agente 2  router 🧑‍🔧📶🛜.md`, `📂 readme agente router  3 🧑‍🔧📶🛜.md`, `📂 readme agente  router 4 🧑‍🔧📶🛜.md`.

## Estado real y GAPs (sonda 13:08 UTC)
- Chat: agente 1 CERRADO 3/3; agente 2 BLOQUEADO (era la ruta: Groq 1.ª clave inválida, NVIDIA saturada, Cerebras 402). HF: agente 3 CERRADO 3/3; agente 4 BLOQUEADO (misma causa). Corregido: `ROUTE.json` (Groq primero) y todas las claves útiles por proveedor; ronda de reintento + auditor despachada.
- Claves: Groq 6 de 7 sirven (la 1 da 401 → el Director debe revisarla); NVIDIA 5 de 5 autentican pero responden 503 (saturada); Cerebras 5 de 5 autentican pero responden 402 (pago requerido con `gpt-oss-120b`; `qwen-3.8-27b` sin probar).
- Vercel: el conector solo lee (crear despliegue, variables y claves = 403). Para el puente con Jev el Director debe dar permiso de escritura al conector, o crear una clave de AI Gateway y dársela al banco. "Lo de Vercel busca la manera / No puedes hacerlo" queda como frase ambigua: si "No puedes" significa "no lo intentes", se deja en pausa.
- Muse Glimmer 30B: existe `meta-models/Muse-Glimmer-30B-GGUF` con `Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf` (16.8 GB), modelo borrador `dflash-Muse-Glimmer-30B-Q4_K_M.gguf` (1.6 GB, decodificación especulativa) y `mmproj-Muse-Glimmer-30B-Q4_K_M.gguf` (1.4 GB, visión para MetaCua). Sin lanzar todavía (cuesta dinero en HF Jobs y falta el DSL DAG de los agentes de Meta).

## Plan más corto para terminar CHAT y HF (sin sobre-ingeniería)
1. Que cierren los agentes 2 y 4 (ruta corregida) → 5/5 con la cadena actual.
2. Auditor: `AUDIT-CHECKLIST.md` dice qué falta y qué agente falla; Claude convierte los PENDIENTES en nuevos pasos de `chain.yaml` (una cadena por agente).
3. Publicar el chat: Static Space (entregable del agente 3) + Job de HF con el Router (entregable del agente 4). Requiere token de HF con escritura y el visto bueno del Director para el gasto del Job.
4. LLM locales: repetir la auditoría con el paquete de modelos (registro del agente 4) y listar lo que el Director debe instalar.

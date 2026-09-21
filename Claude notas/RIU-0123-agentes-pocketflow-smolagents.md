# RIU-0123 — Paso 1 de la orden (p): los 4 agentes con PocketFlow y SmolAgents — 2026-09-21

Instrucciones textuales: `INPUT-VERBATIM-2026-09-21-o-…` y `INPUT-VERBATIM-2026-09-21-p-…`. Los agentes anteriores (`agent-microkernel/`, RIU-0122) NO se borraron: siguen disponibles (su workflow ahora ensambla el banco v2).

## Qué existe (`router inteligente universal/agents/`)
- `ORDERS.yaml`: el DSL DAG que Claude entrega. Claude solo edita este archivo y despacha `RIU Agents Run`.
- `runtime/run_agent.py`: un agente por proceso, según el marco que indicó el Director. `pocketflow`: grafo Generate >> Check (Sheriff), con bucle de corrección (reintento máx. 2). `smolagents`: `CodeAgent` con una herramienta `sheriff_check`, y después el Sheriff decide.
- `runtime/sheriff2.py` (Sheriff + `node --check` para JavaScript), `runtime/endpoint.py` (elige NVIDIA/Groq/Cerebras; respaldo DeepSeek V4 Flash / MiniMax M3).
- Reparto (mi suposición, dicha al Director; él no la corrigió): agente 1 y 3 PocketFlow, agente 2 y 4 SmolAgents.
  - `agent-1-chat` (PocketFlow): `vault_panel.js`, el panel del banco para la pestaña Claves.
  - `agent-2-chat` (SmolAgents): `jobs_panel.js`, el panel de trabajos en paralelo.
  - `agent-3-router` (PocketFlow): `node_monitor.py`, estados GREEN/YELLOW/DRAIN/CLOSED y elección de nodo (regla de RAM/CPU del Director).
  - `agent-4-router` (SmolAgents): `job_spec.py`, el Job de HF que sirve un GGUF montando `hf://models/…:/model:ro`.
- Cada agente escribe `agents/<id>/crazy_wall.state.json`, `result.json`, `HANDOFF.md` y `results/`.
- Tokens: el banco de ejecución v2 tiene 24 claves (NVIDIA, Cerebras, Groq, 2 de Hugging Face y 5 de GitHub). Está en `agent-microkernel/runtime-bank-v2.part1` + `.part2` (partido para publicarlo sin errores de copia; ambas mitades verificadas por huella). Sin la contraseña no se abre.

## Pendiente por orden (Paso 2 y 3)
Paso 2: auditar todas las instrucciones del Director (delegado a los agentes en la siguiente ronda de `ORDERS.yaml`), prioridad Chat, HF y modelos de IA en HF. Paso 3: puente en Vercel con el Router (bloqueado hasta que el Director conecte GitHub en Vercel; hoy no se toca por orden). Después: delegar y, si el trabajo pesa, crear 2 o 4 agentes más.

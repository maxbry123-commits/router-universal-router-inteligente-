# 📂 README — AGENTE 2 (CHAT) · SmolAgents

**Rol:** chat. Marco: SmolAgents. Ruta de modelos: NVIDIA / Groq / Cerebras; si toda la ruta falla, MiniMax M3 / DeepSeek V4 Flash.

## Dónde Claude le da las instrucciones (DSL DAG)
- Cadena de pasos: [`agent-2-chat-hf-smol/chain.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-2-chat-hf-smol/chain.yaml) (raw: https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/agents-yaiwes/agent-2-chat-hf-smol/chain.yaml)
- Se activa despachando el workflow [`RIU Agents Run`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/actions/workflows/riu-agents-run.yml).

## Dónde responde
- Estado (Crazy Wall): [`agent-2-chat-hf-smol/crazy_wall.state.json`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-2-chat-hf-smol/crazy_wall.state.json)
- Handoff: [`agent-2-chat-hf-smol/HANDOFF.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-2-chat-hf-smol/HANDOFF.md)
- Entregables por paso: `agent-2-chat-hf-smol/steps/<paso>/results/` (`jobs_panel`, `fixed_template`, `crazy_wall_chain`).

## Estado (2026-09-21, corrida `35577559436`)
BLOQUEADO en el paso 1 (`jobs_panel`), 0/3. Causa registrada en su Crazy Wall: el `ToolCallingAgent` de SmolAgents recibió NVIDIA error 500, Groq 401 (clave inválida), Cerebras 402 (pago requerido) y MiniMax M3 504 (tiempo agotado). Pendiente de corrección de ruta (ver `HANDOFF-AGENTES-Y-WATCHDOG.md`).

## Reglas
Claude solo edita `chain.yaml`; el agente ejecuta y anota. El PASS lo da el Sheriff determinista. Sin claves en estos archivos. Nada fuera de las instrucciones del Director.

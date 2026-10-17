# 📂 README — AGENTE 1 (CHAT) · PocketFlow

**Rol:** chat. Marco: PocketFlow (grafo Execute → Validate → fix, máx. 2 correcciones). Ruta de modelos: NVIDIA / Groq / Cerebras; si toda la ruta falla, MiniMax M3 / DeepSeek V4 Flash.

## Dónde Claude le da las instrucciones (DSL DAG)
- Cadena de pasos: [`agent-1-chat-hf/chain.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-1-chat-hf/chain.yaml) (raw: https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/agents-yaiwes/agent-1-chat-hf/chain.yaml)
- Se activa despachando el workflow [`RIU Agents Run`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/actions/workflows/riu-agents-run.yml).

## Dónde responde
- Estado (Crazy Wall): [`agent-1-chat-hf/crazy_wall.state.json`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-1-chat-hf/crazy_wall.state.json)
- Handoff del agente: [`agent-1-chat-hf/HANDOFF.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-1-chat-hf/HANDOFF.md)
- Entregables verificados por paso: `agent-1-chat-hf/steps/<paso>/results/` (`vault_panel`, `router_panel`, `wire_panels`).

## Estado (2026-09-21, corrida `35577559436`)
CERRADO 3/3: panel del banco → panel del estado del Router → cableado de paneles. Sheriff: `node --check` de JavaScript + comprobaciones de contenido.

## Reglas
Claude solo edita `chain.yaml`; el agente ejecuta y anota. El PASS lo da el Sheriff determinista, nunca el modelo. Sin claves en estos archivos. Nada fuera de las instrucciones del Director.

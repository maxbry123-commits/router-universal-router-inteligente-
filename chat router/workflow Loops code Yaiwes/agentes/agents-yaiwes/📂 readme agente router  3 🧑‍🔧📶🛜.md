# 📂 README — AGENTE 3 (HUGGING FACE: chat sin PRO) · PocketFlow

**Rol:** Hugging Face — el chat en HF SIN plan PRO (Static Space + OAuth, opción dada por el Director). Marco: PocketFlow. Ruta de modelos: NVIDIA / Groq / Cerebras; respaldo MiniMax M3 / DeepSeek V4 Flash.

## Dónde Claude le da las instrucciones (DSL DAG)
- Cadena de pasos: [`agent-3-router/chain.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-3-router/chain.yaml) (raw: https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/agents-yaiwes/agent-3-router/chain.yaml)
- Se activa despachando el workflow [`RIU Agents Run`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/actions/workflows/riu-agents-run.yml).

## Dónde responde
- Estado (Crazy Wall): [`agent-3-router/crazy_wall.state.json`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-3-router/crazy_wall.state.json)
- Handoff: [`agent-3-router/HANDOFF.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-3-router/HANDOFF.md)
- Entregables por paso: `agent-3-router/steps/<paso>/results/` (`space_readme`, `space_index`, `deploy_script`).

## Estado (2026-09-21, corrida `35577559436`)
CERRADO 3/3: README del Static Space con OAuth → `index.html` → `deploy_static_space.py`. Falta publicarlo en HF (requiere un token de escritura y decidir dónde vive el Router: un Job de HF con puerto expuesto).

## Reglas
Claude solo edita `chain.yaml`; el agente ejecuta y anota. El PASS lo da el Sheriff determinista. Sin claves en estos archivos. Nada fuera de las instrucciones del Director.

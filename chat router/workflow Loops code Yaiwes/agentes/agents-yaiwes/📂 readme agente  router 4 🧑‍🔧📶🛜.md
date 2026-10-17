# 📂 README — AGENTE 4 (HUGGING FACE: modelos locales por pesos remotos) · SmolAgents

**Rol:** Hugging Face — modelos por pesos remotos en Jobs (`hf://models/AUTOR/MODELO:/model:ro` + llama.cpp), registro de modelos y monitor de nodos. Marco: SmolAgents. Ruta de modelos: NVIDIA / Groq / Cerebras; respaldo MiniMax M3 / DeepSeek V4 Flash.

## Dónde Claude le da las instrucciones (DSL DAG)
- Cadena de pasos: [`agent-4-router-smol/chain.yaml`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-4-router-smol/chain.yaml) (raw: https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/agents-yaiwes/agent-4-router-smol/chain.yaml)
- Se activa despachando el workflow [`RIU Agents Run`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/actions/workflows/riu-agents-run.yml).

## Dónde responde
- Estado (Crazy Wall): [`agent-4-router-smol/crazy_wall.state.json`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-4-router-smol/crazy_wall.state.json)
- Handoff: [`agent-4-router-smol/HANDOFF.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/router%20inteligente%20universal/agents-yaiwes/agent-4-router-smol/HANDOFF.md)
- Entregables por paso: `agent-4-router-smol/steps/<paso>/results/` (`models_registry`, `job_spec`, `node_monitor`).

## Estado (2026-09-21, corrida `35577559436`)
BLOQUEADO en el paso 1 (`models_registry`), 0/3: mismo problema que el agente 2 (el `ToolCallingAgent` de SmolAgents no obtuvo respuesta válida de ningún proveedor). Pendiente de corrección de ruta.

## Siguiente (ya pedido por el Director, sin empezar)
Muse Glimmer 30B GGUF (`meta-models/Muse-Glimmer-30B-GGUF`, Q4_K_M 16.8 GB; el repo también trae un modelo borrador `dflash-…` de 1.6 GB para decodificación especulativa y un `mmproj-…` de 1.4 GB para visión) servido en un Job de HF con todos los aceleradores.

## Reglas
Claude solo edita `chain.yaml`; el agente ejecuta y anota. El PASS lo da el Sheriff determinista. Sin claves en estos archivos. Nada fuera de las instrucciones del Director.

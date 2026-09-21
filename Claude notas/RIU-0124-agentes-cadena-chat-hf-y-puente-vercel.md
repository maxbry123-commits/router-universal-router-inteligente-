# RIU-0124 — 2 agentes de chat + 2 de HF con cadena de pasos; puente Vercel–Jev — 2026-09-21

Instrucción textual: `INPUT-VERBATIM-2026-09-21-q-cadena-de-pasos-chat-hf.md`.

## Hallazgo (Q0): se repitió trabajo por los reinicios de la salida
Quedaron DOS implementaciones de los agentes, ambas de Claude: `agents/` (RIU-0123: ORDERS.yaml + runtime; su agente SmolAgents no cambia de proveedor cuando NVIDIA falla) y `agents-yaiwes/` (un `workflow.dag.yaml` por agente; es la que usa el workflow `RIU Agents Run`; su SmolAgents sí recorre ruta y respaldo). También hay tres anotaciones `INPUT-VERBATIM-2026-09-21-p-*`. NO se borró nada. Desde aquí se trabaja solo sobre `agents-yaiwes/`. Los agentes de `agent-microkernel/` (RIU-0122) siguen intactos (se les añadió la validación de JavaScript al Sheriff, compatible hacia atrás).

## Qué se entregó a los agentes (cada uno en su carpeta `agents-yaiwes/<agente>/chain.yaml`; el ejecutor es `chain.py`, fail-closed)
- CHAT — agente 1 (PocketFlow): panel del banco → panel del estado del Router → cableado de paneles (JavaScript, validado con `node --check`).
- CHAT — agente 2 (SmolAgents): panel de trabajos → plantilla fija (`fixed_template.py`) → Crazy Wall encadenado por hash (`crazy_wall_chain.py`).
- HF — agente 3 (PocketFlow): chat en Hugging Face SIN plan PRO (Static Space + OAuth, opción del Director): `README.md` del Space → `index.html` → `deploy_static_space.py`.
- HF — agente 4 (SmolAgents): registro de modelos por pesos remotos (`hf_models_registry.py`) → Job de HF con `hf://…:/model:ro` (`job_spec.py`) → monitor de nodos GREEN/YELLOW/DRAIN/CLOSED (`node_monitor.py`).
- Acceso: banco de ejecución con los 24 tokens (NVIDIA, Cerebras, Groq, 2 de Hugging Face, 5 de GitHub); lectura del archivo único o de sus partes v2 (`boot.py`).
- Ruta de modelos (orden del Director): NVIDIA / Groq / Cerebras; si falla toda la ruta, DeepSeek V4 Flash o MiniMax M3.
- Corrida despachada: run `35577559436` (`RIU Agents Run`). Resultado: ver `agents-yaiwes/<agente>/crazy_wall.state.json` cuando termine.

## Puente Vercel–Router para Jev (Q4)
- El proyecto GitHub→Vercel sigue bloqueado: la cuenta de Vercel no tiene la conexión de GitHub ("Login Connection").
- Se creó el proyecto vacío `riu-jev-bridge` (Vercel Auth desactivado). Crear despliegues en línea da 403 ("no tienes permiso para crear un Production Deployment") y crear variables de entorno da 404: el permiso del conector no llega hasta desplegar. El código del puente está en `vercel-jev-bridge/api/jev.js` (falla cerrado sin `BRIDGE_KEY`).
- Jev necesita `AI_GATEWAY_API_KEY` (o la autenticación automática del proyecto en Vercel). No probado.
- Desbloqueo: o el Director conecta GitHub en Vercel, o da al conector permiso de despliegue.

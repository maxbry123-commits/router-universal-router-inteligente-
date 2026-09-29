# T06 — Asistentes Hermes + OpenClaw

Adaptadores del chat/orquestador YAIWES. Hermes actúa como `planner_supervisor`; OpenClaw como `guardian_supervisor`. Ambos usan el grupo `assistants` del Router (NVIDIA/GLM/Groq/DeepSeek según su política; ninguna llamada directa a proveedores); no se configura Anthropic.

Flujo: `chat/orquestador → puente → Hermes/OpenClaw → Router `assistants` → eventos → State Hub/BITACORA`.

| Asistente | Rol | Función |
|---|---|---|
| Hermes | planner_supervisor | plan, critique, review, debate, delegate |
| OpenClaw | guardian_supervisor | plan, critique, review, debate, monitor, heartbeat |

El endpoint del chat que los consuma puede exponerlos bajo `/chat/agents`. `SIMULADO=1` evita red y escritura de estado durante pruebas.

Arranque: `bash arrancar_asistentes.sh`. Los forks quedan fijados por SHA real configurable con `HERMES_REF` y `OPENCLAW_REF`.

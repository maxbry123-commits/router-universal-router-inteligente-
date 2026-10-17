# 05 — Descarga con los motores de Antonio

Actualizado: 17-oct-2026 00:40, hora Bogotá (UTC-5). Índice: [README.md](README.md).

**Estado: PENDIENTE.** El agente backend ([03](03-BACKEND-CHATBOTS-EVOLUCION.md)) espera esta descarga antes de escribir código.

## Objetivo
Descargar/extraer con los motores de Antonio (**fuera** de la computadora del bot) estos componentes y producir la tabla:

`COMPONENTE → REPO → CARPETA → FUNCIÓN → LICENCIA → SIRVE / NO SIRVE PARA YAIWES`

## Componentes
| Componente | Repo | Carpetas | Agrupación de Antonio |
|---|---|---|---|
| Agent Zero | https://github.com/agent0ai/agent-zero | `plugins/_browser`, `plugins/_memory`, `skills`, `plugins` | memoria + plugins + skills + proyectos + multiagente |
| OpenManus | https://github.com/FoundationAgents/OpenManus | `app`, `run_flow.py`, `run_mcp.py`, `sandbox_main.py`, `protocol/a2a` | agente general + MCP + Flow + A2A + sandbox |
| OpenHands | https://github.com/OpenHands/OpenHands · https://github.com/OpenHands/software-agent-sdk · https://github.com/OpenHands/automation | SDK: `openhands-tools/openhands/tools/browser_use`, `openhands-agent-server` | runtime + estado + herramientas + aislamiento + automatización |
| Agent-S | https://github.com/simular-ai/Agent-S | `gui_agents`, `integrations/openclaw`, `tests` | Computer Use + GUI + percepción → acción |
| Browser Use | https://github.com/browser-use/browser-use | — | transversal |

## Evidencia
- ⚠️ Ya existe en main un inventario de otro agente: [`HANDOFF/CHATBOTS/COMPONENTES-OPENSOURCE.md`](../CHATBOTS/COMPONENTES-OPENSOURCE.md) (rama `docs/componentes-os`, PR #15, merge `fed11c3594`), con la tabla y licencias (MIT; Agent-S Apache-2.0). **Pero** no usó los motores de Antonio (fallback `git clone --sparse`) y el código quedó en la computadora del bot (`/workspace/componentes-os/`, 32 MB). Antonio debe decir si vale o se repite con sus motores fuera de la computadora del bot.

## Pendiente
1. Confirmar con Antonio si vale el inventario de `COMPONENTES-OPENSOURCE.md`; si no, descarga con los motores (no en la computadora del bot).
2. Tabla con licencia y veredicto SIRVE / NO SIRVE por carpeta.
3. Entregar la tabla al agente de [03](03-BACKEND-CHATBOTS-EVOLUCION.md).

## Reglas
- Una tarea = un agente, en su propia rama. Sin trabajo doble.
- Revisión ×3 por otro agente (conecta, prueba en PC y Android).
- Prueba en vivo Android 412 px, 4G, E2E real (Enviar → respuesta visible) **antes** de merge o deploy.
- No borrar nada sin el sí explícito de Antonio.
- No imprimir ni subir secretos (solo por nombre).
- No tocar la arquitectura: COMPONENTE → HARNESS (puente_chat) → HTTP → FICHA → MODELO.
- La computadora del bot es solo para pruebas de frontend.
- Español, mínimo, tiempos como «X s YYY ms». Al empezar y al terminar: actualizar PROGRESO en [`HANDOFF/CHATBOTS/HANDOFF.md`](../CHATBOTS/HANDOFF.md) y [`HANDOFF/TAREAS.md`](../TAREAS.md).

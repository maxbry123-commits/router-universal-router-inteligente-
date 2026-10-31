# Agentes
Destino: `plugins/agentes` (agents-yaiwes, sentinelas, microkernel, workflow-agentes), `09-CLAUDE-CODE` (puente de Claude Code), `plugins/orquestador`, `plugins/parallel`,
n8n, Prefect, Temporal, Durable-*, ruflo, rowboat, autogen, crewAI, langgraph, pydantic-ai, microsoft-agent-framework, haystack,
agentes listos (OpenHands, OpenManus, Agent-S, agent-zero, strix, artemis, rea, browser-use, CLI-Anything), investigación (agents-deep-research, open_deep_research, dzhng-deep-research, gpt-researcher), `componentes/fuentes-extraidas`.

## Qué quedó dónde
- `plugins/agentes/*` → `chat-router/agentes/agentes-yaiwes/` (05-AGENTES, 07-SENTINELAS, agent-microkernel, agents, agents-yaiwes, workflow-agentes).
  `plugins/agentes` queda como enlace simbólico a `../chat-router/agentes/agentes-yaiwes` (lo usa `router/tests/test_lifeguard.py`, protegido).
- `plugins/chat-router/09-CLAUDE-CODE` → `chat-router/agentes/claude-code/` (sin referencias externas; sin enlace).
- Pendiente de mover: plugins/orquestador, plugins/parallel, n8n, etc. (listados arriba).

## Completado de agentes listos (2026-10-31)
Motor usado: `motores/archivos` (`chat/backend/mvp/archivos`: `origen.clonar` clon superficial sin LFS + `acciones.copiar(sobrescribir=False)` con sha256). Solo se copiaron archivos AUSENTES (nada sobrescrito, sin `.git`, tope 20 MB). Comparacion: lista de archivos del upstream vs la carpeta local.

| Agente | Estado | Origen (commit) | Completado |
|---|---|---|---|
| SWE-agent | 385/409 identicos (mismo commit); faltaba `trajectories/` | github.com/SWE-agent/SWE-agent @ 3ea751c | +22 archivos (`trajectories/README.md`, demonstrations `.traj`, `docs/usage/coding_challenge_output.log`). Quedan 2 enlaces simbolicos upstream (`docs/assets/readme_assets`, `docs/config/index.md`): el motor no copia enlaces |
| codex | instantanea mas antigua que upstream (516 archivos distintos, 40 nuevos upstream) | github.com/openai/codex @ 67f0994 | +3 (`.vscode/*`). Los 37 nuevos de `codex-rs/` NO se mezclan: dependen de otros archivos modificados (mezclar versiones rompe la compilacion) |
| opencode | idem (806 distintos, 171 nuevos upstream, sobre todo `packages/core`) | github.com/anomalyco/opencode @ bf544cd | +5 (`.opencode/*`, `.vscode/*.example.json`). Resto = deriva de version, no truncado |
| OpenHands | completo (2725/2725 vs 852132d) | OpenHands/OpenHands | nada |
| openhands-software-agent-sdk | completo (1931/1931 vs fd26808) | OpenHands/software-agent-sdk | nada |
| claude-code | puente propio (pasarela Anthropic->NVIDIA); la CLI es binario npm sin codigo fuente en GitHub | npm `@anthropic-ai/claude-code` | nada que descargar |
| OpenClaw | sin carpeta en `agentes/` (adaptador `adaptadores/openclaw.py` habla con el Gateway existente) | github.com/openclaw/openclaw | nada |

Pendiente (instalar; fuera del alcance de descargar/extraer): ningun adaptador detecta los archivos descargados, buscan CLI/paquete instalado.
- codex: `npm install -g @openai/codex` y `RIU_CODEX_BASE_URL` (endpoint /responses). - opencode: `curl -fsSL https://opencode.ai/v2/install | bash`. - SWE-agent: `pip install -e "agentes/agentes-listos/SWE-agent/SWE-agent-main"` (+ Docker). - OpenHands: `pip install -e agentes-listos/openhands-software-agent-sdk/code/openhands-sdk -e .../openhands-tools` (o `RIU_OPENHANDS_PYTHON`). - claude-code: CLI ya en PATH; faltan `RIU_CLAUDE_PASARELA_URL` y `RIU_CLAUDE_PASARELA_MODELO` (arrancar `claude-code/pasarela.py`). - openclaw: Gateway en 127.0.0.1:18789 + `OPENCLAW_GATEWAY_TOKEN`.
Para llevar codex/opencode al upstream actual hay que reemplazar la instantanea completa (no mezclar): `archivos {"accion":"transferir","origen":"github.com/openai/codex","destino":"agentes/agentes-listos/codex/codex-main-nuevo"}`.

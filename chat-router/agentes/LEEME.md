# Agentes
Destino: `plugins/agentes` (agents-yaiwes, sentinelas, microkernel, workflow-agentes), `09-CLAUDE-CODE` (puente de Claude Code), `plugins/orquestador`, `plugins/parallel`,
n8n, Prefect, Temporal, Durable-*, ruflo, rowboat, autogen, crewAI, langgraph, pydantic-ai, microsoft-agent-framework, haystack,
agentes listos (OpenHands, OpenManus, Agent-S, agent-zero, strix, artemis, rea, browser-use, CLI-Anything), investigación (agents-deep-research, open_deep_research, dzhng-deep-research, gpt-researcher), `componentes/fuentes-extraidas`.

## Qué quedó dónde
- `plugins/agentes/*` → `chat-router/agentes/agentes-yaiwes/` (05-AGENTES, 07-SENTINELAS, agent-microkernel, agents, agents-yaiwes, workflow-agentes).
  `plugins/agentes` queda como enlace simbólico a `../chat-router/agentes/agentes-yaiwes` (lo usa `router/tests/test_lifeguard.py`, protegido).
- `plugins/chat-router/09-CLAUDE-CODE` → `chat-router/agentes/claude-code/` (sin referencias externas; sin enlace).
- Pendiente de mover: plugins/orquestador, plugins/parallel, n8n, etc. (listados arriba).

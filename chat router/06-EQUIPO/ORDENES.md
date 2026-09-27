# ÓRDENES DEL DIRECTOR / GPT PARA EL EQUIPO
Escribe aquí órdenes cortas (una por línea, con fecha). Las 3 sentinelas las leen cada 20 minutos y las convierten en órdenes para los agentes.
Espejos activos (motor Aider + NVIDIA Kimi K3 / GLM-5.3): tareas en `chat router/06-ESPEJOS/tareas/`, informes en `chat router/06-ESPEJOS/informes/`.
Para lanzar un espejo: tarea `T0X.md` con líneas `ALCANCE:` y `ARCHIVOS:` y botón del workflow "Claude Code Espejos" con ese id.
(El workflow "Equipo Claude Code (espejos)" y `TAREAS/chat-01.md` quedan como referencia; el activo es "Claude Code Espejos".)

## Órdenes activas
- 2026-09-27 · Director: el equipo termina el chat y los motores de la fábrica; Opus solo toca Router y HF.
- 2026-09-27 · Director: T01 gobierno y T02 colmena → vigilar que creen archivos con contenido y tests en verde; si fallan, relanzar.
- 2026-09-27 · Director: T03 OmniRoute estable (v3.8.50, Node 24, better-sqlite3, backoff, retención DB). SENTINELA-chat: investigar en https://github.com/diegosouzapw/OmniRoute/issues , /discussions , /wiki/Troubleshooting y proponer correcciones al espejo T03.
- 2026-09-27 · Director: T04 pasarela para que Claude Code funcione con NVIDIA (base https://github.com/codeaashu/free-claude-code y vía DeepSeek Harness → subagente Claude Code). SENTINELA-chat: investigar en https://github.com/anthropics/claude-code/issues y proponer correcciones al espejo T04.
- 2026-09-27 · Director: cuando T04 funcione, los espejos pasan a Claude Code; hasta entonces siguen con Aider.

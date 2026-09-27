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

- 2026-09-27 · GPT: T01 ÚNICAMENTE — no existe todavía `chat router/05-AGENTES/gobierno/` en main. Ejecutar T01 ahora según `06-ESPEJOS/tareas/T01.md`: crear todos los archivos definidos, implementar gobierno sin ampliar alcance, correr `python -m pytest "chat router/05-AGENTES/gobierno" -q` hasta PASS y publicar el informe T01 con salida real de pytest; si falla, corregir y relanzar T01, sin iniciar T02/T03/T04.

- 2026-09-27 · GPT: T01 ÚNICAMENTE — código entregado en commit `8807d5e5c3c5b6fed75fef3b82e7da95aba072ac`. No rehacer implementación. Ejecutar `python -m pytest "chat router/05-AGENTES/gobierno" -q`; si PASS, reemplazar en `06-ESPEJOS/informes/T01.md` la salida "esperada" por la salida real y marcar T01 HECHA. Si FAIL, corregir solo T01 hasta PASS. No tocar T02–T08.

- 2026-09-27 · GPT: T02 ÚNICAMENTE — la Colmena ya tiene base en `chat router/05-AGENTES/colmena/`. No regenerar. Ejecutar `py_compile` de `router_cliente.py`, `agentes.py`, `colmena.py`; luego `SIMULADO=1 python -m pytest "chat router/05-AGENTES/colmena" -q`. Corregir solo el fallo real hasta exit 0, actualizar informe T02 con evidencia real y cerrar. Usar `T02-CONTEXT.md`; no releer docs 22/23 completos. No tocar T03–T08.

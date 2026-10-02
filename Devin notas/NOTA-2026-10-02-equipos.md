# NOTA 2026-10-02 — Plan de 8 equipos para cerrar el backend

Escrita por Claude (Sonnet) a pedido del Director (instrucciones literales en main: `chat router/01-PLAN/INPUT-BLOCK-VERBATIM-2026-10-02-PLAN-7-EQUIPOS.md` y `...-ORGANIZAR-Y-8-EQUIPOS.md`).

## Qué pasó
- Se creó `chat router/📂 workflow Loops code Yaiwes/` como copia exacta de `chat router/wordflow loop code Yaiwes/` (mismo hash de árbol f8aee828; commit 7b52b8e). No se borró nada.
- Haiku no pudo hacerlo: su chat solo tenía Vercel MCP y no podía leer ni escribir en GitHub. Lo hizo Claude.
- Se crearon 8 equipos con cola de 12 tareas y un lugar donde escribir su resultado: `chat router/03-ESTADO/EQUIPOS/`.

## Dónde mirar (empezar por el leeme)
- Leeme y reglas: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/00-LEEME-EQUIPOS.md
- Plan de cierre: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/PLAN-CIERRE-BACKEND.yaml
- Esquema de trazabilidad: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/ESQUEMA-TRAZABILIDAD.json
- Carpeta de handoffs: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/HANDOFF

## Para el próximo Devin
- No se editaron a mano STATE.json, BITACORA.jsonl, CRAZY_WALL.json ni HANDOFF.md (los genera o mantiene el State Hub). Esos archivos todavía no mencionan la carpeta EQUIPOS; se puede agregar con el checkpoint oficial.
- La carpeta vieja `wordflow loop code Yaiwes` sigue existiendo; no borrar sin permiso del Director.
- Prohibido a todos: tocar el router, LFS git, GitHub Actions, Hugging Face.

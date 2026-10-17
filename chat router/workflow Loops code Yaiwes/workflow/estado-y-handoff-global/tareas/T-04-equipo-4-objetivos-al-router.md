# T-04 — Equipo de los 4 objetivos conectado al Router único (y su sentinela)
**Estado:** PENDIENTE · **Depende de:** T-03 · **Nodo:** N-04 · **Paso P1**

## Qué es, en palabras simples
El equipo de agentes que debe cumplir tus 4 objetivos está parado. Hay que conectarlo al Router único, reactivarlo y reactivar su sentinela. El trabajo propio del equipo del objetivo 4 lo hace ese equipo, no yo.

## Dónde estamos (verificado)
- 0 de 4 objetivos entregados. Solo P0-MONTAJE y P0-PRUEBA-PROVEEDOR pasaron (2026-09-21).
- PRs #23 y #24 del repo `agentes` abiertos desde el 21-sep.
- El loop (`agentes/Claude notas/PLAN-OPUS/runner/plan_opus_loop.py`) llama a los proveedores directo; NO usa el Router.
- La cadena anterior (agent-26) solo dio "GAP" y quedó con `router_connected=false`; ya está borrada.

## Cómo se hace
1. Reemplazar las llamadas directas a proveedores por el Router único: `LIVE_URL` + `/chat/send` (o `/chat/route`), con `Authorization: Bearer <HF_TOKEN_1>` y `X-API-Key: <RIU_ROUTER_API_KEY>`. Ya existe un cliente listo: `chat router/05-AGENTES/colmena/router_cliente.py` (`RouterCliente`, con prefijo `[ROL=…]`). Se reutiliza, no se escribe uno nuevo.
2. Los ejecutores (Claude Code, Codex, Open Code) usan la pasarela de Claude Code (`chat router/09-CLAUDE-CODE/pasarela.py`, traduce Anthropic → NVIDIA) y el plugin DeepSeek Harness. Tú dijiste que eso ya resuelve la puerta; no se abre otra.
3. Quitar del loop la descarga del banco por la ruta vieja `Chat%20Mvp/…` (queda innecesaria: las claves las tiene el Router).
4. Guardar los resultados en un lugar legible (bitácora del plan y `Estado y handoff global/`).
5. Reactivar la sentinela `plan4` (hoy en estado RESEARCH).
6. Primera corrida corta de prueba (1 nodo por grupo) y leer el resultado antes de soltar el loop.

## Listo cuando
Una vuelta del loop llega completa por el Router (aparece en `/chat/router/status`), deja resultado legible y la sentinela vigila.

## No hacer
Crear otro router o mini-router. Usar APIs de Anthropic. Poner claves en el repo.

## Evidencia (punto de partida)
`BITACORA.jsonl` B-0009 y `ESTADO.json` → `equipo_4_objetivos`.

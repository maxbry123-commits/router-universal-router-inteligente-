# 02 — Frontend del chat (Chat, ROOM, proyectos, UI)

Actualizado: 17-oct-2026 00:40, hora Bogotá (UTC-5). Índice: [README.md](README.md).

**Estado: ACTIVO**

## Objetivo
Terminar y probar en Android las piezas de frontend del chat: ROOM CONFERENCIAS, «Todos» en ROOM, «＋ Nuevo proyecto», escribir sin esperar y Skills Maxbry UI.

## Ramas y evidencia
| Rama | Qué | Evidencia / tests | Pendiente |
|---|---|---|---|
| [`wip/room-conferencias-rebase2`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/wip/room-conferencias-rebase2) ([`a014c943c0`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/a014c943c0)) | ROOM CONFERENCIAS + A−/A+ | 2×1 = 9 s 249 ms; 3×2 = 72 s 703 ms (412 px headless) | Android real |
| [`wip/room-todos`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/wip/room-todos) ([`604b2866f2`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/604b2866f2)) | «Todos» = 12 modelos; el usuario interviene | Todos = 92 s 872 ms | Preguntas: tope 6 y fila de 6 líneas |
| [`feat/nuevo-proyecto`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/feat/nuevo-proyecto) ([`2078388c18`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/2078388c18)) | «＋ Nuevo proyecto» en Clásico y paneles A/B/C; id + fecha vía `created_at` | — | 7 proyectos de prueba en la memoria real: **borrar solo con el sí de Antonio** |
| [`feat/escribir-sin-esperar`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/feat/escribir-sin-esperar) (`c99902c444`) · [`wip/room-escribir-sin-esperar`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/wip/room-escribir-sin-esperar) (`c086120187`) · [`orquestador-escribir-sin-esperar`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/orquestador-escribir-sin-esperar) (`626eb65024`) — ya en origin | Escribir sin esperar en Chat / ROOM / Chat BOTS | en curso | Revisión ×3 |
| [`wip/skills-maxbry-ui-rebase2`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/wip/skills-maxbry-ui-rebase2) ([`668f6f7442`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/668f6f7442)) | Skills Maxbry UI | 22/22 a 412 px | Pulir gooey-nav |

## Pendiente
1. Prueba Android real (412 px, 4G) de cada rama.
2. Respuestas de Antonio: tope 6 y fila de 6 líneas en ROOM «Todos».
3. Sí de Antonio para borrar los 7 proyectos de prueba.
4. Las 3 ramas «escribir sin esperar» ya están en origin; falta revisión ×3.

## Reglas
- Una tarea = un agente, en su propia rama. Sin trabajo doble.
- Revisión ×3 por otro agente (conecta, prueba en PC y Android).
- Prueba en vivo Android 412 px, 4G, E2E real (Enviar → respuesta visible) **antes** de merge o deploy.
- No borrar nada sin el sí explícito de Antonio.
- No imprimir ni subir secretos (solo por nombre).
- No tocar la arquitectura: COMPONENTE → HARNESS (puente_chat) → HTTP → FICHA → MODELO.
- La computadora del bot es solo para pruebas de frontend.
- Español, mínimo, tiempos como «X s YYY ms». Al empezar y al terminar: actualizar PROGRESO en [`HANDOFF/CHATBOTS/HANDOFF.md`](../CHATBOTS/HANDOFF.md) y [`HANDOFF/TAREAS.md`](../TAREAS.md).

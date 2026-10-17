# 01 — Backend de funciones del chat

Actualizado: 17-oct-2026 00:40, hora Bogotá (UTC-5). Índice: [README.md](README.md).

**Estado: ACTIVO**

## Objetivo
Cerrar los arreglos de backend del chat (identidad Nemotron, /memoria privada, latencia Ask consil, secretos/watchdog/MCP, Constitución) y dejarlos listos para revisión ×3, prueba Android y deploy.

## Ramas y evidencia
| Rama | Qué | Evidencia / tests | Pendiente |
|---|---|---|---|
| [`fix/nemotron-identidad`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/fix/nemotron-identidad) ([`931dce0831`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/931dce0831)) | Nemotron repite la identidad del modelo anterior. Causa: `_contexto()` en `plugins/puente_chat/plugin.py` no etiqueta qué modelo respondió cada turno | test 4/4 | Cubrir `_ck_cargar` («continúa») |
| [`fix/memoria-privada`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/fix/memoria-privada) ([`9cda0a39ef`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/9cda0a39ef)) | `/memoria` estaba abierta (3612 registros). Protección con PIN en cabecera `X-Memoria-Pin` | tests 5/5 + 4/4 | PIN ya dado por Antonio: guardarlo en el Space como `RIU_SECRETOS_PIN` cuando haya `HF_TOKEN` (sin imprimirlo) |
| [`wip/consil-latencia-rebase2`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/wip/consil-latencia-rebase2) ([`9169f1eaca`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/9169f1eaca)) | «Di solo: hola» con ancla: 7/9 llamadas → 1 | test 6/6 | Medir latencia real en el Space |
| [`secretos-watchdog-mcp-rebase2`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/secretos-watchdog-mcp-rebase2) ([`2605d4bdd3`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/2605d4bdd3)) | Secretos `/claves`, watchdog, MCP `/mcp` | 24 tests | **NO desplegar sin `RIU_SECRETOS_PIN`** |
| [`constitucion-contrato-rebase`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/constitucion-contrato-rebase) ([`b1e21a86c1`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/b1e21a86c1)) · [`constitucion-contrato-rebase2`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/constitucion-contrato-rebase2) ([`7ec6a92c69`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/7ec6a92c69)) · [`constitucion-contrato-rebase3`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/constitucion-contrato-rebase3) ([`1a218e6b3b`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/1a218e6b3b)) | Constitución sentinela (regla «termina con SENTINELA7») | sim 20/20 E2E y 10/12 + 2 corregidas | Elegir **una** de las tres. Solo cubre Qwen; falta DeepSeek, NVIDIA y Groq |

## Bug abierto (sin rama)
- En ROOM, la palabra «cambia» manda Ask consil al flujo largo: **189 s 720 ms**.

## Bloqueo
- Falta `HF_TOKEN` para deploy y medición real en el Space.

## Pendiente
1. Revisión ×3 de cada rama + prueba Android 412 px 4G.
2. Elegir rama de Constitución y extender a DeepSeek/NVIDIA/Groq.
3. Arreglar el bug «cambia» en ROOM.
4. Con `HF_TOKEN`: guardar `RIU_SECRETOS_PIN`, medir consil-latencia real, deploy.

## Reglas
- Una tarea = un agente, en su propia rama. Sin trabajo doble.
- Revisión ×3 por otro agente (conecta, prueba en PC y Android).
- Prueba en vivo Android 412 px, 4G, E2E real (Enviar → respuesta visible) **antes** de merge o deploy.
- No borrar nada sin el sí explícito de Antonio.
- No imprimir ni subir secretos (solo por nombre).
- No tocar la arquitectura: COMPONENTE → HARNESS (puente_chat) → HTTP → FICHA → MODELO.
- La computadora del bot es solo para pruebas de frontend.
- Español, mínimo, tiempos como «X s YYY ms». Al empezar y al terminar: actualizar PROGRESO en [`HANDOFF/CHATBOTS/HANDOFF.md`](../CHATBOTS/HANDOFF.md) y [`HANDOFF/TAREAS.md`](../TAREAS.md).

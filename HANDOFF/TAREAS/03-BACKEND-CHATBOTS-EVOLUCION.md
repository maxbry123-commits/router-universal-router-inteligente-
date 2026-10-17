# 03 — Backend de Chat BOTS / evolución (código)

Actualizado: 17-oct-2026 00:40, hora Bogotá (UTC-5). Índice: [README.md](README.md).

**Estado: EN PAUSA** (orden de Antonio). No retomar sin su orden.

## Objetivo
Backend de Chat BOTS (orquestador de agentes) y evolución de Grok Bot a nivel de código, reciclando componentes open source antes de escribir código propio.

## Ramas y evidencia
| Rama | Qué | Evidencia | Pendiente |
|---|---|---|---|
| [`orquestador-agentes-rebase`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/orquestador-agentes-rebase) ([`9dc637165f`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/9dc637165f)) | Plugin backend `plugins/orquestador` (Chat BOTS v2) | sandbox HF Jobs 6 s 627 ms; pruebas v1 (ver [arquitectura](../CHATBOTS/README-ARQUITECTURA.md)) | Red de HF Jobs: pendiente de respuesta de Antonio |
| [`wip/grokbot-evolucionado`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/wip/grokbot-evolucionado) ([`5778306623`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/5778306623)) | 24 propuestas + `research/grokbot-evolucionado/SINTESIS.md` | 24 imágenes `propuesta-01..24.png` | Pasar de propuestas a código |

## Pendiente
1. Mirror desde los enlaces de agentes: **Antonio debe decir de dónde vienen los enlaces**.
2. Respuesta de Antonio sobre la red de HF Jobs.
3. Reciclar componentes open source antes de escribir código: depende de [05-MOTORES-DESCARGA.md](05-MOTORES-DESCARGA.md).

## Reglas
- Una tarea = un agente, en su propia rama. Sin trabajo doble.
- Revisión ×3 por otro agente (conecta, prueba en PC y Android).
- Prueba en vivo Android 412 px, 4G, E2E real (Enviar → respuesta visible) **antes** de merge o deploy.
- No borrar nada sin el sí explícito de Antonio.
- No imprimir ni subir secretos (solo por nombre).
- No tocar la arquitectura: COMPONENTE → HARNESS (puente_chat) → HTTP → FICHA → MODELO.
- La computadora del bot es solo para pruebas de frontend.
- Español, mínimo, tiempos como «X s YYY ms». Al empezar y al terminar: actualizar PROGRESO en [`HANDOFF/CHATBOTS/HANDOFF.md`](../CHATBOTS/HANDOFF.md) y [`HANDOFF/TAREAS.md`](../TAREAS.md).

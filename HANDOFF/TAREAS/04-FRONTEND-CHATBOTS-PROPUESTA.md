# 04 — Frontend de Chat BOTS (propuesta)

Actualizado: 17-oct-2026 00:40, hora Bogotá (UTC-5). Índice: [README.md](README.md).

**Estado: ACTIVO** (aparte). Esperando que Antonio elija A o B.

## Objetivo
Rediseñar el frontend de Chat BOTS. Antonio aprobó crear agente + ficha y dijo: «el frontend no es así».

## Propuestas
- **A**: lista de agentes bajo el chat.
- **B**: pestañas como Chat 1/2/3.
- Capturas locales (computadora del bot, no en el repo): `/workspace/shots/chatbots-propuesta/` — A1, A2, A4, A5, B1, B2, B4, B7.

## Ramas
- Base: [`orquestador-agentes-rebase`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/orquestador-agentes-rebase) ([`9dc637165f`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/commit/9dc637165f)) (`orquestador.js`, `orquestador.css`).
- Rama de la propuesta: por confirmar (no hay rama en origin).

## Fallos actuales (en la rama base)
1. La tira queda encima del chat (`hist.before`).
2. `.orq-plus` con `display:flex` anula `hidden`.
3. `pintar()` no restaura `#orq-dep-repo`.
4. Solapes entre Selectores y «¿Qué hacemos hoy?».
5. Controles tapa la tira.

## Spec
- [PARCHE-RECUPERACION.md:101](../PARCHE-RECUPERACION.md#L101) y [:119](../PARCHE-RECUPERACION.md#L119), [TAREAS.md:40](../TAREAS.md#L42) (§5 «Chat BOTS bajo el chat abierto»; ahora línea 42).

## Pendiente
1. Elección A/B de Antonio.
2. Implementar la elegida con cambios milimétricos, corregir los 5 fallos, capturas 412 px.

## VENTANA DE ARQUITECTURA (orden de Antonio)

Orden de Antonio (verbatim, 17-oct-2026):

> Que haga una comparación investigación como funciona grockbot
> Luego la información que te di
> Luego los componentes que aporta sin sobre ingeniería
> Luego poda usa solo lo escencial
> Luego cablea y actuliza readme de arquitectura
> Borra la basura
>
> El agente backend pasa información a el agente de fromte el sistema chatbot debe tener
> 1. Una arquitectura interna usas skills archify lo descarga y lo usa dentro del chat dentro de chatbot luego crea una ventana de información donde está la pestaña de chatbot y va acrulizando creando la arquitectura de chat bot según
> 1. Fromtend aprobado
> 2. Backend lo que el agente le informa
> Luego el agente de fromtend dibuja en el diagrama el avance

Tarea del agente de frontend:
- Una ventana de información junto a la pestaña de Chat BOTS que muestra el diagrama de arquitectura de Chat BOTS (hecho con archify).
- El diagrama se actualiza según 1) el frontend aprobado y 2) lo que informa el agente backend en `chat router/chat bot/ESTADO-BACKEND.md`.
- El agente de frontend dibuja el avance en el diagrama.
- **Archify**: la skill más probable es [`tt-a1i/archify`](https://github.com/tt-a1i/archify) («Turn any idea, plan, or codebase into a beautiful interactive diagram. An agent skill for Claude Code, Codex, and more»). No está en los repos de Antonio. **Por confirmar con Antonio** que es esa.

## Reglas
- Una tarea = un agente, en su propia rama. Sin trabajo doble.
- Revisión ×3 por otro agente (conecta, prueba en PC y Android).
- Prueba en vivo Android 412 px, 4G, E2E real (Enviar → respuesta visible) **antes** de merge o deploy.
- No borrar nada sin el sí explícito de Antonio.
- No imprimir ni subir secretos (solo por nombre).
- No tocar la arquitectura: COMPONENTE → HARNESS (puente_chat) → HTTP → FICHA → MODELO.
- La computadora del bot es solo para pruebas de frontend.
- Español, mínimo, tiempos como «X s YYY ms». Al empezar y al terminar: actualizar PROGRESO en [`HANDOFF/CHATBOTS/HANDOFF.md`](../CHATBOTS/HANDOFF.md) y [`HANDOFF/TAREAS.md`](../TAREAS.md).


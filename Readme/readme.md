# router-universal-router-inteligente-

> **Código: GitHub (fuente única).** HuggingFace es **espejo + auto-pull mínimo** (lo mínimo para
> servir y actualizar la UI). Vercel publica la interfaz y dispara el trigger del watchdog al encender.
> Índice de navegación: [`CODE_INDEX.md`](../CODE_INDEX.md) · Cableado maestro: [`SATÉLITE CENTRAL CONECCION/SATÉLITE CENTRAL CONECCION.yaml`](../SAT%C3%89LITE%20CENTRAL%20CONECCION/SAT%C3%89LITE%20CENTRAL%20CONECCION.yaml).

app_file: router-mvp/mvp/app.py

## Qué es este repositorio

Router de chat y agentes con **Harness DeepSeek** como centro de distribución: el prompt raíz, las
fichas, los motores, los agentes, la cola, el loop y el watchdog. El cableado oficial vive en
`connections/` y el registro maestro en `SATÉLITE CENTRAL CONECCION/`.

## Las 11 entradas

| # | Componente | Ruta |
|---|---|---|
| 1 | Chatbot | `chat-router/chatbot/` |
| 2 | Chat Router (frontend y backend Chat YAIWES) | `chat-router/chat/frontend/` · `chat-router/chat/backend/` |
| 3 | SWE CODE free | `chat-router/SWE CODE free/` |
| 4 | SWE CODE | `chat-router/SWE CODE/` |
| 5 | Router MVP | `router-mvp/` |
| 6 | Router SWE CODE | `chat-router/SWE CODE/mini_router.py` |
| 7 | Harness DeepSeek | `chat-router/harness/` |
| 8 | Sistema central de conexión y cableo | `SATÉLITE CENTRAL CONECCION/` · `connections/` · `chat-router/MAPA.md` |
| 9 | Agentes | `chat-router/agentes/` |
| 10 | Loop, cola y watchdog | `chat-router/Loop cola wachdog/` |
| 11 | System prompt y motores | `router-mvp/raiz_fichas_prompt/` · `chat-router/motores/` |

## Handoffs

Índice único: [`handoff central/README.md`](../handoff%20central/README.md).

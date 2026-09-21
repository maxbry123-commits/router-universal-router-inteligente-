# RIU-0116 — ADENDA de evidencia (2026-09-21)

Actualiza `HANDOFF-PARCHE-RECUPERACION-2026-09-21.md` §2 (que se escribió antes de esta corrida).
- Pruebas en runner de GitHub (workflow `RIU NVIDIA Pool Test`, run `35548930018`, commit `5fbaf92`): 39 passed, 0 failed. Cubre: pool NVIDIA con cortacircuitos, resiliencia del Router (concurrencia adaptativa, hora pico de DeepSeek, cadenas con autorización, `/chat/route`, `/chat/router/status`), banco en memoria con TTL y bloqueo, API `/vault`, espejo de 14 agentes Wordflow, trabajos en paralelo con commit verificado, caché/uso/DAG y la API del chat.
- Correcciones hechas durante la sesión: orden de las claves del banco (commit `0fa2c51`); la salud de las claves se reinicia entre pruebas (`5fbaf92`).
- Sigue SIN verificar: chat en un navegador real, publicación en un servidor, Job de Hugging Face (ERROR sin log), modelos locales, Graphiti real.

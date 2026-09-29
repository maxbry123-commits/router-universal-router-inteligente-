# HANDOFF — 2026-09-29
Quien retome: lee esto, luego `ESTADO.json`, `CRAZY_WALL.json` y `BITACORA.jsonl` (misma carpeta). No inventes: si algo no está aquí, pregunta al Director.

## Reglas del Director (siempre)
- Seguir sus instrucciones textuales; sin alucinar, sin sobre-ingeniería; si hay duda, preguntar en texto plano (nada de widget de opciones: usa el móvil).
- Modelos SOLO por el Router único: NVIDIA (hasta 4 claves; Kimi K3 o más nuevo) → Groq → DeepSeek V4 Flash al final. Cerebras y OmniRoute eliminados. Sin APIs de Anthropic.
- Nunca claves en el repo (es público): solo nombres de secretos.
- Vercel = solo pantalla. No instalar nada hasta que todo esté listo; un solo deploy final, solo si él lo ordena.
- No tocar ni reiniciar el conector MCP (Space `claude-github-mcp-backup`). `keep-mcp-space-awake` sigue desactivado.
- Prohibido escribir código desde cero: podar, editar quirúrgico y cablear lo descargado.
- Respuestas cortas (~10 líneas), español simple. Explicar el cómo antes de hacer.

## Hecho y verificado (2026-09-29)
1. Router único vivo (Job HF, LIVE_URL en `ROUTER_JOB_PAUSE.flag`). Smoke: /health, /chat/models, /chat/router/status = 200.
2. Watchdog 32 GB (mató al Router) desactivado y borrado. Sentinelas y mini-router en pausa/borrados.
3. Repo limpiado (rama de respaldo previa; commits a53825c, 99e3104).
4. HF limpiado: omniroute-1..5 borrados; queda el Space MCP, el Job del Router y el dataset de memoria.
5. Vercel leído: cuenta maxbry123@gmail.com, proyecto `riu-jev-bridge`, sin deploy nuevo. Variables NO borradas (secretos irrecuperables y necesarios para el deploy final); decisión de borrarlas: "después".
6. Sistema de estado creado: ESTADO.json, CRAZY_WALL.json, BITACORA.jsonl, este HANDOFF, README-HUGGINGFACE.md.

## Estado del equipo de 4 objetivos
0 de 4 entregados. Solo P0-MONTAJE y P0-PRUEBA-PROVEEDOR en PASS (2026-09-21). PRs #23/#24 abiertos desde 09-21. La cadena agent-26 quedó con router_connected=false. El loop (repo agentes, `Claude notas/PLAN-OPUS/runner/plan_opus_loop.py`) llama proveedores directo, NO al Router.

## Pasos pendientes (en orden)
0. Organizar el repo en 2 raíces: Router (`router inteligente universal/`) y chat (`chat router/`). Antes, revisar dependencias: URL cruda de `Chat Mvp/secret_bank/vault.py` (la usa el runner de agentes), rutas del Job del Router, `vercel.json` huérfano. La raíz del Router debe poder moverse a otro repo.
   0b. Quitar Cerebras del código del Router (`providers.py`, `resilience.py`, `vault_bridge.py`) y poner Groq en la cadena. Requiere relanzar el Job (con permiso).
1. Reactivar el equipo de 4 objetivos cableado al Router único (LIVE_URL + `/chat/send` o `/chat/route`, cabeceras Bearer HF_TOKEN_1 + X-API-Key). Ejecutores vía pasarela de Claude Code (`chat router/09-CLAUDE-CODE/pasarela.py`) y plugin DeepSeek Harness. Reactivar su sentinela. El trabajo propio del equipo del objetivo 4 lo hace ese equipo.
   1b. Revisar que el archivo de arquitectura liste los 20 sitios de investigación; si no, elegir 20 y añadirlos a las fuentes del buscador (hoy 12).
2. Cadena: Rowboat → Ruflo → Claude Code → Grok → Claude Code → 4 Meta, con el plugin DeepSeek Harness al centro (ECC, Archify, Agent Skills, Ponytail pasados a esquema Sheriff/DSL DAG; Hermes/OpenClaw como sentinelas en paralelo).
3. Memoria de Manus + puente HF (SQLite → dataset privado `COMAND-CENTER-1/yaiwes-hf-memoria`).
4. ÚLTIMO y solo si lo ordena: deploy final en Vercel de los chats como una página "Riu".

## Abiertos / no inventar
- "Prompt Master": no verificado qué es. Buscar en `Notas del Director (verbatim)/`; si no aparece, decir que no se sabe.
- Rotar las 7 llaves de Groq que pegó en el chat.
- Lo del conector MCP hecho por Opus está documentado, no verificado por mí.

## Cómo se trabaja (herramientas)
- GitHub por conector: `github_api` (puede lanzar workflows), `create_or_update_file` (usa `current_sha` para actualizar). Errores 502: reintentar.
- Limpiezas grandes: workflow de una sola vez con PAT (el token por defecto no puede empujar archivos de workflow).
- Resultados de un run: leer anotaciones del check-run.

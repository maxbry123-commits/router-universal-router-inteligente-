# Handoff: skills, UI OpenClaw, Hermes y cableado de edificios

Solo URL y explicación.

## 1. Skill "Maxbry UI frontend"

**Resultado:** no encontrada en la rama de trabajo ni en `main` (carpeta de skills de frontend revisada).

- Carpeta revisada: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/Main_Skills/Frontend
- Skills de frontend que sí existen en esa carpeta: `ui`, `impeccable`, `playwright`, `shadcn-labs--skills`, `vercel-labs--agent-skills`, `webstudio`, entre otras.

Explicación: el nombre "Maxbry UI frontend" no está en el repo. La búsqueda por código no es fiable aquí (devuelve `incomplete_results`), así que la ausencia se confirma por rutas, no por búsqueda. Falta el enlace o la ruta exacta de la skill.

🚩 Pendiente: que el owner indique la URL o la carpeta de la skill.

## 2. Conexiones de la UI de OpenClaw

**Fuente:** https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/apk_config.json

Explicación: el archivo define las URL con las que la app se conecta a los dos edificios:
- Edificio 2, router: `https://comand-center-1-riu-router.hf.space`
- Edificio 2, MCP: `https://comand-center-1-riu-router.hf.space/mcp`
- Edificio 2, OpenClaw (WebSocket): `wss://comand-center-1-riu-router.hf.space:443/openclaw`
- Edificio 1, modelos: `https://comand-center-1-swe-code-s1.hf.space/v1/chat/completions` (y s2, s3)
- Cabecera de autenticación: `X-API-Key`. Tiempo máximo: 120 s.

Espejo de OpenClaw en el chat (prueba, no réplica en vivo): https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/chat/espejo/espejo_prod.js

🚩 El espejo corre en GitHub Actions (prohibido por el input block). La UI propia de OpenClaw no tiene ruta exacta en el repo.

## 3. Hermes (agente y enlace externo)

**Enlace externo oficial:** https://hermes-agent.nousresearch.com/ (Nous Research), citado en el README del plugin.

**Plugin en el repo:** https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Main_Skills/Code/headroom/code/plugins/hermes/README.md

Explicación: el plugin da a Hermes una herramienta `headroom_retrieve`, que recupera el contenido original de las salidas comprimidas por el proxy headroom. No es el cableado del router.

**Espejo de Hermes en el router:** https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/llm%20system%20HF/llm_router/agentes.py
- Usa la variable `HERMES_URL` (no hay URL fija en el código) y la clave `HERMES_API_KEY`.
- Expone la herramienta `agente_llamar`.

🚩 La URL de la instancia de Hermes del proyecto no está fijada en el repo. Hay que definirla en el entorno.

## 4. Edificio 1 (modelos locales)

**Plano:** https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/handoff/HF_PLAN_ROUTER2.md

Explicación:
- Tres Spaces: `COMAND-CENTER-1/swe-code-s1`, `s2`, `s3`.
- Cada uno ejecuta `llama-server` detrás de un proxy con cabecera `X-API-Key`.
- Código del proxy: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/llm%20system%20HF/manager.py
- Un modelo por Space. Si falla una llamada, salta al siguiente.

## 5. Edificio 2 (router, MCP y agentes)

Explicación:
- Space: `COMAND-CENTER-1/riu-router`.
- Expone el router (HTTP), el MCP y el WebSocket de OpenClaw.
- Registro del servicio y su estado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/SYSTEM_WIRING_REGISTRY.yaml
- Otros Spaces del mismo edificio: `swe-code-web` y `claude-github-mcp-backup`, listados en el plano: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/handoff/HF_PLAN_ROUTER2.md

## 6. Harness DeepSeek y cómo se cablea

**Plugin del harness:** https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/plugins/deepseek_harness/plugin.py

Explicación:
- Acción `invoke`: POST HTTP a `RIU_DEEPSEEK_HARNESS_URL` + `/invoke`.
- Acción `llm`: pasa por `puente_chat.llm_call`, la puerta común a los modelos. Nunca llama directo a un proveedor.
- Si falta la URL, responde `degraded` y no cae.

**Carpeta del harness:** https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat-router/chat/backend/deepseek_harness (`chat-router/harness` es un enlace simbólico a esta carpeta).

**Registro del cableado:** https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/SYSTEM_WIRING_REGISTRY.yaml

Flujo: frontend del chat → backend → Harness DeepSeek (HTTP) → modelo local (edificio 1) o externo (NVIDIA, Groq). El MCP del edificio 2 entra por el mismo registro.

## Flags 🚩
1. Skill "Maxbry UI frontend": falta URL o carpeta exacta.
2. Espejo de OpenClaw corre en GitHub Actions: prohibido.
3. UI propia de OpenClaw: sin ruta exacta.
4. URL de la instancia de Hermes: definir en el entorno.

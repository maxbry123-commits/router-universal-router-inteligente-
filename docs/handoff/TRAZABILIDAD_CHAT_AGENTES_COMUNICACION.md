# Trazabilidad: chat, espejo OpenClaw, agentes y comunicación entre edificios

Solo URL y explicación. Rama de referencia: `main` salvo que se indique otra.

## 1. Frontend del chat

**Carpeta:** https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat-router/chat/frontend

Explicación: es la UI del chat (Chat YAIWES). Contiene `shell.html` (página de entrada), `panel-chat.js` (panel del chat), `selector-modelos.js` (selector de modelos), `agentes-mirror.js` (interruptores de agentes), `ventana-mcp.js` (ventana MCP), `loop-panel.html` (panel del loop) y `vercel.json` (publicación en Vercel). Esta UI es la que el espejo prueba en producción.

## 2. UI de OpenClaw (espejo del chat)

**Script del espejo:** https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/chat/espejo/espejo_prod.js

Explicación: el archivo abre el chat de producción en un navegador de 345×700 px, pulsa cada botón (sin pulsar los que apagan, reinician o borran) y prueba cada selector de modelo. Genera capturas y un informe. **No es una réplica en vivo de la UI de OpenClaw.** Es una prueba de la web de producción.

Hallazgos:
- 🚩 El comentario del archivo dice que corre en GitHub Actions (`.github/workflows/espejo-chat.yml`). El input block prohíbe GitHub Actions. Hay que revisar ese workflow.
- 🚩 La UI real de OpenClaw (su propio frontend) no aparece en la rama de trabajo ni en `main` revisada. Falta la ruta exacta.
- 🚩 El espejo apunta a una URL de Vercel (`riu-jev-bridge.vercel.app`). Confirmar que es la de producción vigente.

## 3. Agentes en la raíz de agentes

**Raíz:** https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat-router/agentes

Subcarpetas de la raíz (todas en `main`):
- `adaptadores/`: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat-router/agentes/adaptadores (claude_code, codex, openclaw, opencode, openhands, swe_agent, dispatcher, workflows, contrato, disponibilidad, modelos).
- `agentes-listos/`, `agentes-yaiwes/`, `claude-code/`, `frameworks/`, `investigacion/`, `orquestacion/`, `runtime/`: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/chat-router/agentes

Espejo único de agentes (Hermes y OpenClaw), en la rama de trabajo: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/llm%20system%20HF/llm_router/agentes.py

Explicación: `agentes.py` define dos agentes (`hermes` y `openclaw`), cada uno con su URL y su clave por variable de entorno, y expone la herramienta `agente_llamar`.

Pendiente: las subcarpetas de `adaptadores/` no están conectadas al Harness DeepSeek todavía (tarea T-C). Cableado de las 9 tools de la raíz de tools: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/tools/__init__.py

## 4. Cómo se comunican los dos edificios

**Plano y roles:** https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/handoff/HF_PLAN_ROUTER2.md

- **Edificio 1 (modelos locales):** `COMAND-CENTER-1/swe-code-s1`, `s2`, `s3`. Cada Space corre `llama-server` detrás de un proxy con cabecera `X-API-Key`. Código del proxy: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/llm%20system%20HF/manager.py
- **Edificio 2 (router, agentes y puente web):** `COMAND-CENTER-1/riu-router`, `swe-code-web` y `claude-github-mcp-backup`. El router expone HTTP y MCP.

### HTTP

1. El chat (frontend) llama al backend en Vercel.
2. El backend llama al Harness DeepSeek por HTTP. Plugin: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/plugins/deepseek_harness/plugin.py
   - Acción `invoke`: POST a `RIU_DEEPSEEK_HARNESS_URL` + `/invoke`.
   - Acción `llm`: pasa por `puente_chat.llm_call` (la puerta común a los modelos). Nunca llama directo a un proveedor.
   - Si falta la URL, responde `degraded`; no cae.
3. El Harness llama al modelo: local (Edificio 1) o externo (NVIDIA, Groq).

### MCP

- El router expone un servidor MCP en el Space `COMAND-CENTER-1/riu-router`. Endpoint por variable `RIU_MCP_URL`, con autenticación `UNIVERSAL_KEY`.
- Ciclo: `initialize` → `notifications/initialized` → `tools/list` → `tools/call`.
- Registro del servicio y su prueba (14 herramientas, 2026-11-06): https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/SYSTEM_WIRING_REGISTRY.yaml
- 🚩 El registro dice que el MCP está en TESTING. No hay un servidor MCP en el repo de trabajo; el código del MCP está en el Space `claude-github-mcp-backup`, que no está en este repo.

### Arranque y registro

- El Space arranca con `entrypoint.sh` y trae su código del repo por auto-pull (rama `GITHUB_BRANCH`).
- El plano de conexiones está en el registro central: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/connections

## Flags 🚩 de esta trazabilidad
1. Workflow de GitHub Actions del espejo: prohibido por el input block.
2. UI real de OpenClaw: sin ruta exacta.
3. MCP sin servidor en el repo de trabajo.
4. Confirmar la URL de producción de Vercel del espejo.

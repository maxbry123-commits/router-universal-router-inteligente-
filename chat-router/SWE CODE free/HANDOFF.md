# HANDOFF — SWE CODE y SWEN CODE free

Para quien tome el trabajo (humano, OpenClaw o cualquier modelo). Leer en este orden: `ARQUITECTURA.md` ➡️ `INSTRUCCIONES.md` ➡️ este archivo.

## Dónde está todo

| Qué | Ruta (en `main`) |
|---|---|
| Arquitectura detallada | `chat-router/SWE CODE free/ARQUITECTURA.md` |
| Manual del agente (los 2 chats) | `chat-router/SWE CODE free/INSTRUCCIONES.md` |
| Cosas que el agente sabe hacer solo | `chat-router/SWE CODE free/agente.md` |
| Config, modos, aliases, cadena de respaldo | `chat-router/SWE CODE free/swen.json` |
| Activador/gramática | `chat-router/SWE CODE free/activar.js` |
| Provider del selector de OpenClaw | `chat-router/SWE CODE free/provider-openclaw.json` |
| Auto-evolución | `chat-router/SWE CODE free/evolucion.py` (+ `test_evolucion.py`) |
| Guía de auditoría X-Ray (v1 verbatim / v2) | `chat-router/SWE CODE free/GUIA_AUDITORIA_XRAY.md`, `…_V2.md` |
| Cascada + mini-router (respaldo Groq→NVIDIA) | `chat-router/SWE CODE/mini_router.py`, `cascada.json`, `motores.json` |
| Puente web (cuentas Qwen/DeepSeek) | `chat-router/SWE CODE/web-bridge/` |
| Puente móvil MCP↔WSS / APK | `chat-router/SWE CODE free/puente-movil/`, `apk-movil/` |
| Enrutado en el chat (ids, respaldo, catálogo) | `chat-router/chat/backend/mvp/swe.py` (+ `test_swe.py`) |
| Selector del chat (grupos) | `chat-router/chat/frontend/chat-selector-modelos.js` |
| Descarga de la APK | Panel Configuración → «13 · Agente móvil (APK)» (`chat-router/chat/frontend/panel-apariencia.html`), servida en `GET /apk` del Space |

## Estado

- Hecho y con pruebas: enrutado de los modelos SWE desde el chat, respaldo Groq ➡️ NVIDIA ➡️ HF local (Router y mini_router), identidad por plataforma, auto-evolución, catálogo del selector sin perder Qwen/DeepSeek/GLM.
- Del lado de HF (no es código): redeploy del Space al último `main` (`/health.commit`), ruta `GET /v1/queue` en el proxy, puente móvil como proceso, cuentas web entregadas por OpenClaw.

## Reglas que no se rompen

1. Dos raíces: `router-mvp/` y `chat-router/`. Nada nuevo en la raíz del repo.
2. Lo protegido (`cableado.manifest.json`) no se toca sin regenerar la guarda en el mismo commit.
3. Credenciales: solo del banco/entorno; nunca en código, prompts ni chat.
4. Sin PASS sin evidencia (curl, test, commit SHA).

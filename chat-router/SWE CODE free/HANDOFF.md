# HANDOFF — SWE CODE free y SWEN CODE

Leer en este orden: `README.md` ➡️ `ARQUITECTURA.md` ➡️ `INSTRUCCIONES.md` ➡️ este archivo.

## Dónde está todo (`chat-router/`)
| Qué | Ruta |
|---|---|
| Router propio (puente web) | `SWE CODE/web-bridge/src/server.js` (+ `motor.js`, `respaldo.js`, `bloques.js`, `sites.js`, `browser.js`, `cuentas.js`) |
| Pruebas del bridge | `SWE CODE/web-bridge/test/` (`node --test test/<archivo>`) |
| Cascada local + respaldo Groq/NVIDIA | `SWE CODE/mini_router.py`, `cascada.json`, `motores.json` |
| Manual, gramática, config | `SWE CODE free/INSTRUCCIONES.md`, `agente.md`, `activar.js`, `swen.json` |
| Selector de OpenClaw | `SWE CODE free/provider-openclaw.json` |
| Auto-evolución | `SWE CODE free/evolucion.py` |
| Puente móvil / APK | `SWE CODE free/puente-movil/`, `apk-movil/` |
| Descarga APK | chat ➡️ Configuración ➡️ «Agente móvil (APK)» (`chat/frontend/panel-apariencia.html`), `GET /apk` del Space |
| Enlaces de plugins | `plugins/swe_code`, `plugins/swen_code_free`, `plugins/deepseek_harness` |

## Cómo recuperar una sección o arreglar algo
1. `GET /health` y `GET /v1/queue`: cuentas cargadas, tabs vivas, `commit`.
2. `GET /v1/secciones`: qué `conv_id` están a medias. Reenviar el mismo `conv_id` y texto.
3. `content` vacío con cuentas OK ➡️ `GET /debug/tab?conv_id=` (url, título, captura). Gate «Confirma tu edad» ya se maneja.
4. `cuentas:{}` ➡️ OpenClaw no las envió: reenviar `cuentas` y `clave` en el POST.
5. `SESSION_EXPIRED` ➡️ el bridge ya reintenta; si persiste, `POST /refresh_session`.
6. `/health.commit` distinto de `main` ➡️ rebuild del Space (el Space clona `main` al arrancar).
7. Tras arreglar algo, registrarlo: `python3 "SWE CODE free/evolucion.py" registrar '{"codigo":"...","accion":"...","resultado":"PASS"}'`.

## Reglas
Dos raíces (`router-mvp/`, `chat-router/`). No se toca el Router MVP. Lo protegido por `cableado.manifest.json` no se toca sin regenerar la guarda. Credenciales solo en el banco o el entorno. Sin PASS sin evidencia.

## Pendiente fuera del código (HF / Grok)
Redeploy del Space al último `main`; ruta `GET /v1/queue` en el proxy `:7860`; `puente-movil` como proceso; `BRIDGE_STATE_DIR` en almacenamiento permanente; cuentas web entregadas por OpenClaw; saldo de HF.

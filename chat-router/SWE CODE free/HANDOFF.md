# HANDOFF — SWE CODE free y SWEN CODE

Leer en este orden: `README.md` ➡️ `ARQUITECTURA.md` ➡️ `INSTRUCCIONES.md` ➡️ este archivo. La cascada local de agentes (SWE CODE) está en `../SWE CODE/README.md`.

## Dónde está todo (`chat-router/`)
| Qué | Ruta |
|---|---|
| Router propio (puente web) | `SWE CODE/web-bridge/src/`: `server.js`, `motor.js`, `respaldo.js`, `bloques.js`, `cuentas.js`, `proyectos.js`, `memoria.js`, `formato.js`, `modos.js`, `consenso.js`, `sites.js`, `browser.js` |
| Memoria compartida con el chat | `SWE CODE/web-bridge/memoria_hf.py` (reutiliza `chat/backend/mvp/memoria.py`) |
| Formato de salida (copia única) | `chat/backend/mvp/prompts/FORMATO_SALIDA.md` |
| Pruebas | `SWE CODE/web-bridge/test/` (`node --test test/<archivo>`), `SWE CODE/web-bridge/test_memoria_hf.py`, `SWE CODE free/test_activar.test.mjs`, `SWE CODE free/test_evolucion.py` |
| Manual, gramática, config | `SWE CODE free/INSTRUCCIONES.md`, `agente.md`, `activar.js`, `documentos.js`, `swen.json` |
| Selector de OpenClaw | `SWE CODE free/provider-openclaw.json` |
| Entrada desde el chat Yaiwes | `chat/frontend/swe-directo.js` (selector: `chat-selector-modelos.js`) |
| Harness con salida por el bridge | `chat/backend/deepseek_harness/server.py` (`RIU_SWE_BRIDGE_URL`) |
| Auto-evolución | `SWE CODE free/evolucion.py` |
| Puente móvil / APK | `SWE CODE free/puente-movil/`, `apk-movil/`; descarga: chat ➡️ Configuración ➡️ «Agente móvil (APK)» (`chat/frontend/panel-apariencia.html`, `GET /apk` del Space) |
| Enlaces de plugins | `plugins/swe_code`, `plugins/swen_code_free`, `plugins/deepseek_harness` |

Estado del bridge en disco (`BRIDGE_STATE_DIR`, por defecto `./state`): `checkpoints/<conv_id>.json`, `proyectos/<proyecto>/ASESORIA.md`, `evolucion/lecciones.jsonl`, `perfiles/<sitio>/`, `cuentas-index.json`.

## Cómo retomar una sección
1. `GET /v1/secciones` ➡️ `conv_id` con `enviados/total` y `completo`. Los que tienen `completo:false` están a medias.
2. Reenviar `POST /v1/chat/completions` con el **mismo `conv_id` y el mismo texto** (y `cuentas`/`clave` si el bridge se reinició). Retoma desde el primer bloque no confirmado; si la tarea cambió o ya estaba completa, empieza de cero.
3. Antes de ejecutar, leer el plan: `GET /v1/proyectos` y `GET /v1/proyectos/<proyecto>` (`ASESORIA.md`). Para generarlo: `model: "swecode-asesoria"` con `proyecto`.
4. Leer el historial guardado: `GET /v1/memoria/<sesion>`. El historial de turnos con `conv_id`/`proyecto` queda en la memoria del chat (scope `chat-ui:hist:openclaw-<slug>`).

## Cómo diagnosticar o arreglar
1. `GET /health` y `GET /v1/queue`: cuentas cargadas, `respaldo: {groq, nvidia, hf_local}` (conteos), `state_dir`, tabs vivas.
2. `content` vacío con cuentas OK ➡️ `GET /debug/tab?conv_id=` (url, título, captura). El gate «Confirma tu edad» se maneja solo.
3. `aviso: CUENTAS_FALTAN` (o `/health` con `WEB_ACCOUNTS_VACIO`) ➡️ OpenClaw no envió `cuentas` y `clave`: reenviarlas en el POST (mientras tanto responde el respaldo).
4. `SESSION_EXPIRED` ➡️ el bridge ya reintenta una vez; si persiste, `POST /refresh_session`.
5. Código desactualizado en el Space (el `commit` de `/health` lo da el proxy del Space; el `/health` del bridge no lo devuelve) ➡️ rebuild del Space (clona `main` al arrancar).
6. `GET /v1/evolucion`: mejoras propuestas por lo que el bridge reparó solo (3 repeticiones); aplicarlas con un commit propio y registrar el resultado.
7. Tras arreglar algo: `python3 "SWE CODE free/evolucion.py" registrar '{"codigo":"...","accion":"...","resultado":"PASS"}'`.

## Reglas
Dos raíces (`router-mvp/`, `chat-router/`). No se toca el Router MVP. Lo protegido por `cableado.manifest.json` no se toca sin regenerar la guarda. Credenciales solo en el banco/vault de OpenClaw o el entorno. Sin PASS sin evidencia.

## Banco de claves (Groq/NVIDIA) sin tocar Hugging Face
- Chat ➡️ `GET/POST/DELETE /web/v1/claves` con `X-API-Key` (clave del chat). Vercel reenvía `/web/*` al Space (`vercel.json`); el proxy del Space lo manda al bridge. Solo devuelve conteos, nunca valores.
- El bridge exige `RIU_API_KEY` (o `RIU_PUBLIC_CHAT_KEY`/`RIU_MCP_KEY`/`RIU_ROUTER_API_KEY`) en su entorno; sin ella responde 503. Guarda cifrado en `BRIDGE_STATE_DIR/banco-swe.bin` y lo publica en la rama `banco-claves` (necesita `GITHUB_TOKEN`; un Space nuevo lo trae solo).
- El Router MVP lee ese banco en solo lectura (`externos.claves`), con la misma clave de acceso. Con ella, los selectores Groq y NVIDIA del chat usan las claves pegadas en Configuración o en la ventana «Banco de claves» (grupo `groq/…` o `nvidia/…`; reemplaza las de ese proveedor).
- `DELETE` solo vacía el banco propio; las claves del entorno o del Router siguen.
- Vercel necesita `RIU_ROUTER_API_KEY` y `HF_POWER_TOKEN` para `/api/power` (encender el Router desde el chat).

## Pendiente fuera del código (HF / Grok)
- Confirmar que el Space lanza el bridge en `:7870` (el código usa `BRIDGE_PORT`, por defecto 7860; el arranque del Space no está en este repo).
- Ruta `GET /v1/queue` (y las de `/v1/*` que usa el chat) en el proxy del Space; el proxy tampoco está en este repo.
- Redeploy del Space al último `main`; `BRIDGE_STATE_DIR` en almacenamiento permanente; `HF_TOKEN` y `mvp` importable para la memoria; `puente-movil` como proceso; cuentas web entregadas por OpenClaw; saldo de HF.
- Desde el chat Yaiwes (`swe-directo.js`) y el Harness no viajan `cuentas`/`clave`: los modelos `web-*` desde ahí solo funcionan si OpenClaw ya las inyectó en el proceso o están en el entorno; si no, responde el respaldo.

# web-bridge — SWEN CODE free

Puente OpenAI-compatible (puerto **7870**) que conduce las cuentas WEB de Qwen y DeepSeek
(chat.qwen.ai / chat.deepseek.com) desde un Space HF scale-to-zero y, si la web falla, responde con
Groq ➡️ NVIDIA ➡️ HF local (S1..S3). Es el router propio de SWE CODE free: no depende del Router MVP.
Documentación completa (arquitectura, recuperación, operación): `chat-router/SWE CODE free/`
(`README.md` ➡️ `ARQUITECTURA.md` ➡️ `INSTRUCCIONES.md` ➡️ `HANDOFF.md`).

## Acceso
Toda ruta salvo `GET /health` exige `x-api-key` con una de las 4 claves de acceso del chat
(`RIU_API_KEY`, `RIU_PUBLIC_CHAT_KEY`, `RIU_MCP_KEY`, `RIU_ROUTER_API_KEY`) o `BRIDGE_TOKEN`
(`Authorization: Bearer` / `x-bridge-key`). Sin ninguna configurada: 503; clave mala: 401.
`/v1/swe/*` exige `BRIDGE_TOKEN` (y `aprobar` y las tools con efectos, además un operador real: `x-operador` + su token individual en `x-operator-token`, verificado contra `BRIDGE_APROBADORES`).

## Flujo
- `POST /v1/chat/completions` con `model`:
  - `web-dsv4-flash` | `web-qwen37max` | `web-qwen38max` → objetivo directo
  - `swecode-consulta` → fan-out a los 3 + síntesis Qwen3.8Max
  - `swecode-revision|solucion|arquitectura|archivos|prompt_code|despliega|asesoria` → objetivo único
  - `groq/<id>` | `nvidia/<id>` | `lfm2.5-350m` | `qwen2.5-coder-1.5b` | `qwen3.5-0.8b` | `qwen3-0.6b` → modelo explícito (sin cambio de modelo en silencio; checkpoint por tarea)
  - `stream:true` → SSE real (`: keepalive` cada `BRIDGE_SSE_KEEPALIVE_MS`); continuación automática ante `finish_reason=length`; failover de claves/APIs (429/402/timeout).
- Entrada grande → bloques `[BLOQUE n/N · MODO X]` (~2500 chars) + `checkpoints/<conv_id>.json`
  en `BRIDGE_STATE_DIR` (montar almacenamiento permanente) → retoma tras reinicio
  (`POST /v1/secciones/<id>/retomar`, o solo al arrancar con `BRIDGE_AUTORETOMAR`).
- Modelos explícitos: checkpoint universal (`retomar_local.js` + `checkpoint_hf.js`: disco + Harness); `tarea_id` derivado de `conv_id`.
- Sesión caída → login con la cuenta actual; falla → rota al siguiente correo
  (cuentas y clave las entrega OpenClaw por llamada). Errores tipados: `SESSION_EXPIRED`,
  `SELECTOR_BROKEN`, `INPUT_NO_ENCONTRADO`.
- `POST /refresh_session` → chequea sesiones vivas (herramienta nativa del agente).
- Diagnóstico: `GET /health` (métricas por modelo: TTFT, tokens/s), `GET /v1/queue`, `GET /v1/modelos/disponibilidad`.
- También: `POST /v1/responses` (Codex), `/v1/swe/*` (OpenClaw ➡️ Harness), `GET /v1/openclaw`, `/v1/claves`.

## Variables de entorno
Las credenciales de las cuentas web son de OpenClaw y viajan por llamada (`cuentas`, `clave`); `WEB_ACCOUNTS`/`WEB_PASS`
son solo un respaldo y la regla del proyecto es no dejarlas en secrets del Space. Ninguna clave va al repo.
Resto (puerto, plazos, `RIU_SWE_TIMEOUTS`, estado, Harness, S1..S3): tabla en `SWE CODE free/HANDOFF.md`, «Variables del bridge».

## Pruebas
`node --test test/<archivo>` (carpeta `test/`) y, desde esta carpeta con `PYTHONPATH=<raíz>/router-mvp:<raíz>/chat-router`, `python3 -m unittest test_memoria_hf test_claves_banco`. Agentes y workflows: `python3 -m pytest chat-router/agentes/adaptadores/tests`.

## Pendiente honesto
- Los selectores `@@` en `src/sites.js` son candidatos genéricos: calibrarlos
  contra la página real en el primer arranque (la web cambia su DOM seguido).
- Login inicial por correo+clave vía script; si el sitio pide captcha/2FA,
  hay que resolverlo una vez manual (fallback: proxy residencial en `BRIDGE_PROXY`).

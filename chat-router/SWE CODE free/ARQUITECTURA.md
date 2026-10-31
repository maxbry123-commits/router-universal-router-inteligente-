# ARQUITECTURA — SWE CODE free y SWEN CODE

Cómo funciona, cómo se recupera y cómo trabaja OpenClaw con el web-bridge. La cascada local de agentes (codex/opencode/swe-agent/openhands) es de SWE CODE: `../SWE CODE/README.md`.

## Camino de una petición
- **OpenClaw** → `POST /v1/chat/completions` del web-bridge (`http://localhost:7870/v1`, ver `provider-openclaw.json`).
- **Chat Yaiwes** → `chat/frontend/swe-directo.js` hace `POST /v1/chat/completions` del mismo origen con `{model, messages, conv_id, proyecto?}` (los ids `hf-*`/`swe-*` del selector se traducen al modelo local real). No pasa por el Router MVP. Que el proxy del Space reenvíe esa ruta al bridge no está en este repo.
- **Vía Harness DeepSeek** (`chat/backend/deepseek_harness/server.py`, `RIU_SWE_BRIDGE_URL`, por defecto `http://127.0.0.1:7870`; vacío = desactivado): los ids `web-*`, `swecode-*` y los locales van al bridge enviando solo `{model, messages}` (sin `conv_id`, así que sin checkpoint ni memoria). Si el Router MVP cae, el Harness sigue por el bridge con un modelo local (`RIU_SWE_LOCAL_MODELO`), sin herramientas.

El puerto: el código arranca en `BRIDGE_PORT` (por defecto 7860, también en el `Dockerfile`); el Space lo lanza en 7870, que es lo que esperan Harness y OpenClaw.

## El web-bridge (router propio)
**POST `/v1/chat/completions`**, campos: `model`, `messages`, `conv_id`, `proyecto`, `cuentas`, `clave`, `documentos`, `modo`.
- `model`: `web-dsv4-flash` | `web-qwen37max` | `web-qwen38max` · `swecode-<modo>` · `groq/<id>` · `nvidia/<id>` · local `lfm2.5-350m` | `qwen2.5-coder-1.5b` | `qwen3.5-0.8b` | `qwen3-0.6b`. Otro id → 400 `MODELO_INVALIDO`. `GET /v1/models` los lista (ese es el selector de OpenClaw).
- Modos (8): `revision`, `solucion`, `arquitectura`, `archivos`, `prompt_code`, `consulta`, `despliega`, `asesoria`. Con `swecode-<modo>` el modo sale del id (modo inexistente → 400 `MODO_INVALIDO`; `swecode-plan` no existe); el campo `modo` solo cuenta con `web-*`. Cada modo es un preámbulo inyectado en el bloque 1.
- `swecode-consulta` = concilio: los 3 modelos web en paralelo + síntesis Qwen 3.8 Max. Los demás modos usan `qwen38max` (`SWECODE_OBJETIVO`).
- `conv_id` = una sección: tab propia y chat nuevo en la web (`BRIDGE_MAX_TABS`=4 por sitio, el resto espera en cola). Sin `conv_id` no hay checkpoint ni memoria.
- `documentos`: `[{nombre, contenido}]` o strings; se incrustan al prompt (máx 100 000 caracteres c/u).
- `cuentas` (lista o texto separado por comas) + `clave`: las credenciales son de OpenClaw y viajan en el POST; el bridge las recuerda en memoria del proceso (tras reiniciar hay que reenviarlas). `WEB_ACCOUNTS`/`WEB_PASS` en el entorno son solo respaldo; la regla del proyecto es no dejarlas en secrets del Space. Desde el chat Yaiwes no viajan: sin ellas responde el respaldo con `aviso: CUENTAS_FALTAN`.
- Respuesta: `choices[0].message.content` + `modelo_usado`, `via_respaldo` (`groq`|`nvidia`|`hf-local`|null), `aviso`, `archivo` (ruta del `ASESORIA.md` en asesoría); headers `x-modelo-usado`, `x-via-respaldo`.
- Errores: 400 `MODO_INVALIDO`/`MODELO_INVALIDO`, 502 `EMPTY_RESPONSE`, 503 `SESSION_EXPIRED`, 504 `UPSTREAM_TIMEOUT`, 500 el resto (p. ej. `RESPALDO_AGOTADO`).
- Otros: `GET /health`, `GET /v1/queue`, `GET /v1/secciones`, `GET /v1/proyectos[/<proyecto>]`, `POST /refresh_session`, `GET /debug/tab?conv_id=&shot=0|1`.
- Formato de salida: el bridge antepone `chat/backend/mvp/prompts/FORMATO_SALIDA.md` (una sola copia, ruta cambiable con `RIU_FORMATO_PATH`) salvo que ya venga en un mensaje `system`. Así Liquid, el chat y OpenClaw responden igual.

## Asesoría antes de ejecutar (`swecode-asesoria`)
Primero Groq (claves del chat; modelo `RIU_SWE_GROQ_MODELO`, por defecto `llama-3.3-70b-versatile`); si falla, la web con `qwen38max`; si todo falla, el respaldo general. Devuelve objetivo, plan numerado, mapa mental en texto, estructura a ejecutar y cómo resolver problemas probables, sin ejecutar nada. Cada asesoría se **agrega** a `BRIDGE_STATE_DIR/proyectos/<proyecto>/ASESORIA.md` (`proyecto` del POST; sin él, el `conv_id`; sin ninguno, `general`). OpenClaw la relee con `GET /v1/proyectos` y `GET /v1/proyectos/<proyecto>`.

## Respaldo (en este orden)
1. **Web**: el modelo pedido y luego `qwen38max → qwen37max → dsv4-flash`. Si la sesión cae, `salud()` hace re-login y rota al siguiente correo (misma clave).
2. **Groq → NVIDIA** (`GROQ_API_KEY`, `NVIDIA_API_KEY` y `*_1..20`; modelos `RIU_SWE_GROQ_MODELO` / `RIU_SWE_NVIDIA_MODELO`, por defecto `meta/llama-3.3-70b-instruct`).
3. **HF local** `lfm2.5-350m`: entra por `SWECODE_URL_S1` y salta a S2/S3.
4. Si todo falla: 500 `RESPALDO_AGOTADO`. El **APK móvil** (`puente-movil`, `POST /mcp`) es el último recurso **manual**: el bridge no lo llama.

Deadline por petición 100 s (`BRIDGE_DEADLINE_MS`); cada proveedor de respaldo 60 s (`BRIDGE_RESPALDO_MS`). Si el modelo pedido es `groq/…`, `nvidia/…` o local y falla, también cae al respaldo.

## Auto-reparación
- `SESSION_EXPIRED`: `salud()` (re-login o rotación de correo) y un reintento (50 s); si sigue mal, respaldo.
- Respuesta vacía, `UPSTREAM_TIMEOUT` (cierra la tab colgada del `conv_id`), `CUENTAS_FALTAN`, `SELECTOR_BROKEN`: respaldo, con el código en `aviso`.
- El perfil del navegador persiste en `BRIDGE_STATE_DIR/perfiles`.

## Retomar una sección
- Cada bloque (~2500 caracteres, cabecera `[BLOQUE n/N · MODO X]`) confirmado se guarda en `BRIDGE_STATE_DIR/checkpoints/<conv_id>.json` con la huella (sha256) del texto de la tarea.
- Solo se retoma un checkpoint **a medias y de la misma tarea**; uno completo o de otra tarea empieza de cero. Al retomar con tab nueva, el bridge envía una tarjeta `[RETOMO]` (bloques enviados y últimos 400 caracteres de salida) y sigue desde el primer bloque no confirmado.
- `GET /v1/secciones` lista `conv_id`, `modo`, `enviados`, `total`, `completo`, `ts` sin volcar contenido. OpenClaw retoma reenviando el **mismo `conv_id` y el mismo texto**.
- `BRIDGE_STATE_DIR` debe ser almacenamiento permanente (el `Dockerfile` usa `/data/state`).
- Cuidado: en el concilio los 3 modelos comparten el `conv_id` dado (misma tab y checkpoint); para trabajo paralelo usa un `conv_id` distinto por sección.

## Memoria compartida con el chat Yaiwes
Con `proyecto` o `conv_id`, cada turno (usuario y respuesta) se guarda en el bucket HF `COMAND-CENTER-1/yaiwes-memoria-storage`, scope `chat-ui:hist:openclaw-<slug>`, forma `{rol, texto, ts}` (`rol` = `user`|`bot`). Lo hace `memoria.js` llamando a `memoria_hf.py`, que reutiliza `mvp.memoria` (no hay almacén nuevo). Necesita `HF_TOKEN` y `mvp` importable por Python; si falta algo no guarda y no rompe la respuesta.

## Auto-evolución
El bridge anota cada arreglo propio (re-login, respaldo usado) en `BRIDGE_STATE_DIR/evolucion/lecciones.jsonl`; `evolucion.py` lee de ahí (o de `SWE_EVOLUCION_DIR`), también registra a mano (`registrar`) y propone mejora cuando el mismo (código, acción) se repite 3 veces (`proponer`, `md` → `PROPUESTAS.md`). Solo dentro de `SWE CODE/` y `SWE CODE free/`, nunca lo protegido por `cableado.manifest.json`.

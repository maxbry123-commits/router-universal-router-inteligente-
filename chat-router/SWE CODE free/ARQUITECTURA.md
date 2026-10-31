# ARQUITECTURA — SWE CODE free y SWEN CODE

Cómo funciona, cómo se recupera y cómo trabaja OpenClaw con el web-bridge. La cascada local de agentes (codex/opencode/swe-agent/openhands) es de SWE CODE: `../SWE CODE/README.md`.

## Camino de una petición
- **OpenClaw** → `POST /v1/chat/completions` del web-bridge (`http://localhost:7870/v1`, ver `provider-openclaw.json`).
- **Chat Yaiwes** → `chat/frontend/swe-directo.js` hace `POST` del mismo origen con `{model, messages, conv_id, proyecto?}` (los ids `hf-*`/`swe-*` del selector se traducen al modelo local real). `web-*` y `swecode-*` van por `/v1/chat/completions`; los locales HF, `groq/…` y `nvidia/…` por `/web/v1/chat/completions` (el proxy del Space manda `/web/*` siempre al bridge; por `/v1/*` un id sin prefijo `web-`/`swecode-` caería en el Router y daría 400 `MODEL_NOT_IN_CERTIFIED_REGISTRY`). No pasa por el Router MVP. El proxy del Space no está en este repo. Con `stream:true` (OpenClaw) el bridge responde SSE (`chat.completion.chunk` + `[DONE]`).
- **Vía Harness DeepSeek** (`chat/backend/deepseek_harness/server.py`, `RIU_SWE_BRIDGE_URL`, por defecto `http://127.0.0.1:7870`; vacío = desactivado): los ids `web-*`, `swecode-*` y los locales van al bridge enviando `{model, messages, conv_id}` (`conv_id` = la tarea del chat cuando existe, así hay checkpoint y memoria). Si el Router MVP cae, el Harness sigue por el bridge con un modelo local (`RIU_SWE_LOCAL_MODELO`), sin herramientas.

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
Primero Groq (claves del chat; modelo `RIU_SWE_GROQ_MODELO`, por defecto `qwen/qwen3.8-27b`); si falla, la web con `qwen38max`; si todo falla, el respaldo general. Devuelve objetivo, plan numerado, mapa mental en texto, estructura a ejecutar y cómo resolver problemas probables, sin ejecutar nada. Cada asesoría se **agrega** a `BRIDGE_STATE_DIR/proyectos/<proyecto>/ASESORIA.md` (`proyecto` del POST; sin él, el `conv_id`; sin ninguno, `general`). OpenClaw la relee con `GET /v1/proyectos` y `GET /v1/proyectos/<proyecto>`.

## Herramientas, memoria y mejora continua
- **Tools:** Groq, NVIDIA y los locales reciben las `tools` del POST y devuelven sus `tool_calls`; el Harness las ejecuta (GitHub, HF, motor de archivos, memoria) mientras el Router MVP esté vivo. Los modelos web (Qwen/DeepSeek) no producen tool_calls.
- **Memoria:** `GET /v1/memoria/<sesion>` lee el historial de OpenClaw de la misma memoria del chat (scope `chat-ui:hist:openclaw-<sesion>`).
- **Evolución:** `GET /v1/evolucion` lista las mejoras propuestas por lo que el bridge reparó solo (3 repeticiones); OpenClaw las aplica con su propio commit.
- **Retoma:** el checkpoint guarda la URL de la conversación web; al retomar se reabre esa misma conversación y, si no abre, sigue en un chat nuevo con la tarjeta [RETOMO].

## Sin tocar Hugging Face: encender el Router, claves y actualizaciones
- **Encender el Router:** la función de Vercel `/api/power` (en `chat/frontend/api/power.js`, ventana «Servidor» del chat) enciende, apaga o reinicia el Space. Necesita en Vercel `RIU_ROUTER_API_KEY` (la clave del chat) y `HF_POWER_TOKEN` o `HF_TOKEN_1`. Un Space dormido también se despierta solo con cualquier petición.
- **Banco de claves:** el bridge lee las claves de Groq/NVIDIA del banco del Router MVP (solo lectura) y de su banco propio cifrado (`BRIDGE_STATE_DIR/banco-swe.bin`), cada 60 s. Lo que pegas en Configuración se guarda ahí y se publica cifrado en la rama `banco-claves` del repo privado de GitHub (nunca en `main`, así no dispara reinicios). Un Space nuevo lo trae de GitHub al arrancar. Usa `GITHUB_TOKEN`, que el Space ya tiene.
- **Código al día:** el Router MVP, el bridge y el puente móvil se actualizan solos desde `main` cada 60 s.
- **Configuración de OpenClaw (solo lectura, sin secretos):** `GET /v1/openclaw` del bridge (con `x-api-key` del chat, igual que `/v1/claves`) devuelve el provider de `provider-openclaw.json` (sin `api_key`), los modos y alias de `swen.json`, los ids vivos de `/v1/models`, conteos de claves Groq/NVIDIA, el workspace (`ruta`, `existe`) y una `version` (hash) para detectar cambios. Se lee del clon de `main` (`RIU_OPENCLAW_DIR` lo cambia) y el vigilante de 60 s (`vigilarConfig`) la mantiene al día. Camino 1 (Vercel): `/web/v1/openclaw` (regla `/web/:path*` de `vercel.json`). Camino 2 (Space): la misma ruta por el proxy del Space, o `provider-openclaw.json` directo del clon.

## Respaldo (en este orden)
1. **Web**: el modelo pedido y luego `qwen38max → qwen37max → dsv4-flash`. Si la sesión cae, `salud()` hace re-login y rota al siguiente correo (misma clave).
2. **Groq → NVIDIA** (`GROQ_API_KEY`, `NVIDIA_API_KEY` y `*_1..20`; modelos `RIU_SWE_GROQ_MODELO` / `RIU_SWE_NVIDIA_MODELO`, por defecto `minimaxai/minimax-m3.1-flash`).
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
- Concilio con `conv_id`: cada modelo y el árbitro usan su propia tab y checkpoint (`<conv_id>-<modelo>`, `<conv_id>-arbitro`); no se mezclan.
- Gramática: si el último mensaje empieza con `SWEN CODE free [modo m] [solo modelo] [chat n] texto`, el bridge la interpreta (`activar.js`) y elige modelo, modo y sección; un modo o modelo inválido da 400 `ACTIVACION_INVALIDA`. `pipeline` se parsea pero lo ejecuta `SWE CODE/mini_router.py`, no el bridge.
- Con `groq/…`, `nvidia/…` o un local más `modo` (p. ej. `despliega`), el modelo recibe el preámbulo de ese modo.

## Memoria compartida con el chat Yaiwes
Con `proyecto` o `conv_id`, cada turno (usuario y respuesta) se guarda en el bucket HF `COMAND-CENTER-1/yaiwes-memoria-storage`, scope `chat-ui:hist:openclaw-<slug>`, forma `{rol, texto, ts}` (`rol` = `user`|`bot`). Lo hace `memoria.js` llamando a `memoria_hf.py`, que reutiliza `mvp.memoria` (no hay almacén nuevo). Necesita `HF_TOKEN` y `mvp` importable por Python; si falta algo no guarda y no rompe la respuesta.

## Auto-evolución
El bridge anota cada arreglo propio (re-login, respaldo usado) en `BRIDGE_STATE_DIR/evolucion/lecciones.jsonl`; `evolucion.py` lee de ahí (o de `SWE_EVOLUCION_DIR`), también registra a mano (`registrar`) y propone mejora cuando el mismo (código, acción) se repite 3 veces (`proponer`, `md` → `PROPUESTAS.md`). Solo dentro de `SWE CODE/` y `SWE CODE free/`, nunca lo protegido por `cableado.manifest.json`.

## OpenClaw como orquestador del chat Yaiwes, salida de tools y espejo de emergencia
**Orquestación (contrato, todo por el bridge OpenAI-compatible, proveedor `swecode` de `provider-openclaw.json`).** El chat envía la tarea al bridge con `{model, messages, conv_id, ejecutor_tools}` (`swe-directo.js`); `conv_id` es la sección/tarea y es la clave compartida: OpenClaw la ve en `GET /v1/secciones` (estado del checkpoint) y lee el historial del chat en `GET /v1/memoria/<sesion>`. OpenClaw orquesta plugins, tools y modelos con su propio runtime (el provider `swecode` para modelos; la entrada `mcp` del provider para las tools del Router) y devuelve el resultado al chat de dos formas: (a) respondiendo la misma petición `POST /v1/chat/completions` (el chat pinta `choices[0].message.content`), o (b) con `ejecutor_tools:"openclaw"`, devolviendo `tool_calls` que OpenClaw ejecuta y reenvía como mensajes `role:"tool"` al mismo `conv_id`. No hay canal de empuje bridge -> OpenClaw: OpenClaw consulta (pull) por `conv_id`.

**Salida de las tools (`ejecutor_tools`).** Selector «Salida: SWE | OpenClaw» (`swe-selectores.js`, `panel-chat.html`; hojas de SWE CODE y SWEN CODE free y panel Selectores, mismo estado), guardado en `localStorage["riu_swe_ejecutor_tools"]`, defecto `swe`, y enviado en CADA POST como `ejecutor_tools` (`swe` | `openclaw`; cualquier otro valor = `swe`). Contrato del bridge:
- `swe`: como hoy; el bridge devuelve los `tool_calls` del modelo (`finish_reason:"tool_calls"`) y el Harness/Router los ejecuta.
- `openclaw`: passthrough; el bridge devuelve los `tool_calls` tal cual al cliente OpenClaw (JSON y SSE), sin ejecutarlos ni reinterpretarlos, y marca la sección (`conv_id`) con estado `WAIT_TOOLS` hasta que llegue la siguiente petición con los resultados `role:"tool"`. Validación: `normalizarEjecutor()` de `web-bridge/src/openclaw.js`.

**Espejo de emergencia.** El chat Yaiwes es la fuente principal; la UI de chat de OpenClaw es el mirror. Si Vercel/Space no sirven el chat, OpenClaw usa el mismo código del Router MVP (`chat/backend/mvp`). `GET /v1/openclaw` devuelve la sección `espejo` (solo nombres, sin secretos): `router_url` (`RIU_ROUTER_URL`, defecto `http://127.0.0.1:7861`), cabecera de auth (`X-API-Key`, alternativas `Authorization: Bearer` y `?key=`; variables aceptadas `RIU_API_KEY`, `RIU_PUBLIC_CHAT_KEY`, `RIU_MCP_KEY`, `RIU_ROUTER_API_KEY`), endpoints (`/mcp`, `/plugins/{plugin}/call/{accion}`, `/almacen`, `/memoria/{save,load,search}`, `/chat/send` con el campo `constitucion`, `/health`, `/chat/ui/*`), tools MCP y plugins. Un test compara ese catálogo con `mcp_route.py`/`app.py`/`memoria.py` para detectar deriva. La entrada `mcp` de `provider-openclaw.json` da la URL (`${RIU_ROUTER_URL}/mcp`) y el nombre de la cabecera; el valor sale del entorno de OpenClaw (`RIU_API_KEY`), nunca del repo.

## Selectores de agente, modelo y workflow (contrato TareaSWE, YAIWES y OpenClaw)
Misma puerta para los dos chats: **chat → backend de su chat → Harness DeepSeek (`invoke`: `swe_iniciar|avanzar|estado|aprobar|reanudar`) → `agentes/adaptadores/`**. Catálogo y contrato únicos en `agentes/adaptadores/{modelos,contrato}.py`; el frontend solo los refleja y el servidor los valida.

**Controles (YAIWES, ventana existente de SWE CODE y SWEN CODE free, `swe-selectores.js`; mismo estado en ambas):** MODELO QUE RESPONDE · MODELO PARA TOOL · AGENTE QUE RESPONDE · AGENTE QUE EJECUTA · MODO AGÉNTICO ON/OFF · WORKFLOW (Individual | SWE CODE cuatro pasos | Liquid Mirror) y el botón de salida «Salida: SWE-agent | OpenClaw» (`ejecutor_tools`, hoy `swe|openclaw`), que es el mismo dato que AGENTE QUE EJECUTA cuando este vale `swe-agent` u `openclaw`. Se guarda en `localStorage["riu_swe_seleccion"]`. Los modelos del catálogo son `hf/lfm2.5-350m`, `hf/qwen2.5-coder-1.5b`, `hf/qwen3.5-0.8b`, `hf/qwen3-0.6b`, `groq/qwen/qwen3.8-27b` y `nvidia/{minimaxai/minimax-m3.1-flash, meta/muse-glimmer-30b, nvidia/nemotron-3-ultra-550b-a55b, z-ai/glm-5.3}`; los dos Llama ya no están. **Liquid Mirror** muestra dos participantes fijos, `LIQUID 1 — LECTOR` (S2) y `LIQUID 2 — EJECUTOR` (S3), ambos `lfm2.5-350m`, sin mezclar con los modelos web; el Harness los corre en secuencia (`ejecucion_s2_s3:"secuencial"`) y cada recibo trae el servidor real.

**Dos caminos.** Individual con modo agéntico OFF = el de siempre (`swe-directo.js` → `/v1|/web/v1/chat/completions` del bridge, modelo elegido en la lista). Workflow ≠ Individual **o** modo agéntico ON = el contrato `TareaSWE` exacto (15 campos) a `POST /chat/swe/iniciar`, luego `avanzar` paso a paso hasta `DONE`, `GAP`, `REQUIERE_APROBACION` o `RECONCILIAR` (tope 24 avances; el estado queda en el almacén del Harness en cada paso, se retoma con el mismo `task_id` por `reanudar`). El navegador nunca llama a una herramienta ni a un agente.
```json
{"task_id":"yaiwes-001","origen":"yaiwes","workflow":"swe_code","mensaje":"Revisar proyecto","modelo_responde":"hf/lfm2.5-350m","modelo_lector":"hf/lfm2.5-350m","modelo_tool":"hf/qwen2.5-coder-1.5b","modelo_revisor":"hf/qwen3.5-0.8b","agente_responde":"openclaw","agente_tool":"swe-agent","agente_verificador":"openhands","modo_agentico":true,"aprobacion":false,"sesion":"chat-001","proyecto":"yaiwes"}
```
OpenClaw envía **el mismo contrato** con `"origen":"openclaw"` (ejemplo `openclaw-001`, `workflow:"liquid_mirror"`, `modelo_tool:"hf/lfm2.5-350m"`); el backend no mantiene dos contratos. `aprobacion` sale siempre `false`: solo la da `swe_aprobar`.

| Chat | Entrada | Auth | Hacia el Harness |
|---|---|---|---|
| YAIWES | `POST /chat/swe/{iniciar,avanzar,estado,aprobar,reanudar}` y `GET /chat/swe/capacidades` (`chat/backend/mvp/app.py`, `harness_client.swe_invoke`) | clave de acceso del chat (`X-API-Key`) | `RIU_DEEPSEEK_HARNESS_URL` + clave del banco (`clave_harness()`, nunca al frontend); `modo_agentico` exige Agentes ON en el servidor |
| OpenClaw | `POST /v1/swe/{iniciar,avanzar,estado,aprobar,reanudar}` (`web-bridge/src/swe_rutas.js`, `llamarHarness`) | **`BRIDGE_TOKEN` obligatorio** (sin él 503 `BRIDGE_TOKEN_NO_CONFIGURADO`; `Authorization: Bearer` o `x-bridge-key`) | `RIU_DEEPSEEK_HARNESS_URL` + `RIU_API_KEY` solo en el backend, timeout 60 s (`RIU_SWE_HARNESS_TIMEOUT_MS`) |

Éxito `{ok:true, resultado}`; fallo del Harness 502 `{ok:false,error:{code:"SWE_HARNESS_ERROR",causa}}` (la causa es un código fijo: `HARNESS_HTTP_<n>`, `HARNESS_EJECUCION_FALLIDA`, `HARNESS_NO_DISPONIBLE`, `HARNESS_TIMEOUT`, `HARNESS_NO_CONFIGURADO`; jamás URL ni claves). Solo cruzan `task_id`, `origen`, `sesion`, `proyecto` (y el contrato completo en `iniciar`); `aprobacion`, `operador`, `estado` o `tool` del cuerpo se descartan.

**Aprobación.** `REQUIERE_APROBACION` trae `pendiente_aprobacion{op_id,paso,agente,modelo,permisos,objetivo}`; el chat muestra «Aprobar y continuar» que llama a `aprobar` con ese `op_id`. El **servidor** fija el operador (YAIWES: `RIU_SWE_OPERADOR`, por defecto `director`; bridge: cabecera `x-operador` o `RIU_SWE_OPERADOR`) y el Harness lo valida contra `RIU_SWE_OPERADORES`. `RECONCILIAR` (operación iniciada sin confirmar) se muestra como GAP y no se reintenta sin que un operador verifique.

**Disponibilidad real (nada se presenta como funcional sin adaptador).** El Harness debe informar en su `status` (`result.swe`): `{"agentes":{"codex":{"disponible":true,"modelos":["hf/qwen2.5-coder-1.5b"],"motivo":""}},"workflows":{"swe_code":{"disponible":true},"liquid_mirror":{"disponible":true}},"modelos":{"groq/qwen/qwen3.8-27b":{"disponible":false,"motivo":"no figura en GET /models"}}}`. `GET /chat/swe/capacidades` lo sanea contra el catálogo y el selector marca **NO DISPONIBLE** (opción deshabilitada) lo que no figura `disponible:true` (agentes y workflows) o figura `false` (modelos), e **incompatible** si el agente declara `modelos` y el elegido no está. Con la selección no disponible el envío se corta con `GAP: SELECCION_NO_DISPONIBLE` (no cambia en silencio de modelo ni de agente). **GAP abierto:** el `status` del Harness aún no emite `result.swe`, así que hasta entonces todos los agentes y workflows ≠ Individual salen NO DISPONIBLE.

**Interfaz OpenClaw:** `openclaw-ui/README.md` (solo contrato, endpoints y controles; el plugin lo genera quien tenga el runtime con `openclaw plugins init swe-selector --name "SWE Selector" --type feature`). Pruebas: `chat/frontend/test/swe-agentico.test.mjs`, `enviar-swe-agentico.test.mjs`, `chat/e2e/swe-selector.e2e.mjs` (sección H), `chat/backend/mvp/test_swe_yaiwes.py`, `web-bridge/test/swe_rutas.test.mjs`.

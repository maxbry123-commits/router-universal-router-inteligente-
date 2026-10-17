# Chat BOTS (orquestador de agentes) + ROOM CONFERENCIAS — arquitectura real

Actualizado: 17-oct-2026 00:35, hora Bogotá (UTC-5). Fuente: solo el código de las ramas citadas. Lo que no sale del código va marcado **por confirmar**.

- Chat BOTS: rama `orquestador-agentes-rebase` (`9dc637165f`, 4 commits sobre main: backend, frontend, tool `crear_agente`, pruebas). **No está en main.**
- ROOM CONFERENCIAS + A−/A+: rama `wip/room-conferencias-rebase2` (`a014c943c0`, 2 commits sobre main `55d9d95fb4`). **No está en main.**
- Handoff para agentes: [`HANDOFF.md`](HANDOFF.md). Bloque de Antonio: [`GROKBOT-FUNCIONAMIENTO-Y-MEJORAS.md`](GROKBOT-FUNCIONAMIENTO-Y-MEJORAS.md).

## 0. Ruta (no cambiar)

```
COMPONENTE → HARNESS (puente_chat) → HTTP → FICHA → MODELO
```

Chat BOTS, tal como está construido:

```
orquestador.js (COMPONENTE, sección #chat-bots)
  → POST /plugins/orquestador/call/<acción>       (Vercel reescribe /plugins → Space)
  → plugin orquestador (plugin.py)
  → HTTP POST <puente>/chat_async  y  <puente>/resultado   (HARNESS puente_chat)
  → FICHA (modelo de la lista MODELOS, ids "qw-…")
  → MODELO
```

- `<puente>` = `RIU_PUENTE_URL` o `RIU_ROUTER_URL` (o `http://127.0.0.1:$PORT`, por defecto 7860) + `/plugins/puente_chat/call` (`plugin.py`, `_puente`). Timeout HTTP 30 s.
- El plugin **no toca fichas** (docstring de `plugin.py`): siempre pasa por el harness.
- Al revés (chat → agentes): la tool `crear_agente` vive en `puente_chat/herramientas.py` y llama `plugins.orquestador.plugin.crear(...)` en el mismo proceso.

ROOM CONFERENCIAS: `room-conferencias.js` → `window.RIU_HARNESS` (la misma función del chat) → plugin `puente_chat` por HTTP (`chat_async` + `/resultado`) → `fichas_qwen` (fichas 1/2/3) o NVIDIA → modelo. Sin backend propio.

## 1. Archivos de Chat BOTS (rama `orquestador-agentes-rebase`)

| Archivo | Qué hace |
|---|---|
| `router inteligente universal/plugins/orquestador/plugin.py` (397 líneas) | Plugin: acciones, persistencia, llamada al harness, mirror, sandbox, deploy |
| `router inteligente universal/plugins/orquestador/sandbox.py` (154) | Ejecución de código: HF Jobs > Vercel Sandbox > local (bwrap / unshare / rlimits) |
| `router inteligente universal/plugins/orquestador/deploy.py` (124) | Enrutador de deploy GitHub / Hugging Face / Vercel y tokens cifrados |
| `router inteligente universal/plugins/orquestador/ficha.json` | Contrato `plugin_host/v1`: id `orquestador`, versión `0.2.0`, estado `testing`, `entry_point plugins.orquestador.plugin:handle`, `timeout_ms 90000`, acciones permitidas |
| `router inteligente universal/plugins/orquestador/__init__.py` | Paquete |
| `router inteligente universal/plugins/puente_chat/herramientas.py` (+16) | Tool `crear_agente(nombre, sistema, modelo)` para la LLM del chat |
| `router inteligente universal/plugins/puente_chat/capacidad.py` (+5) | Regex `_AGENTE` (`agentes?|bots?|chat bots|mirror|crear_agente`): sin intención externa devuelve `CAP_READ` en vez de `CAP_NONE`, así `crear_agente` queda visible cuando se habla de agentes |
| `chat router/chat frontend/orquestador.js` (137) | Frontend de la sección Chat BOTS |
| `chat router/chat frontend/orquestador.css` (34) | Estilos (incluye los de la ventana v1 `#ventana-orq`/`.orq-grid` y los de v2 `.chat-bots`/`.bots-tira`) |
| `chat router/chat frontend/shell.html` (+1) | `<link>` a `orquestador.css` |
| `chat router/chat frontend/shell.js` (+1) | `import "./orquestador.js"` |
| `tests_fix/orq_srv.py`, `orq_srv2.py` | Servidor local de prueba (puerto 8899) que sirve el frontend y el plugin; usa el puente real del Space |
| `tests_fix/orq_test.py` | Prueba Playwright 412 px de la **v1** (botón `#btn-orq`, ya no existe en v2: por confirmar si sigue sirviendo) |
| `tests_fix/orq_test2.py` | Prueba Playwright 412 px de la **v2** (tira `#bots-tira`, crear, hablar, ejecutar en sandbox, archivo, token falso) |

## 2. Endpoints (plugin `orquestador`)

Todas: `POST /plugins/orquestador/call/<acción>` con JSON; respuesta `{status:"ok", result:{…}}`. El frontend manda siempre `seccion` (la sesión del chat abierto).

| Acción | Entrada principal | Qué hace |
|---|---|---|
| `status` | — | Salud de la memoria (`sqlite.health()`), `max_por_seccion`, proveedor de sandbox, destinos de deploy con token (solo `true/false`) |
| `modelos` | — | `ficha: "ficha4-workflow-yaiwes"`, lista MODELOS y estados |
| `listar` | `seccion` | Agentes de la sección (vista corta) |
| `crear` | `nombre, sistema, modelo, icono` | Crea agente; error `MAX_AGENTES` si ya hay 50; `MODELO_NO_FICHA4` si el modelo no está en la lista |
| `chat_crear` | `pedido` | La LLM (`qw-qwen-3-8-flash`, sesión `orq-chat`, `max_tokens 600`) devuelve un JSON `{nombre, sistema, modelo}` y se crea el agente con `creado_por: llm-chat`. Espera hasta 80 s. Error `LLM_SIN_JSON` |
| `mirror` | `de` (`"chat"` o id de agente), `mensajes`, `modelo` | Crea una copia que trabaja en paralelo (ver §5) |
| `enviar` | `id, mensaje, max_tokens` (1200 por defecto) | Manda el hilo al harness (`chat_async`); error `AGENTE_OCUPADO` si ya tiene proceso |
| `estado` | `id, espera` (≤4 s) | Consulta `/resultado` y, al terminar, guarda la respuesta y la latencia |
| `aprobar` | `id` | Pasa el agente de `aprobacion` a `activo` |
| `configurar` | `id, modelo, sistema` | Cambia modelo y/o system |
| `subir` | `id, instruccion` o `nombre + datos_b64` (≤4 000 000 caracteres b64) | Añade instrucción o archivo (memoria + sandbox) |
| `archivos` | `id` | Lista nombre y bytes |
| `ejecutar` | `id, codigo` (si falta, el último bloque ```python del agente), `timeout_s` (30; tope 300) | Corre en el sandbox (§6) |
| `borrar` | `id` | Quita del índice, deja lápida `borrado:true` (el historial sigue en SQLite) y borra la carpeta sandbox |
| `token_guardar` | `destino, token` | Guarda el token cifrado (§7) |
| `deploy` | `id, destino, repo, rama, dry_run, confirmado` | Plan o despliegue de los archivos del agente (§7) |

## 3. Frontend (`orquestador.js`)

- **Montaje:** un `MutationObserver` crea `<div id="chat-bots" class="chat-bots">` **antes** de `#histories` (cambio quirúrgico, sin tocar `panel-chat.js`). Expone `window.RIU_ORQ = { orq, refrescar }`.
- **Base URL:** `localStorage.riu_orq_base` o `RIU_CONFIG.harnessUrl` sin `/plugins/puente_chat/call`. Cabecera `X-API-Key` si hay `sessionStorage.riu_clave`. Timeout 20 s (300 s para `chat_crear`, `ejecutar`, `deploy`).
- **Sección:** `seccionActiva()` lee la sesión del chip activo de `#chat-tabs` («sesión X» en el `title`) o `sessionStorage.riu_sesion` o `web-general`. Al pulsar otra pestaña de chat se recarga su propia sección de bots.
- **Tira** `#bots-tira`: «🤖 Chat BOTS N/50», un chip por agente (icono + semáforo + nombre) y `＋` (`#bots-nuevo`).
- **Formulario nuevo** `#orq-form-nuevo`: nombre, system, selector de modelo; «🧠 Crear con LLM» (`chat_crear`); «🪞 Añadir mirror» del chat abierto o de un agente.
- **Sub-chat abierto** `#orq-sec`: cabecera (icono, nombre, semáforo `#orq-sem`, estado, selector de modelo, ✕), info (system, memoria, archivos, creador, mirror de, última latencia «X s YYY ms»), **stream de 4 líneas** `#orq-stream`, hilo `#orq-hilo`, `+` (archivo o instrucción), 🎙 (SpeechRecognition `es-CO`), Enviar, ✅ Aprobar (solo en `aprobacion`), ▶ Ejecutar, 🪞 Mirror, 🗑 (con `confirm`), y `<details>` 🚀 Deploy.
- Con un panel abierto se **ocultan** `#histories` y `#composer` (el chat sigue debajo, oculto).
- **Repintado:** `pintar()` reemplaza todo el contenido de `#chat-bots` (`replaceChildren`) y solo restaura el valor de `#orq-input`, `+` abierto, deploy abierto y el foco. Si algún agente está `trabajando`, se repite cada 1 200 ms. (Por eso el campo repo `#orq-dep-repo` se borra al repintar: fallo visto en capturas.)
- Semáforo (`orquestador.css`): activo verde, trabajando azul con pulso, bloqueado naranja, aprobación amarillo con pulso, terminado gris, error rojo.

## 4. Agentes y FICHA

- Agente = dict con `id` (`ag-` + 8 hex), `seccion`, `nombre` (≤40), `icono`, `modelo`, `modelo_nombre`, `sistema` (≤4000), `estado`, `memoria_id` (`mem-<id>`), `archivos`, `instrucciones`, `mensajes`, `ejecuciones`, `stream` (últimas 40 líneas; la vista manda 4), `origen`, `creado_por` (`director` o `llm-chat`).
- **Tope: `MAX_AGENTES = 50` por sección** (`plugin.py`).
- Estados: `activo, trabajando, bloqueado, aprobacion, terminado, error`. Tras la respuesta: empieza con `[APROBACION]` → `aprobacion`; `[BLOQUEADO]` → `bloqueado`; si no → `terminado`. `CHAT_OCUPADO_REINTENTA` del harness → `bloqueado`.
- **Modelos (lista `MODELOS`, «ficha 4»):** `ficha-qwen38max`→`qw-qwen-3-8-max`, `ficha-qwen38flash`→`qw-qwen-3-8-flash` (por defecto), `ficha-qwen37max`, `ficha-qwen37plus`, `ficha-qwen36flash`, `ficha-dsv4pro`→`qw-deepseek-v4-pro`, `ficha-dsv4flash`, `ficha-glm52`→`qw-glm-5-2`. Qué ficha real del Router atiende cada id `qw-…`: **por confirmar** (lo decide puente_chat).
- **Mensaje al modelo** (`_mensajes_llm`): system del agente (o uno por defecto en español) + nombre, memoria y ruta del sandbox + reglas `[EJECUTAR]`, `[APROBACION]`, `[BLOQUEADO]` + instrucciones (≤2000 c/u) + archivos adjuntos (≤6000 c/u) + últimos 12 mensajes (≤6000 c/u).
- `enviar` llama `chat_async` con `sesion: agente-<id>`, `tools_habilitadas: false`, `request_id: orq-<id>-<n>` (idempotente). `estado` hace polling de `/resultado`; la latencia se mide en el plugin desde `t0`.

## 5. Mirror

- `mirror(de="chat")`: el frontend manda los últimos 12 elementos visibles de `#histories .chat-history:not([hidden])` (rol por clase CSS, ≤3000 caracteres); el agente nuevo recibe system «mirror del chat principal».
- `mirror(de=<id>)`: copia system, modelo, mensajes, instrucciones y archivos (re-subidos) del agente origen.
- Nombre `Mirror <origen>`, icono 🪞, `origen` = de dónde salió. Cuenta para el tope de 50.
- «Mirror desde los enlaces del agente»: **no existe en el código** (pendiente, ver HANDOFF §PROGRESO).

## 6. Sandbox (`sandbox.py`)

- Proveedor (`proveedor()`): `ORQ_SANDBOX=vercel` con `VERCEL_TOKEN` + `VERCEL_SANDBOX_PROJECT` → `vercel`; si hay token HF y `ORQ_SANDBOX≠local` → `hf-jobs` (**por defecto**); si no → `local`.
- **HF Jobs:** `POST /api/jobs/<RIU_HF_NS o COMAND-CENTER-1>`, imagen `python:3.12-slim`, `cpu-basic`, archivos <200 KB en base64, código en `ORQ_CODE`. Intenta `unshare -rn`; si no puede, la red queda **abierta** con bloqueo solo a nivel Python. Polling cada 3 s. Docstring: «5050 en 6 s 456 ms»; TAREAS: 6 s 627 ms.
- **Vercel Sandbox:** microVM, `networkPolicy deny-all`; docstring: la cuenta Hobby devuelve 402 hasta 2026-11-01.
- **Local:** bubblewrap (sin red, `/` solo lectura) > `unshare -rn` > solo rlimits (CPU 20 s, 768 MB, archivos 20 MB, 64 procesos). Entorno vacío: el código nunca recibe secretos.
- Carpeta: `RIU_ORQ_DIR` o `/tmp/riu-data/orquestador` + `/sandbox/<id>/archivos`; se rematerializa desde la memoria si se perdió.
- Decisión abierta de Antonio sobre la red de HF Jobs (TAREAS §2).

## 7. Deploy (`deploy.py`)

- Destinos: `github`, `hf`, `vercel`. Token: RAM → cifrado en memoria (scope `chat-ui:orq:gov:tokens`, scrypt + AES-256-GCM con `RIU_VAULT_PASSPHRASE` o `FICHA_CLAVE_BANCO`) → `providers.env_keys` → entorno (`GITHUB_TOKEN`/`GH_TOKEN`, `HF_WRITE_TOKEN`/`HF_TOKEN`, `VERCEL_TOKEN`). Nunca se devuelve ni entra al sandbox; los errores HTTP reemplazan el token por `***`.
- Sube los archivos de `sandbox/<id>/archivos`. `dry_run` → `estado: plan`. Sin `confirmado: true` → `FALTA_CONFIRMACION` (el botón «Desplegar» pide `confirm()` cada vez).
- GitHub: `PUT /repos/<repo>/contents/<archivo>` por archivo en `rama` (por defecto `main`). HF: commit NDJSON a `models|spaces|datasets/<repo>`. Vercel: `POST /v13/deployments` con `target: preview`.

## 8. Almacenamiento / memoria

- Sin SQLite propio: todo va a la fachada `memoria_yaiwes` (`integration.chat_mvp.memoria_loader._memory()`), la misma del chat: SQLite `riu_chat.sqlite3` → réplicas (grafo fallback, state-hub) → sync al bucket `yaiwes-memoria-storage` → restauración en frío (docstring de `plugin.py`). La RAM (`_CACHE`) es solo caché.
- Scopes: `chat-ui:orq:<seccion>` (claves `indice`, `agente:<id>`, `archivo:orq:<id>:<nombre>`), `chat-ui:orq:secciones` (`lista`), `chat-ui:orq:gov:tokens`.
- `_guardar(replicas=True)` usa `facade.save`; los latidos del stream usan solo `sqlite.save`. Las claves `archivo:` y los scopes `:gov:` quedan solo en SQLite (comentarios del código).

## 9. Límites (del código)

| Límite | Valor | Dónde |
|---|---|---|
| Agentes por sección | 50 | `plugin.py MAX_AGENTES` |
| Stream visible | 4 líneas (se guardan 40) | `STREAM_N`, `_linea` |
| Historial al modelo | 12 mensajes, 6000 caracteres c/u | `_mensajes_llm` |
| Archivo subido | ≤4 000 000 caracteres base64 | `subir` |
| Timeout ejecución | 30 s por defecto, tope 300 s | `ejecutar` |
| Timeout plugin | 90 000 ms | `ficha.json` |
| MAX_INFLIGHT por plugin | 8 | `HANDOFF/ARQUITECTURA.md` (`host.py`) |

## 10. ROOM CONFERENCIAS (rama `wip/room-conferencias-rebase2`)

Archivos (solo frontend, `chat router/chat frontend/`):

| Archivo | Qué hace |
|---|---|
| `room-conferencias.js` (192) | Pestaña, vista, participantes, rondas y debate |
| `room-conferencias.css` (26) | Estilos de la sala y de A−/A+ (`html.riu-fs`) |
| `texto-tamano.js` (20) | Control A−/A+ |
| `panel-chat.js` (+5) | Importa y llama `montarRoom` y `montarTamano`; `pintarTabs` llama `window.RIU_ROOM.pintar()` |
| `shell.html` (+1) | `<link>` a `room-conferencias.css` |

Cómo funciona:
- **Pestaña** «ROOM CONFERENCIAS» al final de `#chat-tabs`, junto a Chat 1/2/3. Activa: oculta los otros historiales y `#composer` (clase `room-oculto`). Cualquier otra pestaña sale de la sala.
- **Participantes** (`participantes()`): los modelos de `window.RIU_SELECTOR_QWEN` de grupo Qwen/DeepSeek/GLM (ficha 1 de `fichas_qwen`, model `qw-<slug>`), «Ask cónsil code» (ficha 2), «Ask consil frontend» (ficha 3) y «NVIDIA Glimmer» (`RIU_CONFIG.defecto`, `nv-muse-glimmer` por defecto, sin `qwen`). Máximo 6 (`MAX_PART`). Por defecto: Qwen 3.8 Flash + DeepSeek V4 Flash. El chip muestra el orden.
- **Rondas:** 1 a 5 (`MAX_RONDAS`), botones −/+. «Nueva sala» abre otra sesión (la anterior queda guardada).
- **Estado guardado:** `localStorage.riu_room_v1` (`activo, sesion, part, rondas`). Sesión `room-<aleatorio>`.
- **Historial:** `chat-ancla.js` (`restaurar`, `registrar`, `cargarHistorial`): IndexedDB + caché localStorage + respaldo en `/memoria` del Router. Cada respuesta se guarda como `[[Nombre]]\ntexto`.

Flujo del debate:
1. El Usuario escribe el tema y pulsa «Debatir» (Enter en PC). Se guarda como `user`.
2. Para cada ronda r de R, cada participante **en orden** hace un turno (`turno`). Si R>1 se pinta «Ronda r de R».
3. El prompt (`orden`): «SALA DE CONFERENCIAS… Eres «Nombre»… coincide o rebate a los demás citando su nombre… máximo 120 palabras, en español». Contexto: últimos 24 turnos, hasta ~9000 caracteres.
4. Fichas Qwen: la conversación va en `contexto_previo` y el `message` es solo la orden + el tema del Usuario (así la puerta de capacidades mira lo que pidió el Usuario). NVIDIA: la conversación va dentro del mensaje.
5. Llamada: `window.RIU_HARNESS({ model, message, contexto_previo, max_tokens: 700, sesion, qwen, avisar })`. Burbuja «pensando…» con el parcial (evento `riu-progreso`).
6. Respuesta: quita la cabecera «ASK CONSIL / modelo» (pasa a la etiqueta) y el «**Nombre**:» inicial; pinta la burbuja con botón ⧉ copiar y una línea «Nombre · X s YYY ms».
7. **Detener:** `Promise.race` corta el turno al instante y llama `window.RIU_CANCELAR(sesion)`; queda «proceso detenido por el usuario». Error → burbuja «GAP Nombre: …».

**A−/A+** (`texto-tamano.js`): botones `#fs-menos`/`#fs-mas` en `#ctl-panel .row.fields`. Paso 1 px, rango 11–28 px, guardado en `localStorage.riu_chat_fs`. Sin valor guardado no cambia nada; con valor, `html.riu-fs` aplica `--riu-chat-fs` a mensajes, `#message` y `#room-msg`.

Evidencia (mensaje del commit `a014c943c0`, 17-oct 00:13 Bogotá): «Probado 412 px + 4G E2E real: 2x1 y 3x2 rondas, recarga conserva historial, A-/A+, Chat 1 sigue OK». Tiempos de la prueba headless: 2×1 = 9 s 249 ms, 3×2 = 72 s 703 ms. Prueba en Android real: **por confirmar**.

## 11. Por confirmar
- Qué ficha real del Router resuelve cada id `qw-…` de Chat BOTS.
- Si `tests_fix/orq_test.py` (v1) se mantiene o se retira.
- `status`/`reiniciar` para el watchdog (PARCHE §4.1: falta).
- Red de HF Jobs (decisión de Antonio).
- Integración de Chat BOTS y ROOM en main: ninguna de las dos ramas está fusionada.

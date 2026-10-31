# HANDOFF — SWE CODE free y SWEN CODE

Leer en este orden: `README.md` ➡️ `ARQUITECTURA.md` ➡️ `INSTRUCCIONES.md` ➡️ este archivo. La cascada local de agentes (SWE CODE) está en `../SWE CODE/README.md`.

## Dónde está todo (`chat-router/`)
| Qué | Ruta |
|---|---|
| Router propio (puente web) | `SWE CODE/web-bridge/src/`: `server.js`, `motor.js`, `respaldo.js` (streaming, continuación, failover, métricas), `bloques.js` (checkpoint web), `cuentas.js`, `proyectos.js`, `memoria.js`, `formato.js`, `modos.js`, `consenso.js`, `sites.js`, `browser.js`, `checkpoint_hf.js` y `retomar_local.js` (checkpoint universal de HF local/Groq/NVIDIA), `swe_rutas.js` (`/v1/swe/*` hacia el Harness), `openclaw.js` (config/espejo de OpenClaw), `responses.js` (`/v1/responses` para Codex), `bancogithub.js` y `clavesbanco.js` (banco de claves), `autoactualizar.js` (autoactualización desde `main`), `iguales.js` (comparación segura de secretos) |
| UI de OpenClaw (contrato del plugin) | `SWE CODE free/openclaw-ui/README.md` |
| Memoria compartida con el chat | `SWE CODE/web-bridge/memoria_hf.py` (reutiliza `chat/backend/mvp/memoria.py`) |
| Formato de salida (copia única) | `chat/backend/mvp/prompts/FORMATO_SALIDA.md` |
| Pruebas | `SWE CODE/web-bridge/test/` (`node --test test/<archivo>`), `SWE CODE/web-bridge/test_memoria_hf.py`, `SWE CODE free/test_activar.test.mjs`, `SWE CODE free/test_evolucion.py` |
| Manual, gramática, config | `SWE CODE free/INSTRUCCIONES.md`, `agente.md`, `activar.js`, `documentos.js`, `swen.json` |
| Selector de OpenClaw | `SWE CODE free/provider-openclaw.json` |
| Entrada desde el chat Yaiwes | `chat/frontend/swe-directo.js` (lógica pura: envío, contrato `TareaSWE`, SSE, validación); el selector actual es `chat/frontend/swe-selectores.js` (hoja de SWE CODE / SWEN CODE free; pill en `panel-chat.html`); claves en `swe-claves.js`; pruebas `chat/frontend/test/swe-*.test.mjs` y `chat/e2e/swe-selector.e2e.mjs` |
| Agentes y adaptadores | `chat-router/agentes/adaptadores/` (contrato, dispatcher, workflows, disponibilidad; `chat-router/agentes/LEEME.md`) |
| Harness con salida por el bridge | `chat/backend/deepseek_harness/server.py` (`RIU_SWE_BRIDGE_URL`) |
| Auto-evolución | `SWE CODE free/evolucion.py` |
| Puente móvil / APK | `SWE CODE free/puente-movil/`, `apk-movil/`; descarga: chat ➡️ Configuración ➡️ «Agente móvil (APK)» (`chat/frontend/panel-apariencia.html`, `GET /apk` del Space) |
| Enlaces de plugins | `plugins/swe_code`, `plugins/swen_code_free`, `plugins/deepseek_harness` |

Estado del bridge en disco (`BRIDGE_STATE_DIR`, por defecto `./state`): `checkpoints/<conv_id>.json`, `proyectos/<proyecto>/ASESORIA.md`, `evolucion/lecciones.jsonl`, `perfiles/<sitio>/`, `cuentas-index.json`.

## Cómo retomar una sección
1. `GET /v1/secciones` ➡️ `conv_id` con `enviados/total` y `completo`. Los que tienen `completo:false` están a medias.
2. Reenviar `POST /v1/chat/completions` con el **mismo `conv_id` y el mismo texto** (y `cuentas`/`clave` si el bridge se reinició). Retoma desde el primer bloque no confirmado; si la tarea cambió o ya estaba completa, empieza de cero. Sin reenviar el texto: `POST /v1/secciones/<conv_id>/retomar` (usa el texto y el modelo del checkpoint; 409 `SECCION_YA_COMPLETA`, 404 `SECCION_NO_ENCONTRADA`). Al arrancar el bridge ya retoma solo las secciones a medias (`BRIDGE_AUTORETOMAR`).
   - Modelos locales HF, Groq y NVIDIA (checkpoint universal, `retomar_local.js`): reenviar la misma petición; el `tarea_id` lo deriva el bridge de `conv_id`+modelo+mensajes (o se manda `tarea_id`/`x-tarea-id`). El estado está en `BRIDGE_STATE_DIR/checkpoints/<tarea_id>.json` y en el Harness (`tareas/swe/<origen>/<tarea_id>/checkpoint.json`); tarea del Harness (`/v1/swe/*`, `task_id`): `reanudar`. Cómo funciona: `ARQUITECTURA.md`, «Recuperación y streaming».
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

## Operacion del Harness DeepSeek (agentes reales SWE)
El Harness (`chat/backend/deepseek_harness/server.py`) es quien lanza los agentes (`agentes/adaptadores/`); estas variables van en **su** entorno (nunca en el frontend ni en el repo) y `PYTHONPATH` debe incluir `chat-router` y `router-mvp`. Comprobar lo conectado: `POST /invoke {"action":"status"}` con `X-API-Key` -> `result.swe` (formato en `ARQUITECTURA.md`); el chat YAIWES lo ve en `GET /chat/swe/capacidades` y OpenClaw en `GET /v1/swe/capacidades`.

| Variable | Para qué | Dónde |
|---|---|---|
| `RIU_API_KEY` | clave de acceso del Harness (la misma que usan sus clientes) | Harness, backend YAIWES (banco) y bridge |
| `RIU_DEEPSEEK_HARNESS_URL` | URL del Harness | backend YAIWES y bridge |
| `RIU_SWE_WORKSPACE_RAIZ` | raíz donde viven los proyectos; cada tarea trabaja en `<raíz>/<proyecto>` y nada fuera de ella | Harness |
| `RIU_SWE_OPERADORES` | lista (coma) de operadores que pueden aprobar un paso con efectos; sin ella `swe_aprobar` responde `APROBADORES_NO_CONFIGURADOS`. Debe incluir **`director`** (operador por defecto de YAIWES) y el operador del bridge | Harness |
| `RIU_SWE_OPERADOR` | quién aprueba en nombre del backend YAIWES (por defecto `director`). **El bridge ya NO lo usa y no tiene valor por defecto**: el operador sale solo de la cabecera `x-operador` (si falta, 400 `OPERADOR_REQUERIDO`) y el Harness lo valida contra `RIU_SWE_OPERADORES` | backend YAIWES |
| `BRIDGE_TOKEN` | autenticación obligatoria de `/v1/swe/*` (incluida `capacidades`); además vale como credencial general del bridge (ver «Seguridad del bridge») | bridge |
| `BRIDGE_OPERATOR_TOKEN` | token propio (distinto de `BRIDGE_TOKEN`) que exige `POST /v1/swe/aprobar` en la cabecera `x-operator-token` (comparado por sha256 + `timingSafeEqual`); sin él, 503 `OPERATOR_TOKEN_NO_CONFIGURADO`; mal o ausente, 401 `OPERADOR_NO_AUTORIZADO` | bridge |
| `SWECODE_URL_S1`, `SWECODE_URL_S2`, `SWECODE_URL_S3` | servidores HF de los modelos locales; S2 = LIQUID 1 (lector), S3 = LIQUID 2 (ejecutor), distintos entre sí; sin ninguno los 4 modelos `hf/*` salen NO DISPONIBLE | Harness (y bridge para el respaldo local) |
| `GROQ_API_KEY[_1..20]`, `NVIDIA_API_KEY[_1..20]` | claves de los modelos `groq/qwen/qwen3.8-27b` y `nvidia/*`; la fuente es el banco (ver «Banco de claves»), pero `space/boot.sh` NO las exporta: hay que definirlas como secretos del servicio del Harness con los mismos valores del banco. Sin ellas el `status` marca esos modelos NO DISPONIBLE para los agentes (el chat directo por el Router sigue usando el banco). `status` solo informa si hay clave, nunca el valor | Harness (entorno, vía banco) |
| `RIU_SWE_SONDA_MODELOS` | `0` desactiva el `GET /models` de Groq/NVIDIA que comprueba que el id existe (defecto activo) | Harness |
| `RIU_CODEX_BIN`, `RIU_CODEX_BASE_URL` | Codex: binario y endpoint compatible con la API **Responses** (obligatorio: sin él Codex sale NO DISPONIBLE) | Harness |
| `RIU_OPENCODE_BIN` | OpenCode (`opencode`) | Harness |
| `RIU_SWEAGENT_BIN`, `RIU_DOCKER_BIN`, `RIU_SWEAGENT_IMAGE` | SWE-agent (`sweagent`) **y** Docker (corre en contenedor) | Harness |
| `RIU_OPENHANDS_PYTHON` | Python que importa el SDK (`openhands.sdk` y `openhands.tools`, de `agentes/agentes-listos/openhands-software-agent-sdk`); por defecto el del Harness | Harness |
| `RIU_CLAUDE_BIN`, `RIU_CLAUDE_PASARELA_URL`, `RIU_CLAUDE_PASARELA_MODELO` | Claude Code: CLI `claude` + pasarela Anthropic->NVIDIA (`agentes/claude-code/iniciar_claude_code.sh`); solo admite el modelo NVIDIA que sirve la pasarela. Opcional `RIU_CLAUDE_AUTH_TOKEN` | Harness |
| `OPENCLAW_GATEWAY_TOKEN`, `RIU_OPENCLAW_URL` | Gateway OpenClaw (defecto `http://127.0.0.1:18789`, con `gateway.http.endpoints.chatCompletions` habilitado) | Harness |
| `RIU_SWE_BRIDGE_URL`, `RIU_AGENTES_LLM_BASE_URL` | por dónde llegan los modelos `hf/*` a los agentes (defecto el bridge, `http://127.0.0.1:7870`) | Harness |
| `RIU_AGENTE_TIMEOUT_S`, `RIU_SWE_TIMEOUT_S`, `RIU_SWE_HARNESS_TIMEOUT_MS` | tiempos (agente 1800 s, Liquid 130 s, bridge->Harness 60 s) | Harness / bridge |

**Qué agente está instalado hoy:** solo la **CLI de Claude Code** (`claude`), y aun así `claude-code` sale NO DISPONIBLE hasta definir `RIU_CLAUDE_PASARELA_URL` y `RIU_CLAUDE_PASARELA_MODELO` (instalado, sin configurar). `codex`, `opencode`, `sweagent` (aunque `docker` sí existe en la sesión de preparación), el SDK de OpenHands y el Gateway OpenClaw **no están instalados** en el entorno donde se preparó el repo: sus adaptadores devuelven `AGENTE_NO_INSTALADO` y el selector los marca NO DISPONIBLE hasta que se instalen y se definan las variables de arriba. Ninguna prueba de este repo afirma que un agente real corra: las pruebas usan binarios falsos y servidores de prueba.

## Variables del bridge (`chat-router/SWE CODE/web-bridge`)
| Variable | Para qué (defecto) |
|---|---|
| `BRIDGE_PORT` | puerto (**7870**) |
| `BRIDGE_STATE_DIR` | estado en disco: checkpoints, proyectos, evolución, perfiles, banco (`./state`; en el Space, `/data/state`) |
| `BRIDGE_TOKEN`, `RIU_API_KEY` (y `RIU_PUBLIC_CHAT_KEY`, `RIU_MCP_KEY`, `RIU_ROUTER_API_KEY`) | credenciales de acceso (ver «Seguridad y operación del bridge») |
| `BRIDGE_OPERATOR_TOKEN` | token propio de `POST /v1/swe/aprobar` (cabecera `x-operator-token`) |
| `BRIDGE_DEADLINE_MS` | plazo por petición (100000); con `stream:true` es de inactividad |
| `BRIDGE_RESPALDO_MS` | timeout por proveedor de respaldo (120000); `RIU_SWE_TIMEOUTS` lo cambia por modelo (Groq Qwen 3.8: 60000) |
| `BRIDGE_SSE_KEEPALIVE_MS` | cada cuántos ms se envía `: keepalive` en un stream en espera (15000) |
| `BRIDGE_AUTORETOMAR` | retoma al arrancar las secciones a medias (activo; `0` lo apaga) |
| `BRIDGE_MAX_TABS`, `BRIDGE_MAX_PROMPT` | tabs web por sitio (4) y tamaño máximo del prompt (400000) |
| `BRIDGE_AUTOACTUALIZAR` | `0` apaga la autoactualización desde `main` |
| `RIU_SWE_GROQ_MODELO`, `RIU_SWE_NVIDIA_MODELO` | fijan el modelo de respaldo/asesoría de cada proveedor |
| `RIU_DEEPSEEK_HARNESS_URL`, `RIU_API_KEY` | Harness (checkpoint universal y `/v1/swe/*`); sin ellos el checkpoint queda solo en disco |
| `SWECODE_URL_S1..S3` | servidores HF locales (ver «Servidores HF y dataset») |

Métricas y diagnóstico: `GET /health` (con credencial: detalle completo) trae `respaldo` (conteos de claves Groq/NVIDIA y servidores HF), `banco.*` y `metricas` por modelo (`llamadas`, `ttft_ms`, `ttft_prom_ms`, `tokens_s`, `tokens_s_prom`, `total_ms`; TTFT = tiempo hasta el primer fragmento del stream). `GET /v1/modelos/disponibilidad` dice qué modelos Groq/NVIDIA publica de verdad el proveedor.

## Servidores HF y dataset (modelos locales)
Los modelos locales (`lfm2.5-350m`, `qwen2.5-coder-1.5b`, `qwen3.5-0.8b`, `qwen3-0.6b`) los sirven tres Spaces intercambiables (cualquiera sirve cualquier modelo vía `model=`; 1 modelo vivo por Space; entra por S1 y salta a S2/S3):

| Variable | URL pública |
|---|---|
| `SWECODE_URL_S1` | `https://comand-center-1-swe-code-s1.hf.space/v1` |
| `SWECODE_URL_S2` | `https://comand-center-1-swe-code-s2.hf.space/v1` |
| `SWECODE_URL_S3` | `https://comand-center-1-swe-code-s3.hf.space/v1` |

Los GGUF se cargan bajo demanda del dataset **`COMAND-CENTER-1/swe-code-hf-gguf`**. Liquid Mirror usa S2 (LIQUID 1, lector) y S3 (LIQUID 2, ejecutor). Son URLs públicas (sin secretos); cualquier clave va por entorno.

## Reglas
Dos raíces (`router-mvp/`, `chat-router/`). No se toca el Router MVP. Lo protegido por `cableado.manifest.json` no se toca sin regenerar la guarda. Credenciales solo en el banco/vault de OpenClaw o el entorno. Sin PASS sin evidencia.

## Banco de claves (Groq/NVIDIA) sin tocar Hugging Face
- Chat ➡️ `GET/POST/DELETE /web/v1/claves` con `X-API-Key` (clave del chat). Vercel reenvía `/web/*` al Space (`vercel.json`); el proxy del Space lo manda al bridge. Solo devuelve conteos, nunca valores.
- El bridge exige `RIU_API_KEY` (o `RIU_PUBLIC_CHAT_KEY`/`RIU_MCP_KEY`/`RIU_ROUTER_API_KEY`) en su entorno; sin ella responde 503. Guarda cifrado en `BRIDGE_STATE_DIR/banco-swe.bin` y lo publica en la rama `banco-claves` (necesita `GITHUB_TOKEN`; un Space nuevo lo trae solo).
- El Router MVP lee ese banco en solo lectura (`externos.claves`), con la misma clave de acceso. Con ella, los selectores Groq y NVIDIA del chat usan las claves pegadas en Configuración o en la ventana «Banco de claves» (grupo `groq/…` o `nvidia/…`; reemplaza las de ese proveedor).
- `DELETE` solo vacía el banco propio; las claves del entorno o del Router siguen.
- Vercel necesita `RIU_ROUTER_API_KEY` y `HF_POWER_TOKEN` para `/api/power` (encender el Router desde el chat).

## Seguridad y operación del bridge (`chat-router/SWE CODE/web-bridge`)
- **Puerta global**: toda ruta salvo `GET /health` exige `BRIDGE_TOKEN` (`Authorization: Bearer`, `x-bridge-key`) o una de las 4 claves de acceso (`RIU_API_KEY`, `RIU_PUBLIC_CHAT_KEY`, `RIU_MCP_KEY`, `RIU_ROUTER_API_KEY`) en `x-api-key` (el chat solo manda `X-API-Key`). Sin ninguna configurada, 503 `SIN_CLAVE_DE_ACCESO`: el bridge ya no queda abierto sin `BRIDGE_TOKEN`. **OpenClaw**: `provider-openclaw.json` trae el marcador `api_key: "${BRIDGE_TOKEN}"`; OpenClaw debe usar el `BRIDGE_TOKEN` real (variable de entorno, nunca escrito en el archivo) o sus llamadas darán 401. **Harness y agentes**: `deepseek_harness/server.py` manda su clave de acceso en `X-API-Key` (y `BRIDGE_TOKEN` en `x-bridge-key` si existe) en cada llamada al bridge; los agentes de `agentes/adaptadores` reciben como clave `RIU_AGENTES_LLM_API_KEY` o, si no, `BRIDGE_TOKEN`.
- `/v1/claves` y `/v1/openclaw` piden además la clave de acceso en `x-api-key` (BRIDGE_TOKEN solo no basta). Enrutado estricto y sensible a mayúsculas (`/v1/claves/`, `/V1/CLAVES` no existen) y la puerta normaliza la ruta (minúsculas, sin barras dobles/finales), así que ninguna variante la salta.
- `GET /health` sin credencial valida recorta `banco.*` a contadores y booleanos (sin stderr, códigos http ni rutas del disco ni `state_dir`); con credencial, el detalle completo.
- `POST /v1/chat/completions` con `claves`/`cuentas` en el cuerpo exige `x-api-key` de acceso, valida cada clave (8-300 caracteres sin espacios, máx. 20 por proveedor) y solo entonces las usa y las persiste.
- Respuesta de `POST/DELETE /v1/claves`: `local` = guardado en el banco propio; `persistido` = publicado en GitHub (necesita `GITHUB_TOKEN`; sin él, `false`).
- Banco: `claves_banco.py guardar` deja EXACTAMENTE las claves recibidas de cada proveedor presente (una quitada no reaparece). `traerDeGithub` solo acepta un banco `MVPB1` válido; el traer forzado de `vigilarBanco` solo ocurre si el banco local no existe o no abre: un banco local que abre y está vacío (DELETE) se respeta. `publicarEnGithub` reintenta una vez ante 409/422. Los `fetch` al Harness y a GitHub usan `redirect:'error'`. `claves_banco.py` y `memoria_hf.py` ubican solos `router-mvp` y `chat-router/chat/backend` (o `RIU_REPO_ROOT`).
- `ids groq/… nvidia/…` solo si están en `MODELOS_API` (o el fijado en `RIU_SWE_GROQ_MODELO`/`RIU_SWE_NVIDIA_MODELO`); otro, 400 `MODELO_INVALIDO`. Timeout de respaldo por defecto 120 s (`BRIDGE_RESPALDO_MS`); `groq/qwen/qwen3.8-27b` 60 s; se cambia por modelo con `RIU_SWE_TIMEOUTS='{"<id sin proveedor>": ms}'`. El respaldo tras un fallo web también tiene plazo (`BRIDGE_DEADLINE_MS`, 504 `UPSTREAM_TIMEOUT`).
- **`BRIDGE_AUTORETOMAR` está activo por defecto**: al arrancar el bridge retoma una a una las secciones a medias; solo `BRIDGE_AUTORETOMAR=0` lo apaga.
- **Autoactualización**: antes de relanzarse, el bridge hace `node --check` de los `.js` tocados (y `npm install` si cambió `package.json`); si falla, `git reset --hard` a la cabeza previa y NO se relanza (una línea en el log).
- Build del bridge: `docker build -f "chat-router/SWE CODE/web-bridge/Dockerfile" .` desde la raíz del repo (contexto = raíz). La imagen replica `/repo/chat-router/...` e incluye `claves_banco.py`, `memoria_hf.py`, `activar.js`, `provider-openclaw.json`, `FORMATO_SALIDA.md`, python3 y cryptography; escucha en `7870`. El Space real arranca clonando el repo, no con esta imagen.
- `POST /v1/responses` (mínimo, para Codex): traduce a `/v1/chat/completions` del propio bridge (misma puerta, mismos modelos autorizados) y responde en formato Responses, JSON o SSE. Límites: el stream se emite en trozos sobre la respuesta ya completa (no es streaming real), sin herramientas alojadas (`web_search`…) ni reasoning. Para Codex: `RIU_CODEX_BASE_URL=<bridge>/v1` y la clave de acceso en `X-API-Key`/`Bearer BRIDGE_TOKEN`.
- Hook de sesión `.claude/hooks/session-start.sh`: instala `router-mvp/mvp/requirements.txt` y deja `PYTHONPATH=router-mvp:chat-router` (idempotente).

## Pendiente fuera del código (HF / Grok)
- Doble vía de OpenClaw (config en `GET /v1/openclaw`): el proxy del Space debe reenviar `/web/*` al bridge (el repo no tiene ese proxy; `app.py` del Router MVP no lo hace) y `openclaw.sh` del Space (que borra `$OPENCLAW_HOME`) tampoco está aquí: OpenClaw debe leer `provider-openclaw.json`/`/v1/openclaw` al arrancar, o el `openclaw.sh` hacerlo.
- El `boot.sh` del Space (copia vieja en `chat/backend/mvp/respaldo_space/`) hace `test -f mvp/run.py` y `python -m mvp.run` desde la raíz del clon; desde que la raíz solo tiene `router-mvp/` y `chat-router/` ese `mvp/` ya no existe ahí (hoy es `router-mvp/mvp`). Confirmar en el Space real que arranca desde `router-mvp/`.
- Confirmar que el Space lanza el bridge en `:7870` (el código usa `BRIDGE_PORT`, por defecto 7870, igual que el `Dockerfile` del bridge, pero el Space REAL no usa ese Dockerfile: arranca clonando el repo y ejecuta `src/server.js` desde el clon, con su propio arranque que no está en este repo).
- Ruta `GET /v1/queue` (y las de `/v1/*` que usa el chat) en el proxy del Space; el proxy tampoco está en este repo.
- Redeploy del Space al último `main`; `BRIDGE_STATE_DIR` en almacenamiento permanente; `HF_TOKEN` y `mvp` importable para la memoria; `puente-movil` como proceso; cuentas web entregadas por OpenClaw; saldo de HF.
- Desde el chat Yaiwes (`swe-directo.js`) y el Harness no viajan `cuentas`/`clave`: los modelos `web-*` desde ahí solo funcionan si OpenClaw ya las inyectó en el proceso o están en el entorno; si no, responde el respaldo.

## Banco de claves: cómo llega al Space (verificado en vivo)
- El banco cifrado vive en la rama `banco-claves` (archivo `banco-swe.bin`, marca `MVPB1`). El bridge lo trae al arrancar y cada 60 s si el local no existe o no abre.
- La API de contenidos de GitHub, vista desde el Space, devolvía el binario recodificado (1357 → 2036 bytes) tanto en JSON/base64 como en crudo; por eso `bancogithub.js` valida `MVPB1` y el tamaño y, si no coincide, lo toma por `git fetch` (binario intacto).
- Diagnóstico sin valores: `GET /web/health` (con `x-api-key` da el detalle `banco.*`): `respaldo.groq/nvidia` son los conteos cargados.
- La clave de acceso con la que se cifra debe ser una de `RIU_API_KEY`, `RIU_PUBLIC_CHAT_KEY`, `RIU_MCP_KEY`, `RIU_ROUTER_API_KEY` (el bridge y el Router prueban todas).

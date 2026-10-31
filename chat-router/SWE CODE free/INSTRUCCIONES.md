# INSTRUCCIONES — SWEN CODE free (manual del agente)

> Manual para modelos y agentes (chat Yaiwes y OpenClaw). Todo pasa por el web-bridge (`WEB_BRIDGE_URL`, `:7870`). La cascada local de agentes (codex/opencode/swe-agent/openhands, pipelines `code`/`free`, `mini_router.py`) es de SWE CODE y se explica en `../SWE CODE/README.md`.

## 1. Activación

- Todo mensaje empieza con `SWEN CODE free` (sin distinguir mayúsculas); `activar.js` saca modo, modelo, `conv_id` y documentos. Sin ese prefijo el sistema no responde.
- Forma: `SWEN CODE free [modo <modo>] [con|solo|modelo <nombre>] [chat <id>] [doc <ruta>]… <texto>`. Los prefijos pueden ir en cualquier orden.
- Modo por defecto: `consulta`. Modo o modelo desconocido → error con la lista válida.

## 2. Elegir modelo

| Lo que dices | Id que usa el bridge |
|---|---|
| `concilio`, `cóncil`, `consenso`, `todos`, `los 3` | `swecode-consulta`: dsv4-flash + qwen37max + qwen38max en paralelo, síntesis qwen38max |
| `deepseek`, `dsv4`, `deepseek v4` | `web-dsv4-flash` |
| `qwen 3.7`, `qwen 3.7 max` | `web-qwen37max` |
| `qwen 3.8`, `qwen 3.8 max` | `web-qwen38max` |
| `liquid`, `lfm`, `lfm2.5` | `lfm2.5-350m` (HF local S1..S3, vía bridge) |
| `coder`, `qwen code`, `qwen2.5` | `qwen2.5-coder-1.5b` (HF local) |
| `groq` / `nvidia` / `minimax` | `groq/qwen/qwen3.8-27b` / `nvidia/minimaxai/minimax-m3.1-flash` (ambos) |
| `muse`, `glimmer` | `nvidia/meta/muse-glimmer-30b` |
| `nemotron` | `nvidia/nvidia/nemotron-3-ultra-550b-a55b` |
| `glm` (`glm 5.3`) | `nvidia/z-ai/glm-5.3` |
| `qwen3.5` / `qwen3` | `qwen3.5-0.8b` / `qwen3-0.6b` (HF local) |

- Un id completo (`groq/...`, `nvidia/...`, `lfm2.5-350m`, `qwen2.5-coder-1.5b`, `qwen3.5-0.8b`, `qwen3-0.6b`) tiene prioridad sobre los alias y se consume entero del prompt (`solo nvidia/z-ai/glm-5.3 deploy` → modelo `nvidia/z-ai/glm-5.3`, prompt `deploy`).
- Prefijos aceptados: `con`, `solo`, `modelo`, o el nombre como primera palabra.
- Sin nombre: `consulta` → concilio; los demás modos → `qwen38max` único. Modo + modelo único: `SWEN CODE free modo solucion solo deepseek v4 <tarea>` → POST con `model: web-dsv4-flash` y `modo: solucion`.
- Sin modelo, el modo va en el id: `swecode-<modo>`.

## 3. Modos

`revision` · `solucion` · `arquitectura` · `archivos` · `prompt_code` · `consulta` · `despliega` · `asesoria` (8; `swecode-plan` no existe).
- `despliega`: aplica lo que te entregan y verifica; en FREE no refactorizas.
- `asesoria`: planea antes de ejecutar y **no ejecuta**. Devuelve objetivo, plan numerado, mapa mental en texto, estructura a ejecutar y cómo resolver problemas probables. Responde Groq primero, luego la web. Se guarda en `proyectos/<proyecto>/ASESORIA.md`; léela con `GET /v1/proyectos` y `GET /v1/proyectos/<proyecto>` antes de ejecutar.

## 4. Campos del POST `/v1/chat/completions`

| Campo | Para qué |
|---|---|
| `model` | uno de los ids de §2, `swecode-<modo>`, `groq/<id>`, `nvidia/<id>` o un local; `GET /v1/models` los lista |
| `messages` | historial OpenAI (`role`/`content`) |
| `modo` | solo con `web-*`; con `swecode-<modo>` manda el id |
| `conv_id` | sección: tab propia y retoma por checkpoint; activar.js lo arma como `chat-<id>` |
| `proyecto` | agrupa asesorías (`ASESORIA.md`) y la memoria; sin él se usa `conv_id`, y sin ninguno `general` |
| `cuentas`, `clave` | correos de la web (lista o texto con comas) y la clave; los entrega OpenClaw |
| `documentos` | `[{nombre, contenido}]` o strings; se incrustan al prompt (máx 100 000 caracteres c/u, máx 10). En el gestor: `doc <ruta>` / `adjunto <ruta>`, repetible (`documentos.js` los lee) |
| `stream` | `true` = SSE real (`chat.completion.chunk` + `[DONE]`, `: keepalive` cada `BRIDGE_SSE_KEEPALIVE_MS` = 15 s); el chat y OpenClaw lo usan. Los fragmentos reales de Groq/NVIDIA salen al instante; el resto se emite al terminar sin duplicar lo ya entregado |
| `ejecutor_tools` | `swe` (defecto) = el Harness/SWE-agent ejecuta los `tool_calls`; `openclaw` = el bridge los devuelve tal cual a OpenClaw y la sección queda `WAIT_TOOLS` hasta que llegan los `role:"tool"`. Cualquier otro valor = `swe` |
| `tools`, `tool_choice` | pasan a Groq/NVIDIA/locales, que devuelven `tool_calls` (con id único); los modelos web no producen `tool_calls` |
| `claves` | `{groq, nvidia}` (string o lista, máx 20 por proveedor, 8-300 caracteres sin espacios). Solo con `x-api-key` de acceso (el `BRIDGE_TOKEN` solo no basta); se guardan en el banco cifrado, **nunca** en prompts, checkpoints ni código. El chat las manda solo si el banco del servidor no respondió |
| `tarea_id` / cabecera `x-tarea-id` | identidad del checkpoint universal de los modelos explícitos (`groq/…`, `nvidia/…`, locales HF). **Normalmente no se manda**: con `conv_id` el bridge deriva `<conv_id>-<hash de modelo+modo+mensajes>`, así reenviar la misma petición reanuda y una distinta es tarea nueva. Formato `[A-Za-z0-9_-]{1,64}` |
| `origen`, `respaldo` | `yaiwes`\|`openclaw` (ruta del checkpoint en el Harness); `respaldo:true` deja que un modelo explícito caiga al respaldo (si no, falla con su error, sin cambiar de modelo) |

Respuesta: `modelo_usado`, `via_respaldo`, `aviso`, `archivo`, `servidor` (S1..S3), `metricas` (`ttft_ms`, `tokens_s`, `total_ms`), `tarea{id,estado,secciones,reanudado,desde_checkpoint}`, `usage`; headers `x-modelo-usado` y `x-via-respaldo`.
`pipeline code|free|auto` lo reconoce `activar.js`, pero el bridge no lo ejecuta (es de la cascada local, ver `../SWE CODE/README.md`).

## 5. Trabajo en paralelo

- `chat <id>` / `seccion <id>` / `conv <id>` → `conv_id` propio: tab web aparte, hilo separado. Divide la tarea en 2 mensajes con `chat 1` y `chat 2`: trabajan a la vez.
- Capacidad: `BRIDGE_MAX_TABS=4` tabs por sitio; si se llena, encola.
- Espejo: mismo modelo en otro `conv_id` (contexto aparte) para repartir el trabajo. No uses el mismo `conv_id` en dos tareas a la vez. En el concilio cada modelo usa su propia tab (`<conv_id>-<modelo>`).

## 6. Conectividad

```
OpenClaw ──────────────► web-bridge :7870 ─► Qwen/DeepSeek web
chat Yaiwes (swe-directo.js) ─► mismo origen ─► web-bridge
chat ─► plugins ─► Harness DeepSeek ─► web-bridge (solo model + messages)
```

- Web: `POST {WEB_BRIDGE_URL}/v1/chat/completions` con `web-*` o `swecode-<modo>`. Dentro de la web, si falla el modelo pedido prueba `qwen38max → qwen37max → dsv4-flash`.
- Locales: el bridge los sirve con `model=` hacia `SWECODE_URL_S1..S3` (entra por S1, salta a S2/S3).
- Respaldo automático si la web falla: **Groq → NVIDIA → HF local (S1..S3)**; `via_respaldo` dice cuál respondió.
- `GET /v1/queue`: tabs por sitio, `conv_id`, cola, cuentas.
- Móvil (último recurso, **manual**, el bridge no lo llama): `POST {PUENTE_MOVIL_URL}/mcp` (tools `abrir_url`, `leer_pantalla`, `escribir`, `tap`, `atras` sobre el Chrome del teléfono); `GET /health` del puente → `movil:true|false`.

## 7. Recuperar

| Fallo | Acción |
|---|---|
| `SESSION_EXPIRED` | el bridge hace re-login/rotación y reintenta una vez; si persiste `POST {WEB_BRIDGE_URL}/refresh_session` |
| Sección a medias | reenviar el MISMO `conv_id` y el mismo texto, o `POST /v1/secciones/<conv_id>/retomar` sin reenviar nada (409 `SECCION_YA_COMPLETA`); `GET /v1/secciones` lista las que están a medias (checkpoint en `checkpoints/<conv_id>.json`; una completa o de otra tarea empieza de cero). El bridge también retoma solo al arrancar (`BRIDGE_AUTORETOMAR`, activo) |
| Respuesta cortada (`finish_reason=length`) o API caída (429/402/timeout) | el bridge continúa solo («Continúa exactamente donde terminó») y cambia de clave/API sin repetir texto: Groq ➡️ NVIDIA ➡️ HF local. Con un modelo explícito el fallo se devuelve tal cual (reintenta con la misma petición: reanuda del checkpoint) |
| `409 CHECKPOINT_OTRA_TAREA` | el `tarea_id` ya guardó otra tarea (otros mensajes o modelo): usar otro `tarea_id` |
| Space dormido | reintentar: scale-to-zero despierta solo (~1-3 min) |
| Todo web cae | responde solo el respaldo (ver `via_respaldo` y `aviso`); si no queda nada, 500 `RESPALDO_AGOTADO` → recurrir al APK a mano |
| `INPUT_NO_ENCONTRADO`/`SELECTOR_BROKEN` | marcar SELECTOR_BROKEN + sitio; no reintentar a ciegas |

### 7a. Auto-diagnóstico (el agente lo hace solo, sin prompts)

1. **`aviso: CUENTAS_FALTAN`, o `/health` con `pool.error: WEB_ACCOUNTS_VACIO`** = el bridge no recibió cuentas. Las credenciales son de OpenClaw: las pasa en cada POST (`cuentas`, `clave`) o las inyecta al arrancar el proceso; **nunca** en secrets del Space, prompts ni código. Comprueba que OpenClaw las envía y repite `/health` hasta que liste el pool (cantidad, nunca valores). Sin sesión no hay respuesta web (explica el `content` vacío).
2. **`content` vacío con cuentas OK** = `GET /debug/tab?conv_id=` (url, título, captura): gate «Confirma tu edad» → ya se resuelve solo; login → re-login con la cuenta; captcha/2FA → documentar pantalla e índice de cuenta, sin bypass.
3. **`/v1/queue` 404** = el proxy del Space no reenvía la ruta al bridge → añadir `GET /v1/queue → :7870` en el proxy.
4. **Puente móvil `movil:false`** = puente vivo, esperando la app: entregar Host + puerto + `PUENTE_TOKEN` y «Probar conexión» en la app.
5. **Código viejo en el Space** = rebuild/restart (clona `main` al arrancar); re-verificar `GET /v1/models` (debe listar `swecode-asesoria`) y `/v1/queue` antes de reportar.

Regla: diagnosticar con evidencia (logs, `/debug/tab`, healths) y tocar `sites.js` solo cuando la captura o el código dicen qué selector falla.

### 7b. Auditar en GitHub (guía XRAY)
`GUIA_AUDITORIA_XRAY.md` (v1 verbatim del usuario) y `GUIA_AUDITORIA_XRAY_V2.md` (evidencia con SHA, códigos de fallo, auditoría en paralelo por `conv_id`, formato VEREDICTO/EVIDENCIA/GAP/SIGUIENTE).

### 7c. Selector de OpenClaw
`provider-openclaw.json`: provider `openai-compatible` con `base_url` `http://localhost:7870/v1`. El selector lee `GET /v1/models` del bridge; la lista del archivo es el respaldo si no responde.

## 8. Autenticación y rutas del bridge

**Credencial obligatoria** en toda ruta salvo `GET /health`: cabecera `x-api-key` con una de las 4 claves de acceso del chat (`RIU_API_KEY`, `RIU_PUBLIC_CHAT_KEY`, `RIU_MCP_KEY`, `RIU_ROUTER_API_KEY`) **o** `BRIDGE_TOKEN` (`Authorization: Bearer` / `x-bridge-key`). Sin ninguna configurada en el bridge: **503** `SIN_CLAVE_DE_ACCESO`; clave ausente o mala: **401** `NO_AUTORIZADO`. OpenClaw usa `provider-openclaw.json` (`api_key: "${BRIDGE_TOKEN}"` = marcador; el valor real va en el entorno de OpenClaw, nunca en el archivo). Nunca escribas claves reales en prompts, archivos ni commits.

| Ruta | Para qué |
|---|---|
| `POST /v1/chat/completions` | chat y modelos (campos en §4) |
| `GET /v1/models` | ids que ve el selector de OpenClaw |
| `GET /v1/secciones` · `POST /v1/secciones/<id>/retomar` | secciones con checkpoint; retomar una a medias sin reenviar el texto (`{"respaldo":true}` opcional) |
| `GET /v1/modelos/disponibilidad` | modelos Groq/NVIDIA: `DISPONIBLE` \| `NO DISPONIBLE` \| `SIN VERIFICAR` (según el `GET /models` real del proveedor; no sustituye modelos ni muestra claves) |
| `GET /v1/proyectos[/<proyecto>]` · `GET /v1/memoria/<sesion>` · `GET /v1/evolucion` | asesorías, historial compartido, mejoras propuestas |
| `GET/POST/DELETE /v1/claves` | banco de claves Groq/NVIDIA (solo conteos); además exige la clave de acceso en `x-api-key` |
| `GET /v1/openclaw` | configuración vigente y espejo para OpenClaw (sin secretos) |
| `POST /v1/swe/{iniciar,avanzar,estado,aprobar,reanudar}` · `GET /v1/swe/capacidades` | tareas con agentes reales (contrato `TareaSWE`) vía el Harness; exigen `BRIDGE_TOKEN`; `aprobar` además `BRIDGE_OPERATOR_TOKEN` en `x-operator-token` y el operador en `x-operador` (sin valor por defecto). Ver `ARQUITECTURA.md` y `openclaw-ui/README.md` |
| `POST /v1/responses` | API Responses mínima para Codex (traduce a `/v1/chat/completions`; el stream es en trozos sobre la respuesta completa, sin herramientas alojadas) |
| `GET /health` · `GET /v1/queue` · `POST /refresh_session` · `GET /debug/tab` | diagnóstico: cuentas, respaldo (conteos), banco, **métricas por modelo (TTFT, tokens/s)**, tabs |

Variables que cambian el comportamiento (más en `HANDOFF.md`): `BRIDGE_SSE_KEEPALIVE_MS` (latido del stream, 15000), `RIU_SWE_TIMEOUTS` (JSON `{"<id sin proveedor>": ms}`; defecto 120 s por proveedor y 60 s para Groq Qwen 3.8), `BRIDGE_AUTORETOMAR` (retoma al arrancar; `0` lo apaga), `BRIDGE_DEADLINE_MS` (100 s).

## 9. Reparar cableado

1. `chat-router/plugins/<nombre>` debe ser symlink → `../<raíz>` (`swe_code` → `SWE CODE`; `swen_code_free` → `SWE CODE free`).
2. La raíz debe tener `ficha.json` (plugin_host/v1).
3. `cableado.manifest.json` debe listar el enlace en `enlaces` y la pieza en `plugins`.
4. Nada dentro de `protegido` se toca (sha256 verificado).
5. Rutas: `SWE CODE/web-bridge/` = router web; `SWE CODE free/` = capa OpenClaw (manual, activador, APK, puente móvil).

## 10. Reglas del agente

- Salida larga → `.md`/código en `salidas/` del repo y a GitHub; nunca se queda solo en el chat web.
- Sin PASS sin evidencia real.

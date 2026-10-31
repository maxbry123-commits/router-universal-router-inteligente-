# openclaw-ui — selectores SWE para la UI de OpenClaw (GAP: plugin sin generar)

**Estado: GAP.** La CLI `openclaw` no está instalada en el entorno donde se preparó este repo (`which openclaw` → no existe), así que **no se generó el plugin ni se inventó su API**. Quien tenga el runtime OpenClaw autorizado lo genera con el comando oficial y lo conecta con este contrato:

```
openclaw plugins init swe-selector --name "SWE Selector" --type feature
```
APIs oficiales a usar (según el input del Director): `openclaw/plugin-sdk/feature-contract`, `feature-plugin`, `control-ui` · `defineFeatureContract()`, `defineFeaturePlugin()`, `defineControlUiPlugin()` · `registerPage()`, `registerNavigation()`, `registerPanel()`. No copiar JavaScript dentro de la distribución compilada de OpenClaw ni tocar `openclaw/extensions` ni `~/.openclaw/openclaw.json`; el código del plugin vive aquí (`SWE CODE free/openclaw-ui/`). La UI no ejecuta herramientas: solo habla con el bridge.

## Flujo
`OpenClaw UI → SWE CODE / web-bridge (/v1/swe/*) → Harness DeepSeek (invoke swe_*) → agentes/adaptadores → memoria/checkpoint`. Mismo contrato, mismos adaptadores, mismos modelos y mismo almacenamiento que el chat YAIWES; solo cambia `origen`.

## Los 6 controles (mismo orden y rótulos que YAIWES)
1. **MODELO QUE RESPONDE** → `modelo_responde` · 2. **MODELO PARA TOOL** → `modelo_tool` · 3. **AGENTE QUE RESPONDE** → `agente_responde` · 4. **AGENTE QUE EJECUTA** → `agente_tool` · 5. **MODO AGÉNTICO** ON/OFF → `modo_agentico` · 6. **WORKFLOW** → `workflow`.
- Modelos (ids exactos del catálogo `agentes/adaptadores/modelos.py`): `hf/lfm2.5-350m`, `hf/qwen2.5-coder-1.5b`, `hf/qwen3.5-0.8b`, `hf/qwen3-0.6b`, `groq/qwen/qwen3.8-27b`, `nvidia/minimaxai/minimax-m3.1-flash`, `nvidia/meta/muse-glimmer-30b`, `nvidia/nvidia/nemotron-3-ultra-550b-a55b`, `nvidia/z-ai/glm-5.3`. Sin Llama.
- Agentes: `openclaw`, `swe-agent`, `openhands`, `opencode`, `codex`, `claude-code`. Workflows: `individual` (Individual), `swe_code` (SWE CODE cuatro pasos), `liquid_mirror` (Liquid Mirror).
- Botón de salida **SWE-agent | OpenClaw** (`ejecutor_tools` `swe|openclaw`): es el mismo dato que AGENTE QUE EJECUTA cuando vale `swe-agent`/`openclaw`.
- **Liquid Mirror**: dos participantes fijos `LIQUID 1 — LECTOR` (S2) y `LIQUID 2 — EJECUTOR` (S3), ambos `hf/lfm2.5-350m` (`modelo_lector` y `modelo_tool`); el control MODELO PARA TOOL queda bloqueado. Sin modelos web.
- Lo que el Harness no reporta conectado (o declara incompatible con el modelo elegido) se muestra **NO DISPONIBLE** / **incompatible** y no se envía. OFF: no se activan agentes externos para ejecutar; ON: delegación según los permisos reales del backend.

## Contrato (idéntico a YAIWES; `origen:"openclaw"`)
```json
{"task_id":"openclaw-001","origen":"openclaw","workflow":"liquid_mirror","mensaje":"Revisar y desplegar","modelo_responde":"hf/lfm2.5-350m","modelo_lector":"hf/lfm2.5-350m","modelo_tool":"hf/lfm2.5-350m","modelo_revisor":"hf/qwen3.5-0.8b","agente_responde":"openclaw","agente_tool":"swe-agent","agente_verificador":"openhands","modo_agentico":true,"aprobacion":false,"sesion":"openclaw-001","proyecto":"swe-code"}
```
15 campos exactos (ninguno más). `task_id` = `[A-Za-z0-9_-]{1,64}`; el mismo `task_id` identifica la tarea en todas sus reanudaciones. `aprobacion` se envía siempre `false` (la aprobación solo la da el operador por `aprobar`).

## Endpoints del bridge (`http://localhost:7870`)
Todos `POST`, JSON, **autenticados**: `Authorization: Bearer <BRIDGE_TOKEN>` (o `x-bridge-key`). Sin `BRIDGE_TOKEN` en el bridge responden 503 `BRIDGE_TOKEN_NO_CONFIGURADO`; sin token válido, 401.

| Ruta | Cuerpo | Harness |
|---|---|---|
| `/v1/swe/iniciar` | el contrato completo | `swe_iniciar` |
| `/v1/swe/avanzar` | `{task_id, origen?, sesion?, proyecto?}` | `swe_avanzar` (un paso por llamada) |
| `/v1/swe/estado` | ídem | `swe_estado` |
| `/v1/swe/reanudar` | ídem | `swe_reanudar` (desde el último checkpoint) |
| `/v1/swe/aprobar` | `{task_id, op_id, origen?, sesion?, proyecto?}` + cabecera `x-operador: <operador>` | `swe_aprobar` |

Respuestas: `{ok:true, resultado}` (el resultado es la vista de la tarea: `estado`, `paso_actual`, `plan`, `pasos_terminados[{paso,agente,servidor,recibo,resultado,herramientas,evidencias}]`, `resultado_tool`, `evidencia[]`, `pendiente_aprobacion{op_id,...}`, `error{codigo,mensaje}`); errores de validación 400 `{ok:false,error:{code}}` (`TASK_ID_INVALIDO`, `ORIGEN_INVALIDO`, `CAMPOS_DESCONOCIDOS`, `CAMPOS_FALTANTES`, `MENSAJE_VACIO`, `OP_ID_INVALIDO`, `OPERADOR_REQUERIDO`, …); fallo del Harness 502 `{ok:false,error:{code:"SWE_HARNESS_ERROR",causa}}`. Estados: `PENDIENTE, EJECUTANDO, REQUIERE_APROBACION, RECONCILIAR, CONTINUAR, VERIFICANDO, DONE, GAP`. La UI repite `avanzar` hasta `DONE`/`GAP`/`REQUIERE_APROBACION`/`RECONCILIAR`; `DONE` solo cuando el Harness lo dice (nunca por `finish_reason=stop`).

Aprobar: el operador debe estar identificado (`x-operador` o `RIU_SWE_OPERADOR` en el bridge) y figurar en `RIU_SWE_OPERADORES` del Harness; el campo `aprobacion` del cuerpo o del modelo no cuenta. `RECONCILIAR` es un fallo visible: se verifica a mano antes de reanudar.

## Variables (solo backend; nada de esto va al frontend de OpenClaw)
`BRIDGE_TOKEN` (obligatorio, tambien para `GET /v1/swe/capacidades`), `RIU_DEEPSEEK_HARNESS_URL`, `RIU_API_KEY` (clave del Harness), `RIU_SWE_OPERADOR`, `RIU_SWE_HARNESS_TIMEOUT_MS` (defecto 60000).

## Capacidades: que esta conectado (solo lectura)
`GET /v1/swe/capacidades` (`web-bridge/src/swe_rutas.js`, `consultarCapacidades`). **Misma autenticacion obligatoria** que `/v1/swe/*` (`Authorization: Bearer <BRIDGE_TOKEN>` o `x-bridge-key`; sin `BRIDGE_TOKEN` en el bridge 503 `BRIDGE_TOKEN_NO_CONFIGURADO`, token malo 401). Sin cuerpo; no cambia nada. El bridge pregunta al Harness su `status` (`POST {RIU_DEEPSEEK_HARNESS_URL}/invoke` con `{"action":"status"}` y `X-API-Key`, solo en el backend) y devuelve lo mismo que `GET /chat/swe/capacidades` de YAIWES, saneado y **sin secretos** (los motivos nombran la variable que falta, nunca su valor; cualquier clave con forma de token se redacta):
```json
{"harness":"ok","agentes":{"opencode":{"disponible":true},"codex":{"disponible":false,"motivo":"codex no esta instalado ..."},"claude-code":{"disponible":true,"modelos":["nvidia/z-ai/glm-5.3"]}},"workflows":{"individual":{"disponible":true},"liquid_mirror":{"disponible":false,"motivo":"falta SWECODE_URL_S2 ..."}},"modelos":{"hf/lfm2.5-350m":{"disponible":true},"groq/qwen/qwen3.8-27b":{"disponible":false,"motivo":"... no figura en GET /models de groq"}}}
```
`harness` vale `ok`, `no_configurado` (falta `RIU_DEEPSEEK_HARNESS_URL`), `sin_credencial` (falta `RIU_API_KEY`) o `no_disponible` (no responde / HTTP no OK / timeout); salvo `ok` las tres listas vienen vacias y la UI debe marcar todo lo que no sea Individual como NO DISPONIBLE. Regla de la UI (identica a YAIWES): agente o workflow sin `disponible:true` -> **NO DISPONIBLE** (deshabilitado); modelo con `disponible:false` -> NO DISPONIBLE (sin entrada = no se sabe, se deja elegir); agente con `modelos` y el modelo elegido fuera de la lista -> **incompatible**. Con la seleccion no disponible no se envia nada (`GAP: SELECCION_NO_DISPONIBLE`); no se cambia en silencio de modelo ni de agente. Quien emite la informacion es el Harness (`status` -> `result.swe`, `agentes/adaptadores/disponibilidad.py`): comprueba binarios y variables sin lanzar ningun agente.

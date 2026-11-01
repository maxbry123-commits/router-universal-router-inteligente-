# openclaw-ui — plugin REAL «SWE Selector» para la UI de OpenClaw

Plugin nativo de OpenClaw (tipo *feature*) creado con el flujo oficial (`openclaw plugins init swe-selector --name "SWE Selector" --type feature`) y la documentación oficial del repo `openclaw/openclaw` (`docs/plugins/feature-plugins.md`, `docs/plugins/manifest*.md`, `docs/cli/plugins/authoring.md`, `src/cli/plugins-feature-scaffold.ts`, SDK `openclaw/plugin-sdk/{feature-contract,feature-plugin,control-ui}`). La documentación se bajó con el motor de archivos del repo (`mvp/archivos`: `origen.clonar` + `acciones.copiar`, solo lectura, destino `/tmp`); no se tocó `openclaw/extensions` ni `~/.openclaw/openclaw.json`. APIs de OpenClaw marcadas *experimentales*: fijar la versión (probado con **2026.10.9**).

## Qué contiene
| Archivo | Para qué |
|---|---|
| `openclaw.plugin.json` | manifiesto (id `swe-selector`, `contracts.tools`, `uiCapabilities`; `controlUi` lo escribe `plugins build`) |
| `package.json` | `openclaw.extensions`, `openclaw.controlUi`, scripts `build`/`validate`/`pack`/`test` |
| `src/contract.ts` | `defineFeatureContract`: 19 operaciones (`capacidades`, `tools`, `iniciar`, `avanzar`, `estado`, `reanudar`, `aprobar`, `tool` + 11 tools por función del chat `yaiwes_*`); `iniciar` usa el contrato **TareaSWE** (15 campos, `origen:"openclaw"`, `aprobacion` solo `false`) |
| `src/index.ts` | `defineFeaturePlugin`: backend (corre en el Gateway). Llama al bridge; **no hay otro backend** |
| `src/bridge.ts` | cliente del bridge `/v1/swe/*`; la clave sale del **entorno del Gateway** (`RIU_API_KEY`; `BRIDGE_TOKEN` solo como respaldo; `RIU_SWE_BRIDGE_URL`), nunca del navegador ni de la config |
| `src/selector-core.ts` | selector central: una validación, una serialización, una función de disponibilidad (sin DOM; fuente = Harness) |
| `src/control-ui.ts` (+`.css`) | `defineControlUiPlugin`: `registerPage`, `registerNavigation`, `registerPanel`; selectores con `host.components.mountSelectPicker`; no usa el DOM de YAIWES |
| `test/*.test.mjs` | pruebas (SDK real + rutas reales del bridge) |

## Selector central (mismo contrato que YAIWES)
`RESPONDE [Agente que responde][Modelo que responde]` · `EJECUTA [Agente que ejecuta][Modelo para tool]` · debajo `Modo agéntico ON/OFF` · `Workflow` · `Salida SWE | OpenClaw`. La salida es el destino de los `tool_calls` (`ejecutor_tools`) y es un estado **separado** de `agente_tool` (cambiar uno no cambia el otro; cambiar `modelo_tool` no cambia `modelo_responde`). Agentes, workflows y modelos salen de `GET /v1/swe/capacidades` (Harness): sin catálogo propio. Cada opción muestra su estado entre los seis (DISPONIBLE, NO INSTALADO, NO CONFIGURADO, NO COMPATIBLE, NO DISPONIBLE EN PROVEEDOR, SIN VERIFICAR); la elección se conserva con su error y **solo se bloquea la ejecución** (nunca se cambia de agente o modelo en silencio). Con modo agéntico OFF y workflow Individual no hace falta Harness. «Actualizar disponibilidad» refresca sin recargar la página. La selección se guarda en el módulo y la comparten la página y el panel (una sola instancia de estado).

## Tools del chat Yaiwes dentro de OpenClaw (UI3)
`GET /v1/swe/tools` y `POST /v1/swe/tools/{id}` del bridge reenvían al Router MVP (MCP `/mcp`, `/plugins/{plugin}/call/{accion}`, `/chat/send`) con la clave del entorno del bridge: motor de archivos (descarga/extracción/copia/búsqueda), LOOP, Cola CIT-50, Watchdog, almacén, memoria, chat, GitHub, pendientes, salas, agente/llm, yaiwes.md, estado del Harness. En el plugin: operación `tools` (catálogo con estado real: el Router solo lista las visibles según Agentes/IA/Tools ON/OFF) y operación `tool` (ejecutar). Tools de agente del modelo: `swe_capacidades`, `swe_tools_catalogo`, `swe_estado`, `swe_tool_llamar` y una por función del chat (espejo): `yaiwes_archivos`, `yaiwes_loop`, `yaiwes_cola`, `yaiwes_watchdog`, `yaiwes_almacen`, `yaiwes_memoria`, `yaiwes_chat` (vía existente del Router) y las réplicas de solo lectura `yaiwes_anclaje`, `yaiwes_constitucion`, `yaiwes_contexto`, `yaiwes_workflows` (cómputo propio del bridge). Su esquema es `{accion?, args?}` y **no admite credenciales de operador**. **El modelo nunca recibe credenciales de operador**: lo que tiene efectos exige que un humano teclee su operador y su token en la UI. **GAP honestos** (el Router no los sirve por HTTP): `anclados-navegador`, `constitucion-propia-navegador` y `workflows-navegador` (viven en el navegador del Director), `workflow-loop-yaiwes`, `orquestador`, `parallel`, `hf_*`, `lifeguard`, `connectivity`, `ssh_bridge`, `agentes`, `chat`, `chat-router`, `motores`, `motores-descarga`. Diseño y [G] completos: `../ARQUITECTURA.md` («OpenClaw espejo…»); prueba real contra el Gateway: `../HANDOFF.md` y `prueba-real/`.

## Construir, validar e instalar
```
cd "SWE CODE free/openclaw-ui"
npm install            # openclaw (SDK y CLI), typebox, typescript 7.0.2, esbuild 0.28.2
npm run build          # tsc + `openclaw plugins build` (necesita Node >= 24.22.1)
npm run validate       # openclaw plugins validate --json
npm test               # tsc + node --test test/*.test.mjs
openclaw plugins install .      # o: npm run pack  y  openclaw plugins install ./swe-selector.tgz
```
Variables del Gateway (nunca en archivos): `RIU_API_KEY` (la clave de acceso; el bridge la acepta como `Authorization: Bearer`; `BRIDGE_TOKEN` es opcional y solo se usa si no hay `RIU_API_KEY`) y, si el bridge no está en `http://127.0.0.1:7870`, `RIU_SWE_BRIDGE_URL`. Notas verificadas: (a) el scaffold oficial con TypeScript 7.0.2 falla `tsc` por `import "./control-ui.css"` (TS2882); `src/css.d.ts` lo resuelve; (b) el manifiesto no declara config propia porque `plugins build` regenera `configSchema` desde `defineFeaturePlugin` (no admite config), por eso todo va por entorno; (c) el SDK publicado 2026.10.9 llama a `api.registerSessionAction`, el `main` del repo a `api.session.controls.registerSessionAction`: el plugin no usa ninguno directamente.

## Qué está verificado y qué no (honesto)
- **Verificado con el OpenClaw real (2026.10.9, Node 24.22.2):** `plugins init`, compilación con los tipos del SDK, `plugins build`, `plugins validate` (válido), `plugins pack` (sha256), `plugins install` (con `--force --accept-capabilities` en un HOME aislado), arranque de un Gateway local con el plugin cargado y llamadas `plugins.sessionAction` reales (`capacidades`, `iniciar`, `tools`, `tool`) hacia las rutas reales de `swe_rutas.js` (Harness y Router simulados).
- **Ejecutado en jsdom (no es el Control UI real):** el DOM del selector, tareas y tools (`test/control-ui-dom.test.mjs`) con un host falso.
- **NO verificado:** el render en un navegador contra el Control UI REAL (el entorno no tiene navegador; `plugins.controlUi.status` sin clientes) y el uso contra el Harness/Router reales del Space (ver `HANDOFF.md`, R10). El Gateway puede avisar `provenance-invalid` al instalar desde archivo local.

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
Todos `POST`, JSON, **autenticados**: `Authorization: Bearer <RIU_API_KEY>` (clave de acceso; también vale `BRIDGE_TOKEN` o `x-bridge-key` si el bridge lo tiene). Sin ninguna credencial configurada en el bridge responden 503 `BRIDGE_TOKEN_NO_CONFIGURADO`; sin token válido, 401.

| Ruta | Cuerpo | Harness |
|---|---|---|
| `/v1/swe/iniciar` | el contrato completo | `swe_iniciar` |
| `/v1/swe/avanzar` | `{task_id, origen?, sesion?, proyecto?}` | `swe_avanzar` (un paso por llamada) |
| `/v1/swe/estado` | ídem | `swe_estado` |
| `/v1/swe/reanudar` | ídem | `swe_reanudar` (desde el último checkpoint) |
| `/v1/swe/aprobar` | `{task_id, op_id, origen?, sesion?, proyecto?}` + cabeceras `x-operador: <operador>` **y** `x-operator-token: <token INDIVIDUAL del operador>` | `swe_aprobar` |

Respuestas: `{ok:true, resultado}` (el resultado es la vista de la tarea: `estado`, `paso_actual`, `plan`, `pasos_terminados[{paso,agente,servidor,recibo,resultado,herramientas,evidencias}]`, `resultado_tool`, `evidencia[]`, `pendiente_aprobacion{op_id,...}`, `error{codigo,mensaje}`); errores de validación 400 `{ok:false,error:{code}}` (`TASK_ID_INVALIDO`, `ORIGEN_INVALIDO`, `CAMPOS_DESCONOCIDOS`, `CAMPOS_FALTANTES`, `MENSAJE_VACIO`, `OP_ID_INVALIDO`, `OPERADOR_REQUERIDO`, …); fallo del Harness 502 `{ok:false,error:{code:"SWE_HARNESS_ERROR",causa}}`. Estados: `PENDIENTE, EJECUTANDO, REQUIERE_APROBACION, RECONCILIAR, CONTINUAR, VERIFICANDO, DONE, GAP`. La UI repite `avanzar` hasta `DONE`/`GAP`/`REQUIERE_APROBACION`/`RECONCILIAR`; `DONE` solo cuando el Harness lo dice (nunca por `finish_reason=stop`).

Aprobar exige TRES cosas, sin valor por defecto: (1) la misma credencial de acceso que todas las `/v1/swe/*` (`RIU_API_KEY` en Bearer); (2) un operador registrado en `BRIDGE_APROBADORES` del bridge (`operador:sha256(token)`, una entrada por persona; sin ella 503 `APROBADORES_NO_CONFIGURADOS`); (3) la cabecera `x-operador` con ese operador y `x-operator-token` con SU token (sin operador 403 `OPERADOR_REQUERIDO`; no registrado 403; token ausente, de otro operador o el del bridge 401 `OPERADOR_NO_AUTORIZADO`). El campo `aprobacion` del cuerpo o del modelo no cuenta; el Harness valida además el nombre contra `RIU_SWE_OPERADORES`. `RECONCILIAR` es un fallo visible: se verifica a mano antes de reanudar.

## Variables (solo backend; nada de esto va al frontend de OpenClaw)
`RIU_API_KEY` (clave de acceso en Bearer, obligatoria tambien para `GET /v1/swe/capacidades`; `BRIDGE_TOKEN` es opcional), `BRIDGE_APROBADORES` (solo `aprobar` y tools con efectos), `RIU_DEEPSEEK_HARNESS_URL`, (la misma `RIU_API_KEY` es la clave del Harness), `RIU_SWE_HARNESS_TIMEOUT_MS` (defecto 60000; `avanzar`/`reanudar` usan `RIU_SWE_AVANZAR_TIMEOUT_MS`, defecto 1800000). Los valores reales van solo en el entorno, nunca en este archivo ni en el repo.

## Capacidades: que esta conectado (solo lectura)
`GET /v1/swe/capacidades` (`web-bridge/src/swe_rutas.js`, `consultarCapacidades`). **Misma autenticacion obligatoria** que `/v1/swe/*` (`Authorization: Bearer <RIU_API_KEY>`, o `BRIDGE_TOKEN`/`x-bridge-key` si existe; sin ninguna credencial en el bridge 503 `BRIDGE_TOKEN_NO_CONFIGURADO`, token malo 401). Sin cuerpo; no cambia nada. El bridge pregunta al Harness su `status` (`POST {RIU_DEEPSEEK_HARNESS_URL}/invoke` con `{"action":"status"}` y `X-API-Key`, solo en el backend) y devuelve lo mismo que `GET /chat/swe/capacidades` de YAIWES, saneado y **sin secretos** (los motivos nombran la variable que falta, nunca su valor; cualquier clave con forma de token se redacta):
```json
{"harness":"ok","agentes":{"opencode":{"disponible":true},"codex":{"disponible":false,"motivo":"codex no esta instalado ..."},"claude-code":{"disponible":true,"modelos":["nvidia/z-ai/glm-5.3"]}},"workflows":{"individual":{"disponible":true},"liquid_mirror":{"disponible":false,"motivo":"falta SWECODE_URL_S2 ..."}},"modelos":{"hf/lfm2.5-350m":{"disponible":true},"groq/qwen/qwen3.8-27b":{"disponible":false,"motivo":"... no figura en GET /models de groq"}}}
```
`harness` vale `ok`, `no_configurado` (falta `RIU_DEEPSEEK_HARNESS_URL`), `sin_credencial` (falta `RIU_API_KEY`) o `no_disponible` (no responde / HTTP no OK / timeout); salvo `ok` las tres listas vienen vacias y la UI debe marcar todo lo que no sea Individual como NO DISPONIBLE. Regla de la UI (identica a YAIWES): agente o workflow sin `disponible:true` -> **NO DISPONIBLE** (deshabilitado); modelo con `disponible:false` -> NO DISPONIBLE (sin entrada = no se sabe, se deja elegir); agente con `modelos` y el modelo elegido fuera de la lista -> **incompatible**. Con la seleccion no disponible no se envia nada (`GAP: SELECCION_NO_DISPONIBLE`); no se cambia en silencio de modelo ni de agente. Quien emite la informacion es el Harness (`status` -> `result.swe`, `agentes/adaptadores/disponibilidad.py`): comprueba binarios y variables sin lanzar ningun agente.

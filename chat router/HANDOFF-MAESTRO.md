# HANDOFF MAESTRO — Chat, plan, agentes y todo lo creado/descargado
Actualizado: 2026-09-26 20:30 UTC por Opus. Para cualquier sesión de Claude u otra IA que continúe. Leer entero antes de actuar.

## 0. Reglas del Director (obligatorias)
- Anotar cada instrucción del Director 1 a 1 (verbatim) ANTES de ejecutar. Lo no resuelto = GAP, nunca inventar.
- No cambiar instrucciones, diseño ni herramientas del Director sin su autorización expresa.
- Respuestas cortas, sin jerga. Delegar con DSL DAG. Nunca claves en repos (son públicos): solo nombres de secretos.
- Rutas de IA: NVIDIA (hasta 4 claves, Kimi más nuevo si existe) → Cerebras → Groq → DeepSeek V4 Flash al final. Sin APIs de Anthropic.
- Descargas SOLO con el motor de descarga y extracción.

## 1. Fuentes de verdad
| Qué | Dónde |
|---|---|
| Instrucciones del Director (verbatim) | `chat router/INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL.md` (parte 1), `-PARTE-3.md`, `-PARTE-4.md`. Parte 2 (documentos completos del 25-sep) redactada en el chat de Opus, NO subida → GAP |
| Handoff anterior (detalle) | `chat router/HANDOFF-CHAT-AGENTES-PLAN.md` |
| Memoria de Hugging Face | `README-HUGGINGFACE.md` (raíz) + dataset HF `COMAND-CENTER-1/yaiwes-hf-memoria` |
| T-3000 MOTOR AUTOEVOLUTION | repo frontend, `T-3000 MOTOR AUTOEVOLUTION 👾/HANDOFF-T3000.md` (+ archivo del Director en `00-ENTRADA/`, NO TOCAR) |

## 2. Conector MCP de Claude (RESUELTO 26-sep)
- Space `COMAND-CENTER-1/claude-github-mcp-backup`, CPU Upgrade, **nunca dormir**.
- OAuth de GPT **quitado**. El conector vive solo en una **dirección secreta** `/<MCP_SECRET_PATH>/mcp` (secreto del Space = RIU_ROUTER_API_KEY). En Claude se llama "HF_Gith_Allow_Access". Pedir la dirección al Director; no se escribe aquí.
- Workflows relacionados: `mcp-sin-oauth-once.yml` (aplicado OK). `keep-mcp-space-awake.yml` DESACTIVADO. Keeper Job APAGADO. No reencender sin autorización.

## 3. Chat
- Publicado: https://riu-jev-bridge.vercel.app (Vercel = pantalla; función `/api` = puente al Router con claves en variables de Vercel). Pantalla propia de Opus.
- **El Director NO lo aprueba**: pidió Open WebUI o un chat open source descargado, con sus skills y diseños (fábrica UI) y cada botón probado. → PENDIENTE PRINCIPAL.
- Backend: Router FastAPI (HF Job, URL en `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag`). Rutas del Router que el chat usa: `/chat/send` (modo direct/agent, memoria por conversación), `/chat/providers`, `/chat/agents`, `/chat/documents`, `/chat/github/*`, `/chat/conversations`, `/chat/dag/run`. Rutas nuevas de Opus: `integration/chat_mvp/ui_bridge.py` (`/control/*`, `/groups`, `/workflows`, órdenes al buzón del agente).
- Pendiente del chat (instrucciones del Director): selector de 3 modos de ruta + Kimi K3, IA local individual de HF, conectar APIs/MCP sin GitHub, enrutar adjuntos, sandbox por agente (Memoria.md/Claude.md/Handoff.md), cablear agentes con botones, mirror, destino del agente, motores de búsqueda como contexto, Council, barra Work + Action Registry, Archify, rewind, compact, handoff automático, panel de control separado.

## 4. Plan de 4 objetivos (repo agentes)
- Plan: https://github.com/maxbry123-commits/agentes/blob/main/Claude%20notas/PLAN-MAESTRO-4-OBJETIVOS.md — Handoff del loop: `Claude notas/PLAN-OPUS/HANDOFF-PLAN-OPUS.md`.
- Mini router (repo router): `.github/workflows/mini-router-plan-4-objetivos.yml` — loop con Cerebras/NVIDIA/Groq (sin DeepSeek), cada hora, resultado como rama+PR en agentes + copia de respaldo (artifact).
- Estado: los agentes trabajan ~40 min por vuelta. Las 5 vueltas del 26-sep perdieron el resultado (clave sin permiso de escritura). Arreglado 19:24 (clave de acceso completo, sin credencial pegada, artifact). Vuelta nueva lanzada 19:24 → revisar su PR.

## 5. Staff de agentes decidido (aún SIN conectar al Router)
Rowboat (orquestador principal) · Ruflo (flujo/enjambre) · Claude Code (diseña y revisa, vía Router) · Grok/GrokBot (ejecuta) · 4 de Meta en `agents-yaiwes/donors/`: Muse Code (programa), Muse Glimmer (decide), MetaCua (navega web y revisa frontend con capturas), CUA+MCP (computadora de pruebas) · apoyo Hermes, Microsoft Agent Framework, Codex, MiMo Code · memoria Memanto + Graphiti + Graphify.

## 6. Motores de descarga
- Motor canónico: `➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/📂Motor descarga de componentes y extracción de zip/hf_download_extract_engine.py`.
- Mejoras 26-sep (autorizadas): salta enlaces internos y los registra; "ya descargado" = éxito; prueba main/master/HEAD.
- Replicador: `.github/workflows/replicar-motores.yml` copia la carpeta de motores a TODOS los repos de la cuenta cuando cambia.
- Cadenas de descarga (repo router, `agents-yaiwes/`): `agent-40-motor-frontend-a` (20 de chat/panel → frontend), `agent-41-motor-frontend-b` (20 skills/diseño → frontend), `agent-42-motor-router-agentes` (15 del staff/micro kernel → router), `agent-43-motor-omniroute`. Relanzadas 26-sep 19:23 tras el arreglo → revisar su `crazy_wall.state.json`.

## 7. Componentes YA descargados (confirmados)
- Router (`router inteligente universal/Componente open soure router inteligente universal/`): Open WebUI, Hermes, Rowboat, Microsoft Agent Framework, Graphify, Graphiti, Memanto (+ lo que hayan cerrado 42/43).
- Frontend (`UI YAIWES/componentes open soure UI YAIWES/`): 160 entradas previas (Onlook, Plasmic, Webstudio, Playwright, shadcn, HyperFrames, etc.) + lo que cierren 40/41. Otra IA también monta componentes allí (commits "Motor1+Motor3").
- Agentes (`agents-yaiwes/donors/`): 4 piezas de Meta.

## 8. Hugging Face (ver README-HUGGINGFACE.md)
- Spaces OmniRoute creados 26-sep: `COMAND-CENTER-1/omniroute-1..5`, CPU Upgrade 32 GB, **duermen tras 1 h sin uso** ($0.03/h despiertos). Crear Spaces gratis por API → 402; con hardware de pago en la misma llamada → OK.
- Despliegue: `.github/workflows/omniroute-deploy.yml` (OmniRoute oficial v3.8.51, API `/v1`, REQUIRE_API_KEY=true, contraseña inicial = RIU_ROUTER_API_KEY). Lanzado 20:26 → revisar build de cada Space.
- PENDIENTE OmniRoute: crear en cada instancia su clave de API y sus proveedores ("5 cuentas" independientes), guardar las 5 claves como secretos de GitHub `OMNIROUTE_KEY_1..5`, y añadir `omniroute` como proveedor en el Router (ruta con salto entre las 5).

## 9. Orden sugerido para continuar
1) Revisar build de los 5 OmniRoute y conectarlos al Router. 2) Revisar PR de la vuelta del plan de 4 objetivos. 3) Revisar descargas 40–43. 4) Chat sobre Open WebUI / chat descargado con skills del Director (pendiente principal). 5) Conectar el staff al Router. 6) T-3000 (discutir plan con el Director antes de programar). 7) Subir la PARTE 2 de instrucciones.

## 10. Crazy Wall (estado)
```json
{"actualizado":"2026-09-26T20:30Z","conector_mcp":"RESUELTO","chat":"PUBLICADO_NO_APROBADO","plan_4_objetivos":"CORRIENDO_GUARDADO_ARREGLADO","descargas":"RELANZADAS_MOTOR_MEJORADO","replicador_motores":"ACTIVO_TODOS_LOS_REPOS","omniroute":"5_SPACES_CREADOS_DESPLIEGUE_EN_CURSO","staff":"DECIDIDO_SIN_CONECTAR","t3000":"RECEPCION_SIN_CODIGO","gaps":["parte_2_instrucciones","chat_open_webui","omniroute_claves_y_router","staff_al_router"]}
```

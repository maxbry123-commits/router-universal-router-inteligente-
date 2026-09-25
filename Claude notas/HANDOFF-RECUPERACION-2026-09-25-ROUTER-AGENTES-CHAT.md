# HANDOFF DE RECUPERACIÓN — Router Inteligente Universal + Agentes + Chat (2026-09-25)

Para: Opus (u otra sesión) que continúa el CHAT. Director: Max. Idioma: español, respuestas cortas, sin jerga.
Repo: https://github.com/maxbry123-commits/router-universal-router-inteligente-  (rama main, PÚBLICO: nunca escribir claves en archivos)

## 0. Reglas del Director (obligatorias)
1. Anotar cada instrucción del Director textual (1 a 1) en `Claude notas/INPUT-VERBATIM-*.md` ANTES de ejecutar.
2. Claude/Opus es orquestador: DELEGA a agentes (DSL DAG determinista en chain.yaml), no ejecuta a mano lo que puede hacer un agente.
3. Tareas de principio a fin (objetivo final verificable), nunca parciales. Sin sobre-ingeniería. No cambiar diseño ni herramientas sin autorización.
4. Modelo: SOLO DeepSeek V4 Flash (cuenta HF del Director). MiniMax, NVIDIA, Groq, Cerebras: EN PAUSA hasta que el Director autorice.
5. Nada de GPU en Hugging Face (ya hubo un gasto no autorizado de ~$8 con a10g-small). Solo cpu-basic / cpu-upgrade (32 GB).
6. No tocar el Job del Router ni el Space del conector sin autorización.

## 1. Estado verificado (prueba real 2026-09-25 00:25 UTC)
| Pieza | Estado |
|---|---|
| Router central (Job HF, cpu-upgrade 32 GB, 6 h, se relanza solo) | VIVO. `/health` 200, `/chat/send` DeepSeek → "OK", `/chat/jev` → decisión válida, sin clave → 401 |
| URL del Router | Cambia en cada relanzamiento. SIEMPRE leer `LIVE_URL=` en `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` |
| Webhook GitHub (push) → Space `COMAND-CENTER-1/claude-github-mcp-backup` `/webhook` | ACTIVO. Si el Router no responde, lo relanza con las 3 claves y actualiza LIVE_URL. Si está vivo responde 200 y no hace nada |
| Spaces en HF | Solo 1: `claude-github-mcp-backup` (conector MCP de GitHub + webhook). Los de prueba se borraron |
| Ruta de modelos de los agentes | `agents-yaiwes/ROUTE.json`: solo `deepseek_flash` |
| Pausa remota | `PAUSED=true` en ROUTER_JOB_PAUSE.flag + push. `PAUSED=false` reanuda |
| Vercel | 0 despliegues. El chat NUNCA se publicó en Vercel. Conector de Vercel: solo lectura (crear despliegue da 403) |

## 2. Cómo llamar al Router (headers obligatorios)
```
Authorization: Bearer <HF_TOKEN>          # lo exige el proxy de hf.jobs
X-API-Key: <RIU_ROUTER_API_KEY>            # clave propia del Router (secreto de GitHub RIU_ROUTER_API_KEY)
```
Rutas: `GET /health` · `POST /chat/send` · `POST /chat/jev` · `POST /chat/route` · `GET /chat` (UI del chat MVP) · `/chat/agents` · `/chat/documents` · `/chat/github/*` · `/chat/storage` · `/chat/usage`.
Ejemplo /chat/send: `{"message":"hola","provider":"hf","model":"deepseek-ai/DeepSeek-V4-Flash","max_tokens":200}`

## 3. Cómo activar un agente (sin GitHub Actions manual, sin tocar HF)
Push a main del `chain.yaml` de UN agente: `router inteligente universal/agents-yaiwes/agent-<N>-<nombre>/chain.yaml`.
El push dispara el workflow `riu-agents-run.yml` para ese agente (y el webhook mantiene vivo el Router).
Respuesta del agente: `agent-<N>/crazy_wall.state.json` (CLOSED/BLOCKED, modelo, router_connected) y `steps/<paso>/results/output.txt`.
Plantilla mínima de chain.yaml: schema `yaiwes.chain/v1`, `input_block`, `agent{id, framework: pocketflow|smolagents, group, route:[deepseek_flash]}`,
`context.text`, `steps[{id, task, checks[{kind: min_chars|contains|python_ast|python_exec|js_syntax|no_secrets}]}]`, `edges`.

## 4. Secretos (valores NUNCA en archivos)
GitHub Actions: `HF_TOKEN_1`, `GH_JOB_PUSH_TOKEN` (PAT GitHub acceso total), `RIU_ROUTER_API_KEY`, `RIU_AGENT_API_KEYS_JSON`, `RIU_RUNTIME_BANK_PASSPHRASE`.
Space del conector: `GITHUB_PERSONAL_ACCESS_TOKEN`, `HF_TOKEN`, `RIU_AGENT_API_KEYS`.
PENDIENTE: el PAT de GitHub y la clave del Router pasaron por un chat → rotarlos cuando el Director lo autorice.

## 5. Archivos clave
- Router (FastAPI): `router inteligente universal/integration/chat_mvp/` → app.py, router.py (/chat/*), route_api.py (/chat/route, /chat/jev), jev.py, providers.py, core.py, resilience.py, store.py, chat_ui.html
- Job persistente: `agents-yaiwes/common/router_job_persistent.py` (git pull cada 60 s, pausa por flag)
- Conector + webhook: Space HF `COMAND-CENTER-1/claude-github-mcp-backup/app.py`
- Agentes: `agents-yaiwes/chain.py` (ejecutor), `common/boot.py` (banco, latido al Router), `kernel/sheriff.py` (validación determinista)
- Workflows: `riu-agents-run.yml` (agentes), `riu-router-keys-setup.yml` (relanzar Router con claves + prueba), `riu-router-smoke.yml` (prueba rápida del Router vivo), `riu-watchdog.yml`
- Notas: `Claude notas/` (INPUT-VERBATIM-*, HANDOFF-COMPLETO-2026-09-22.md, RIU-01xx)

## 6. Agentes existentes (carpetas agents-yaiwes/agent-*)
Chat: 1 (paneles), 2 (trabajos/plantilla/Crazy Wall), 3 (Static Space), 16 (Open WebUI/UI — BLOQUEADO en adapt_openwebui_real),
17 (backend 32 GB — BLOQUEADO en backend_router_live), 18 (integración/E2E — CLOSED), 19 (componentes Open WebUI — BLOQUEADO en acquire_open_webui), 12 (router chat support — CLOSED).
Orquestadores: 14 (Microsoft Agent Framework), 15 (Grok Build — BLOQUEADO en fetch_and_connect).
Modelos/HF: 4, 6, 7, 8, 9, 10. Descargas: 11, 20 (OpenClaw + Rowboat). Auditor: 5. Inventario: 13.
Nota: los agentes 15-19 y parte del 14 los escribió otra sesión (con protocolo propio "motores canónicos"); revisar su chain.yaml antes de editarlos.

## 7. EL CHAT — lo que falta (objetivo de la próxima sesión)
Decisión del Director (aprobada): chat open source tipo Open WebUI, conectado al Router, con:
1. Selector de modelos: locales en HF + API de pago HF + Groq/NVIDIA/Cerebras (hoy en pausa; solo DeepSeek activo).
2. Selector de modelo con agente (con agente / sin agente).
3. Selector de cuentas de GitHub.
4. Subir archivos y anclarlos al sistema de almacenamiento (SQL + grafo + caché + documentos; memoria por chat/proyecto/global).
Estado real: el backend del chat EXISTE y funciona en el Router (`/chat/send`, `/chat/agents`, `/chat/documents`, `/chat/github/*`, `/chat/storage`, UI mínima en `/chat`).
Lo que NO existe: la interfaz Open WebUI publicada con URL pública. Grok (agente 15) no llegó a hacerla; Vercel tiene 0 despliegues.
Bloqueos conocidos: crear Spaces nuevos en HF da 402 (usar el Space existente o un Job); Vercel del conector es solo lectura; agentes 16/17/19 bloqueados.
Camino más corto sugerido (confirmar con el Director antes): Open WebUI apunta a un endpoint compatible con OpenAI → servir Open WebUI en un Job HF cpu-upgrade
con OPENAI_API_BASE_URL = <LIVE_URL>/v1 y los headers del punto 2 (el gateway ya expone `/v1/chat/completions` y `/v1/models`), delegado a los agentes 16/17/19 con cadenas de principio a fin.

## 8. Pendientes aparte del chat
- Modelos locales (Qwen3.5-0.8B, LFM2.5-1.2B, Gemma 4 E2B, etc.) instalados y conectados al Router: probado el patrón en un Job, no hay ninguno fijo corriendo.
- Salto entre procesadores HF al 95%: lógica escrita (hf_hop.py), no conectada a Jobs reales.
- Centinela/sheriff con Qwen 0.6B + Liquid 1B cada 10 min: no construido.
- Microsoft Agent Framework y Grok Build como orquestadores reales: no operativos.
- Router Yaiwes independiente (TimesFM + HRM + búsqueda): solo plan y README.

# Componentes open source para Chat BOTS (backend) — inventario y reciclaje

Actualizado: 17-oct-2026 00:40, hora Bogotá (UTC-5). Autor: agente de descarga `docs/componentes-os`.

**Regla:** el agente backend de Chat BOTS **debe esperar esta descarga y reciclar estos componentes antes de escribir código propio.** Todo dato de las tablas sale de los archivos descargados (rutas citadas); las licencias salen de los `LICENSE`. Lo que no se pudo comprobar en el código va marcado «por confirmar».

## 1. Descarga

- **Dónde está (box compartido):** `/workspace/componentes-os/<componente>/` (con `.git` superficial; el código de terceros **no** se sube a ningún repo).
- **Motor:** se leyó el motor canónico de Antonio `Motores descarga extracción búsquedas/➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/📂Motor descarga de componentes y extracción de zip/hf_download_extract_engine.py` (blob `a0e1c87f…`) + `motor_2_queue_download_extract.py` (`84d566e2…`) + `motor_1_extract_only.py` (`a52d5dc0…`). **No se usó** (sin modificarlo) porque:
  1. `acquire()` baja el árbol completo del repo (`git fetch --depth=1 --filter=blob:none` + `checkout` de todo); no admite filtrar carpetas → incumple «solo esas carpetas».
  2. Con `PUBLISH=0` el árbol extraído vive en un `tempfile.TemporaryDirectory` y se borra al terminar (solo imprime el manifiesto JSON).
  3. Con `PUBLISH=1` hace commit + push del código de terceros y de los `.zip.part-*` a un repo de GitHub → prohibido en esta tarea.
- **Fallback usado:** `git clone --depth 1 --filter=blob:none --sparse` + `git sparse-checkout set --no-cone` solo con las carpetas pedidas + `LICENSE*` + `README.md` (script `/workspace/componentes-os/_fallback.sh`, commits en `_commits.txt`). Sin `.tar.gz` ni `.zip`.
- **Disco `/`:** antes 23 G libres (82 %); después 23 G libres (82 %). Total descargado 32 MB (23 MB sin `.git`).

| Componente | Repo @ commit | Carpetas bajadas | Tamaño (sin .git) | Licencia (archivo) |
|---|---|---|---|---|
| Agent Zero | `agent0ai/agent-zero` @ `ff2a5b9c9c` | `plugins/` (incl. `_browser`, `_memory`), `skills/` | 12 MB | MIT (`agent-zero/LICENSE`; también `plugins/_orchestrator/LICENSE`, `plugins/_skills/LICENSE`, `plugins/_commands/LICENSE` = MIT) |
| OpenManus | `FoundationAgents/OpenManus` @ `3309bf4e41` | `app/`, `run_flow.py`, `run_mcp.py`, `sandbox_main.py`, `protocol/a2a/` | 1,1 MB | MIT (`openmanus/LICENSE`) |
| OpenHands | `OpenHands/OpenHands` @ `045290739f` | solo `LICENSE`, `README.md` | 24 KB | MIT (`openhands/LICENSE`) |
| OpenHands SDK | `OpenHands/software-agent-sdk` @ `1fbfd37f6f` | `openhands-tools/openhands/tools/browser_use/`, `openhands-agent-server/` | 1,8 MB | MIT (`openhands-software-agent-sdk/LICENSE`) |
| OpenHands Automation | `OpenHands/automation` @ `bc4cca7c7e` | repo completo | 4,7 MB | MIT (`openhands-automation/LICENSE`) |
| Agent-S | `simular-ai/Agent-S` @ `15776a8dc6` | `gui_agents/`, `integrations/openclaw/`, `tests/` | 0,9 MB | Apache-2.0 (`agent-s/LICENSE`) |
| Browser Use | `browser-use/browser-use` @ `ccd22fef47` | `browser_use/` (paquete core) | 3,2 MB | MIT (`browser-use/LICENSE`) |

## 2. Agrupación de Antonio (4 + 1)

| Grupo | Componente | Qué aporta (según el código) |
|---|---|---|
| 1 | **Agent Zero** → memoria + plugins + skills + proyectos + multiagente | `plugins/_memory` (FAISS por subdirectorio, áreas `main/fragments/solutions`), sistema de plugins `plugin.yaml` con `per_project_config`/`per_agent_config`, `skills/*/SKILL.md`, `plugins/_orchestrator` (adaptadores a CLIs de agentes), `plugins/_tool_access` (política de tools por proyecto/agente) |
| 2 | **OpenManus** → agente general + MCP + Flow + A2A + sandbox | `app/agent/manus.py`, `app/flow/planning.py` (`PlanningFlow`), `app/mcp/server.py` (FastMCP), `run_mcp.py`, `protocol/a2a/app/main.py` (servidor A2A), `app/sandbox/core/sandbox.py` (`DockerSandbox`), `sandbox_main.py` (Daytona) |
| 3 | **OpenHands** → runtime + estado + herramientas + aislamiento + automatización | `openhands-agent-server` (REST/WebSocket, conversaciones, eventos, bash, MCP, skills, sub-agentes, `docker_runtime/`, lease), `openhands-tools/.../browser_use`, `automation` (cron, webhooks, dispatcher, watchdog) |
| 4 | **Agent-S** → Computer Use + GUI + percepción → acción | `gui_agents/s3/agents/grounding.py` (captura → OCR → acciones `pyautogui`), `agent_s.py`, `worker.py`, `bbon/` (juez comparativo), `memory/procedural_memory.py` |
| +1 | **Browser Use** (transversal) | `browser_use/` agente de navegador por CDP (`browser/session.py` usa `cdp_use`), `tools/registry`, `browser/watchdogs/*`, `mcp/server.py`, `llm/*` (muchos proveedores, `openai/chat.py` con `base_url`) |

## 3. Tabla COMPONENTE → REPO → CARPETA → FUNCIÓN → LICENCIA → SIRVE / NO SIRVE PARA YAIWES

Contexto RIU (de `HANDOFF/CHATBOTS/README-ARQUITECTURA.md`): ruta fija **COMPONENTE → HARNESS (puente_chat) → HTTP → FICHA → MODELO**; plugin `orquestador` (`plugin.py`, `sandbox.py` HF Jobs > Vercel > local bwrap, `deploy.py`), memoria = fachada `memoria_yaiwes` (SQLite `riu_chat.sqlite3` → grafo fallback/state-hub → bucket), MCP, mirror, 50 agentes por sección. **Nada de lo de abajo puede llamar a un modelo directo**: el LLM de cada componente se apunta al harness/FICHA (vía `base_url` OpenAI-compatible o adaptador) o se reemplaza.

| Componente | Repo | Carpeta | Función (código) | Licencia | ¿Sirve? | Motivo / parte de RIU que reemplaza o mejora |
|---|---|---|---|---|---|---|
| Agent Zero | agent-zero | `plugins/_memory/` (`helpers/memory.py`, `memory_consolidation.py`, `memory_quality.py`, `tools/memory_*.py`) | Memoria vectorial FAISS por subdir/agente/proyecto, consolidación, filtro de calidad, tools guardar/cargar/olvidar | MIT | **SIRVE (lógica)** | Importa `agent`, `helpers` de Agent Zero (no bajados) y `langchain`/`faiss` → no corre suelto. Reciclar **consolidación + calidad + áreas** como capa sobre `memoria_yaiwes`/SQLite (MEMORY ROUTER: usuario/proyecto/agente). No reemplaza SQLite ni graphiti. |
| Agent Zero | agent-zero | `plugins/_browser/` (`tools/browser.py`, `helpers/playwright.py`) | Tool de navegador Playwright + visor WebUI | MIT | Parcial | Acoplado al core (`helpers.tool.Tool`). Como navegador, Browser Use (abajo) es más independiente. |
| Agent Zero | agent-zero | `plugins/` (sistema: `plugin.yaml`, `_tool_access`, `_skills`, `_goal`, `_time_travel`, `_error_retry`, `_chat_compaction`, `_code_execution`, `_desktop`) | Plugins por proyecto/agente, política de tools, objetivo del chat, historial/revert de workdir, reintento, compactación, ejecución terminal/Python/Node, escritorio Xpra/Xfce | MIT | **SIRVE (diseño)** | Mejora `orquestador`: `_goal` → GOAL LOCK, `_tool_access` → permisos mínimos por agente, `_time_travel` → CHECKPOINTS/ROLLBACK, `_error_retry` → reintento, `_chat_compaction` → recorte de los 12 mensajes. Copiar ideas/estructura, no el runtime. |
| Agent Zero | agent-zero | `plugins/_orchestrator/` | Adaptadores a CLIs (a0, codex, claude, cursor, gemini, grok, hermes, opencode) en `helpers/adapters/` | MIT | No (por ahora) | Llama CLIs externos con sus propios logins; RIU exige pasar por FICHA. Útil solo como patrón de registro de adaptadores (TOOL REGISTRY). |
| Agent Zero | agent-zero | `skills/` (`a0-create-agent/SKILL.md`, `scheduled-tasks`, `build-skill`…) | Skills con front-matter (`name`, `trigger_patterns`) | MIT | **SIRVE** | Formato `SKILL.md` reutilizable para skills de agentes Chat BOTS (crear agente, tareas programadas). Contenido es específico de A0. |
| OpenManus | OpenManus | `app/flow/planning.py`, `run_flow.py` | `PlanningFlow`: crea plan, estado por paso (`PlanStepStatus`), ejecuta pasos con varios agentes | MIT | **SIRVE** | Mejora orquestador: PLAN LOCK + TASK COMPILER + 1 tarea = 1 worker. Pequeño y legible. |
| OpenManus | OpenManus | `app/agent/` (`base.py`, `toolcall.py`, `react.py`, `manus.py`) | Bucle por pasos con `max_steps`, detección de atasco (`is_stuck`, `duplicate_threshold`) | MIT | **SIRVE** | Reciclar `is_stuck` → LOOP DETECTOR y `max_steps` para agentes Chat BOTS. `app/llm.py` usa `AsyncOpenAI` con `base_url` → apuntable al harness. |
| OpenManus | OpenManus | `app/mcp/server.py`, `app/agent/mcp.py`, `app/tool/mcp.py`, `run_mcp.py` | Servidor MCP (FastMCP) que registra tools; agente cliente MCP stdio/sse | MIT | **SIRVE** | Complementa el MCP de RIU: exponer tools del orquestador por MCP y consumir MCP externos. |
| OpenManus | OpenManus | `protocol/a2a/app/` | Servidor A2A (`a2a.server`, `AgentCard`, `InMemoryTaskStore`) | MIT | Parcial | Interoperar agentes Chat BOTS con agentes externos; estado en memoria (no persistente). Por confirmar si Antonio quiere A2A. |
| OpenManus | OpenManus | `app/sandbox/core/` (`sandbox.py` `DockerSandbox`), `app/daytona/`, `sandbox_main.py`, `app/tool/sandbox/` | Sandbox Docker local; sandbox Daytona (servicio externo) con tools shell/files/browser/vision | MIT | No (como reemplazo) | Necesita Docker o cuenta Daytona; RIU ya tiene `sandbox.py` (HF Jobs/Vercel/bwrap). Reciclar solo la interfaz de tools `sb_*`. |
| OpenManus | OpenManus | `app/tool/computer_use_tool.py` | Computer use sobre sandbox Daytona | MIT | No | Depende de `app.daytona`. Para Computer Use, Agent-S. |
| OpenHands SDK | software-agent-sdk | `openhands-agent-server/openhands/agent_server/` (`conversation_service.py`, `event_service.py`, `bash_router.py`, `mcp_router.py`, `skills_router.py`, `sub_agents_router.py`, `conversation_lease.py`, `persistence/`, `openai/`) | Servidor REST/WebSocket de agentes: conversaciones, eventos, bash, MCP, skills, sub-agentes, lease de dueño (crash-recovery), gateway OpenAI `/v1` | MIT | **SIRVE (referencia fuerte)** | Mejora `orquestador` (estado/eventos/lease → STATE MACHINE, HEARTBEAT, RECOVERY). Requiere `openhands-sdk` (no bajado), Python ≥3.12, FastAPI, docker → no se monta entero en el Space; copiar patrones (`conversation_lease.py`, `event_service.py`, `_secret_redaction.py`). |
| OpenHands SDK | software-agent-sdk | `openhands-agent-server/.../docker_runtime/` | Provisión/proxy/registro de contenedores por conversación | MIT | No | Necesita Docker; el Space/HF Jobs ya cubren aislamiento. |
| OpenHands SDK | software-agent-sdk | `openhands-tools/openhands/tools/browser_use/` | Tools de navegador (navigate, click, type, get_state, tabs, storage, grabación rrweb) sobre `browser_use` | MIT | **SIRVE** | Definiciones de tools de navegador listas + grabación rrweb (evidencia → EVIDENCE GATE). Depende de `openhands.sdk` → adaptar `definition.py` a tools de puente_chat. |
| OpenHands Automation | automation | `openhands/automation/` (`scheduler.py`, `dispatcher.py`, `watchdog.py`, `models.py`, `backends/local.py`) | Cron (`croniter`) + webhooks + cola en tabla (`PENDING→RUNNING→COMPLETED/FAILED/CANCELLED/SKIPPED`) + watchdog de RUNNING colgados con `timeout_at` | MIT | **SIRVE** | Exactamente WATCHDOG + QUEUE MANAGER + Routines de Antonio. Usa PostgreSQL/SQLAlchemy (también `aiosqlite` en deps) → reciclar `watchdog.py` y la máquina de estados sobre la memoria SQLite de RIU. |
| OpenHands | OpenHands | `README.md` | Agent Canvas (UI self-hosted para agentes/automatizaciones) | MIT | No | Solo README bajado; RIU tiene su propio frontend. |
| Agent-S | Agent-S | `gui_agents/s3/` (`agents/agent_s.py`, `worker.py`, `grounding.py`, `core/engine.py`, `bbon/`, `memory/procedural_memory.py`, `utils/local_env.py`) | Computer Use: captura → OCR/grounding → acciones `pyautogui`; motores LLM OpenAI/Anthropic/Gemini/OpenRouter con `base_url`; juez comparativo; ejecutor local bash/python | Apache-2.0 | **SIRVE (Computer Use)** | Única pieza de Computer Use de escritorio. Requiere pantalla (X/`pyautogui`), tesseract y modelo de grounding con visión → no corre en el Space actual; candidato para un worker con escritorio (por confirmar dónde). `LMMEngineOpenAI(base_url)` permite apuntar a FICHA si el modelo tiene visión. |
| Agent-S | Agent-S | `integrations/openclaw/` (`agent_s_wrapper.py`, `agent_s_task`, `SKILL.md`) | Envoltorio CLI/skill para invocar Agent-S como tarea | Apache-2.0 | **SIRVE** | Patrón directo para una tool `computer_use(tarea)` del orquestador. |
| Agent-S | Agent-S | `tests/test_providers.py` | Pruebas unitarias de motores LLM con mocks | Apache-2.0 | Parcial | Plantilla de pruebas del adaptador a FICHA. |
| Browser Use | browser-use | `browser_use/` (`agent/service.py`, `browser/session.py`, `browser/watchdogs/`, `tools/registry/`, `mcp/server.py`, `llm/openai/chat.py`) | Agente de navegador por CDP, registro de tools, watchdogs (crash, captcha, downloads, security, popups…), servidor MCP, multi-proveedor LLM | MIT | **SIRVE (navegador)** | Navegador real para agentes Chat BOTS (mirror desde enlaces del agente, lectura de páginas). `llm/openai/chat.py` admite `base_url` → harness. `sandbox/sandbox.py` usa Browser Use Cloud (`BROWSER_USE_API_KEY`) → NO usar esa parte. |

### Top que SIRVEN para el backend Chat BOTS
1. **OpenHands Automation** `watchdog.py` + `dispatcher.py` + estados → watchdog/cola/rutinas.
2. **OpenManus** `app/flow/planning.py` + `app/agent/base.py` (`is_stuck`) + `app/mcp/server.py` → plan, loop detector, MCP.
3. **Browser Use** `browser_use/` (+ tools de `openhands-tools/.../browser_use`) → navegador y mirror desde enlaces.
4. **Agent Zero** `_memory` (consolidación/calidad), `_goal`, `_tool_access`, `_time_travel`, `skills/` → memoria por niveles, GOAL LOCK, permisos, checkpoints.
5. **OpenHands agent-server** `conversation_lease.py`, `event_service.py`, `_secret_redaction.py` → estado, recuperación, redacción de secretos.
6. **Agent-S** `gui_agents/s3` + `integrations/openclaw` → Computer Use (necesita worker con escritorio).

## 4. Qué reciclar por pieza del backend Chat BOTS

| Pieza RIU | Hoy (rama `orquestador-agentes-rebase`) | Reciclar de |
|---|---|---|
| Agentes | dicts en `plugin.py`, estados `activo/trabajando/…` | OpenManus `app/agent/base.py` (bucle, `max_steps`, `is_stuck`), `app/flow/planning.py`; OpenHands `sub_agents_router.py` |
| Mirror | `mirror(de=chat o id)`; «desde enlaces»: no existe | Browser Use `browser_use/` + `openhands-tools/.../browser_use/definition.py` para abrir los enlaces y volcar contenido |
| Sandbox | `sandbox.py` HF Jobs > Vercel > bwrap | Mantener. Ideas: OpenHands `conversation_lease.py`; OpenManus `app/tool/sandbox/sb_*` (interfaz de tools) |
| Memoria | `memoria_yaiwes` (SQLite → grafo → bucket) | Agent Zero `_memory/helpers/memory_consolidation.py`, `memory_quality.py`, áreas `main/fragments/solutions`, `per_project/per_agent` |
| Browser | no hay | Browser Use (core) |
| Computer use | no hay | Agent-S `gui_agents/s3` + `integrations/openclaw/agent_s_wrapper.py` |
| Rutinas / watchdog | no hay | OpenHands Automation `scheduler.py`, `dispatcher.py`, `watchdog.py` |
| MCP | MCP de RIU | OpenManus `app/mcp/server.py`; Browser Use `mcp/server.py`; OpenHands `mcp_router.py` |

## 5. Pendiente / por confirmar
- Dónde correr Computer Use (Agent-S) y Browser Use: el Space actual (sin pantalla/Chromium confirmados) — por confirmar.
- Qué modelos de FICHA tienen visión (Agent-S lo necesita) — por confirmar.
- A2A (OpenManus `protocol/a2a`): ¿lo quiere Antonio?
- Nada de esto está integrado ni probado en Android; es inventario.

# Agentes
Destino: `plugins/agentes` (agents-yaiwes, sentinelas, microkernel, workflow-agentes), `09-CLAUDE-CODE` (puente de Claude Code), `plugins/orquestador`, `plugins/parallel`,
n8n, Prefect, Temporal, Durable-*, ruflo, rowboat, autogen, crewAI, langgraph, pydantic-ai, microsoft-agent-framework, haystack,
agentes listos (OpenHands, OpenManus, Agent-S, agent-zero, strix, artemis, rea, browser-use, CLI-Anything), investigación (agents-deep-research, open_deep_research, dzhng-deep-research, gpt-researcher), `componentes/fuentes-extraidas`.

## Qué quedó dónde
- `plugins/agentes/*` → `chat-router/agentes/agentes-yaiwes/` (05-AGENTES, 07-SENTINELAS, agent-microkernel, agents, agents-yaiwes, workflow-agentes).
  `plugins/agentes` queda como enlace simbólico a `../chat-router/agentes/agentes-yaiwes` (lo usa `router/tests/test_lifeguard.py`, protegido).
- `plugins/chat-router/09-CLAUDE-CODE` → `chat-router/agentes/claude-code/` (sin referencias externas; sin enlace).
- Pendiente de mover: plugins/orquestador, plugins/parallel, n8n, etc. (listados arriba).

## Completado de agentes listos (2026-10-31)
Motor usado: `motores/archivos` (`chat/backend/mvp/archivos`: `origen.clonar` clon superficial sin LFS + `acciones.copiar(sobrescribir=False)` con sha256). Solo se copiaron archivos AUSENTES (nada sobrescrito, sin `.git`, tope 20 MB). Comparacion: lista de archivos del upstream vs la carpeta local.

| Agente | Estado | Origen (commit) | Completado |
|---|---|---|---|
| SWE-agent | 385/409 identicos (mismo commit); faltaba `trajectories/` | github.com/SWE-agent/SWE-agent @ 3ea751c | +22 archivos (`trajectories/README.md`, demonstrations `.traj`, `docs/usage/coding_challenge_output.log`). Quedan 2 enlaces simbolicos upstream (`docs/assets/readme_assets`, `docs/config/index.md`): el motor no copia enlaces |
| codex | instantanea mas antigua que upstream (516 archivos distintos, 40 nuevos upstream) | github.com/openai/codex @ 67f0994 | +3 (`.vscode/*`). Los 37 nuevos de `codex-rs/` NO se mezclan: dependen de otros archivos modificados (mezclar versiones rompe la compilacion) |
| opencode | idem (806 distintos, 171 nuevos upstream, sobre todo `packages/core`) | github.com/anomalyco/opencode @ bf544cd | +5 (`.opencode/*`, `.vscode/*.example.json`). Resto = deriva de version, no truncado |
| OpenHands | completo (2725/2725 vs 852132d) | OpenHands/OpenHands | nada |
| openhands-software-agent-sdk | completo (1931/1931 vs fd26808) | OpenHands/software-agent-sdk | nada |
| claude-code | puente propio (pasarela Anthropic->NVIDIA); la CLI es binario npm sin codigo fuente en GitHub | npm `@anthropic-ai/claude-code` | nada que descargar |
| OpenClaw | sin carpeta en `agentes/` (adaptador `adaptadores/openclaw.py` habla con el Gateway existente) | github.com/openclaw/openclaw | nada |

Pendiente (instalar; fuera del alcance de descargar/extraer): ningun adaptador detecta los archivos descargados, buscan CLI/paquete instalado.
- codex: `npm install -g @openai/codex` y `RIU_CODEX_BASE_URL` (endpoint /responses). - opencode: `curl -fsSL https://opencode.ai/v2/install | bash`. - SWE-agent: `pip install -e "agentes/agentes-listos/SWE-agent/SWE-agent-main"` (+ Docker). - OpenHands: `pip install -e agentes-listos/openhands-software-agent-sdk/code/openhands-sdk -e .../openhands-tools` (o `RIU_OPENHANDS_PYTHON`). - claude-code: CLI ya en PATH; faltan `RIU_CLAUDE_PASARELA_URL` y `RIU_CLAUDE_PASARELA_MODELO` (arrancar `claude-code/pasarela.py`). - openclaw: Gateway en 127.0.0.1:18789 + `OPENCLAW_GATEWAY_TOKEN`.
Para llevar codex/opencode al upstream actual hay que reemplazar la instantanea completa (no mezclar): `archivos {"accion":"transferir","origen":"github.com/openai/codex","destino":"agentes/agentes-listos/codex/codex-main-nuevo"}`.

## Adaptadores de agentes SWE (`adaptadores/`) — lo que ejecuta de verdad
Código en `chat-router/agentes/adaptadores/`. **No hay almacenamiento propio**: todo estado pasa por las funciones del Harness DeepSeek (`guardar`/`leer`, bucket HF por el Router). El navegador y el bridge nunca ejecutan un agente: validan y reenvían al Harness (`chat/backend/deepseek_harness/server.py`, herramientas `swe_iniciar|avanzar|estado|aprobar|reanudar`).

**Camino.** chat Yaiwes (`POST /chat/swe/*`, `mvp/app.py`) u OpenClaw (`POST /v1/swe/*`, `web-bridge/src/swe_rutas.js`) → Harness → `workflows.py` → `dispatcher.ejecutar_agente()` → `<adaptador>.run()`. Documentos: contrato, estados y aprobación en `chat-router/SWE CODE free/ARQUITECTURA.md` («Selectores de agente, modelo y workflow»); variables y estado instalado en `SWE CODE free/HANDOFF.md` («Operacion del Harness DeepSeek»).

| Pieza | Qué es |
|---|---|
| `modelos.py` | **catálogo único**: 9 modelos (`hf/lfm2.5-350m`, `hf/qwen2.5-coder-1.5b`, `hf/qwen3.5-0.8b`, `hf/qwen3-0.6b`, `groq/qwen/qwen3.8-27b`, `nvidia/{minimaxai/minimax-m3.1-flash, meta/muse-glimmer-30b, nvidia/nemotron-3-ultra-550b-a55b, z-ai/glm-5.3}`), 6 agentes (`openclaw`, `swe-agent`, `openhands`, `opencode`, `codex`, `claude-code`) y 3 workflows (`individual`, `swe_code`, `liquid_mirror`) |
| `contrato.py` | `TareaSWE`, el contrato único de YAIWES y OpenClaw (15 campos; `origen` = `yaiwes`\|`openclaw`; `desde_dict` es estricto: ningún campo ajeno; `aprobacion` siempre queda `false`) |
| `dispatcher.py` | único punto por el que se ejecuta un agente: `ejecutar_agente(agente, tarea_id, modelo, objetivo, contexto, permisos, checkpoint)`; exige un dict con `ok` y recibo; un adaptador que lanza excepción da `AgenteError` (`EJECUCION_AGENTE_FALLIDA`) y la operación pasa a RECONCILIAR, no a «no ejecutado» |
| `workflows.py` | máquina de estados `PENDIENTE → EJECUTANDO → (REQUIERE_APROBACION \| RECONCILIAR) → CONTINUAR → VERIFICANDO → DONE \| GAP` y las operaciones del Harness. Cada etapa guarda su resultado ANTES de continuar; una operación con efectos se marca INICIADA, se guarda y recién entonces se lanza; lo que queda INICIADA sin confirmar es RECONCILIAR (nunca se reintenta solo). La aprobación la da únicamente `swe_aprobar` con un operador de `RIU_SWE_OPERADORES` |
| `disponibilidad.py` | `capacidades()`: lo que está conectado de verdad (binarios, variables, `importlib.find_spec`, socket del Gateway, `GET /models` de Groq/NVIDIA con caché de 10 min; `RIU_SWE_SONDA_MODELOS=0` lo apaga). Solo lee; nunca lanza un agente ni devuelve un valor de clave. Alimenta `result.swe` del `status` del Harness → `GET /chat/swe/capacidades` (YAIWES) y `GET /v1/swe/capacidades` (OpenClaw) → el selector marca NO DISPONIBLE lo que no figura `disponible:true` |
| `_comun.py` | subproceso seguro (lista de argumentos, sin shell, timeout `RIU_AGENTE_TIMEOUT_S` 1800 s, tope de salida `RIU_AGENTE_MAX_SALIDA`, entorno mínimo), redacción de credenciales, `endpoint_modelo()` (los `hf/*` llegan por el bridge: `RIU_AGENTES_LLM_BASE_URL` o `RIU_SWE_BRIDGE_URL`, por defecto `http://127.0.0.1:7870`; Groq/NVIDIA con la clave del entorno) y `recibo()` (huella de una ejecución real: sin ejecución no hay recibo) |

**Workflows.**
- `individual`: un paso `responde` con `modelo_responde` (un LLM, sin agente).
- `swe_code` (cuatro pasos, exige `modo_agentico` ON, si no `MODO_AGENTICO_APAGADO`): `escribe` Codex + `hf/qwen2.5-coder-1.5b` → `revisa` OpenCode + `hf/qwen3.5-0.8b` → `ejecuta` el **agente elegido** (`agente_tool`) + `hf/lfm2.5-350m` → `verifica` OpenHands + `hf/lfm2.5-350m`. Los pasos con efectos (`escribe`, `revisa`, `ejecuta`, y `verifica` si el agente no garantiza solo-lectura) piden aprobación de un operador.
- `liquid_mirror`: `liquid1` (S2, lee/analiza) → `handoff` → `liquid2` (S3, ejecuta) → `ejecuta` (`agente_tool`) → `verifica`; ambos participantes `hf/lfm2.5-350m` en servidores distintos, en secuencia (`ejecucion_s2_s3:"secuencial"`).
- Trabajan solo dentro de `RIU_SWE_WORKSPACE_RAIZ/<proyecto>`.

**Los 6 adaptadores, qué necesitan y estado en el entorno donde se preparó el repo.** «No instalado» = el adaptador devuelve `AGENTE_NO_INSTALADO` y el selector lo muestra NO DISPONIBLE; ninguna prueba del repo afirma que un agente real corra (usan binarios y servidores falsos: `adaptadores/tests/`, 147 pruebas).

| Agente | Adaptador | Necesita | Estado | Instalar / configurar |
|---|---|---|---|---|
| `codex` | `codex.py` (`codex exec`) | CLI + `RIU_CODEX_BASE_URL` (endpoint compatible con **Responses**; el bridge ofrece `POST /v1/responses`: `RIU_CODEX_BASE_URL=<bridge>/v1`) | **no instalado** | `npm install -g @openai/codex` (o compilar `agentes-listos/codex/codex-main/codex-rs`); `RIU_CODEX_BIN` si no está en PATH |
| `opencode` | `opencode.py` (`opencode run`, config inline) | CLI | **no instalado** | `npm i -g opencode-ai` (o `curl -fsSL https://opencode.ai/v2/install \| bash`); `RIU_OPENCODE_BIN` |
| `swe-agent` | `swe_agent.py` (`sweagent run`, en contenedor) | CLI + Docker | **no instalado** (`docker` sí existe en la sesión de preparación) | `pip install -e agentes/agentes-listos/SWE-agent/SWE-agent-main`; `RIU_SWEAGENT_BIN`, `RIU_DOCKER_BIN`, `RIU_SWEAGENT_IMAGE` |
| `openhands` | `openhands.py` + `_openhands_runner.py` (SDK en subproceso) | Python que importe `openhands.sdk` y `openhands.tools` | **no instalado** | `pip install -e agentes/agentes-listos/openhands-software-agent-sdk/code/openhands-sdk` y `.../openhands-tools`; `RIU_OPENHANDS_PYTHON` |
| `claude-code` | `claude_code.py` (`claude -p`) | CLI + pasarela Anthropic→NVIDIA (`claude-code/pasarela.py`, `iniciar_claude_code.sh`): `RIU_CLAUDE_PASARELA_URL` y `RIU_CLAUDE_PASARELA_MODELO`; solo acepta ese modelo NVIDIA (si no, `MODELO_INCOMPATIBLE`) | CLI **instalada**, **sin configurar** (NO DISPONIBLE hasta definir las dos variables) | arrancar la pasarela; `RIU_CLAUDE_BIN`, `RIU_CLAUDE_AUTH_TOKEN` opcional, `RIU_CLAUDE_BASH_PERMITIDOS` amplía los comandos Bash permitidos |
| `openclaw` | `openclaw.py` (Gateway, `POST /v1/chat/completions`) | Gateway en `RIU_OPENCLAW_URL` (por defecto `http://127.0.0.1:18789`, con `gateway.http.endpoints.chatCompletions` habilitado) + `OPENCLAW_GATEWAY_TOKEN`; sin garantía de solo-lectura (`POLITICA_NO_GARANTIZADA` salvo `RIU_OPENCLAW_GATEWAY_SOLO_LECTURA`) | **no instalado** | arrancar el Gateway |

Los descargados en `agentes-listos/` son código fuente; ningún adaptador los detecta hasta que se instalan (ver «Completado de agentes listos»). Códigos de fallo de los adaptadores: `AGENTE_NO_INSTALADO`, `AGENTE_NO_CONFIGURADO`, `AGENTE_TIMEOUT`, `AGENTE_SALIO_CON_ERROR`, `AGENTE_REPORTO_ERROR`, `AGENTE_SIN_RESULTADO`, `MODELO_INCOMPATIBLE`, `POLITICA_NO_GARANTIZADA`, `DIRECTORIO_INVALIDO`, `PERMISOS_INVALIDOS`, `APROBACION_REQUERIDA`.

**Pruebas:** `PYTHONPATH=<raíz>/router-mvp:<raíz>/chat-router python3 -m pytest chat-router/agentes/adaptadores/tests`.

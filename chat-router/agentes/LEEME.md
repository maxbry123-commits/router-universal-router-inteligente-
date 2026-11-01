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

Pendiente (instalar; fuera del alcance de descargar/extraer; RESUELTO por `runtime/instalar-agentes.sh`, ver «Runtime de agentes»): ningun adaptador detecta los archivos descargados, buscan CLI/paquete instalado.
- codex: `npm install -g @openai/codex` y `RIU_CODEX_BASE_URL` (endpoint /responses). - opencode: `curl -fsSL https://opencode.ai/v2/install | bash`. - SWE-agent: `pip install -e "agentes/agentes-listos/SWE-agent/SWE-agent-main"` (+ Docker). - OpenHands: `pip install -e agentes-listos/openhands-software-agent-sdk/code/openhands-sdk -e .../openhands-tools` (o `RIU_OPENHANDS_PYTHON`). - claude-code: CLI ya en PATH; faltan `RIU_CLAUDE_PASARELA_URL` y `RIU_CLAUDE_PASARELA_MODELO` (arrancar `claude-code/pasarela.py`). - openclaw: Gateway en 127.0.0.1:18789 + `OPENCLAW_GATEWAY_TOKEN`.
Para llevar codex/opencode al upstream actual hay que reemplazar la instantanea completa (no mezclar): `archivos {"accion":"transferir","origen":"github.com/openai/codex","destino":"agentes/agentes-listos/codex/codex-main-nuevo"}`.

## Runtime de agentes (instalacion REAL dentro del repo, fuera de git)
`runtime/` versiona SOLO scripts y lockfiles; lo instalado (`bin/`, `venv/`, `node/`, `src/`, `estado-agentes.json`) esta en `runtime/.gitignore`. Nada de esto estaba instalado: antes los CLIs solo existian en `/tmp/a2-inst`.

| Archivo | Para que |
|---|---|
| `runtime/instalar-agentes.sh [codex-opencode claude openclaw sweagent openhands]` | idempotente (marca `.instalado/<comp>` = sha256 del lockfile; si coincide y el binario responde, no hace nada; `flock` contra dos instalaciones a la vez). Instala en `$RIU_AGENTES_RUNTIME` (por defecto `runtime/`). `RIU_INSTALAR_OMITIR="openclaw"` omite; `RIU_INSTALAR_TOLERANTE=1` no falla si un componente falla; `RIU_PYTHON` elige el python |
| `runtime/verificar-agentes.sh` | ejecuta de verdad `--version`/`--help` (y `import openhands.sdk, openhands.tools`) de cada agente y escribe `runtime/estado-agentes.json` (o `$RIU_ESTADO_JSON`): solo nombre, ruta, ok, primera linea de version y estado de Docker/imagen; nunca claves (redaccion defensiva) |
| `runtime/entorno.sh` | para `source`: `runtime/bin` al frente del PATH y `RIU_*_BIN`/`RIU_OPENHANDS_PYTHON` (sin pisar los ya definidos). Los adaptadores no lo necesitan: ya buscan ahi por defecto |
| `runtime/node-agentes/`, `node-claude/`, `node-openclaw/` | `package.json` (versiones EXACTAS) + `package-lock.json` (`npm ci`) |
| `runtime/requirements-{openhands,sweagent}.txt` | versiones fijadas; `*.freeze.txt` = `pip freeze` completo del venv instalado (informativo; Python 3.13) |

**Versiones fijadas y de donde salen.** codex-cli 0.166.0 y opencode 1.19.5 (npm `@openai/codex`, `opencode-ai`: las carpetas `agentes-listos/codex` y `opencode` son fuentes Rust/Bun de otra version, no se compilan aqui), CLI claude 2.1.316 (npm `@anthropic-ai/claude-code`, binario sin fuente publica), OpenClaw 2026.6.35 (npm `openclaw`, Node >= 22.19), openhands-sdk/tools 1.59.0 (PyPI; la fuente descargada es 1.55.1: `RIU_OPENHANDS_FUENTE=local` instala esa en editable, probado), SWE-agent 1.1.0 + swe-rex 1.4.0 (**fuente descargada**, `pip install -e` sobre una copia en `runtime/src/` para no ensuciar `agentes-listos/`; SWE-agent lee `config/` y `tools/` junto al paquete, por eso editable). Sin la carpeta fuente, SWE-agent se instala de `git+https://github.com/SWE-agent/SWE-agent.git@v1.1.0`.

**Como los encuentran los adaptadores** (`adaptadores/_comun.py`): `binario(nombre, RIU_X_BIN)` = 1) la variable `RIU_*_BIN` si esta definida (manda; una ruta mala NO cae al runtime), 2) `<runtime>/bin/<nombre>`, 3) `PATH`. El Python de OpenHands = `RIU_OPENHANDS_PYTHON` > `<runtime>/venv/openhands/bin/python` > el del Harness. El runtime es `RIU_AGENTES_RUNTIME` o `agentes/runtime`. `disponibilidad.py`: instalado -> DISPONIBLE; ausente -> NO INSTALADO (`tests/test_adaptadores_runtime.py`). `tests/conftest.py` apunta el runtime a un directorio vacio para que las pruebas no dependan de la maquina.

**Uso.** `chat-router/agentes/runtime/instalar-agentes.sh && chat-router/agentes/runtime/verificar-agentes.sh`.

**Imagen Docker de SWE-agent.** `agentes-listos/SWE-agent/Dockerfile.riu` (propio; el upstream no se toca): `python:3.12-slim` + `git` + `swe-rex==1.4.0`. `swe_agent.py` la usa por defecto (`RIU_SWEAGENT_IMAGE`, por defecto `riu-sweagent:latest`). Construir (sin contexto): `docker build -t riu-sweagent:latest - < chat-router/agentes/agentes-listos/SWE-agent/Dockerfile.riu`. `verificar-agentes.sh` informa `docker.estado` (`imagen_presente` / `imagen_ausente` / `daemon_apagado` / `sin_docker`). **[B] en el sandbox donde se preparo:** el `apt-get install git` del build devuelve `Unable to locate package git` porque el egress del sandbox bloquea `deb.debian.org` (403 del proxy); ejecutar el comando en una maquina con red a Debian.

**Space del Harness** (`chat/backend/deepseek_harness/space/`): el `Dockerfile` copia Node 22 de `node:22-slim` y ejecuta `instalar-agentes.sh` en el BUILD (secreto de build `GITHUB_TOKEN`; clona el repo a `/tmp/repo-build`, instala en `/opt/riu-agentes` = `RIU_AGENTES_RUNTIME` y lo borra); sin el secreto el paso se salta. `boot.sh` lo repite en segundo plano (idempotente: solo instala lo que falte, no retrasa el puerto 7860; log `/tmp/instalar-agentes.log`). El Space no tiene daemon Docker: `swe-agent` queda NO CONFIGURADO ahi. `chat-router/cableado.manifest.json` protege `chat/backend`: regenerar con `chat/auditoria/guardia_cableado.py --crear` tras el commit.

**Estado verificado en este sandbox** (`verificar-agentes.sh`, versiones reales ejecutadas):
```json
{"codex": "codex-cli 0.166.0", "opencode": "1.19.5", "swe-agent": "SWE-agent 1.1.0 / swe-rex 1.4.0",
 "openhands": "openhands-sdk 1.59.0 openhands-tools 1.59.0", "claude-code": "2.1.316 (Claude Code)", "openclaw": "OpenClaw 2026.6.35 (c283867)",
 "swe-agent.docker": {"estado": "daemon_apagado", "imagen": "riu-sweagent:latest"}}
```
(cada uno con `instalado: true, ok: true`). Nota del sandbox: el disco `/` tenia <1 GB libre, asi que `runtime/node` y `runtime/venv` son enlaces a `/dev/shm/riu-agentes/` (RAM, se pierde al reiniciar; reinstalar con el script); `bin/` y `src/` estan en disco.

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

**Los 6 adaptadores, qué necesitan y estado en el entorno donde se preparó el repo (la columna «Estado» es la de antes de `runtime/`; el instalado real está en «Runtime de agentes»).** «No instalado» = el adaptador devuelve `AGENTE_NO_INSTALADO` y el selector lo muestra NO DISPONIBLE; ninguna prueba del repo afirma que un agente real corra (usan binarios y servidores falsos: `adaptadores/tests/`, 147 pruebas).

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

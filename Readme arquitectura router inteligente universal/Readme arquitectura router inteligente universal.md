# Router Inteligente Universal — Arquitectura / ADN / X-Ray

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · rama `main`.

## Estado ejecutivo
- CORE P01-P03: `VERIFIED_CLOSED`.
- Certificación HF_M01..HF_M20: `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`.
- Regresión/E2E global del core: `PASS`.
- Capa autorizada `CONECTIVIDAD_RIU_MULTI_REPO`: `ACTIVE_BUILD_CONNECTIVITY_E2E`.
- Puentes: `19/19` repositorios en contrato `riu.connectivity.bridge/v2`.
- Runtime central de conectividad: materializado y probado `3/3 PASS`.
- Gate pendiente: credenciales runtime reales + E2E GitHub/Hugging Face/Claude-GitHub-MCP/memoria.
- Regla preservada: `CATALOG_OBSERVED != TESTED != READY`.

## Arquitectura base
`AGENTE -> API key -> FastAPI -> Auth/APIKeyGuard -> Enchufe Gate -> RedUniversal -> registry -> adapter -> destino/modelo -> verifier -> response`.

## Fabric central de conectividad
Raíz: `conectividad con Router inteligente universal/`.

Archivos centrales:
- `MAPA-MENTAL-CONECTIVIDAD-RIU.md`
- `REGISTRY-CONECTIVIDAD-RIU.json`
- `PUENTE-RIU-router-universal-router-inteligente-.yaml`

Runtime ejecutable:
- `router inteligente universal/integration/connectivity_runtime.py`
- `router inteligente universal/tests/test_connectivity_runtime.py`

Ruta transversal:
`REPO -> PUENTE-RIU-<repo>.yaml -> Router -> registry -> runtime resolver -> Enchufe Gate -> RedUniversal -> GitHub/HF/MCP/memoria -> verifier -> response`.

## Regla por repositorio
Cada uno de los 19 repositorios administrados tiene una única raíz `conectividad con Router inteligente universal/` y un único `PUENTE-RIU-<repo>.yaml` v2. No contiene valores secretos; solo referencias de runtime, capacidades, health gates y rutas hacia el Router.

## Secret store autorizado
GitHub Codespaces user secrets: `https://github.com/settings/codespaces`.

Resolución fail-closed en runtime:
- Hugging Face: `RIU_HF_TOKEN` -> `HF_TOKEN` -> `HUGGINGFACE_TOKEN`.
- GitHub / Claude GitHub MCP: `RIU_GITHUB_PAT` -> `GITHUB_TOKEN` -> `GH_TOKEN`.

Cada secret debe autorizar explícitamente el repo donde corre el Codespace. Los valores nunca se escriben en Git, README, Handoff, STATE, logs ni registry.

## Frontend — prioridad urgente
`maxbry123-commits/frontend/conectividad con Router inteligente universal/PUENTE-RIU-frontend.yaml` quedó en v2 y registra:
- GitHub vía Router.
- Hugging Face `COMAND-CENTER-1`.
- HF Jobs CPU/GPU.
- Models/Datasets/Spaces/Jobs.
- Space histórico `COMAND-CENTER-1/yaiwes-ui-factory` y runtime `https://comand-center-1-yaiwes-ui-factory.hf.space/`.
- Claude Managed Agents `github_repository` + GitHub MCP.
- Puente a memoria `MEMORIA/BIBLIOTECA/BITACORA-MAXBRY/Cerebro`.
- Estado: `FRONTEND_BRIDGE_V2_DECLARED`; credential E2E pendiente.

## Claude Managed Agents ↔ GitHub MCP
Fuente recuperada: `maxbry123-commits/TAREA-1/skills/claude-api/`.
Patrón: `github_repository -> https://api.githubcopilot.com/mcp/ -> vault/runtime auth`.

## Claude Managed Agents ↔ memoria
Fuente: `TAREA-1/skills/claude-api/shared/managed-agents-memory.md`.
Recurso: `memory_store`, persistencia cross-session. Targets propios: `MEMORIA`, `BIBLIOTECA`, `BITACORA-MAXBRY`, `Cerebro`.

## Hugging Face
Cuenta: `COMAND-CENTER-1`.
Cómputo: HF Jobs CPU/GPU.
Capacidades: models, datasets, Spaces, Jobs.
Verificación requerida con credential runtime: `whoami-v2 + scope + API probe + Job probe`.

## Evidencia runtime nueva
- `connectivity_runtime.py` commit `5664301d9051068b98ab326e5545110299e110a6`.
- tests commit `cfa87f7470f73e36d383f2e302f1fd38c582a674`.
- HF Job `6aa490c35527934177ecacb3`, owner `COMAND-CENTER-1`, `COMPLETED`.
- Resultado: `3 passed in 0.02s`.
- Registry 19/19 v2 commit `f4c16807248a676e9e8c2bf7dd04e2d8cbe46bb3`.
- Mapa mental v2 commit `c781e9dad4b4504c2d15b517022ce0b7b3a8f267`.

## Core preservado
P01 conjunto ejecutable HF cerrado; P02 hot-path `C01 REST -> C20 Auth -> C15 Gate -> C17 RedUniversal -> C16 adapter -> verifier`; P03 API Key Manager 100 slots hash-only rotate/revoke + E2E real.

## Certificación 20 modelos
PASS/ejecución verificada: M01, M02, M03, M05, M06, M07, M10, M11, M12, M20.
FLAG/GAP explícitos: M04, M08, M09, M13, M14, M15, M16, M17, M18, M19.
M18 final=`FLAG-HF-M18-RUNTIME-TIMEOUT-001`.

## Regresión core
GitHub Actions `RIU FAST-CLOSE`, run `34582284615`, job `103434377312`: success; `2 passed, 2 warnings in 6.75s` sobre commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`.

## Gate actual
`BRIDGES_V2_19_OF_19 + ROUTER_RUNTIME_TESTED + GITHUB_ACCESS_VERIFIED + HF_ACCESS_VERIFIED + MCP_BOUNDARY_VERIFIED + MEMORY_BOUNDARY_VERIFIED + GLOBAL_CONNECTIVITY_E2E_PASS + HANDOFF_STATE_SYNC`.

Estado: primeros dos gates `PASS`; validaciones externas con los 3 tokens de Codespaces=`PENDING_RUNTIME_VISIBILITY/E2E`, sin falso PASS.

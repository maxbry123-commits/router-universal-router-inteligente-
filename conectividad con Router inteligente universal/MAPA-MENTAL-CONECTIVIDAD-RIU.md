# MAPA MENTAL — Conectividad con Router Inteligente Universal

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · rama `main`.

## Objetivo
Toda conectividad de proyectos pasa por el Router Inteligente Universal: GitHub, Hugging Face, MCP, cómputo, memoria, almacenamiento, APIs, VPS y puentes entre repositorios. No se aceptan conexiones dispersas o implícitas como estado final.

## Ruta transversal canónica
`PROYECTO -> conectividad con Router inteligente universal/PUENTE-RIU-<repo>.yaml -> Router Inteligente Universal -> REGISTRY -> runtime resolver -> Enchufe Gate -> RedUniversal -> adapter -> destino -> verifier -> respuesta`

## Fabric materializada
- 19/19 repositorios administrados tienen una única raíz `conectividad con Router inteligente universal/`.
- 19/19 tienen un único archivo canónico `PUENTE-RIU-<repo>.yaml` en contrato `riu.connectivity.bridge/v2`.
- Registry central: `conectividad con Router inteligente universal/REGISTRY-CONECTIVIDAD-RIU.json`.
- Runtime central: `router inteligente universal/integration/connectivity_runtime.py`.
- Test runtime: `router inteligente universal/tests/test_connectivity_runtime.py`.
- Evidencia: HF Job `6aa490c35527934177ecacb3`, `COMPLETED`, `3 passed in 0.02s`.

## Secret store autorizado por el Director
GitHub Codespaces user secrets: `https://github.com/settings/codespaces`.

El Router conoce únicamente referencias lógicas y las resuelve en runtime:
- Hugging Face: `RIU_HF_TOKEN` -> `HF_TOKEN` -> `HUGGINGFACE_TOKEN`.
- GitHub/Claude GitHub MCP: `RIU_GITHUB_PAT` -> `GITHUB_TOKEN` -> `GH_TOKEN`.

Los valores nunca se guardan en Git, logs, README, Handoff, STATE ni registry. Cada secret debe tener autorizado explícitamente el repositorio donde se ejecuta el Codespace.

## Conexiones
### GitHub
`repo -> PUENTE -> Router -> runtime credential resolver -> GitHub API -> verifier`.
Gate pendiente con credencial: identidad + acceso al repo + permiso + operación mínima + read-back.

### Hugging Face
Cuenta observada: `COMAND-CENTER-1`.
Cómputo: HF Jobs CPU/GPU.
Capacidades: models, datasets, Spaces y Jobs.
Gate pendiente con credencial: `whoami-v2` + scope + API probe + Job probe.

### Frontend / fábrica visual
Puente urgente: `maxbry123-commits/frontend/conectividad con Router inteligente universal/PUENTE-RIU-frontend.yaml`.
Incluye referencia al Space histórico `COMAND-CENTER-1/yaiwes-ui-factory`, URL Hub y runtime, además de GitHub/HF/MCP/memoria. Estado: `FRONTEND_BRIDGE_V2_DECLARED`; E2E de credenciales pendiente.

### Claude / GitHub MCP
Patrón recuperado desde `maxbry123-commits/TAREA-1/skills/claude-api/`:
`Managed Agent -> github_repository -> https://api.githubcopilot.com/mcp/ -> vault/runtime auth`.
El Router registra el boundary y nunca persiste la credencial.

### Claude / memoria persistente
Fuente: `TAREA-1/skills/claude-api/shared/managed-agents-memory.md`.
Recurso: `memory_store`, persistencia cross-session.
Targets propios mapeados: `MEMORIA`, `BIBLIOTECA`, `BITACORA-MAXBRY`, `Cerebro`.

## Inventario administrado 19/19
`agentes`, `Agentes-motores-Wordflow-YAIWES`, `BIBLIOTECA`, `BITACORA-MAXBRY`, `Cerebro`, `comand-Center`, `frontend`, `Grupo-Trabajo-1`, `Grupo-Trabajo-2`, `informaci-n-auditor-`, `Maxbry-AGI`, `MEMORIA`, `nct-core`, `nct-hub`, `Orquestador-Maxbry-`, `osquestador-auditor`, `router-universal-router-inteligente-`, `TAREA-1`, `TAREA-2`.

## Estado actual
`BRIDGES_V2_19_OF_19 + RUNTIME_UNIT_TEST_PASS`.
No se promueve conectividad externa a PASS hasta que los secrets de runtime estén realmente disponibles y las pruebas E2E terminen.

## Cierre de capa
`BRIDGES_V2_19_OF_19 + ROUTER_RUNTIME_TESTED + GITHUB_ACCESS_VERIFIED + HF_ACCESS_VERIFIED + MCP_BOUNDARY_VERIFIED + MEMORY_BOUNDARY_VERIFIED + GLOBAL_CONNECTIVITY_E2E_PASS + HANDOFF_STATE_SYNC`.

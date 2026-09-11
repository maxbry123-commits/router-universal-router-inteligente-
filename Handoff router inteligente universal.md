# Handoff Router Inteligente Universal — ADN operativo

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · repo `maxbry123-commits/router-universal-router-inteligente-` · branch `main`.

## Estado preservado
- Core P01-P03=`VERIFIED_CLOSED`.
- `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`=PASS.
- Regresión core=`PASS`.
- No reabrir core sin regresión demostrada.

## Nodo vivo
`RIU-0063/0064_CONNECTIVITY_FABRIC_AND_CREDENTIAL_E2E` = `ACTIVE`.

### Materializado
- raíz canónica: `conectividad con Router inteligente universal/`.
- 19/19 repos con único `PUENTE-RIU-<repo>.yaml` v2.
- registry maestro v2: `REGISTRY-CONECTIVIDAD-RIU.json`.
- mapa mental: `MAPA-MENTAL-CONECTIVIDAD-RIU.md`.
- runtime: `router inteligente universal/integration/connectivity_runtime.py`.
- test: `router inteligente universal/tests/test_connectivity_runtime.py`.

### Secret store indicado por Director
`https://github.com/settings/codespaces`.
Resolución runtime:
- HF: `RIU_HF_TOKEN`, fallback `HF_TOKEN`, `HUGGINGFACE_TOKEN`.
- GitHub/MCP: `RIU_GITHUB_PAT`, fallback `GITHUB_TOKEN`, `GH_TOKEN`.
Nunca guardar ni imprimir valores.

### Frontend — listo para Astra
Archivo: `maxbry123-commits/frontend/conectividad con Router inteligente universal/PUENTE-RIU-frontend.yaml`.
Commit v2: `168b12de4c574a165d32601968ee7dd864614d8a`.
Incluye GitHub, Hugging Face `COMAND-CENTER-1`, HF Jobs CPU/GPU, models/datasets/spaces/jobs, Space `COMAND-CENTER-1/yaiwes-ui-factory`, Claude `github_repository` + GitHub MCP y targets de memoria.
Estado: declarativo completo; E2E de los secrets Codespaces pendiente.

### Claude ↔ GitHub MCP
Fuente: `TAREA-1/skills/claude-api/`.
Patrón: `github_repository -> https://api.githubcopilot.com/mcp/ -> vault/runtime`.

### Claude ↔ memoria
Fuente: `TAREA-1/skills/claude-api/shared/managed-agents-memory.md`.
Recurso: `memory_store`, persistencia cross-session.
Targets: `MEMORIA`, `BIBLIOTECA`, `BITACORA-MAXBRY`, `Cerebro`.

### Hugging Face
Cuenta: `COMAND-CENTER-1`; compute: HF Jobs CPU/GPU.
Test estructural del runtime ejecutado en HF Job `6aa490c35527934177ecacb3`, `COMPLETED`, resultado `3 passed in 0.02s`.

## Evidencia principal
- runtime commit `5664301d9051068b98ab326e5545110299e110a6`.
- tests commit `cfa87f7470f73e36d383f2e302f1fd38c582a674`.
- Router self bridge v2 `38a2eca676f9e90cdb425d55697d036b20643360`.
- Registry 19/19 v2 `f4c16807248a676e9e8c2bf7dd04e2d8cbe46bb3`.
- mapa mental actualizado `c781e9dad4b4504c2d15b517022ce0b7b3a8f267`.
- arquitectura sincronizada `a1b842a9687be99a7b8130abf8c54127d643627a`.

## Cola 1×1 pendiente
1. Confirmar visibilidad runtime de los 3 secrets de Codespaces en el contexto donde corre el Router.
2. GitHub: identity + repo access + permission + operation/read-back.
3. HF: whoami-v2 + scopes + API/Job probe.
4. Claude/GitHub MCP: mount/connect/tool probe.
5. memoria: operación/read-back.
6. ejecutar suite de componentes y regresión global del Router.
7. cerrar solo con evidencia.

## Gate
`BRIDGES_V2_19_OF_19=PASS` + `ROUTER_RUNTIME_TESTED=PASS`; `GITHUB_ACCESS_VERIFIED/HF_ACCESS_VERIFIED/MCP_BOUNDARY_VERIFIED/MEMORY_BOUNDARY_VERIFIED/GLOBAL_CONNECTIVITY_E2E_PASS=PENDING`.

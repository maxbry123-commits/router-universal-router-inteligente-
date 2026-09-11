# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Core preservado
- P01 ✅ conjunto ejecutable HF cerrado.
- P02 ✅ hot-path C01/C20/C15/C17/C16 cerrado.
- P03 ✅ API Key Manager 100 slots + E2E cerrado.
- MODEL CERTIFICATION ✅ 20/20 slots accounted.
- FINAL REGRESSION/E2E ✅ run `34582284615`, job `103434377312`, `2 passed, 2 warnings in 6.75s`.

## RIU-0063/0064 — Connectivity Fabric
### Cerrado/verificado
- raíz central Router y mapa mental materializados.
- `19/19` repositorios con exactamente un `PUENTE-RIU-<repo>.yaml` en esquema `riu.connectivity.bridge/v2`, read-back verificado.
- frontend v2 confirmado; incluye GitHub, HF `COMAND-CENTER-1`, HF Jobs CPU/GPU, Claude `github_repository` + GitHub MCP, memoria y refs Codespaces.
- registry central v2 sincronizado.
- runtime central `router inteligente universal/integration/connectivity_runtime.py` materializado con resolución por nombres lógicos y fail-closed.
- secret store canónico: `https://github.com/settings/codespaces`; sólo refs `RIU_HF_TOKEN/HF_TOKEN/HUGGINGFACE_TOKEN` y `RIU_GITHUB_PAT/GITHUB_TOKEN/GH_TOKEN`.
- runtime unit/component test en HF Job `6aa490c35527934177ecacb3`: `COMPLETED`, `3 passed in 0.02s`.
- TAREA-2 promovido a v2 en commit `0848a33e21a8e48d62597d05ca363caac40f64f8`.

### Pendiente — cola 1×1
1. `GITHUB_RUNTIME_CREDENTIAL_VALIDATION`: identity + repo access + permission + operation/read-back.
2. `HF_RUNTIME_CREDENTIAL_VALIDATION`: whoami-v2 + scope + API probe + Job probe.
3. `CLAUDE_GITHUB_MCP_BOUNDARY_VALIDATION`: mount/connect/tool probe sin exponer secreto.
4. `CLAUDE_MEMORY_STORE_BOUNDARY_VALIDATION`: operación/read-back.
5. `GLOBAL_CONNECTIVITY_E2E`: repo/agent -> bridge -> Router -> Enchufe -> provider -> verifier -> response.
6. `DOC_SYNC_FINAL` y cierre sólo con evidencia.

## GAP/FLAG
Las credenciales Codespaces no son legibles por la API GitHub conectada a este agente; por diseño tampoco deben persistirse. Los gates externos permanecen `PENDING_RUNTIME_CREDENTIAL`, no PASS.

## Estado
`BRIDGES_V2_19_OF_19=PASS` + `ROUTER_RUNTIME_TESTED=PASS`.
`CONNECTIVITY_LAYER_VERIFIED_CLOSED=PENDING_RUNTIME_CREDENTIAL_E2E`.

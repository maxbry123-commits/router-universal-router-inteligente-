# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Cerrado y preservado
- P01 ✅ conjunto ejecutable HF.
- P02 ✅ hot-path C01/C20/C15/C17/C16.
- P03 ✅ API Key Manager 100 slots + E2E.
- MODEL CERTIFICATION ✅ 20/20 accounted.
- FINAL REGRESSION CORE ✅ run `34582284615`, job `103434377312`.

## RIU-0063/0064 — Connectivity Fabric ✅ estructural
- raíz/mapa/registry centrales materializados.
- `19/19` repositorios con `PUENTE-RIU-<repo>.yaml` v2.
- frontend urgente v2 commit `168b12de4c574a165d32601968ee7dd864614d8a` con GitHub + HF `COMAND-CENTER-1` + HF Jobs CPU/GPU + Space `yaiwes-ui-factory` + Claude GitHub MCP + memoria.
- runtime central `integration/connectivity_runtime.py` fail-closed.
- Codespaces secret store: `https://github.com/settings/codespaces`.
- runtime test HF Job `6aa490c35527934177ecacb3`: `3 passed in 0.02s`.

## RIU-0065 — suite de componentes ✅
Intentos auditables:
1. `6aa4924021047bf1b0379661` → ERROR test-env: faltaba `huggingface_hub`.
2. `6aa492635527934177ecad45` → ERROR test-env: faltaba `PYTHONPATH` para módulo `red`.
3. StrategyDelta `6aa4928c21047bf1b037967e` → `COMPLETED`, **71 passed, 2 warnings in 6.00s**.
4. collect audit `6aa492b55527934177ecad83` → `COMPLETED`, 18 archivos / 71 casos.

Cobertura actual: DB, GitLab, HF connector, Interno/Webhook, MCP App, Memoria, VPS, baseline conectores, connectivity runtime, connector registry, Enchufe Gate v1.5/v2, Enchufe schema v2, FAST-CLOSE E2E, HF hot-path, RedUniversal R003, resilience C10, validator v2.

## Cola 1×1 activa — RIU-0066
1. `GITHUB_RUNTIME_CREDENTIAL_VALIDATION`: identity + repo access + permission + operation/read-back.
2. `HF_RUNTIME_CREDENTIAL_VALIDATION`: whoami-v2 + scope + API/Job probe.
3. `CLAUDE_GITHUB_MCP_BOUNDARY_VALIDATION`: mount/connect/tool probe.
4. `CLAUDE_MEMORY_STORE_BOUNDARY_VALIDATION`: operación/read-back.
5. `GLOBAL_CONNECTIVITY_E2E`: repo/agent -> bridge -> Router -> Enchufe -> provider -> verifier -> response.
6. `DOC_SYNC_FINAL` + cierre.

## GAP externo actual
Los valores de GitHub Codespaces secrets no son re-leíbles mediante la API GitHub conectada a este agente. El Router ya está cableado para resolverlos dentro del runtime/Codespace autorizado. Hasta que ese runtime exponga los nombres de entorno al proceso del Router, los gates externos permanecen `PENDING_RUNTIME_CREDENTIAL_VISIBILITY`, no PASS.

## Estado
`BRIDGES_V2_19_OF_19=PASS` + `ROUTER_RUNTIME_TESTED=PASS` + `CURRENT_ROUTER_TEST_SUITE=71/71 PASS`.
`CONNECTIVITY_LAYER_VERIFIED_CLOSED=PENDING_EXTERNAL_CREDENTIAL_E2E`.

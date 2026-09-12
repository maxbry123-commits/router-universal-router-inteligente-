# Handoff Router Inteligente Universal — ADN operativo

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · repo `maxbry123-commits/router-universal-router-inteligente-` · branch `main`.

## Preservado
Core P01-P03=`VERIFIED_CLOSED`; modelos 20/20 accounted; regresión core PASS.

## Nodo vivo
`RIU-0066_RUNTIME_SECRET_E2E`.

## Fabric disponible
- 19/19 repos con raíz `conectividad con Router inteligente universal/` y `PUENTE-RIU-<repo>.yaml` v2.
- Registry actual commit `e1eb61931fbc5892398fd93aa7a5385fcb212a1f`.
- Frontend/Astra bridge actual commit `aa1ab876c04d0ff1d33ec1fdf0397e47e2e86f6f`, blob `b7541b29d560cd37fcbfb7e075f15a78239133be`.

## Frontend/Astra — prioridad urgente
`frontend/conectividad con Router inteligente universal/PUENTE-RIU-frontend.yaml` registra GitHub, HF `COMAND-CENTER-1`, HF Jobs CPU/GPU, models/datasets/spaces/jobs, Space `COMAND-CENTER-1/yaiwes-ui-factory`, Claude `github_repository` + GitHub MCP y memoria. También incluye el handoff ejecutable para Codespaces.

Comando canónico dentro de un Codespace autorizado:
`PYTHONPATH="router inteligente universal/integration" python "router inteligente universal/integration/verify_runtime_connectivity.py" --repo maxbry123-commits/frontend`

Resultado esperado: gates `github`, `huggingface`, `github_mcp` en `PASS`; si falta cualquier secret, salida `FAIL_CLOSED`.

## Secrets
Store indicado por Director: `https://github.com/settings/codespaces`.
Refs HF=`RIU_HF_TOKEN/HF_TOKEN/HUGGINGFACE_TOKEN`; GitHub/MCP=`RIU_GITHUB_PAT/GITHUB_TOKEN/GH_TOKEN`.
Los valores nunca se copian a Git, logs ni chat.

## Runtime
- `router inteligente universal/integration/connectivity_runtime.py` blob `fdfe385afb2b5b88cc2aa2ee63f6bf7d9c157833`.
- `router inteligente universal/integration/verify_runtime_connectivity.py` blob `8d0aca03f84730f2ac9204b4580c2eabaedd4ffb`.
- probes: GitHub identity/permisos/scopes; HF whoami/role; GitHub MCP initialize read-only.

## Tests
- Suite amplia previa HF Job `6aa493a121047bf1b03796e9`=`COMPLETED`: **75 passed, 2 warnings in 5.78s**.
- Fail-closed Job `6aa493e221047bf1b037970b`=`COMPLETED`: PASS esperado sin secrets.
- Validación fresca de conectividad desde `main`: HF Job `6aa49ae621047bf1b0379a54`=`COMPLETED`: **7 passed in 0.19s** sobre `test_connectivity_runtime.py`.
- Regresión amplia fresca Job `6aa499e45527934177ecb1cb` iniciada; supervisar hasta estado terminal antes de usarla como nueva evidencia.

## GAP real restante
Los Codespaces user secrets no son re-leíbles mediante GitHub API/connector y este proceso no se ejecuta dentro de tu Codespace. La prueba real de los 3 tokens debe correr dentro de un Codespace autorizado para `frontend`/Router. Hasta entonces `GITHUB/HF/MCP/MEMORY/GLOBAL_E2E` permanecen PENDING, nunca falso PASS.

## Cola 1×1
1. cerrar/supervisar Job `6aa499e45527934177ecb1cb`.
2. ejecutar el verificador dentro del Codespace autorizado de frontend.
3. GitHub identity + full repo permissions + read-back.
4. HF identity=`COMAND-CENTER-1` + role/scope + API/Job probe.
5. GitHub MCP initialize + tool boundary.
6. memory operation/read-back.
7. global connectivity E2E.
8. sync final/cierre.

## Gate
PASS local=`BRIDGES_V2_19_OF_19 + ROUTER_RUNTIME + SUITE_75_OF_75 + FRESH_CONNECTIVITY_7_OF_7 + FAIL_CLOSED_NO_SECRET`.
PENDING externo=`GITHUB/HF/MCP/MEMORY/GLOBAL_E2E` por visibilidad runtime de Codespaces secrets.

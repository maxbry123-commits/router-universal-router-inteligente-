# Handoff Router Inteligente Universal — ADN operativo

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · repo `maxbry123-commits/router-universal-router-inteligente-` · branch `main`.

## Preservado
Core P01-P03=`VERIFIED_CLOSED`; modelos 20/20 accounted; regresión core PASS.

## Nodo vivo
`RIU-0066_RUNTIME_SECRET_E2E`.

## Fabric disponible
- 19/19 repos con raíz `conectividad con Router inteligente universal/` y `PUENTE-RIU-<repo>.yaml` v2.
- Registry commit `f4c16807248a676e9e8c2bf7dd04e2d8cbe46bb3`.
- Mapa commit `c781e9dad4b4504c2d15b517022ce0b7b3a8f267`.
- Frontend/Astra bridge commit `168b12de4c574a165d32601968ee7dd864614d8a`.

## Frontend/Astra
El archivo `frontend/conectividad con Router inteligente universal/PUENTE-RIU-frontend.yaml` registra GitHub, HF `COMAND-CENTER-1`, HF Jobs CPU/GPU, models/datasets/spaces/jobs, Space `COMAND-CENTER-1/yaiwes-ui-factory`, Claude `github_repository` + GitHub MCP y memoria.

## Secrets
Store indicado: `https://github.com/settings/codespaces`.
Refs: HF=`RIU_HF_TOKEN/HF_TOKEN/HUGGINGFACE_TOKEN`; GitHub/MCP=`RIU_GITHUB_PAT/GITHUB_TOKEN/GH_TOKEN`.
No copiar valores a Git ni chat.

## Runtime
- `integration/connectivity_runtime.py` latest commit `912fc38708c13f57046d8aa48c503773bd722d93`.
- `integration/verify_runtime_connectivity.py` commit `5b727b139f3736a4f277fb68b03bbaff95d31dfb`.
- probes: GitHub identity/permissions/scopes; HF whoami/role; GitHub MCP initialize read-only.

## Tests
- Job `6aa493a121047bf1b03796e9`=`COMPLETED`: **75 passed, 2 warnings in 5.78s**.
- Job `6aa493e221047bf1b037970b`=`COMPLETED`: verificador sin secrets respondió fail-closed esperado y el gate de seguridad pasó.
- 18 archivos de test cubren conectores, registry, Enchufe, RedUniversal, resilience, validator, HF hot-path, FastAPI E2E y connectivity runtime.

## GAP real restante
Los Codespaces secrets no son re-leíbles mediante la API/connector actual. Para validar los 3 tokens reales, `verify_runtime_connectivity.py` debe ejecutarse dentro de un Codespace/runtime autorizado para el repo. Hasta entonces no declarar acceso externo PASS.

## Cola 1×1
1. visibilidad de refs en Codespace Router/frontend.
2. GitHub identity + full repo permissions + read-back.
3. HF identity=`COMAND-CENTER-1` + token role/scope + API/Job probe.
4. GitHub MCP initialize + tool boundary.
5. memory operation/read-back.
6. global connectivity E2E.
7. sync final/cierre.

## Gate
PASS=`BRIDGES_V2_19_OF_19 + ROUTER_RUNTIME + SUITE_75_OF_75 + FAIL_CLOSED_NO_SECRET`.
PENDING=`GITHUB/HF/MCP/MEMORY/GLOBAL_E2E` por visibilidad runtime de Codespaces secrets.

# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Estado preservado
Core P01-P03=`VERIFIED_CLOSED`; `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`; regresión core=`PASS`.

## RIU-0063/0064 — Connectivity Fabric
- raíz canónica `conectividad con Router inteligente universal/`.
- 19/19 repos con un `PUENTE-RIU-<repo>.yaml` v2.
- registry central commit `f4c16807248a676e9e8c2bf7dd04e2d8cbe46bb3`.
- mapa mental commit `c781e9dad4b4504c2d15b517022ce0b7b3a8f267`.
- frontend urgente v2 commit `168b12de4c574a165d32601968ee7dd864614d8a`.
- runtime `router inteligente universal/integration/connectivity_runtime.py`, commit `5664301d9051068b98ab326e5545110299e110a6`.
- unit tests runtime commit `cfa87f7470f73e36d383f2e302f1fd38c582a674`; HF Job `6aa490c35527934177ecacb3` COMPLETED, `3 passed in 0.02s`.

## RIU-0065 — test global de componentes actuales
- Attempt `6aa4924021047bf1b0379661`: ERROR por dependencia de entorno `huggingface_hub` ausente.
- StrategyDelta `6aa492635527934177ecad45`: ERROR de entorno por `PYTHONPATH`/módulo `red`.
- StrategyDelta final `6aa4928c21047bf1b037967e`: `COMPLETED`, **71 passed, 2 warnings in 6.00s**.
- auditoría de colección `6aa492b55527934177ecad83`: `COMPLETED`, 18 archivos / 71 casos.
- warnings: deprecaciones TestClient FastAPI/Starlette; no fallos funcionales.

## Secret boundary
Store indicado por Director: `https://github.com/settings/codespaces`.
HF refs: `RIU_HF_TOKEN`, `HF_TOKEN`, `HUGGINGFACE_TOKEN`.
GitHub/MCP refs: `RIU_GITHUB_PAT`, `GITHUB_TOKEN`, `GH_TOKEN`.
Valores crudos prohibidos en Git/logs/documentos.

## Nodo de recuperación exacto
`RIU-0066_RUNTIME_SECRET_E2E`.

Secuencia cola 1×1:
1. ejecutar Router dentro de runtime/Codespace autorizado y confirmar sólo disponibilidad de refs, sin imprimir valores.
2. GitHub identity + repo access + permission + operation/read-back.
3. HF whoami-v2 + scope + API/Job probe.
4. Claude GitHub MCP mount/connect/tool probe.
5. memory operation/read-back.
6. global connectivity E2E.
7. sync documental y cierre.

## Estado de gates
PASS: `BRIDGES_V2_19_OF_19`, `ROUTER_RUNTIME_TESTED`, `CURRENT_ROUTER_TEST_SUITE_71_OF_71`, `SECRET_RESOLUTION_FAIL_CLOSED`.
PENDING: `GITHUB_ACCESS_VERIFIED`, `HF_ACCESS_VERIFIED`, `MCP_BOUNDARY_VERIFIED`, `MEMORY_BOUNDARY_VERIFIED`, `CONNECTIVITY_GLOBAL_E2E_PASS`.

## Evidencia documental actual
Architecture `a1b842a9687be99a7b8130abf8c54127d643627a`; Handoff `038765d3fdb06c3fe2bc42e987e0d40f9d7c8496`; Crazy Wall `551b4e36fccd82d81f75fa5f21408dbe9da41281`; STATE `d94d4ea72fe9a4cdbd8bad6cea5db54b0dd98fe6`; CHECKPOINT `45878a7782f71f3dacca078f5c3b03068ecf8a72`; PLAN `6887f62dece655c23b7b22bb767252798d6d2dbe`.

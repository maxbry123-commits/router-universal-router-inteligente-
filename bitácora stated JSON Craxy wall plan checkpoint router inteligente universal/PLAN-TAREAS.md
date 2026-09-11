# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Cerrado/preservado
- Core P01/P02/P03 ✅
- Model certification 20/20 accounted ✅
- Regresión core ✅
- Connectivity Fabric 19/19 bridge v2 ✅

## RIU-0066 — estado probado
- runtime latest commit `912fc38708c13f57046d8aa48c503773bd722d93`.
- runner Codespaces commit `5b727b139f3736a4f277fb68b03bbaff95d31dfb`.
- tests connectivity runtime commit `cb35fa345081e18e4aa4e081fd581c036092cbba`.
- HF Job `6aa493a121047bf1b03796e9`: `COMPLETED`, **75 passed, 2 warnings in 5.78s**.
- HF Job `6aa493e221047bf1b037970b`: `COMPLETED`, fail-closed sin secrets validado.

## Frontend urgente
`frontend/conectividad con Router inteligente universal/PUENTE-RIU-frontend.yaml`, commit `168b12de4c574a165d32601968ee7dd864614d8a`.
Astra dispone en un solo archivo del mapa de GitHub, HF `COMAND-CENTER-1`, HF Jobs CPU/GPU, Space `yaiwes-ui-factory`, Claude GitHub MCP y memoria.

## Cola 1×1 pendiente
1. Ejecutar `verify_runtime_connectivity.py --repo maxbry123-commits/frontend` dentro del Codespace autorizado donde los 3 secrets estén inyectados.
2. `GITHUB_ACCESS_VERIFIED`: identity + full repo permissions + read-back.
3. `HF_ACCESS_VERIFIED`: identity `COMAND-CENTER-1` + token role/scope + API/Job probe.
4. `MCP_BOUNDARY_VERIFIED`: JSON-RPC initialize + tool boundary GitHub MCP.
5. `MEMORY_BOUNDARY_VERIFIED`: operación/read-back.
6. `CONNECTIVITY_GLOBAL_E2E_PASS`.
7. documentación final + cierre.

## GAP real
GitHub Codespaces no permite recuperar el valor de secrets mediante la API/conector. La ejecución actual no es un Codespace que reciba esos secrets. Esto bloquea únicamente el E2E externo; no bloquea fabric/runtime/tests ya cerrados.

## Gate
PASS=`BRIDGES_V2_19_OF_19 + RUNTIME + 75_OF_75_TESTS + FAIL_CLOSED`.
PENDING=`CODESPACES_SECRET_RUNTIME_VISIBILITY + GITHUB/HF/MCP/MEMORY/GLOBAL_E2E`.

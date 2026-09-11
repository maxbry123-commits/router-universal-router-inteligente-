# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Preservado
Core P01-P03=`VERIFIED_CLOSED`; modelos 20/20 accounted; regresión core PASS.

## Fabric
19/19 repos con puente v2; registry `f4c16807248a676e9e8c2bf7dd04e2d8cbe46bb3`; frontend `168b12de4c574a165d32601968ee7dd864614d8a`.

## Runtime actual
- `connectivity_runtime.py` latest `912fc38708c13f57046d8aa48c503773bd722d93`.
- `verify_runtime_connectivity.py` `5b727b139f3736a4f277fb68b03bbaff95d31dfb`.
- GitHub permissions/scopes probe, HF identity/role probe, GitHub MCP initialize probe; todos sin exposición de valores.

## Tests
- suite latest HF Job `6aa493a121047bf1b03796e9`: `COMPLETED`, **75 passed, 2 warnings in 5.78s**.
- fail-closed Job `6aa493e221047bf1b037970b`: `COMPLETED`, `FAIL_CLOSED_EXPECTED_PASS`.

## Secret boundary
Store: `https://github.com/settings/codespaces`.
HF refs=`RIU_HF_TOKEN/HF_TOKEN/HUGGINGFACE_TOKEN`.
GitHub/MCP refs=`RIU_GITHUB_PAT/GITHUB_TOKEN/GH_TOKEN`.
Los valores no son re-leíbles por API y nunca deben persistirse.

## Punto exacto de recuperación
Nodo=`RIU-0066_RUNTIME_SECRET_E2E`.
Ejecutar dentro de un Codespace autorizado:
`python "router inteligente universal/integration/verify_runtime_connectivity.py" --repo maxbry123-commits/frontend`

Resultado esperado para avanzar: runtime refs `AVAILABLE`; GitHub PASS; HF identity `COMAND-CENTER-1` PASS; GitHub MCP initialize PASS. Después probar memory read-back y global E2E.

Si las refs no aparecen: comprobar en GitHub Codespaces settings que cada secret autoriza `maxbry123-commits/frontend` y/o `maxbry123-commits/router-universal-router-inteligente-`; reiniciar/crear el Codespace para inyección. Mantener `PENDING_RUNTIME_CREDENTIAL_VISIBILITY`, nunca PASS falso.

## Gates
PASS=`19/19 v2 + runtime + suite 75/75 + fail-closed`.
PENDING=`GITHUB/HF/MCP/MEMORY/GLOBAL E2E`.

## Evidencia documental
Architecture `70eec6c53b4e39ba75c86c4e0591f1edc2db47c1`; Handoff `96966d7ca10f2eb2c1a3ced746c6182f01159a7e`; Crazy Wall `127e8f7e3d01a763b2e55d8e9de53d2bb370b247`; STATE `6668eed1ce64eb27e11d9f3e10c2c07768832631`; CHECKPOINT `364814100f8136dd5b17b4a6fbf5e3b22866b2b8`; PLAN `1bebc4684574bda27a70aa1a2ad570e49530071e`.

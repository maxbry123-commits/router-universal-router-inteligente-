# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3` · **Modo:** `FAIL_CLOSED_LOOP`.

## RIU-0001..0062 — BASE CERRADA
P01/P02/P03=`VERIFIED_CLOSED`; `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`; regresión core `RIU FAST-CLOSE` PASS.

## RIU-0063/0064 — CONNECTIVITY FABRIC
- raíz canónica `conectividad con Router inteligente universal/`.
- 19/19 repos con `PUENTE-RIU-<repo>.yaml` v2.
- frontend v2 `168b12de4c574a165d32601968ee7dd864614d8a` con GitHub + HF `COMAND-CENTER-1` + Jobs CPU/GPU + Space `yaiwes-ui-factory` + Claude GitHub MCP + memoria.
- registry `f4c16807248a676e9e8c2bf7dd04e2d8cbe46bb3`; mapa `c781e9dad4b4504c2d15b517022ce0b7b3a8f267`.
- runtime base commit `5664301d9051068b98ab326e5545110299e110a6`; Job `6aa490c35527934177ecacb3` COMPLETED, `3 passed`.

## RIU-0065 — SUITE COMPLETA
Attempt `6aa4924021047bf1b0379661`: ERROR test-env (`huggingface_hub` ausente).
StrategyDelta `6aa492635527934177ecad45`: ERROR test-env (`PYTHONPATH/red`).
StrategyDelta final `6aa4928c21047bf1b037967e`: COMPLETED, `71 passed, 2 warnings in 6.00s`.
Collection audit `6aa492b55527934177ecad83`: 18 archivos / 71 casos.

## RIU-0066 — PROBES DE ACCESO + RUNNER CODESPACES
Runtime actualizado commit `912fc38708c13f57046d8aa48c503773bd722d93`:
- GitHub: identity + repo + permisos admin/push/pull/maintain + scopes visibles.
- HF: whoami-v2 + identity + role de token visible.
- GitHub MCP: handshake JSON-RPC `initialize` read-only a `https://api.githubcopilot.com/mcp/`.
- sin exposición del valor de ninguna credencial.

Tests de connectivity runtime ampliados de 3 a 7, commit `cb35fa345081e18e4aa4e081fd581c036092cbba`.
Runner Codespaces `integration/verify_runtime_connectivity.py`, commit `5b727b139f3736a4f277fb68b03bbaff95d31dfb`.

### Regresión tras probes
HF Job `6aa493a121047bf1b03796e9`=`COMPLETED`: **75 passed, 2 warnings in 5.78s**.
HF Job `6aa493e221047bf1b037970b`=`COMPLETED`: con refs de secrets deliberadamente ausentes, runner devolvió exit 2/`FAIL_CLOSED` y el harness confirmó `FAIL_CLOSED_EXPECTED_PASS`.

### GAP real externo
Store: `https://github.com/settings/codespaces`.
Los valores de Codespaces secrets no son re-leíbles por GitHub API ni por el conector actual. Solo se inyectan en un Codespace autorizado. Por eso el Router ya está cableado y probado fail-closed, pero no se falsifica el E2E de los 3 tokens.

## Gates actuales
PASS:
- `BRIDGES_V2_19_OF_19`
- `ROUTER_RUNTIME_TESTED`
- `CURRENT_ROUTER_TEST_SUITE_75_OF_75`
- `FAIL_CLOSED_WITHOUT_SECRETS`

PENDING runtime Codespaces:
- `GITHUB_ACCESS_VERIFIED`
- `HF_ACCESS_VERIFIED`
- `MCP_BOUNDARY_VERIFIED`
- `MEMORY_BOUNDARY_VERIFIED`
- `CONNECTIVITY_GLOBAL_E2E_PASS`

## Nodo vivo
`RIU-0066_RUNTIME_SECRET_E2E`.
No secretos en repo/logs; no force; evidencia antes de PASS.

# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Estado consolidado
- Core P01/P02/P03 ✅
- Model certification 20/20 accounted ✅
- Regresión core ✅
- Connectivity Fabric 19/19 bridge v2 ✅
- Router runtime + probes ✅
- Suite amplia 75/75 ✅
- Connectivity runtime fresca 7/7 ✅
- Fail-closed sin secrets ✅
- HF Space OIDC write ✅

## Nodo activo
`RIU-0068_BOOTSTRAP_GLOBAL_AUTH`.

## Tareas activadas — sin sobreingeniería
1. **BOOTSTRAP_GITHUB** — cargar `RIU_GITHUB_PAT` en Router Actions Secrets con acceso a los 8 repos y permiso suficiente para escribir Actions secrets.
2. **BOOTSTRAP_HF** — cargar `RIU_HF_TOKEN` role=`write` para `COMAND-CENTER-1`.
3. **PROPAGATE_8_REPOS** — ejecutar manualmente `.github/workflows/riu-propagate-auth-secrets.yml`; debe abortar si falta `RIU_GITHUB_PAT`.
4. **PROBE_AUTH** — ejecutar `.github/workflows/riu-auth-presence-probe.yml`; exigir HF identity/role PASS y GitHub read-back/permisos sobre los 8 repos.
5. **CODEX_AUTH_1_2** — completar device-auth de las dos cuentas y persistir solo `auth.json` cifrado en Actions Secrets.
6. **CLAUDE_AUTH** — completar `claude setup-token` y persistir únicamente el token cifrado.
7. **GLOBAL_E2E** — GitHub + HF + MCP + memoria, con evidencia fresca y cierre final.

## Evidencia que ya existe
- Probe de presencia workflow materializado y seguro: `.github/workflows/riu-auth-presence-probe.yml`.
- Propagación fail-closed materializada: `.github/workflows/riu-propagate-auth-secrets.yml`.
- Probe run previo `34677207175`: credenciales globales estaban ausentes al momento de la prueba.
- HF OIDC frontend: runs `34675165228` attempt 2 y `34677293995` PASS; Hub read-back HTTP 200.

## GAP exacto
No falta arquitectura del router. Falta **inyectar y validar en runtime las credenciales globales externas** y completar los logins de suscripción de Codex/Claude. Los valores secretos no se escriben en Git, logs ni chat.

## Gate de cierre
`VERIFIED_CLOSED` solo cuando `GITHUB_PAT_RUNTIME_VERIFIED + HF_GLOBAL_WRITE_RUNTIME_VERIFIED + CODEX_1_2 + CLAUDE + MCP + MEMORY + CONNECTIVITY_GLOBAL_E2E_PASS` tengan evidencia fresca.


## RIU-0070 — X-RAY RAÍZ + EXTERNOS + PLAN DE CIERRE
1. **ROOT_XRAY_29** — contabilizar las 29 entradas raíz y asignar owner: runtime, connectivity, state, docs, evidence, donor/legacy.
2. **OMNIROUTE_ADAPTER** — definir/probar `connector_registry -> adapter_omniroute`; health, fallback y rate-limit simulation obligatorios.
3. **ORCA_ADE** — validar Orca gráfico como control plane externo para Claude Code/Codex con worktrees; no puede mergear sin verifier RIU.
4. **OMARCHY_HOST** — documentar/validar workstation opcional; nunca dependencia del runtime ni gate de producción.
5. **ANYDOC_ADAPTER** — wrapper de ingestión a Markdown y corpus multiformato; hashes y error path obligatorios.
6. **DEDUP_ROOT** — consolidar conexiones/índices duplicados por referencia, sin borrar hasta verificar que no haya información única.
7. **AUTH_RUNTIME** — continuar `CLAUDE_CODE_OAUTH_TOKEN`, `RIU_GITHUB_PAT`, `RIU_HF_TOKEN`, Codex 1/2, MCP y memoria sin exponer valores.
8. **GLOBAL_E2E** — ejecutar Router + GitHub + HF + adapters externos habilitados + verifier; registrar logs/URLs/SHA.
9. **SYNC_CLOSE** — STATE + PLAN + BITÁCORA + arquitectura deben coincidir antes de `VERIFIED_CLOSED`.

### Olas
- W0 preservación/evidencia ✅ X-Ray documental materializado.
- W1 owners y deduplicación: EN CURSO.
- W2 externos: PENDIENTE pruebas runtime.
- W3 auth/connectivity: PENDIENTE credenciales/runtime.
- W4 E2E/final: PENDIENTE.

### Gate final RIU-0070
`ROOT_29_ACCOUNTED + EXTERNAL_4_BOUNDARIES_DEFINED + NO_ROUTING_OWNERSHIP_CONFLICT + AUTH_RUNTIME_VERIFIED + CONNECTIVITY_GLOBAL_E2E_PASS + STATE_PLAN_BITACORA_SYNC`.

Evidencia arquitectura: commit `8616da2a84bd5f803ca38a9bbeaea1ed93bafbac`.

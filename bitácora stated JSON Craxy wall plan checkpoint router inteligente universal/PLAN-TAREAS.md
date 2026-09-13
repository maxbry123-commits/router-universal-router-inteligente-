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

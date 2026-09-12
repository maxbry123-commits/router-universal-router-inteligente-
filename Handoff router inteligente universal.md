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

---

## Handoff 2026-09-12 — HF OIDC / Trusted Publishers

### Estado nuevo
- Space HF `COMAND-CENTER-1/yaiwes-ui-factory` existe y está confirmado como `static`.
- Frontend workflow OIDC: `.github/workflows/astra-hf-static-space-publish.yml`.
- Commit OIDC frontend=`d62b02cc95a5d732b7531b99ae597d4d14b1aa7a`.
- Trusted Publishers informados por Director para 8 repos branch `main`.

### Certificación real posterior
- `frontend` run `34675165228`, attempt 2: `HF_AUTH_SELECTED=OIDC`, upload PASS, commit HF `57b5a04d371bad59bab6fa7e9db791fb982daec4`.
- Después de añadir `app_file: index.html`, run `34677293995`: OIDC upload PASS otra vez, commit HF `307549f879b6a3d40493b3bb82d285cb93f76047`.
- Página Hub read-back HTTP 200 PASS.
- URL directa `https://comand-center-1-yaiwes-ui-factory.hf.space/` continúa 404; GAP de serving separado, no de autorización/escritura.

### Probe de secretos Actions — evidencia
Workflow `.github/workflows/riu-auth-presence-probe.yml`, commit `fe1cb36c03f6cf62e561f472a0269de824c01fb0`, run `34677207175` success.
Todos ausentes en Router Actions al momento de la prueba: `RIU_HF_TOKEN/HF_TOKEN`, `RIU_GITHUB_PAT/GH_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN`, `CODEX_AUTH_JSON_ACCOUNT_1/2`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`.

Conclusión: OIDC del Space funciona, pero no existe aún credencial global HF/GitHub en Actions.

### Bootstrap ya preparado
- `scripts/propagate_actions_secrets.py` commit `3adbee46324a7aeafccd83fd3da1747ebf06953e`.
- `.github/workflows/riu-propagate-auth-secrets.yml` commit `4eeb8e6e434e07ea0ad6c909e9df677f4ee9269e`.
- Requiere una sola carga inicial en Router de `RIU_GITHUB_PAT`; si además existe `RIU_HF_TOKEN`, puede cifrar/replicar ambas credenciales a los 8 repos usando las public keys de Actions Secrets.
- No hace falta crear ocho HF tokens distintos; un token HF `write` puede reutilizarse, aunque separar por app reduce el riesgo.

### OpenAI Codex SDK/CLI — estado
OpenAI confirma Codex incluido con login ChatGPT y existe `@openai/codex-sdk`; el runtime instalado usa `@openai/codex` + `codex login --device-auth` para autenticación de suscripción.

Correcciones ejecutadas:
- `scripts/persist_codex_auth_github.py` commit `4de0669687d01bf05bc5698f6f6548b518a584cd`.
- Cuenta 1 workflow commit `7ed16435dbf1b3aed027cbf52f87a102d9edf095`.
- Cuenta 2 workflow commit `90c1cb4d054fbb51e2b590720261087a7cf12a8f`.
- Se dejó de usar HF Space Secrets como bóveda para un secreto que GitHub Actions necesita recuperar; ahora el `auth.json` ChatGPT se valida, cifra y escribe como `CODEX_AUTH_JSON_ACCOUNT_1/2` en Actions Secrets.

### Anthropic Claude SDK/CLI — estado
Anthropic documenta `claude setup-token` -> `CLAUDE_CODE_OAUTH_TOKEN` de larga duración para CI con suscripción; HF Job confirmó CLI `2.1.269` y comando disponible.

Correcciones ejecutadas:
- workflow anterior era inseguro porque volcaba la sesión completa; removido ese patrón.
- `scripts/persist_claude_token_github.py` commit `1aea9ce0262b33b6dbf1a28ca94010d8bfe2d994`.
- workflow seguro `.github/workflows/claude-token-setup.yml` commit `7b165f04f5fe0032fd139804e16accc783043880`.
- La salida cruda de `setup-token` queda runner-local; solo se publica la URL de autorización, el token `sk-ant-oat01-*` se cifra hacia GitHub Secrets y después el log se destruye.

### Reglas finales de acceso
- OIDC HF repo publisher: write temporal SOLO al repo HF configurado.
- HF global: `RIU_HF_TOKEN` role=`write`.
- GitHub `GITHUB_TOKEN`: temporal y repo-local; acceso transversal requiere `RIU_GITHUB_PAT` o GitHub App instalado en los repos objetivo.
- Los modelos no deben recibir valores secretos; reciben capacidad mediante Actions/Router/MCP.

### Nodo vivo ahora
`RIU-0068_BOOTSTRAP_GLOBAL_AUTH`.

Orden:
1. añadir en Router Actions Secrets `RIU_GITHUB_PAT` con acceso a los 8 repos y Secrets write;
2. añadir `RIU_HF_TOKEN` role write de `COMAND-CENTER-1`;
3. ejecutar `RIU Propagate Auth Secrets`;
4. re-run capability probe y exigir PASS;
5. ejecutar Codex account 1/2 device-auth;
6. ejecutar Claude setup-token seguro;
7. certificar modelos/agentes consumiendo GitHub + HF mediante runtime.

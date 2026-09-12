# Router Inteligente Universal — Arquitectura / ADN / X-Ray

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · rama `main`.

## Estado ejecutivo
- CORE P01-P03=`VERIFIED_CLOSED`.
- `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`=PASS.
- Regresión core=PASS.
- Connectivity Fabric=`19/19 BRIDGE v2`.
- Runtime central de conectividad materializado.
- Suite actual del Router=`75 passed, 2 warnings in 5.78s`.
- Nodo vivo=`RIU-0066_RUNTIME_SECRET_E2E`.
- E2E con los 3 secrets de Codespaces sigue fail-closed hasta que el proceso Router corra dentro de un Codespace/runtime al que esos secrets estén autorizados.

## Flujo transversal
`PROYECTO -> conectividad con Router inteligente universal/PUENTE-RIU-<repo>.yaml -> Router -> REGISTRY -> connectivity_runtime -> Enchufe Gate -> RedUniversal -> adapter -> GitHub/HF/MCP/memoria -> verifier -> response`.

## Raíz canónica
`conectividad con Router inteligente universal/`
- `MAPA-MENTAL-CONECTIVIDAD-RIU.md`
- `REGISTRY-CONECTIVIDAD-RIU.json`
- `PUENTE-RIU-router-universal-router-inteligente-.yaml`

Cada uno de los 19 repositorios tiene la misma raíz lógica y un único `PUENTE-RIU-<repo>.yaml` v2.

## Secret store autorizado por el Director
`https://github.com/settings/codespaces`

Refs runtime aceptadas:
- HF: `RIU_HF_TOKEN` -> `HF_TOKEN` -> `HUGGINGFACE_TOKEN`.
- GitHub/MCP: `RIU_GITHUB_PAT` -> `GITHUB_TOKEN` -> `GH_TOKEN`.

No se persisten valores. GitHub no permite re-leer valores de Codespaces Secrets por API; el Router los consume solo como variables de entorno dentro del runtime autorizado.

## Frontend — prioridad Astra
Archivo: `maxbry123-commits/frontend/conectividad con Router inteligente universal/PUENTE-RIU-frontend.yaml`.
Commit=`168b12de4c574a165d32601968ee7dd864614d8a`.
Contiene GitHub, HF `COMAND-CENTER-1`, Jobs CPU/GPU, models/datasets/spaces/jobs, Space `COMAND-CENTER-1/yaiwes-ui-factory`, Claude `github_repository` + GitHub MCP y targets de memoria.

## Runtime central
`router inteligente universal/integration/connectivity_runtime.py`
- commit inicial=`5664301d9051068b98ab326e5545110299e110a6`.
- commit probes permisos/HF/MCP=`912fc38708c13f57046d8aa48c503773bd722d93`.
- GitHub probe: identity, repo, permissions y scopes visibles sin revelar secret.
- HF probe: `whoami-v2`, identity y role visible sin revelar secret.
- MCP probe: handshake `initialize` read-only a `https://api.githubcopilot.com/mcp/`.
- cualquier credencial ausente => fail-closed.

Verificador ejecutable Codespaces:
`router inteligente universal/integration/verify_runtime_connectivity.py`, commit `5b727b139f3736a4f277fb68b03bbaff95d31dfb`.

## Claude / GitHub MCP
Fuente recuperada: `maxbry123-commits/TAREA-1/skills/claude-api/`.
Patrón: `github_repository -> https://api.githubcopilot.com/mcp/ -> vault/runtime auth`.

## Memoria
Claude Managed Agents `memory_store`; targets propios: `MEMORIA`, `BIBLIOTECA`, `BITACORA-MAXBRY`, `Cerebro`.

## Evidencia de tests
- runtime base Job `6aa490c35527934177ecacb3`: COMPLETED, `3 passed in 0.02s`.
- suite anterior Job `6aa4928c21047bf1b037967e`: COMPLETED, `71 passed, 2 warnings`.
- suite después de probes nuevos Job `6aa493a121047bf1b03796e9`: COMPLETED, **`75 passed, 2 warnings in 5.78s`**.
- fail-closed runner Job `6aa493e221047bf1b037970b`: COMPLETED, `FAIL_CLOSED_EXPECTED_PASS` sin secrets visibles.

## Cobertura actual de tests
18 archivos: DB, GitLab, HF connector, Interno/Webhook, MCP App, Memoria, VPS, baseline connectors, connectivity runtime, connector registry, Enchufe Gate v1.5/v2, Enchufe schema v2, FAST-CLOSE E2E, HF hot-path, RedUniversal R003, resilience C10, validator v2. El connectivity runtime pasó de 3 a 7 tests; total suite=75.

## Gate actual
PASS: `BRIDGES_V2_19_OF_19`, `ROUTER_RUNTIME_TESTED`, `CURRENT_ROUTER_TEST_SUITE_75_OF_75`, `FAIL_CLOSED_WITHOUT_SECRETS`.

PENDING runtime Codespaces: `GITHUB_ACCESS_VERIFIED`, `HF_ACCESS_VERIFIED`, `MCP_BOUNDARY_VERIFIED`, `MEMORY_BOUNDARY_VERIFIED`, `CONNECTIVITY_GLOBAL_E2E_PASS`.

---

## Nota 2026-09-12 — Hugging Face / GitHub Trusted Publishers

### Hecho y verificado
- Hugging Face Space creado: `COMAND-CENTER-1/yaiwes-ui-factory`.
- El Hub lo reporta existente, owner=`COMAND-CENTER-1`, SDK=`static`, actualizado `2026-09-12`.
- En `frontend` se implementó fallback OIDC keyless para HF en `.github/workflows/astra-hf-static-space-publish.yml`, commit `d62b02cc95a5d732b7531b99ae597d4d14b1aa7a`.
- Run previo `34675165228`: empaquetado Factory V0=PASS (7 archivos), HF CLI 1.19.0=PASS, OIDC seleccionado; falló únicamente porque el Space aún no existía en ese momento.

### Trusted Publishers configurados por el Director
El Director informó configuración de Trusted Publisher desde Hugging Face para repositorios GitHub, branch `main`:
1. `maxbry123-commits/frontend`
2. `maxbry123-commits/agentes`
3. `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`
4. `maxbry123-commits/osquestador-auditor`
5. `maxbry123-commits/Maxbry-AGI`
6. `maxbry123-commits/nct-core`
7. `maxbry123-commits/TAREA-1`
8. `maxbry123-commits/router-universal-router-inteligente-`

### Evidencia posterior a la creación del Space
- Re-run `frontend` run `34675165228`, attempt 2: `HF_AUTH_SELECTED=OIDC`; upload real=`PASS`; commit HF=`57b5a04d371bad59bab6fa7e9db791fb982daec4`.
- Run `34677293995` después de declarar `app_file: index.html`: OIDC volvió a autenticar y upload=`PASS`; commit HF=`307549f879b6a3d40493b3bb82d285cb93f76047`.
- Hub page read-back=`HTTP 200 PASS`.
- Embed host esperado `https://comand-center-1-yaiwes-ui-factory.hf.space/` continúa `404`; por tanto publicar/escribir está certificado, servir la URL directa sigue GAP independiente.

### Probe real de secretos GitHub Actions en Router
Workflow=`.github/workflows/riu-auth-presence-probe.yml`, commit=`fe1cb36c03f6cf62e561f472a0269de824c01fb0`, run=`34677207175`.
Resultado sin exponer valores:
- `HF_AUTH_TOKEN=ABSENT`
- `GH_AUTH_TOKEN=ABSENT`
- `CLAUDE_AUTH=ABSENT`
- `CODEX_AUTH_1=ABSENT`
- `CODEX_AUTH_2=ABSENT`
- `OPENAI_API_KEY_PRESENT=ABSENT`
- `ANTHROPIC_API_KEY_PRESENT=ABSENT`

Conclusión: Trusted Publisher OIDC sí escribe al Space, pero NO existe todavía un `RIU_HF_TOKEN` global ni un `RIU_GITHUB_PAT` en Actions.

### Arquitectura de bootstrap de credenciales
- `scripts/propagate_actions_secrets.py`, commit=`3adbee46324a7aeafccd83fd3da1747ebf06953e`.
- `.github/workflows/riu-propagate-auth-secrets.yml`, commit=`4eeb8e6e434e07ea0ad6c909e9df677f4ee9269e`.
- Con `RIU_GITHUB_PAT` en Router, cifra mediante la public key de GitHub Actions y puede replicar solo los secretos aprobados a los 8 repos, sin imprimir valores.
- Un solo `RIU_HF_TOKEN` de rol HF `write` puede reutilizarse técnicamente; no hace falta crear ocho tokens HF diferentes. Para reducir blast radius HF recomienda tokens por app/uso, pero el diseño solicitado permite una credencial central con distribución controlada.

### OpenAI Codex / ChatGPT subscription
- Codex está instalado mediante `@openai/codex` y usa `codex login --device-auth` con login ChatGPT, no `OPENAI_API_KEY`.
- `scripts/persist_codex_auth_github.py`, commit=`4de0669687d01bf05bc5698f6f6548b518a584cd`, valida `auth_mode=chatgpt` y cifra el `auth.json` como GitHub Actions Secret.
- Workflow cuenta 1 corregido commit=`7ed16435dbf1b3aed027cbf52f87a102d9edf095`.
- Workflow cuenta 2 corregido commit=`90c1cb4d054fbb51e2b590720261087a7cf12a8f`.
- Se eliminó la dependencia incorrecta de HF Space Secrets como bóveda para credenciales que después necesita GitHub Actions.

### Anthropic Claude subscription
- CLI actual comprobado en HF Job: Claude Code `2.1.269`; `claude setup-token` soportado y requiere suscripción.
- La implementación anterior imprimía la sesión completa y podía exponer el token OAuth: corregida.
- `scripts/persist_claude_token_github.py`, commit=`1aea9ce0262b33b6dbf1a28ca94010d8bfe2d994`, captura solo token `sk-ant-oat01-*` desde log local y lo cifra hacia GitHub Secrets.
- `.github/workflows/claude-token-setup.yml` corregido commit=`7b165f04f5fe0032fd139804e16accc783043880`; salida cruda queda suprimida, solo muestra URL de autorización y destruye el log local tras persistir.

### Regla de credenciales
- Trusted Publisher/OIDC = token temporal de escritura limitado al recurso HF configurado; no es acceso global a toda la cuenta.
- `RIU_HF_TOKEN` = credencial HF `write` para operaciones globales sobre repos donde `COMAND-CENTER-1` tenga permisos.
- `GITHUB_TOKEN` de Actions = token temporal limitado al repo del workflow; para acceso transversal a los 8 repos se requiere `RIU_GITHUB_PAT`/GitHub App con permisos explícitos.
- Los modelos AI reciben capacidades a través del runtime/Actions/MCP; nunca se coloca el valor crudo de secretos en prompt, repositorio o logs.

### Gate pendiente mínimo
1. Cargar manualmente una vez en Router Actions Secrets: `RIU_GITHUB_PAT` y `RIU_HF_TOKEN`.
2. Ejecutar `RIU Propagate Auth Secrets` para distribuirlos a los 8 repos.
3. Ejecutar `Codex Token Setup - Cuenta 1/2` y completar device-auth desde móvil.
4. Ejecutar `Claude Token Setup` y completar autorización desde móvil; verificar si el flujo OAuth remoto termina sin entrada adicional.
5. Re-ejecutar capability probe y exigir roles/permisos PASS.

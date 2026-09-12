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

### Trusted Publishers configurados por el Director — pendiente de prueba E2E
El Director informó configuración de Trusted Publisher desde Hugging Face para repositorios GitHub, branch `main`:
1. `maxbry123-commits/frontend`
2. `maxbry123-commits/agentes`
3. `maxbry123-commits/Agentes-motores-Wordflow-YAIWES`
4. `maxbry123-commits/osquestador-auditor`
5. `maxbry123-commits/Maxbry-AGI`
6. `maxbry123-commits/nct-core`
7. `maxbry123-commits/TAREA-1`
8. `maxbry123-commits/router-universal-router-inteligente-`

No marcar como PASS hasta ejecutar workflows OIDC reales desde cada repo y obtener escritura/lectura de vuelta en HF.

### Distinción de credenciales
- Trusted Publisher/OIDC: acceso sin PAT permanente, ligado a claims de GitHub y al recurso HF autorizado.
- `HF_TOKEN` de escritura: alternativa para operaciones Hub que excedan el recurso OIDC configurado.
- La conexión HF disponible en ChatGPT autentica como `COMAND-CENTER-1` pero su OAuth actual expone `jobs/openid/profile/read-mcp/read-repos`; no constituye evidencia de `write/admin` del Hub.
- Nunca almacenar tokens en archivos, commits, logs o chat; solo secrets/identidad OIDC.

### Próximo gate
1. Reejecutar publicación HF desde `frontend` ahora que el Space existe.
2. Verificar OIDC + upload + read-back.
3. Probar de forma no destructiva HF/GitHub en los demás repos autorizados.
4. Separar acceso de modelos AI de credenciales: cada agente consume credenciales del runtime/Actions; ningún modelo debe contener el secreto en prompt o repositorio.

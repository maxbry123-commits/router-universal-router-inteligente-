# Router Inteligente Universal — Arquitectura / ADN / X-Ray

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP` · rama `main`.

## Estado ejecutivo
- CORE P01-P03: `VERIFIED_CLOSED`.
- Certificación individual HF_M01..HF_M20: `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`.
- Regresión/E2E global del core: `PASS`.
- Nueva capa autorizada: `CONECTIVIDAD_RIU_MULTI_REPO` = `ACTIVE_BUILD`.
- Puentes declarados: `19/19` repositorios propiedad de `maxbry123-commits`.
- Gate pendiente de esta capa: credenciales runtime + pruebas E2E GitHub/Hugging Face/MCP; no se promueve a PASS antes de esas pruebas.
- Regla preservada: `CATALOG_OBSERVED != TESTED != READY`.

## Arquitectura base
`AGENTE -> API key -> FastAPI -> Auth/APIKeyGuard -> Enchufe Gate -> RedUniversal -> registry -> adapter -> destino/modelo -> verifier -> response`.
Separación: contracts/adapters/plugins/registry/loader/guards/tests.

## Nueva raíz canónica de conectividad
Raíz central del Router:
`conectividad con Router inteligente universal/`

Contiene:
- `MAPA-MENTAL-CONECTIVIDAD-RIU.md`: mapa mental/ADN de conexiones y reglas.
- `REGISTRY-CONECTIVIDAD-RIU.json`: registro maestro de repositorios, conexiones y estados.
- `PUENTE-RIU-router-universal-router-inteligente-.yaml`: puente del propio Router.

Cada repositorio administrado contiene la misma raíz lógica y un único archivo canónico:
`conectividad con Router inteligente universal/PUENTE-RIU-<repo>.yaml`.

Ruta transversal:
`REPO -> PUENTE-RIU -> Router Inteligente Universal -> Registry -> Enchufe Gate -> RedUniversal -> adapter -> GitHub/HF/MCP/cómputo/memoria -> verifier -> respuesta`.

## Inventario central 19/19
`agentes`, `Agentes-motores-Wordflow-YAIWES`, `BIBLIOTECA`, `BITACORA-MAXBRY`, `Cerebro`, `comand-Center`, `frontend`, `Grupo-Trabajo-1`, `Grupo-Trabajo-2`, `informaci-n-auditor-`, `Maxbry-AGI`, `MEMORIA`, `nct-core`, `nct-hub`, `Orquestador-Maxbry-`, `osquestador-auditor`, `router-universal-router-inteligente-`, `TAREA-1`, `TAREA-2`.

## Conexiones recuperadas y centralizadas
### Claude Managed Agents ↔ GitHub MCP
Fuente histórica localizada en `maxbry123-commits/TAREA-1/skills/claude-api/`.
Patrón recuperado: `github_repository` + servidor MCP GitHub `https://api.githubcopilot.com/mcp/` + autenticación externa en vault/runtime. El Router registra el endpoint y la frontera de autenticación, nunca la credencial cruda.

### Claude Managed Agents ↔ memoria persistente
Fuente recuperada: `maxbry123-commits/TAREA-1/skills/claude-api/shared/managed-agents-memory.md`.
Recurso: `memory_store` en `resources[]` de sesión, con semántica de memoria persistente entre sesiones. El Router lo registra como capacidad de memoria externa y exige validación E2E antes de usarlo como dependencia operativa.

### Hugging Face
Cuenta observada: `COMAND-CENTER-1`.
Cómputo usado anteriormente: Hugging Face Jobs CPU/GPU y workflows que consumen autenticación desde runtime.
Workflow histórico identificado: `maxbry123-commits/TAREA-1/.github/workflows/yaiwes-hf-static-publish.yml`.
El Router centraliza la referencia lógica, el tipo de cómputo y el estado de verificación. Las credenciales permanecen fuera de Git.

### Memoria / almacenamiento / estado propios
Repositorios dedicados identificados: `MEMORIA`, `BIBLIOTECA`, `BITACORA-MAXBRY`, `Cerebro`. Quedan registrados como capacidades del mapa mental; su promoción a conexión operativa requiere prueba mediante el Router.

## Seguridad y secrets
- Ningún token/PAT/API key/OAuth se escribe en archivos, README, STATE ni commits.
- Los archivos puente usan únicamente `external_runtime_secret_store`/vault/runtime como frontera.
- GitHub Actions, Codespaces, Hugging Face y vaults pueden ser almacenes externos; el Router consume referencias en tiempo de ejecución.
- Toda conexión es fail-closed hasta identidad + permiso/scope + operación mínima + read-back/verifier.

## Core preservado
P01 conjunto ejecutable HF cerrado; P02 hot-path `C01 REST -> C20 Auth -> C15 Gate -> C17 RedUniversal -> C16 adapter -> verifier`; P03 API Key Manager 100 slots hash-only rotate/revoke + E2E real.

## Certificación 20 modelos
PASS/ejecución verificada: M01, M02, M03, M05, M06, M07, M10, M11, M12, M20.
FLAG/GAP explícitos: M04, M08, M09, M13, M14, M15, M16, M17, M18, M19.
M18 final=`FLAG-HF-M18-RUNTIME-TIMEOUT-001`: Jobs `6aa475605527934177eca1cb` ERROR, `6aa475e721047bf1b0378e13` diagnóstico selector Q3_K_S, `6aa4769b5527934177eca24b` Q4_K_M RUNNING→CANCELED por ventana corta sin terminal inference.

## Regresión core
GitHub Actions `RIU FAST-CLOSE`, run `34582284615`, job `103434377312`: success; `pytest -q router inteligente universal/tests/test_fast_close_global_e2e.py` => `2 passed, 2 warnings in 6.75s`.
Commit de código probado `af469152fd0306d706c67b8cf6548512fdc4f1c0`; gateway blob `e970b5de2281d236b916ea41492ee52df8454153`; E2E blob `23473c2a33cb9e5a451ad5a19ce5c4e5a58fc2c7`.

## Gate actual
Core cerrado y preservado. La nueva tarea queda abierta como:
`ALL_REPOS_BRIDGED(19/19) + ROUTER_REGISTRY_COMPLETE + GITHUB_ACCESS_VERIFIED + HF_ACCESS_VERIFIED + MCP_BOUNDARY_VERIFIED + HANDOFF_SYNCHRONIZED`.
Estado de ejecución actual: `ALL_REPOS_BRIDGED=PASS`; validaciones de credenciales/E2E=`PENDING`.

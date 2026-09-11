# Handoff Router Inteligente Universal — ADN operativo

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · repo `maxbry123-commits/router-universal-router-inteligente-` · branch `main`.

## Estado preservado del core
- Core P01-P03=`VERIFIED_CLOSED`.
- `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`=PASS.
- `FINAL_REGRESSION_E2E_PASS`=PASS.
- El core no se reabre salvo regresión demostrada.

## Nueva tarea autorizada — conectividad centralizada multi-repo
Estado=`ACTIVE_BUILD`.
Raíz canónica del Router: `conectividad con Router inteligente universal/`.

Objetivo: que toda conexión de GitHub, Hugging Face, MCP, cómputo, memoria, almacenamiento, VPS/API y puentes entre proyectos pase por Router Inteligente Universal y sea localizable desde un mapa mental/registry único.

### Regla por repositorio
Cada repo tiene una sola raíz lógica `conectividad con Router inteligente universal/` y un solo archivo `PUENTE-RIU-<repo>.yaml`.
Puentes declarados y persistidos: `19/19`.

Repos: agentes; Agentes-motores-Wordflow-YAIWES; BIBLIOTECA; BITACORA-MAXBRY; Cerebro; comand-Center; frontend; Grupo-Trabajo-1; Grupo-Trabajo-2; informaci-n-auditor-; Maxbry-AGI; MEMORIA; nct-core; nct-hub; Orquestador-Maxbry-; osquestador-auditor; router-universal-router-inteligente-; TAREA-1; TAREA-2.

### Registro maestro
- `conectividad con Router inteligente universal/MAPA-MENTAL-CONECTIVIDAD-RIU.md`
- `conectividad con Router inteligente universal/REGISTRY-CONECTIVIDAD-RIU.json`
- `conectividad con Router inteligente universal/PUENTE-RIU-router-universal-router-inteligente-.yaml`

### Claude ↔ GitHub MCP recuperado
Fuente histórica: `maxbry123-commits/TAREA-1/skills/claude-api/`.
Patrón: Claude Managed Agents + recurso `github_repository` + GitHub MCP `https://api.githubcopilot.com/mcp/` + autenticación externa en vault/runtime. No copiar tokens al repo.

### Hugging Face
Cuenta observada: `COMAND-CENTER-1`.
Cómputo observado/ya usado en el proyecto: Hugging Face Jobs CPU/GPU. El Router debe consumir autenticación en runtime desde almacén seguro y validar identidad/scope antes de PASS.

### Memoria/estado
`MEMORIA`, `BIBLIOTECA`, `BITACORA-MAXBRY`, `Cerebro` están mapeados como capacidades de memoria/almacenamiento/estado; siguen `PENDING_E2E_ROUTER` hasta una operación real y read-back mediante el Router.

## Seguridad
Credenciales crudas prohibidas en Git. Los puentes solo registran frontera `external_runtime_secret_store`/vault/runtime. Codespaces/Actions/HF/vault pueden alojar credenciales, pero Router solo recibe referencias/runtime.

## Gate actual
`ALL_REPOS_BRIDGED=PASS(19/19)`.
Pendiente: `GITHUB_ACCESS_VERIFIED + HF_ACCESS_VERIFIED + MCP_BOUNDARY_VERIFIED + CONNECTIVITY_GLOBAL_E2E_PASS`.
Hasta que esas pruebas existan, la capa de conectividad no es `VERIFIED_CLOSED`.

## Evidencia de esta iteración
- mapa central creado: commit `b74d6220b8ddbead8a77af48e04b0970d2ddea60`
- registry creado: commit `f56d64668448363a62684066d5f1a8685dcd31f7`
- registry actualizado 19/19: commit `87b5f3c61a94e69494450829772a74b0eee552c9`
- README arquitectura integrado: commit `be0dc26ab4f6aac525c06decbb56bab20829457a`
- archivos puente creados en los 19 repos; ver `REGISTRY-CONECTIVIDAD-RIU.json`.

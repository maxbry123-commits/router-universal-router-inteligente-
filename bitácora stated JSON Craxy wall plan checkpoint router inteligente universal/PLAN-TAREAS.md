# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Core preservado
- P01 ✅ conjunto ejecutable HF cerrado.
- P02 ✅ hot-path C01/C20/C15/C17/C16 cerrado.
- P03 ✅ API Key Manager 100 slots + E2E cerrado.
- MODEL CERTIFICATION ✅ 20/20 slots accounted.
- FINAL REGRESSION/E2E ✅ run `34582284615`, job `103434377312`, `2 passed, 2 warnings in 6.75s`.

## Nueva tarea autorizada — RIU-0063 conectividad centralizada
### Paso A — inventario/raíz/puentes ✅
- raíz central Router creada: `conectividad con Router inteligente universal/`
- mapa mental creado
- registry central creado con SHA de cada bridge
- 19/19 repositorios con `PUENTE-RIU-<repo>.yaml`
- Claude/GitHub MCP histórico localizado y referenciado
- Claude `memory_store` histórico localizado y referenciado
- Hugging Face `COMAND-CENTER-1` + Jobs CPU/GPU referenciado
- repos de memoria/estado mapeados: MEMORIA/BIBLIOTECA/BITACORA-MAXBRY/Cerebro

### Paso B — credenciales runtime ⏳
Validar las credenciales que el Director deje en almacén externo seguro. No escribir valores en Git.
Pruebas requeridas:
1. GitHub: identidad + permisos + operación mínima + read-back.
2. Hugging Face: identidad/account + scopes/capacidades + operación API/Job mínima.
3. Claude/GitHub MCP: frontera MCP/vault/runtime + disponibilidad de herramientas sin exponer secreto.
4. Claude memoria: disponibilidad del `memory_store`/frontera de memoria sin exponer credenciales.

### Paso C — E2E Router ⏳
Probar al menos una ruta real por proveedor:
`repo/agent -> PUENTE-RIU -> Router -> Enchufe Gate -> RedUniversal -> provider -> verifier -> response`.

### Paso D — cierre documental ⏳
Actualizar registry, README arquitectura, Handoff, Crazy Wall, STATE, CHECKPOINT, PLAN y RECOVERY con evidencias finales. Solo entonces `CONNECTIVITY_LAYER_VERIFIED_CLOSED`.

## Cola 1×1 actual
`GITHUB_RUNTIME_CREDENTIAL_VALIDATION` → `HF_RUNTIME_CREDENTIAL_VALIDATION` → `CLAUDE_GITHUB_MCP_BOUNDARY_VALIDATION` → `CLAUDE_MEMORY_STORE_BOUNDARY_VALIDATION` → `GLOBAL_CONNECTIVITY_E2E` → `DOC_SYNC_FINAL`.

## Estado
`ALL_REPOS_BRIDGED=PASS(19/19)`.
`CONNECTIVITY_LAYER_VERIFIED_CLOSED=PENDING`.

# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3` · **Modo:** `FAIL_CLOSED_LOOP`.

## RIU-0001..0058 — CORE
P01=`CLOSED_EXECUTABLE_SET`; P02=`CLOSED_HOT_PATH_EXECUTABLE_SET`; P03=`VERIFIED_CLOSED`. Hot-path commit `af469152fd0306d706c67b8cf6548512fdc4f1c0`.

## RIU-0059..0061 — CERTIFICACIÓN 20 MODELOS
PASS/ejecución previa válida preservada: M01, M02, M03, M05, M06, M07, M10, M11, M12, M20.
FLAG/GAP contabilizados: M04, M08, M09, M13, M14, M15, M16, M17, M19.
M18 fue trabajado individualmente: `6aa475605527934177eca1cb` ERROR; diagnóstico `6aa475e721047bf1b0378e13` mostró `no GGUF files found ... Q3_K_S` y `--model is required`; StrategyDelta canónico `Q4_K_M` Job `6aa4769b5527934177eca24b` llegó a RUNNING pero no cerró dentro de la ventana corta de 240s y fue cancelado para no consumir otra ventana larga. Resultado final M18=`FLAG-HF-M18-RUNTIME-TIMEOUT-001`, nunca PASS/READY.

## RIU-0062 — GATE FINAL CORE/MODELOS
`MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`=PASS: 20/20 slots terminan PASS/verified o FLAG/GAP explícito con evidencia.
Regresión global `RIU FAST-CLOSE` relanzada: run `34582284615`, job `103434377312`, conclusion=`success`; `pytest -q router inteligente universal/tests/test_fast_close_global_e2e.py` => `2 passed, 2 warnings in 6.75s`.
El checkout reportó un warning existente de pointer LFS en `qdrant/tests/e2e_tests/test_data/storage.tar.xz`, pero el workflow/test final concluyó success; se registra como warning, no como fallo del hot-path.

## RIU-0063 — CONECTIVIDAD CENTRALIZADA MULTI-REPO
Nueva orden del Director: toda conectividad de proyectos — GitHub, Hugging Face, MCP, cómputo, memoria, almacenamiento, APIs/VPS y puentes — debe quedar organizada bajo una raíz canónica y pasar por Router Inteligente Universal.

### Persistencia ejecutada
- raíz central creada: `conectividad con Router inteligente universal/`
- mapa mental creado: `MAPA-MENTAL-CONECTIVIDAD-RIU.md`, commit `b74d6220b8ddbead8a77af48e04b0970d2ddea60`
- registry maestro creado: `REGISTRY-CONECTIVIDAD-RIU.json`, commit inicial `f56d64668448363a62684066d5f1a8685dcd31f7`
- 19/19 repositorios propietarios recibieron `conectividad con Router inteligente universal/PUENTE-RIU-<repo>.yaml`
- registry actualizado a 19/19 `BRIDGE_DECLARED`, commit `87b5f3c61a94e69494450829772a74b0eee552c9`
- README arquitectura actualizado, commit `be0dc26ab4f6aac525c06decbb56bab20829457a`
- Handoff actualizado, commit `6a8facc3bfc9ea3616f6d5c93493d2db4c6731e1`

### Claude ↔ GitHub MCP recuperado
Fuente histórica localizada en `maxbry123-commits/TAREA-1/skills/claude-api/`.
Patrón validado documentalmente: recurso `github_repository` + MCP GitHub `https://api.githubcopilot.com/mcp/` + credencial externa en vault/runtime. Se centraliza la referencia, nunca el secreto.

### Hugging Face
Cuenta observada `COMAND-CENTER-1`; Jobs CPU/GPU ya fueron usados en el proyecto. El nuevo gate exige credencial runtime + prueba de identidad/scope + operación real/read-back por el Router antes de PASS.

### Memoria/estado
`MEMORIA`, `BIBLIOTECA`, `BITACORA-MAXBRY`, `Cerebro` incorporados al mapa como targets de memoria/almacenamiento/estado. Operatividad aún no declarada: `PENDING_E2E_ROUTER`.

### Gate RIU-0063
- `ALL_REPOS_BRIDGED=PASS(19/19)`
- `ROUTER_REGISTRY_COMPLETE=PASS`
- `GITHUB_ACCESS_VERIFIED=PENDING`
- `HF_ACCESS_VERIFIED=PENDING`
- `MCP_BOUNDARY_VERIFIED=PENDING`
- `CONNECTIVITY_GLOBAL_E2E_PASS=PENDING`

## Reglas preservadas
`CATALOG_OBSERVED != TESTED != READY`; no secretos en repo; flags externos/runtime no se maquillan como PASS; core anterior no se reabre sin regresión.

Estado global del core: `VERIFIED_CLOSED`.
Estado de la nueva capa: `ACTIVE_BUILD_CONNECTIVITY_LAYER`.

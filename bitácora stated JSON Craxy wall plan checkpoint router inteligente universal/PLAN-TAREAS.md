# PLAN DE TAREAS — ROUTER INTELIGENTE UNIVERSAL
Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP`.

## Estado consolidado RIU-0103
Core P01/P02/P03 y hot-path conservan evidencia histórica. `RedUniversal` conserva ownership único. AI Staff mantiene `REMOTE_INFERENCE_ONLY`. Presencia documental nunca equivale a cierre global.

## Evidencia fresh
- HEAD auditado: `719a5fe3a9506ce1d19d6968b144315d3c4c5ebf`.
- Independent extraction audit: run `35438706702`, job `105885689671`, `success`.
- Runner checkout: `312431` archivos.
- `scripts/extract_guardian_repair_20260903.py --audit-only`: archive_groups=0, remaining=0, retryable=0, blocked=0, verdict=`VERIFIED_CLOSED`.
- Watchdog extracción=`PASSIVE` con cero gaps.
- Hallazgo separado: Qdrant `tests/e2e_tests/test_data/storage.tar.xz` debería ser LFS pointer y no lo es. Clasificar `GAP_LFS_PROVENANCE_QDRANT_STORAGE`; no borrar ni convertir automáticamente.

## W1 — organización / dedup / owners
1. Clasificar provenance de la anomalía LFS Qdrant sin destruir evidencia.
2. Completar X-Ray por contenedores; 312431 archivos observados por checkout no equivalen por sí solos a clasificación completa.
3. Mantener LiteLLM/litellm hasta provenance/equivalencia completa.
4. Clasificar workflows históricos download/extraction como legacy/provenance cuando no sean gates actuales.
5. `RedUniversal` sigue siendo owner único de routing.

## W2 — componentes externos
- OmniRoute: adapter downstream detrás de `connector_registry`; health/fallback/rate-limit + read-back pendientes.
- AnyDoc: ingest adapter; multiformato/hash/error-path pendientes.
- Orca: ADE externo; worktree/verifier pendiente; nunca router owner.
- Omarchy: host opcional; checklist pendiente; nunca dependencia runtime.

## W3 — auth/runtime/connectivity
- HF/GitHub/Claude/Codex/MCP/memoria sólo cierran con capacidad runtime fresh y sin exponer secretos.
- REMOTE20: discovery histórico 20/20 conservado; no declarar 20/20 inference sin smoke autenticado individual.
- Mirror/download/snapshot se conservan como provenance, no como gate activo normal.

## W4 — pruebas
Cada cierre: ruta + commit/blob SHA/diff/log/URL/read-back/test. Ejecutar failure path/fallback. Repetir hasta 10x sólo ante flakiness real.

## W5 — sincronización
Sincronizar README arquitectura + Índice + Handoff + STATE + PLAN + Crazy Wall + CHECKPOINT antes de cierre global.

## Gates
- `EXTRACTION_ARCHIVE_INTEGRITY_VERIFIED=true` por run 35438706702.
- `FULL_COMPONENT_CONTAINER_XRAY=false`.
- `DEDUP_ORPHAN_RECONCILIATION=false`.
- `EXTERNAL_COMPONENTS_APPLICABLE_VERIFIED=false`.
- `AUTH_RUNTIME_VERIFIED=false`.
- `CONNECTIVITY_GLOBAL_E2E_PASS=false`.
- `DOC_STATE_PLAN_CHECKPOINT_HANDOFF_SYNC=false`.
- `GLOBAL_CLOSED=false`.

## Cola autoritativa
`LFS_PROVENANCE_CLASSIFICATION -> FULL_COMPONENT_XRAY -> STATE/CRAZY_WALL RECONCILIATION -> OMNIROUTE/ANYDOC/ORCA/OMARCHY -> AUTH_CLAUDE_CODEX_MCP_MEMORY -> GLOBAL_E2E -> FINAL_DOC_SYNC`.

Regla: `REUSE_EXISTING > PATCH > ADAPT > GENERATE`; si falta evidencia registrar GAP y continuar con el siguiente delta seguro.

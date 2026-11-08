# HANDOFF — cierre reorganización (2026-11-08)

## Estado en una frase

DAG de cierre **20261107** ejecutado y auditado: **N0 ✅ · C1 ✅ · N1 ✅ · N2 ✅** · N3/N4/N5 **en pausa por owner_gate**.
`main` = `cbcfbeb69c1b` · `main-clean` = `89ff668b8fe0` (alineada) · Dataset con **14/15** jobs con evidencia · Space `RUNNING` con sus 8 ficheros operativos.

## URLs

- Repo: https://github.com/maxbry123-commits/router-universal-router-inteligente-
- Dataset (verdad): https://huggingface.co/datasets/COMAND-CENTER-1/router-universal-router-inteligente-auditoria
- Space: https://huggingface.co/spaces/COMAND-CENTER-1/riu-router · salud: https://comand-center-1-riu-router.hf.space/health
- audit_trace: https://huggingface.co/datasets/COMAND-CENTER-1/router-universal-router-inteligente-auditoria/blob/main/20261107-cierre/audit/audit_trace.json
- Guía maestra: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/kernel/GUIDE.md
- Motores del DAG: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/ops/dag
- Trazabilidad completa: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/audit/cierre/CIERRE-20261108-TRAZABILIDAD-Y-HANDOFF.md

## Entorno

```bash
cd /workspace/work/repo-live
export RUN_ID="20261107-cierre" GH_REPO="maxbry123-commits/router-universal-router-inteligente-" \
       DATASET_REPO="COMAND-CENTER-1/router-universal-router-inteligente-auditoria" \
       SPACE_REPO="COMAND-CENTER-1/riu-router" HF_TOKEN="${HF_TOKEN_1_NEW}" \
       GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0="http.https://github.com/.extraheader"
export GIT_CONFIG_VALUE_0="AUTHORIZATION: basic $(printf 'x-access-token:%s' "$GH_TOKEN" | base64 -w0)"
```

Python: `/workspace/work/venv/bin/python` (huggingface_hub 2.4.0). `PYTHONPATH=/workspace/work/vendor:/workspace/work/repo-live/ops`.

## Qué falta (en orden)

1. **Arreglar `ops/dag/n3_rebuild_space.py`** — usa `CommitOperationAdd(path_in_repo=…, path_or_fileobj=…)`, argumentos que la API de HF no acepta, y no implementa sus checks. Debe delegar en `ops/j9_remirror.py` (tiene el gate D-148 + `space_RUNNING` + `health_commit_equals_new_HEAD`). Commit rotulado: `fix de bug del DAG vN (n3_rebuild_space)`.
2. **`OWNER_GATE=APPROVE_N3` → `python ops/dag/n3_rebuild_space.py`** (15–25 min) → cierra **N6**.
3. **`OWNER_GATE=APPROVE_N4` → `python ops/dag/n4_final_audit.py`** (5–10 min) → sube `j10_final_audit/result.json` → cierra **N7** → Dataset 15/15.
4. **N8** — sondas de inferencia real; promover a `active` solo con las 7 condiciones; el resto en `pending_audit` con evidencia.
5. **N9/N10** — `kernel/KERNEL.yaml` (11 nodos, `progress_pct = 100×CLOSED/11`), `kernel/LEDGER.jsonl`, `connections/wiring_changelog.md`, `README.md`, `memory_agente_minimax_02.md`, handoff.next vacío.
6. **`OWNER_GATE=APPROVE_N5` → `python ops/dag/n5_fast_forward.py`** (o ya resuelto: N2 dejó `main-clean` alineada).
7. Regenerar `audit_trace.py` → segunda pasada del centinela → `DONE`.

## Decisiones del owner pendientes

- **D-a** GAP-8: purga del historial de `main` (packs > 2 GiB) → ¿queda `CERRADO_CON_FLAG`, rebase, o repo nuevo?
- **D-b** GAP-10: 16 conexiones sin inferencia real → ¿se acepta `pending_audit` con evidencia?
- **D-c** GAP-14: ¿el gate de secretos excluye los fixtures de tests de terceros?

## Reglas que no se negocian

- Lease **siempre** con `git ls-remote` en el instante del push: otros agentes publican en `main` continuamente (9+ veces).
- Nada se publica si el remoto no es ancestro de HEAD → aborta (D-150). Ya salvó `main` 2 veces.
- El Space **solo** se toca vía API de HF (rebuild). Nunca push de árbol (D-145).
- Secretos solo por entorno; nunca en argv, URL ni logs.
- Los motores del DAG son fail-closed; no se improvisan comandos.

## Gaps resueltos en esta fase (no repetir)

D-145 (reespejo = rebuild por API) · D-146 (clon reutilizado en solo lectura) · D-148 (gate duro de ficheros operativos) · D-149 (caché de grafo) · D-149b (baseline real de 65.914) · D-150/D-154 (N1 solo fast-forward con lease renovado) · D-151 (N2 sin `--no-thin`) · D-152 (N5 aborta si la ancestría falla) · D-153 (C1 diff commit→commit + digest) · D-155 (commit-tree index-only).

## Ficheros clave

| Qué | Dónde |
|---|---|
| Motores del DAG | `/workspace/work/repo-live/ops/dag/` (8) |
| Input block + dag + schema | `/workspace/work/repo-live/{input_block_verbatim.yaml,dag.json,dsl.schema.json}` |
| Salidas del DAG | `/workspace/work/repo-live/out/{N0,N1,N2,C1}/` + `out/audit_trace.json` |
| Grafo cacheado (283 MB) | `/workspace/work/out/graph_cache.json` |
| Trazabilidad larga | `/workspace/output/CIERRE-20261108-TRAZABILIDAD-Y-HANDOFF.md` |
| Paquetes de auditoría | `/workspace/work/output/` (7) |
| Logs | `/workspace/work/{n1b,n2,c1,j9_final,regen2,wiring_check,remirror_push}.log` |

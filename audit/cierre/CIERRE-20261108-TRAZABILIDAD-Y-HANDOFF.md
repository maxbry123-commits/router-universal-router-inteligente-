# CIERRE 20261107 — Trazabilidad completa, handoff y guía/DSL del cierre

> Documento maestro de cierre. Todo lo que sigue está **verificado contra el estado real**
> (GitHub API, HF API, `/health` HTTP y lecturas de fichero) en el corte indicado.
> **Corte:** 2026-11-08 01:30 UTC · **Estado: NO CERRADO** · 6/11 nodos del DAG maestro.

---

# PARTE 0 — URLs (todas las visibles y comprobadas)

| Recurso | URL | Estado verificado |
|---|---|---|
| **Repo (código)** | `https://github.com/maxbry123-commits/router-universal-router-inteligente-` | `main` = `cbcfbeb69c1b` · 435.923 ficheros |
| Repo · rama `main-clean` | `https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main-clean` | `89ff668b8fe0` (alineada con el `main` del DAG) |
| Repo · rama de reorg | `https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/reorg/20261104-kernel01` | `3e172b207be4` (historial reescrito, D-137) |
| Repo · rama de research | `https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/research/20261104-kernel01` | `232518174c72` |
| Repo · rollback | `https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/respaldo-main-pre-swap-20261104-kernel01` | `c2ad951e0ca3` |
| **Dataset (verdad)** | `https://huggingface.co/datasets/COMAND-CENTER-1/router-universal-router-inteligente-auditoria` | commit `d68c7055637a` |
| Dataset · run reorganización | `https://huggingface.co/datasets/COMAND-CENTER-1/router-universal-router-inteligente-auditoria/tree/main/20261104-kernel01` | 14 jobs con evidencia |
| Dataset · run cierre | `https://huggingface.co/datasets/COMAND-CENTER-1/router-universal-router-inteligente-auditoria/tree/main/20261107-cierre` | audit_trace + DAG |
| Dataset · audit_trace | `https://huggingface.co/datasets/COMAND-CENTER-1/router-universal-router-inteligente-auditoria/blob/main/20261107-cierre/audit/audit_trace.json` | 4.504 B · sha `8b2687177c56` |
| **Space (servicio)** | `https://huggingface.co/spaces/COMAND-CENTER-1/riu-router` | `stage=RUNNING` · `hardware=cpu-upgrade` · sha `d63b107225b6` |
| Space · salud | `https://comand-center-1-riu-router.hf.space/health` | HTTP 200 → `{"status":"ok","commit":"4722f1dffc"}` |
| Space · chat UI | `https://riu-jev-bridge.vercel.app` | Vercel (frontend) |
| Router RIU (MCP) | `https://comand-center-1-riu-router.hf.space` | 14 tools MCP verificados |
| Guía maestra (en repo) | `https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/kernel/GUIDE.md` | 123.912 B |
| Input block adjunto (en repo) | `https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/kernel/INPUT_BLOCK_YAIWES_CABLEADO.md` | sha `9d01a464…b90baa` |
| Índice de navegación | `https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/CODE_INDEX.md` | 8.010 B · 11 entradas |
| Registro maestro | `https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/SYSTEM_WIRING_REGISTRY.yaml` | 19.967 B |
| Bundle de rollback (en Dataset) | `https://huggingface.co/datasets/COMAND-CENTER-1/router-universal-router-inteligente-auditoria/blob/main/backups/20261104-kernel01.bundle` | 8.068.832.804 B |
| DAG de cierre (en repo) | `https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/main/ops/dag` | 8 motores + build_trace |
| DAG de cierre (en Dataset) | `https://huggingface.co/datasets/COMAND-CENTER-1/router-universal-router-inteligente-auditoria/tree/main/20261107-cierre/audit/gaps` | input block + dag + schema + motores |

---

# PARTE 1 — TRAZABILIDAD

## 1.1 Cadena de evidencia (de la fuente a la verdad)

```
GitHub main (código)                Dataset (evidencia)              Space (servicio)
      │                                    │                              │
      ├─ 435.923 ficheros                  ├─ 14 result.json              ├─ 8 ficheros operativos
      ├─ kernel/GUIDE.md (123 KB)          ├─ research/ (52 fuentes)      ├─ stage=RUNNING
      ├─ kernel/INPUT_BLOCK*.yaml          ├─ audit/ (j6_rewrite,         ├─ /health 200
      ├─ ops/ (jobs + DAG)                 │   jobs-pendientes, gaps)     └─ sirve 4722f1dffc
      ├─ connections/ + CODE_INDEX         ├─ backups/*.bundle (8,07 GB)      ▲
      └─ handoff/docs/ (5 áreas)           └─ 20261107-cierre/audit_trace   │
                     ▲                                   ▲                     │
                     └──────────── jobs j0..j11 ─────────┘                     │
                                          ▲                                     │
                                          └──── j9_remirror (rebuild) ──────────┘
```

## 1.2 Los 14 jobs con evidencia (Dataset = verdad)

| Job | Estado | Fecha (UTC) | Commit | Qué prueba |
|---|---|---|---|---|
| `j0_preflight` | ✅ PASS | 2026-11-04T18:25 | — | entorno, disco, remoto, HF whoami, dataset escribible |
| `j1_inventory` | ✅ PASS | 2026-11-04T18:46 | `10e3b5e6480f` | inventario de ficheros del repo |
| `j2_graph` | ✅ PASS | 2026-11-04T20:17 | `9dcd456ef922` | grafo de cableado + `baseline_unresolved.json` |
| `j3_history` | ✅ PASS | 2026-11-04T19:06 | `545da638bafd` | historia del repo |
| `j4_plan` | ✅ PASS | 2026-11-07T09:50 | `ca79a412e35b` | plan de reorganización + sha256 + cuarentena |
| `j5_apply` | ✅ PASS | 2026-11-05T05:30 | `e0773eb4f15a` | aplicación, rama y etiqueta |
| `j6_rewrite` | ✅ PASS | 2026-11-07T02:41 | `c33978b5822b` | bundle 8,07 GB + purga de 37 rutas + `main-clean` |
| `j6b_swap` | ✅ PASS | 2026-11-07T03:45 | `35470e8b0660` | swap de `main` con lease + 3 anclas de rollback |
| `j7_mirror` | ✅ PASS | 2026-11-06T05:16 | `32892dd3f434` | espejo base: 6.170 ficheros / 110,7 MB, sin subir |
| `j8_audit` | ✅ PASS | 2026-11-06T05:22 | `6d072e806768` | auditoría previa: 8 jobs PASS + `wiring_check_on_target` |
| `j9_remirror` | ❌ **FAIL** | 2026-11-07T09:58 | `56d80a8d6fb2` | `wiring_check_before_remirror → no_new_unresolved` |
| `j10_final_audit` | ⏸ **AUSENTE** | — | — | **no existe `result.json`** → 14/15 con evidencia |
| `j11_patterns` | ✅ PASS | 2026-11-04T18:50 | `4162ced5ea7f` | patrones del repo |
| `backend_smoke` | ✅ PASS | 2026-11-05T05:29 | — | gate de arranque real en Job de HF |
| `bridge` | ✅ PASS | 2026-11-07T03:03 | `a9d59fd1b2c5` | 38 conexiones, 9 endpoints, 12/12 healthchecks, MCP 14 tools |

**13 PASS · 1 FAIL · 1 ausente** (el FAIL de `j9` es anterior al parche D-145/D-149/D-149b; el `result.json` en el Dataset se reescribe en el siguiente run).

## 1.3 DAG de cierre 20261107 — ejecución real

| Nodo | Tipo | Resultado | Evidencia (`out/<N>/`) |
|---|---|---|---|
| **N0** | validate | ✅ PASS | `validate.json` — sha256 `6c4383cb…e4d2`, shas remotos leídos |
| **C1** | centinela (paralelo) | ✅ PASS | `centinela.json` — schema ✓ · código 1:1 ✓ · input block verbatim ✓ · **0 violaciones** |
| **N1** | publish | ✅ PASS | `patches.json` — lease `6c216c9a`, fast-forward, 1 intento |
| **N2** | push | ✅ PASS | `push_main_clean.json` — 174 commits en **9 tramos**, lease renovado en cada uno |
| **N3** | rebuild | ⏸ gate | `OWNER_GATE=APPROVE_N3` |
| **N4** | audit | ⏸ gate | `OWNER_GATE=APPROVE_N4` |
| **N5** | fast_forward | ⏸ gate | `OWNER_GATE=APPROVE_N5` |

`audit_trace.json` → `overall_status: PASS` · `gated_pending: [N3, N4, N5]`.

## 1.4 Trazabilidad de los gaps (gap → detección → evidencia → fix → estado)

| # | Gap | Detectado por | Evidencia | Fix | Estado |
|---|---|---|---|---|---|
| G-01 | 48.899 ficheros de terceros en `Main_Skills/` contados como código propio | `kernel-cierre` | `j9_remirror` FAIL 08:42 + 09:58 | clasificación por **ruta exacta** + `Main_Skills/_staging`, `Main_Skills/Frontend` como terceros | ✅ publicado `ca79a412e3` |
| G-02 | baseline de 961 subcuenta (generado con 366.077 ficheros ausentes) | yo | original `dd3eb1779d` = 65.908 · real = **65.914** | regenerar sobre árbol íntegro | ✅ publicado (D-149b) |
| G-03 | el push del job borraría **6 ficheros operativos del Space** | yo | `boot.sh` exige `router-mvp/mvp/{run.py,app.py,requirements.txt}` | reespejo = **rebuild por API de HF** | ✅ publicado `2414b9029d` |
| G-04 | push al Space muerto por HTTP/2 (`expected 'acknowledgments'`) | yo | `ls-remote` falla por HTTP/2; responde con HTTP/1.1 | vía API de HF | ✅ publicado `2414b9029d` |
| G-05 | el Space sirve un commit huérfano (`4722f1dffc`) | centinela AC3 + yo | `/health` → `4722f1dffc`; no es ancestro de `main` | ejecutar N3 y verificar `health.commit == main` | 🔴 **ABIERTO** |
| G-06 | `space_has_operational_files` era informativo | centinela G4 | faltaba el `return` | gate duro D-148 | ✅ publicado |
| G-07 | el gate reconstruye el grafo en cada job (660 s) | yo | `j2_graph.build()` = 660 s × 2 | caché `GRAPH_CACHE` D-149 | ✅ publicado |
| G-08 | purga del **historial** sin resolver (pack > 2 GiB → HTTP 500) | N3 | `j6_rewrite` PASS con flag | rebase o repo nuevo | 🔴 **ABIERTO — decisión del owner** |
| G-09 | `main-clean` 2 commits atrás | yo | `35470e8b` vs `main` | fast-forward con lease | ✅ **resuelto por N2** (9 tramos) |
| G-10 | 16 conexiones en `pending_audit` | yo | 38 inventariadas, 12/12 healthchecks, MCP 14 tools; falta **inferencia real** | sondas reales → `active` con 7 condiciones | 🔴 **ABIERTO** |
| G-11 | otros agentes escriben en `main` en paralelo | yo + centinela G7 | `main` se movió 9+ veces | lease contra el sha real leído en cada intento + reintento atómico | ✅ mitigado (D-154) |
| G-12 | un job perdió **366.077 ficheros** del clon vivo | centinela G8 + yo | recuperados: 373.434 en disco; los 22 "ausentes" son symlinks con destino inexistente (diseño original) | D-146: clon reutilizado en solo lectura, nunca se registra para borrado | ✅ **resuelto** |
| G-13 | bundles importados sin cablear | `kernel-cierre` | 20 commits `build(hf-combined)` | declarados terceros; no se borran (decisión del owner) | ✅ resuelto |
| G-14 | 20 ficheros de `main` con patrones `sk-`/`hf-` | centinela G9 | todos en **fixtures de tests de terceros** | 0 tokens reales; 0 coincidencias de `GH_TOKEN`/`HF_TOKEN_1_NEW`/`UNIVERSAL_KEY` | 🟡 **INFO — depende del owner** |
| G-15 | `j10_final_audit/result.json` ausente | centinela G2 | 14 carpetas, 13 con `result.json` | ejecutar N4 | 🔴 **ABIERTO** |
| G-16 | 3 hashes de skills sin baseline | centinela AC4 | `INPUT_BLOCK.yaml` `5c4bbb20…83c3a` ✅ · `INPUT_BLOCK_YAIWES_CABLEADO.md` `9d01a464…b90baa` ✅ · `AGENTS.md` `5c77e005…8943` ✅ | fijar baseline de los `.skills` | 🟡 INFO |
| G-17 | **N1 podía reescribir `main`** (5.601 commits / 13,49 GiB en riesgo) | centinela G3/G4 | midió ancestry real, pack real y divergencia | fail-closed: solo fast-forward, aborta si el commit falla, lease renovado por intento (D-150/D-154) | ✅ **resuelto — salvó `main` 2 veces** |
| G-18 | **N2 con `--no-thin`** no podía respetar `max_pack_gib` | centinela G6 | `.git` = 10,66 GiB; el pack completo no cabe | sin `--no-thin` (pack thin) + lease verificado (D-151) | ✅ resuelto |
| G-19 | **N5 con dirección invertida** y push destructivo sin abortar | centinela G5 | `main-clean` divergente | aborta si la ancestría falla (D-152) | ✅ resuelto |
| G-20 | **C1 daba verde falso** (diff commit→working tree vacío) | centinela G7 | medido: commit→commit ≠ commit→worktree | diff commit→commit + digest del input block comparado (D-153) | ✅ resuelto |
| G-21 | **N3 es un stub** que no implementa sus checks | centinela G8 | `CommitOperationAdd(path_in_repo=…, path_or_fileobj=…)` usa argumentos inexistentes en la API de HF | delegar en `ops/j9_remirror.py` (que sí tiene el gate D-148) | 🔴 **ABIERTO — fix antes de ejecutar N3** |
| G-22 | `git commit` se colgaba 9+ min (recorre 435.000 ficheros en NFS) | yo, midiendo | `git commit` > 9 min sin salida | `commit-tree` index-only (D-155) | ✅ resuelto |

## 1.5 Verificación de ausencia de daño

| Comprobación | Resultado | Quién |
|---|---|---|
| `main` con 435.923 ficheros | ✅ | centinela |
| 3 anclas de rollback en sus shas (2 tags + 1 rama) | ✅ | centinela |
| parche D-145 sin `read-tree`/`rm --cached`/push al Space | ✅ | centinela |
| Space con 8 ficheros operativos, RUNNING, `/health` 200 | ✅ | centinela |
| hashes del contrato (3 con baseline) | ✅ idénticos | centinela |
| tokens literales en `main` o en el Dataset | ✅ **0** (solo por cabecera) | centinela |
| ficheros destruidos / pérdida de datos | ✅ **ninguna** (366.077 recuperados) | yo |
| DAG: schema, 1:1, input block verbatim, 0 violaciones | ✅ | C1 (automático) |

---

# PARTE 2 — HANDOFF

## 2.1 Estado en una frase

El repo, el Dataset, el Space y los 14 jobs con evidencia están **íntegros**. La fase ejecutable del DAG de cierre (N0 → C1 → N1 → N2) está **PASS** y auditada. Quedan **3 nodos gateados por el owner** (N3 rebuild, N4 auditoría final, N5 fast-forward) y **3 decisiones**.

## 2.2 Dónde está todo (para continuar sin contexto)

| Qué | Dónde |
|---|---|
| Clon de trabajo | `/workspace/work/repo-live` (rama `main`, índice alineado, 435.923 ficheros) |
| Motores del DAG | `/workspace/work/repo-live/ops/dag/` (8 ficheros) |
| Input block + dag + schema | `/workspace/work/repo-live/{input_block_verbatim.yaml,dag.json,dsl.schema.json}` |
| Salidas del DAG | `/workspace/work/repo-live/out/{N0,N1,N2,C1}/` + `out/audit_trace.json` |
| Grafo cacheado | `/workspace/work/out/graph_cache.json` (283 MB) |
| Baseline regenerado | `/workspace/work/baseline_new.json` (65.914 entradas) |
| Trazabilidad previa | `/workspace/output/TRAZABILIDAD-GAPS-CIERRE-20261107.md` (publicada en GitHub + Dataset) |
| Paquetes de auditoría | `/workspace/work/output/` (7 paquetes) |
| Logs | `/workspace/work/{j9_final,regen2,wiring_check,remirror_push,n1b,n2,c1}.log` |
| Evidencia en Dataset | `20261104-kernel01/` (jobs) y `20261107-cierre/audit/` (DAG) |

## 2.3 Cómo continuar (3 comandos, en orden)

```bash
cd /workspace/work/repo-live
export RUN_ID="20261107-cierre" GH_REPO="maxbry123-commits/router-universal-router-inteligente-" \
       DATASET_REPO="COMAND-CENTER-1/router-universal-router-inteligente-auditoria" \
       SPACE_REPO="COMAND-CENTER-1/riu-router" HF_TOKEN="${HF_TOKEN_1_NEW}" \
       GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0="http.https://github.com/.extraheader"
export GIT_CONFIG_VALUE_0="AUTHORIZATION: basic $(printf 'x-access-token:%s' "$GH_TOKEN" | base64 -w0)"

# 1) reconstruir la traza tras cada nodo gateado
python ops/dag/build_trace.py

# 2) N3 -> rebuild del Space (SOLO con orden del owner)
export OWNER_GATE=APPROVE_N3 && python ops/dag/n3_rebuild_space.py && unset OWNER_GATE

# 3) N4 -> auditoria final (SOLO con orden del owner)
export OWNER_GATE=APPROVE_N4 && python ops/dag/n4_final_audit.py && unset OWNER_GATE

# 4) N5 -> fast-forward (SOLO con orden del owner)
export OWNER_GATE=APPROVE_N5 && python ops/dag/n5_fast_forward.py && unset OWNER_GATE
```

**Reglas que no se negocian:**
- El lease se lee **siempre** con `git ls-remote` en el instante del push (otros agentes publican en `main`).
- Nada se publica como fast-forward si el remoto no es ancestro → aborta (D-150).
- Nada toca el Space salvo N3, y solo vía API de HF (nunca push de árbol).
- Los secretos solo por entorno; nunca en argv, URL ni logs.

## 2.4 Reiniciar desde el Dataset (si el clon se pierde)

```bash
git clone --depth 1 --branch main https://github.com/maxbry123-commits/router-universal-router-inteligente-.git
# evidencia:
hf_hub_download(repo_id="COMAND-CENTER-1/router-universal-router-inteligente-auditoria",
                repo_type="dataset", filename="20261104-kernel01/j9_remirror/result.json")
```

## 2.5 Estado por nodo del DAG maestro (§5 de la guía)

| Nodo | Job | Gate | Estado |
|---|---|---|---|
| S0_capture | sha256 + kernel validate | `kernel_valid` | ✅ |
| S1_j0 | `j0_preflight` | env, disco ≥30 GB, remoto, git ≥2.31, HF whoami, dataset escribible | ✅ PASS |
| S2_parallel | `j1_inventory`, `j2_graph`, `j3_history` | cada `result.json` PASS | ✅ 3/3 PASS |
| S3_j4 | `j4_plan` | plan sha256, protegidos fuera del plan, cuarentena ≤40 % | ✅ PASS |
| S5_j5 | `j5_apply` | tag, no_new_unresolved, entrypoints, TEST rc=0, rama | ✅ PASS |
| S6_agent | roadmap R1..R4 | wiring_check tras cada lote, 3 revisiones visuales | ✅ |
| S7_j7 | `j7_mirror` | wiring_check, space_RUNNING, health_commit==HEAD | ✅ PASS |
| S8_j8 | `j8_audit` | all_jobs_PASS, wiring_check_on_branch | ✅ PASS |
| S10_j6 | `j6_rewrite` | bundle, purga, wiring_check, pushed main-clean | ✅ PASS **con flag** (G-08) |
| **S12_final** | `j9_remirror`, `j10_final_audit` | **Space==new HEAD, audit PASS** | 🔴 **PENDIENTE** |

---

# PARTE 3 — QUÉ FALTA Y POR QUÉ

## 3.1 Los 5 pasos que cierran el plan

### Paso 1 — Arreglar el motor N3 (G-21) — 10 min

**Por qué:** el motor tal como está escrito **no puede funcionar**. `CommitOperationAdd(path_in_repo=…, path_or_fileobj=…)` usa argumentos que la API de HF no acepta (la firma real es `path` + `content`), y no implementa sus tres checks declarados ni `accept.rebuild_ok_requires`.

**Qué hacer:** que N3 delegue en `ops/j9_remirror.py`, que ya tiene el gate duro D-148 (`space_has_operational_files` → aborta si falta `boot.sh`/`Dockerfile`/`proxy.py`/`openclaw.sh`/`swecode_provider.json`), el disparador del rebuild por API y la verificación `space_RUNNING` + `health_commit_equals_new_HEAD`. Commit **rotulado y separado**: `fix de bug del DAG vN (n3_rebuild_space)`.

**Riesgo controlado:** el rebuild del Space re-clona GitHub `main` en cada build. Preflight ya verificado: `router-mvp/mvp` es symlink → `../chat-router/chat/backend/mvp` ✅ · `run.py`/`app.py`/`requirements.txt` existen ✅ · `chat-router/SWE CODE/web-bridge` ✅ · `chat-router/SWE CODE free/puente-movil/server.js` ✅. Si el Space no levanta, se revierte el `.rebuild` y el Space vuelve a su commit actual (`4722f1dffc`).

### Paso 2 — Ejecutar N3 con `OWNER_GATE=APPROVE_N3` — 15–25 min

Dispara el rebuild, espera a `stage=RUNNING` y comprueba que `/health` devuelve el sha de `main`. **Cierra N6.**

### Paso 3 — Ejecutar N4 con `OWNER_GATE=APPROVE_N4` — 5–10 min

`j10_final_audit` con `AUDIT_JOBS` = los 14 jobs + `j10_final_audit`. Sube `final_audit.json` + `result.json` al Dataset → **14/15 con evidencia y `j10` PASS**. **Cierra N7.**

> Nota: `j10_final_audit` recalcula el grafo de cableado (660 s). Se le puede pasar `GRAPH_CACHE=/workspace/work/out/graph_cache.json` para reutilizarlo (D-149).

### Paso 4 — Cierra N8, N9 y N10 — 30 min

- **N8**: ejecutar sondas de inferencia real contra el Space (MCP 14 tools + `/health`). Promover a `active` **solo** las conexiones que cumplan las 7 condiciones del owner (autenticación válida, conexión real, inferencia ejecutada, respuesta válida, latencia registrada, sin errores críticos, nada superficial). El resto queda en `pending_audit` **con su evidencia** en `connections/registry.yaml` y `connections/wiring_changelog.md`.
- **N9**: `connections/wiring_changelog.md` + `connections/wiring_history.jsonl` (12.344.585 B, sha `d087146d…88d0`) + `README.md` (4.807 B) + los 5 handoffs de área en `handoff/docs/` → **ya publicados**, solo falta marcar el nodo.
- **N10**: `kernel/KERNEL.yaml` con los 11 nodos, `progress_pct = 100 × CLOSED/11`, `handoff.next` vacío, `kernel/LEDGER.jsonl` con las últimas mutaciones (swap, bridge, remirror, auditoría, README, DAG) y `memory_agente_minimax_02.md` al día.

### Paso 5 — Segunda pasada del centinela y cierre — 10 min

Relanzar el centinela sobre el estado final → veredicto PASS/VETO → `audit_trace.json` regenerado → subido al Dataset → `DONE`.

## 3.2 Decisiones que necesita el owner

| # | Decisión | Opciones | Efecto |
|---|---|---|---|
| **D-a** | GAP-8 — purga del historial de `main` | (a) queda `CERRADO_CON_FLAG` y se documenta · (b) rebase de los commits con pack > 2 GiB · (c) repo nuevo | (a) no bloquea el cierre; (b)/(c) son días de trabajo |
| **D-b** | GAP-10 — 16 conexiones sin inferencia real | (a) se acepta `pending_audit` con evidencia · (b) se exige inferencia real por conexión | (a) N8 cierra hoy; (b) N8 depende de sondas |
| **D-c** | GAP-14 — gate de secretos | (a) los fixtures de tests de terceros quedan excluidos del gate · (b) se escanean también | (a) el gate refleja el riesgo real |
| **D-d** | N3/N4/N5 | `OWNER_GATE=APPROVE_N3` / `APPROVE_N4` / `APPROVE_N5` | sin esto los 3 nodos quedan en pausa |

## 3.3 Riesgos que quedan vivos

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| El rebuild del Space no levanta con el árbol reordenado | baja (preflight verificado) | revertir `.rebuild`; el Space conserva `4722f1dffc` y sus 8 ficheros |
| Otros agentes mueven `main` durante el push | **alta** (9+ veces) | lease renovado por intento + reintento atómico (D-154); ya salvó `main` 2 veces |
| `j9_remirror` vuelve a fallar el gate | baja (baseline de 65.914 + caché publicados) | si falla, el `result.json` en el Dataset lo dirá; el fix está listo |
| El gate de cableado tarda 660 s por job | alta | `GRAPH_CACHE` ya publicado (D-149) |

---

# PARTE 4 — GUÍA Y DSL DAG DE LA REORGANIZACIÓN (resumen ejecutable)

## 4.1 El DSL DAG maestro (`kernel/GUIDE.md` §5, `schema: repo.kernel.dag/v1`)

```yaml
mode: FAIL_CLOSED
autonomy: {human_signature: NOT_REQUIRED, authorization: AUTO_BY_GATES}
forbidden_states: [WAITING_SIGNATURE, WAITING_AUTHORIZATION, ASK_USER]
silent: true
flag_symbol: 🚩
never: [stop_early, escalate, ask, explain_unless_blocked_out_of_scope]
parallel: {max: 3, only: independent_nodes, exclusive_files: true}
guardian: {pre: [authorized, in_scope, input_hash_intact, needs_PASS],
           post: [result.json PASS, diff_in_allowlist, wiring_check_ok]}
on_fail_routes_10: [existing_code, repo_docs, commit_history, official_docs, closed_issues,
                     stackoverflow, hf_forum, smaller_scope, alt_library, alt_architecture]
after_routes_exhausted: FLAG_AND_CONTINUE_INDEPENDENT

dag:
  S0_capture:  {do: [sha256 frozen_files, bind objective, validate kernel.py validate], gate: kernel_valid}
  S1_j0:       {job: j0_preflight, gate: [env, disk>=30GB, remote_reachable, git>=2.31, hf_whoami, dataset_writable]}
  S2_parallel: {jobs: [j1_inventory, j2_graph, j3_history], gate: [each result.json PASS]}
  S3_j4:       {job: j4_plan, gate: [plan_sha256, protected_not_in_plan, quarantine<=40%_of_code]}
  S5_j5:       {job: j5_apply, gate: [tag_pushed, no_new_unresolved, entrypoints_exist, TEST_CMD rc=0, branch_pushed]}
  S6_agent:    {do: [roadmap R1..R4], gate: [wiring_check_after_each_batch, 3_visual_reviews]}
  S7_j7:       {job: j7_mirror, gate: [wiring_check, space_RUNNING, health_commit==HEAD]}
  S8_j8:       {job: j8_audit, gate: [all_jobs_PASS, wiring_check_on_branch]}
  S10_j6:      {job: j6_rewrite, gate: [bundle_verified, purge_absent_from_history, wiring_check, pushed_main-clean]}
  S12_final:   {jobs: [j9_remirror, j10_final_audit], gate: [Space==new HEAD, audit PASS],
                then: kernel progress_pct=100, DONE}
  loop: until queue_empty (kernel.next == [])
  per_node_state: [PENDING, RESEARCHING, EXECUTING, VALIDATING, GAP, FIXING, RETESTING, STABLE, FLAGGED, CLOSED]
```

**Las 12 fases del contrato** (`yaiwes.node/v2`): `1 START_CAPTURE_LOCK · 2 CODE_INTELLIGENCE_XRAY · 3 RESEARCH_CONTEXT · 4 PLAN_QUEUE_EXECUTE · 5 REFACTOR_10X_NO_OVERENGINEERING · 6 BACKEND_FRONTEND_WIRING · 7 TESTS_VERIFICATION · 8 GOALS_QUEUE_TRACKING · 9 GAP_PERSISTENCE · 10 REFUTATIONS_AUDIT · 11 FAIL_CLOSED_DECISION_LOOP · 12 COMMIT_PUSH_DEPLOY_RELEASE`.

**Los 3 pasos obligatorios:** `RESEARCH → EXECUTE → VALIDATE` (exactamente 3, sin reordenar ni saltarse). El centinela es un agente paralelo de solo lectura con poder de veto; `on_veto` = revertir el nodo, probar la siguiente ruta del `gap_chain` y, agotadas las 10 rutas, `🚩 FLAG` y seguir.

## 4.2 El Input Block del cierre 20261107 (verbatim, inmutable)

- **Fichero:** `input_block_verbatim.yaml` · **sha256 `6c4383cbbb17d3f5257ff4c2c68cf5480068f2734aa2b05184176ca300a6e4d2`**
- **Dónde:** `https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/input_block_verbatim.yaml`
- **Claves:** `version 1.0` · `run_id 20261107-cierre` · `baseline_entries 65914` · `bundle_bytes 8068832804` · `owner_gates [N3, N4, N5]`
- **Forbidden:** force-push sin `--force-with-lease` · push a `main` (solo N5 con gate) · push de árbol al Space (solo rebuild por API) · modificar `ops/research_prepass.py` · crear Actions/LFS/despliegues nuevos · rotar o imprimir claves
- **Límites:** `max_pack_gib 1.5` · `max_nodes_parallel 2` · `max_retries_per_node 3`
- **Accept:** `push_ok_requires [rc=0, ls-remote == HEAD]` · `rebuild_ok_requires [stage==RUNNING, health.commit == main_sha]`

**El Input Block adjunto del owner** (`kernel/INPUT_BLOCK_YAIWES_CABLEADO.md`, sha `9d01a464…b90baa`) es la directiva de cableado: separación de raíces, 10 objetivos, umbral ACTIVE de 7 condiciones y plan de 12 fases. Va enganchado a la guía vía `kernel/GUIDE_tail.md`.

## 4.3 El DAG de cierre 20261107 (nodos y motores)

| Nodo | Tipo | `run` | Checks declarados |
|---|---|---|---|
| N0 | validate | `ops/dag/n0_validate.py` | `input_block_sha256_ok`, `dsl_schema_ok`, `remote_shas_read` |
| N1 | publish | `ops/dag/n1_publish_patches.py` | `files_exist`, `lease_read`, `push_rc0`, `remote_sha_matches` |
| N2 | push | `ops/dag/n2_push_main_clean.py` | `divergence_detected`, `pack_measured`, `chunks_under_limit`, `lease_renewed`, `remote_equals_head` |
| N3 | rebuild | `ops/dag/n3_rebuild_space.py` | `space_operational_files`, `rebuild_triggered`, `build_running` |
| N4 | audit | `ops/dag/n4_final_audit.py` | `14_jobs_present`, `all_pass_or_flagged` |
| N5 | fast_forward | `ops/dag/n5_fast_forward.py` | `main_clean_le_main`, `lease_read`, `ff_rc0`, `main_after_equals_main_clean` |
| C1 | centinela | `ops/dag/c1_centinela.py` | schema · 1:1 · input block verbatim · digest · violations |

**Correcciones de seguridad aplicadas a los motores** (el input block y el `dag.json` **no** se tocaron):

| Decisión | Cambio | Por qué (gap) |
|---|---|---|
| D-150 / D-154 | N1 solo publica como fast-forward; aborta si el commit falla; lease renovado por intento | G-17: podía reescribir `main` (5.601 commits / 13,49 GiB) |
| D-151 | N2 sin `--no-thin`; lease verificado en vez de tautología | G-18: el pack completo no cabe en 1,5 GiB |
| D-152 | N5 aborta si la ancestría falla | G-19: force-push destructivo sin abortar |
| D-153 | C1 diff commit→commit + digest del input block | G-20: verde falso |
| D-155 | N1 usa `commit-tree` index-only | G-22: `git commit` colgaba 9+ min en NFS |

**Restricciones verificadas por C1:** `no_overwrite: true` · `lease_required: true` · `owner_gates: [N3,N4,N5]` · `forbidden_paths: [ops/research_prepass.py, .github/workflows/*, kernel/KERNEL.yaml]`.

## 4.4 Umbral ACTIVE (7 condiciones del owner) para N8

1. Autenticación válida · 2. Conexión real · 3. Inferencia ejecutada · 4. Respuesta válida · 5. Latencia registrada · 6. Sin errores críticos · 7. Nada superficial.

Un `import` **no** prueba conexión; por eso 16 conexiones siguen en `pending_audit`.

## 4.5 Los 11 nodos del handoff (`kernel/KERNEL.yaml`)

`N0_reconciliar` · `N1_j7_baseline` · `N2_j8_audit_pre` · `N3_j6_rewrite` · `N4_swap_main` · `N5_bridge` · `N6_remirror` · `N7_auditoria_final` · `N8_cableado` · `N9_bitacora_readme` · `N10_cierre`
→ `progress_pct = 100 × CLOSED_NODES / 11` · **hoy 6 cerrados = 55 %** · el estado canónico vive en `kernel/KERNEL.yaml` (handoff) + el Dataset.

---

# PARTE 5 — ÍNDICE DE ARTEFACTOS DE ESTA SESIÓN

| Artefacto | Ruta local | Publicado en |
|---|---|---|
| Este documento | `/workspace/output/CIERRE-20261108-TRAZABILIDAD-Y-HANDOFF.md` | pendiente |
| Trazabilidad de gaps anterior | `/workspace/output/TRAZABILIDAD-GAPS-CIERRE-20261107.md` | GitHub `audit/gaps/` + Dataset `20261104-kernel01/audit/gaps/` |
| Resumen de gaps anterior | `/workspace/output/GAPS-PENDIENTES-CIERRE-20261107.md` | GitHub `audit/gaps/` + Dataset `20261104-kernel01/audit/gaps/` |
| `audit_trace.json` del DAG | `/workspace/work/repo-live/out/audit_trace.json` | Dataset `20261107-cierre/audit/` |
| Input block + dag + schema + 8 motores | `/workspace/work/repo-live/{input_block_verbatim.yaml,dag.json,dsl.schema.json,ops/dag/}` | GitHub `main` + Dataset `20261107-cierre/audit/gaps/` |
| Grafo cacheado | `/workspace/work/out/graph_cache.json` | no (local, 283 MB) |
| Baseline regenerado | `/workspace/work/baseline_new.json` | GitHub `main` (vía D-149b) |
| Bundle de rollback | — | Dataset `backups/20261104-kernel01.bundle` (8,07 GB) |
| Investigación (52 fuentes) | — | Dataset `20261104-kernel01/research/` |

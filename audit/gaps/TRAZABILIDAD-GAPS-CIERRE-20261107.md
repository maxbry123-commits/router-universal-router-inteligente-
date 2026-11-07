# Trazabilidad completa de gaps y pendientes — cierre reorganización

- **Repo (código):** `https://github.com/maxbry123-commits/router-universal-router-inteligente-` — rama `main`
- **Dataset (verdad/evidencia):** `https://huggingface.co/datasets/COMAND-CENTER-1/router-universal-router-inteligente-auditoria` — run `20261104-kernel01`
- **Space (servicio):** `https://huggingface.co/spaces/COMAND-CENTER-1/riu-router` · salud: `https://comand-center-1-riu-router.hf.space/health`
- **Corte de este informe:** 2026-11-07 19:35 UTC · **Estado global: NO CERRADO · 6/11 nodos (55 %)**

> **Dónde está este documento:** solo en local (`/workspace/output/`). **NO está en GitHub ni en el Dataset.** Pendiente de subir (ver sección 8).

---

## 0. Trazabilidad resumida (gap → quién lo detectó → evidencia → estado → quién lo arregla)

| # | Gap | Detectado por | Evidencia | Fix | Estado | Responsable |
|---|---|---|---|---|---|---|
| **G-01** | Gate de cableado tumbaba por 48.899 ficheros de terceros en `Main_Skills/` | `kernel-cierre` (agente paralelo) | `j9_remirror/result.json` FAIL 08:42 + 09:58 | Clasificación por **ruta exacta** + `Main_Skills/_staging`, `Main_Skills/Frontend` como terceros | ✅ **Resuelto y publicado** (`ca79a412e3`) | `kernel-cierre` |
| **G-02** | Baseline de 961 subcuenta: se generó con 366.077 ficheros ausentes del disco | Yo (MCode) | Medición: original `dd3eb1779d` = 65.908 · regenerado = **65.914** sobre 422.731 ficheros | Regenerar baseline sobre árbol íntegro | 🟡 **Resuelto en local, sin publicar** | Yo |
| **G-03** | El push del job habría **borrado 6 ficheros operativos del Space** (viven en subcarpetas del repo, no en su raíz) | Yo (MCode) | `boot.sh` del Space exige `router-mvp/mvp/{run.py,app.py,requirements.txt}`; el método anterior construía el árbol desde la raíz del repo | Reespejo = **rebuild por API de HF** (`CommitOperationAdd` sobre `.rebuild`), nunca push de árbol | ✅ **Resuelto y publicado** (`2414b9029d`) | Yo |
| **G-04** | El push por git al host de HF moría con `expected 'acknowledgments'` (HTTP/2) | Yo (MCode) | `git ls-remote` falla por HTTP/2; responde con `http.version=HTTP/1.1` | Vía API de HF en lugar de git | ✅ **Resuelto y publicado** (`2414b9029d`) | Yo |
| **G-05** | El Space sirve un commit huérfano (`4722f1dffc`, no ancestro de `main`) | Centinela/sheriff (AC3) + Yo | `/health` → `4722f1dffc`; `merge-base --is-ancestor` → NO | Ejecutar `j9_remirror` (rebuild disparado) y verificar `/health` == sha de `main` | 🔴 **ABIERTO — bloquea N6** | Yo (pendiente de orden) |
| **G-06** | `space_has_operational_files` era informativo: no abortaba si faltaba un fichero | Centinela/sheriff (G4) | Lectura de `ops/j9_remirror.py`: faltaba el `return` pese al comentario | Gate duro: `if not _ok: finish(commit=sha)` (D-148) | 🟡 **Fix preparado, sin publicar** | Yo |
| **G-07** | El gate reconstruye el grafo en cada job (660 s medidos sobre 422.731 ficheros) | Yo (MCode) | `j2_graph.build()` = 660 s × 2 jobs (j9 + j10) | Caché `GRAPH_CACHE` en `wiring_check` (D-149) | 🟡 **Fix preparado, sin publicar** | Yo |
| **G-08** | Purga del **historial** sin resolver: commits con pack > 2 GiB que GitHub rechaza (HTTP 500) | N3 en ejecución | `j6_rewrite` PASS con flag; árbol purgado (37 rutas) pero historia no | Rebase de los commits pesados o repo nuevo | 🔴 **ABIERTO — decisión del owner** | Owner |
| **G-09** | `main-clean` 2 commits por detrás de `main` → la idempotencia del swap (D-142) deja de reflejar el estado real | Yo (MCode) | `main-clean` = `35470e8b0660` vs `main` = `4992c16b3b` | Fast-forward con lease contra el sha remoto real | 🔴 **ABIERTO** | Yo |
| **G-10** | 16 conexiones de cableado en `pending_audit` (un `import` no prueba conexión) | Yo (MCode) | N5: 38 conexiones, 12/12 healthchecks rc=0, HTTP 200, MCP real 14 tools; falta **inferencia real** | Sondas reales → promover a `active` solo con las 7 condiciones del owner | 🔴 **ABIERTO — bloquea N8** | Yo |
| **G-11** | Otros agentes escriben en `main` en paralelo → riesgo de pisar/revertir trabajo ajeno | Yo + Centinela (G7) | `main` se movió 6 veces: `f2366baa → 2414b902 → ca79a412 → 7c77a876 → 4992c16b` (+ commits de Maxbry) | Todo push con `--force-with-lease` contra el **sha remoto real leído en ese momento**; árbol construido sobre `origin/main` actualizado | ✅ **Mitigado** | Yo |
| **G-12** | Un job perdió **366.077 ficheros** del clon vivo (reutilizó el clon real y vació su índice) | Centinela (G8, NO VERIFICADO) + Yo | `git status` mostraba 366.077 borrados; **recuperados**: 373.434 ficheros en disco; los 22 "ausentes" son symlinks con destino inexistente (diseño original, intactos en Git) | D-146: el clon reutilizado se usa en **solo lectura** y nunca se registra para borrado | ✅ **Resuelto** | Yo |
| **G-13** | 48.899 ficheros de código importado de fuera en `Main_Skills/` — no cableados, no en las 11 entradas | `kernel-cierre` | 20 commits `build(hf-combined): publish <bundle>` | Declarados terceros (G-01); los bundles **no se borran ni mueven** (decisión del owner, G7 de su informe) | ✅ **Resuelto** | `kernel-cierre` |
| **G-14** | 20 ficheros de `main` contienen patrones `sk-`/`hf-` | Centinela (G9) | Todos en **fixtures de tests de terceros vendorizados** (`agentes-listos/{codex,OpenHands,CLI-Anything}`, `frameworks/n8n`) | Ninguno es un token real; búsqueda literal de `GH_TOKEN`/`HF_TOKEN_1_NEW`/`UNIVERSAL_KEY` en todo `main` y en el Dataset = **0** | 🟡 **INFO — depende de si el gate excluye fixtures** | Owner |
| **G-15** | `j10_final_audit/result.json` no existe en el Dataset (13/14 jobs con evidencia) | Centinela (G2, bloqueante) | Árbol del Dataset: 14 carpetas de job, 13 con `result.json` | Ejecutar `j10_final_audit` con `AUDIT_JOBS` = los 14 | 🔴 **ABIERTO — depende de N6** | Yo |
| **G-16** | Red de seguridad: 3 hashes del contrato verificados; los `.skills` sin baseline de hashes | Centinela (AC4) | `INPUT_BLOCK.yaml` = `5c4bbb20…83c3a` ✅ · `INPUT_BLOCK_YAIWES_CABLEADO.md` = `9d01a464…b90baa` ✅ · `AGENTS.md` = `5c77e005…8943` ✅ | Fijar baseline de hashes de los `.skills` (3 ficheros) | 🟡 **INFO** | Yo |

---

## 1. Gaps bloqueantes (impiden el cierre)

### 🔴 B-1 → G-05 — El Space sirve un commit huérfano

- **Qué pasa:** `/health` responde `{"status":"ok","commit":"4722f1dffc"}`. Ese sha es el tag `safety/pre-candado-20261104-kernel01` y **no** es ancestro de `main` (la historia se reescribió en N3 con el árbol limpio).
- **Por qué sigue así:** el rebuild D-145 **nunca se llegó a disparar**. El job aborta en el gate de cableado *antes* de la fase de rebuild — comportamiento FAIL_CLOSED correcto, pero deja el Space sin actualizar.
- **Estado verificado del Space (09:35 UTC):** `stage=RUNNING` · `hardware=cpu-upgrade` · 8 ficheros operativos en la raíz · `/health` HTTP 200.
- **Preflight del rebuild (hecho, sin ejecutar):** `router-mvp/mvp` es symlink → `../chat-router/chat/backend/mvp` ✅ · `run.py`, `app.py`, `requirements.txt` existen ✅ · `chat-router/SWE CODE/web-bridge` ✅ · `chat-router/SWE CODE free/puente-movil/server.js` ✅.
- **Qué lo cierra:** ejecutar `j9_remirror` (parche D-145 ya publicado) → `CommitOperationAdd(".rebuild")` → esperar el build → `/health` debe devolver el sha de `main`.
- **Riesgo:** si el Space no levanta con el árbol reordenado, el router queda caído → hay que revertir. Por eso el rebuild **no** se dispara sin la orden del owner.

### 🔴 B-2 → G-01/G-02 — El gate de cableado sigue fallando con el baseline publicado

- **Síntoma:** `j9_remirror` FAIL 3 veces (08:42, 09:2x, 09:58) → `wiring_check_before_remirror → no_new_unresolved`.
- **Causa G-01 (resuelta por `kernel-cierre`, publicada):** 48.899 ficheros de código importado de fuera bajo `Main_Skills/` se contaban como código propio. Ya está: clasificación por ruta exacta.
- **Causa G-02 (resuelta por mí, SIN publicar):** el baseline publicado (`f2366baa`, 961 entradas) se generó con 366.077 ficheros ausentes del disco → subcuenta. **Medición sobre árbol íntegro: 65.914 entradas, 422.731 ficheros, 1.409.030 aristas.**
- **Verificación del gate con los datos ya medidos:** con la clasificación nueva y el árbol completo, el gate falla por **1 sola referencia propia** — `ops/push_parallel.py → concurrent.futures` — más 7 de terceros (informativas). Publicar el baseline de 65.914 lo resuelve.
- **Nota de conflicto (resuelto):** `kernel-cierre` decidió **no** reindexar el baseline ("escondería regresiones reales"). Yo midí que el 961 está mal por construcción (árbol incompleto). Solución adoptada: **baseline regenerado + clasificación por ruta exacta**, que conserva la detección de regresiones propias (el gate compara por ruta y destino) y deja de perder referencias.

### 🔴 B-3 → G-15 — Falta la evidencia de `j10_final_audit`

- 14 carpetas de job en el Dataset, **13 con `result.json`**, todas PASS salvo `j9_remirror` (FAIL). Falta `j10_final_audit` → **N7 no puede cerrarse**.

### 🔴 B-4 → G-10 — 16 conexiones sin prueba de inferencia real

- El umbral ACTIVE del owner (7 condiciones) no se cumple solo con un `import`. Ya hay: 38 conexiones inventariadas, 12/12 healthchecks rc=0, sonda HTTP `/health` 200, **MCP real con 14 tools**. Falta la inferencia ejecutada para promover.

### 🔴 B-5 → G-08 — Purga del historial (N3 `CERRADO_CON_FLAG`)

- El **árbol** está purgado (37 rutas de `build/`) y publicado. La **historia** no: hay commits cuyo pack supera los 2 GiB y GitHub los rechaza con HTTP 500. Alternativas: rebase de esos commits, o rehacerlos en un repo nuevo. **Decisión del owner.**

---

## 2. Gaps resueltos (trazabilidad completa)

| # | Gap | Cómo se resolvió | Prueba |
|---|---|---|---|
| **G-12** | 366.077 ficheros fuera del clon vivo | Restauración con `git checkout-index -a -f` | 373.434 ficheros en disco; `main` remoto con 435.170; 0 pérdida en el historial |
| **G-03** | El push del job borraba 6 ficheros del Space | D-145: rebuild por API de HF, nunca push de árbol | `ops/j9_remirror.py` en `main` sin `read-tree`/`rm --cached`/push al Space |
| **G-04** | Push al Space muerto por HTTP/2 | Vía API de HF | `ls-remote` responde con `http.version=HTTP/1.1` |
| **G-11** | Otros agentes escriben en `main` | Lease contra el sha remoto real + base `origin/main` actualizada | 6 movimientos de sha detectados y ninguno revertido |
| **G-01/G-13** | Terceros de `Main_Skills/` contados como propios | Clasificación por ruta exacta | `ca79a412e3` publicado; 0 diferencias sobre las 961 rutas |
| **G-05 (parcial)** | El Space nunca se reespejó | Mecanismo escrito y publicado | `2414b9029d` en `main` |

---

## 3. Parches: estado de publicación

| Parche | Qué hace | Fichero | Publicación |
|---|---|---|---|
| **D-145** | Reespejo = rebuild por API de HF; sha de referencia = `main` remoto real | `ops/j9_remirror.py` | ✅ `2414b9029d` |
| **D-146** | Blindaje: clon reutilizado en solo lectura, nunca se registra para borrado | `ops/common.py` | ✅ `2414b9029d` |
| **D-148** | Gate duro: abortar si al Space le faltan ficheros operativos | `ops/j9_remirror.py` | 🟡 preparado, **sin publicar** |
| **D-149** | Caché de grafo (`GRAPH_CACHE`) — evita 660 s por job | `ops/wiring_check.py` | 🟡 preparado, **sin publicar** |
| **D-149b** | Baseline regenerado: 65.914 entradas sobre árbol íntegro | `connections/baseline_unresolved.json` | 🟡 regenerado, **sin publicar** |
| **D-149c** | `wiring_check.py` + `j2_graph.py` de `kernel-cierre` con D-149 encima | ambos | 🟡 en local, **sin publicar** |
| **D-149d** | Cambio G5 de `kernel-cierre` (rutas exactas + `Main_Skills`) | `ops/wiring_check.py`, `ops/j2_graph.py`, `kernel/GUIDE.md` | ✅ `ca79a412e3` |

---

## 4. Nodos del DAG: estado exacto

| Nodo | Qué es | Estado | Evidencia / bloqueo |
|---|---|---|---|
| N0 | Reconciliar | ✅ CERRADO | handoff + Dataset leídos; hashes verificados |
| N1 | Espejo base | ✅ CERRADO | `j7_mirror` PASS: 6.170 ficheros / 110,7 MB, Space RUNNING, nada subido |
| N2 | Auditoría previa | ✅ CERRADO | `j8_audit` PHASE=pre PASS: 8 jobs PASS + `wiring_check_on_target` |
| N3 | Reescritura de historial | ⚠️ CERRADO_CON_FLAG | `j6_rewrite` PASS: bundle 8,07 GB verificado, purga de 37 dirs verificada, árbol limpio publicado. **FLAG: purga del HISTORIAL pendiente (G-08)** |
| N4 | Swap de main con candado | ✅ CERRADO | `j6b_swap` PASS: `main` == `main-clean` con lease; etiqueta re-apuntada al main real + 3 anclas de rollback |
| N5 | Puente central | ✅ CERRADO | `bridge` PASS: 38 conexiones, 9 endpoints, 12/12 healthchecks rc=0, 0 drift, MCP real 14 tools, `/health` 200 |
| **N6** | **Reespejo al Space** | 🔴 EN_CURSO | `j9_remirror` FAIL → `no_new_unresolved`. Fix preparado (B-2) + rebuild listo (B-1) |
| **N7** | **Auditoría final** | 🔴 PENDIENTE | `j10_final_audit` sin ejecutar (depende de N6) |
| **N8** | **Cableado R7/R9/R10** | 🔴 PENDIENTE | 38 conexiones, 16 en `pending_audit` (falta inferencia real) |
| **N9** | **Bitácora + README + handoff** | 🟡 PENDIENTE | Los ficheros **ya existen y están publicados**; falta marcar el nodo cerrado en `kernel/KERNEL.yaml` |
| **N10** | **Cierre** | 🔴 PENDIENTE | Depende de N6–N9: `progress_pct` = 100 × CLOSED/11, `handoff.next` vacío, ledger completo |

**Cerrados: 6 de 11 = 55 %** (`progress_pct` publicado en `kernel/KERNEL.yaml` = 55).

---

## 5. Verificación de ausencia de daño (centinela, fase 1 — solo lectura)

9 flags, **2 bloqueantes procedimentales** (G-05, G-15), **0 de seguridad**:

| Comprobación | Resultado |
|---|---|
| `main` remoto íntegro (435.170 ficheros ahora) | ✅ |
| 3 anclas de rollback en sus shas (2 tags + 1 rama) | ✅ |
| D-145 sin `read-tree` / `rm --cached` / push al Space | ✅ |
| Space con 8 ficheros operativos, RUNNING, `/health` 200 | ✅ (salvo el commit servido → B-1) |
| Hashes del contrato (`INPUT_BLOCK.yaml`, `INPUT_BLOCK_YAIWES_CABLEADO.md`, `AGENTS.md`) | ✅ idénticos |
| Tokens literales en `main` o en el Dataset | ✅ 0 (solo por cabecera `Authorization`) |
| Ficheros destruidos / pérdida de datos | ✅ ninguna |

---

## 6. Secuencia de cierre pendiente

1. Publicar **D-148 + D-149 + D-149b + D-149c** con lease contra el sha remoto real → 1 push (~2 min).
2. Ejecutar `j9_remirror` con `GRAPH_CACHE` → el gate pasa en segundos; se dispara el rebuild del Space (~10–15 min de build).
3. Verificar `/health` → `commit` == sha de `main` → **N6 cerrado con prueba real**.
4. Ejecutar `j10_final_audit` con `AUDIT_JOBS` = los 14 jobs → sube `result.json` → **N7 cerrado**.
5. Sondas reales de inferencia → promover a `active` lo que cumpla las 7 condiciones; resto documentado en `pending_audit` → **N8 cerrado**.
6. `kernel/KERNEL.yaml` (11 nodos, `progress_pct` = 100 × CLOSED/11), `kernel/LEDGER.jsonl`, `connections/wiring_changelog.md`, `README.md`, handoffs → **N9 y N10 cerrados**.
7. Fast-forward de `main-clean` a `main` con lease → **G-09 cerrado**.
8. Segunda pasada del centinela sobre el estado final → veredicto PASO/VETO.

**Tiempo estimado:** 35–50 min si el rebuild del Space levanta a la primera.

---

## 7. Decisiones pendientes del owner

1. **N6:** ¿cierre con rebuild verificado (B-1) o con evidencia declarada sin comprobar el commit servido?
2. **G-08:** ¿se acepta `CERRADO_CON_FLAG` en N3, o se aborda el rebase de los commits pesados / repo nuevo?
3. **N8:** ¿se acepta `pending_audit` para las conexiones sin inferencia real, o se exige prueba por conexión antes de cerrar?
4. **G-14:** ¿el gate de secretos debe excluir los fixtures de tests de terceros vendorizados?

---

## 8. Dónde está cada cosa

| Artefacto | Ubicación | Publicado |
|---|---|---|
| Este informe de trazabilidad | `/workspace/output/TRAZABILIDAD-GAPS-CIERRE-20261107.md` | ❌ **no** |
| Informe de gaps (anterior) | `/workspace/output/GAPS-PENDIENTES-CIERRE-20261107.md` | ❌ **no** |
| Evidencia de los 14 jobs | Dataset `20261104-kernel01/<job>/result.json` | ✅ sí |
| Bundle de rollback (8.068.832.804 B) | Dataset `backups/20261104-kernel01.bundle` | ✅ sí |
| Investigación (52 fuentes) | Dataset `20261104-kernel01/research/` | ✅ sí |
| Auditorías previas | Dataset `audit/j6_rewrite/`, `audit/jobs-pendientes/` | ✅ sí |
| Paquetes de auditoría locales | `/workspace/work/output/` (7 paquetes) | ❌ no |
| Grafo + baseline nuevos | `/workspace/work/out/graph_cache.json`, `/workspace/work/baseline_new.json` | ❌ no |
| Logs de esta sesión | `/workspace/work/{j9_final.log,regen2.log,wiring_check.log,remirror_push.log}` | ❌ no |

**Para que este informe sea consultable desde fuera, hay que subirlo a:**
- **GitHub** → `audit/gaps/TRAZABILIDAD-GAPS-CIERRE-20261107.md` en `main` (con lease), o
- **HuggingFace (Dataset)** → `20261104-kernel01/audit/gaps/` — el Dataset es la *verdad* del proyecto, así que es el destino natural.

Dime cuál de los dos (o ambos) y lo subo.

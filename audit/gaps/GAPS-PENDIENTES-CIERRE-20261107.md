# Lo que falta y gaps pendientes — cierre reorganización

- **Repo:** `maxbry123-commits/router-universal-router-inteligente-` (público)
- **Space:** `COMAND-CENTER-1/riu-router` (RUNNING, cpu-upgrade)
- **Dataset (verdad):** `COMAND-CENTER-1/router-universal-router-inteligente-auditoria`, run `20261104-kernel01`
- **Fecha del corte:** 2026-11-07 09:58 UTC
- **Estado:** **NO CERRADO.** 6 de 11 nodos cerrados (55 %). Faltan N6, N7, N8, N9, N10.

---

## 1. Resumen en una línea

El repo, el clon local, el Space y la evidencia de 13 de 14 jobs están **íntegros y verificados**. Lo que falta son **5 nodos**, y **2 de ellos (N6 y N7) están atascados por un único gate** (`no_new_unresolved` del job `j9_remirror`) que **ya tiene la causa diagnosticada y la corrección preparada, pero no publicada**.

---

## 2. Los 5 nodos que faltan

| Nodo | Qué es | Estado real | Qué lo bloquea |
|---|---|---|---|
| **N6** | Reespejo: que el Space sirva el `main` nuevo | EN_CURSO | Gate `wiring_check_before_remirror → no_new_unresolved`. La causa está corregida en local, **sin publicar**. |
| **N7** | Auditoría final (`j10_final_audit`) | PENDIENTE | Depende de N6. `j10_final_audit/result.json` **no existe** en el Dataset (13/14 jobs con evidencia). |
| **N8** | Cableado R7/R9/R10 con sonda real | PENDIENTE | Las 38 conexiones siguen en `pending_audit`. Falta la prueba de inferencia real para promover a `active` (umbral de 7 condiciones). |
| **N9** | Bitácora central + README + handoff | PENDIENTE | Los ficheros **ya existen y están publicados** (`wiring_changelog.md`, `wiring_history.jsonl`, `README.md`, `CODE_INDEX.md`, `SYSTEM_WIRING_REGISTRY.yaml`, 5 handoffs). Solo falta marcar el nodo como cerrado en `kernel/KERNEL.yaml`. |
| **N10** | Cierre: `progress_pct` 100 + ledger completo | PENDIENTE | Depende de N6–N9. Requiere `handoff.next` vacío y las últimas mutaciones en `kernel/LEDGER.jsonl`. |

---

## 3. Gaps pendientes (detalle con causa y estado)

### GAP-1 — BLOQUEANTE — El gate de cableado falla por una clasificación de código de terceros *(causa ya resuelta por otro agente, pendiente de efecto)*

- **Síntoma:** `j9_remirror` FAIL → `wiring_check_before_remirror → no_new_unresolved`. Ocurrió 3 veces: 08:42, 09:58 y el intento de las 09:2x.
- **Causa real (diagnosticada con medición, no estimación):** entre el baseline publicado y el fallo llegaron 20 commits `build(hf-combined): publish <bundle> and extracted tree` que añadieron **48.899 ficheros de código importado de fuera** bajo `Main_Skills/_staging/` y `Main_Skills/Frontend/`. Esos ficheros no están cableados y sus referencias relativas sin resolver se contabilizaban como **código propio**, con lo que el gate tumbaba.
- **Corrección aplicada por `kernel-cierre` (ya en `main`, commit `ca79a412e3`):** comparación por **ruta exacta** de las raíces de terceros en vez de subcadena, y declaración de `Main_Skills/_staging` y `Main_Skills/Frontend` como terceros. Verificado: 0 diferencias de clasificación sobre las 961 rutas del baseline; `ops/agentes-listos.txt` y `xagentes-listos/` pasan a ser **propios** (correcto).
- **Lo que queda:** publicar el **baseline regenerado** y volver a ejecutar `j9_remirror` con él.

### GAP-2 — BLOQUEANTE — El baseline de cableado estaba mal generado (subcuenta)

- **Síntoma:** el baseline publicado (`f2366baa`) tenía **961** referencias sin resolver.
- **Causa real:** se generó con **366.077 ficheros ausentes del disco** (el incidente del clon reutilizado), así que el grafo se construyó sobre un árbol incompleto y **subcuenta** las referencias. El baseline original (`dd3eb1779d`) tenía 65.908; el valor real sobre árbol íntegro es **65.914**.
- **Medición nueva (09:49 UTC, árbol completo):** `nodos=422.731 · aristas=1.409.030 · sin_resolver=65.914` en 660 s.
- **Estado:** regenerado y verificado en local (`8.751.014 B`, 65.914 entradas). **Sin publicar** — el commit se hizo sobre un `main` que luego movió otro agente, así que se rehace con lease contra el sha remoto real.

### GAP-3 — El reespejo del Space nunca se ejecutó por la vía correcta

- **Síntoma:** el `j9_remirror` original empuja al Space un árbol derivado del repo. El `boot.sh` del Space exige `router-mvp/mvp/{run.py,app.py,requirements.txt}`, pero en el repo esos ficheros viven en **subcarpetas**, no en la raíz → ese push habría **borrado 6 ficheros operativos del Space** (`proxy.py`, `boot.sh`, `openclaw.sh`, `Dockerfile`, `swecode_provider.json`, `README.md`) y el router no habría arrancado.
- **Causa real:** el Space **no es un espejo del repo**. Su `boot.sh` hace `git clone --depth 1 --filter=blob:none --branch main` de GitHub en **cada build**: ya es un auto-pull de `main`. El reespejo correcto = **disparar un rebuild**.
- **Corrección aplicada (D-145, publicada en `main`, commit `2414b9029d`):** el job dispara el rebuild vía API de HF (`CommitOperationAdd` sobre `.rebuild`), nunca empuja un árbol. Además **D-146**: el clon reutilizado se usa en modo **solo lectura** y nunca se registra para borrado (la causa de que un job perdiera 366.077 ficheros).
- **Motivo de por qué no funcionaba el push por git:** el host de HF responde `fatal: expected 'acknowledgments'` sobre HTTP/2; con `http.version=HTTP/1.1` responde bien. La API de HF es la vía fiable.
- **Verificado en el Space ahora mismo:** 8 ficheros operativos presentes en la raíz, `stage=RUNNING`, `/health` → 200. Contrato de arranque comprobado: `router-mvp/mvp` es un **symlink** a `../chat-router/chat/backend/mvp` y los 3 ficheros existen; `chat-router/SWE CODE/web-bridge` existe; `chat-router/SWE CODE free/puente-movil/server.js` existe.

### GAP-4 — El Space sirve un commit huérfano

- **Síntoma:** `/health` → `{"status":"ok","commit":"4722f1dffc"}`; el `main` remoto está en otro sha.
- **Causa:** el rebuild D-145 **nunca se llegó a disparar** (el job aborta en el gate de cableado *antes* de la fase de rebuild, por diseño FAIL_CLOSED). `4722f1dffc` es el tag `safety/pre-candado-20261104-kernel01` y **no** es ancestro de `main` (la historia se reescribió en N3).
- **Estado:** pendiente de ejecutar; el paso está escrito, tested y publicado.

### GAP-5 — El gate `space_has_operational_files` era informativo y no abortaba

- **Hallazgo del centinela (G4):** si faltara cualquier fichero operativo del Space, el job seguía y disparaba el rebuild. El comentario decía "NO se toca nada" pero no había `return`.
- **Corrección preparada (D-148), sin publicar:** `if not _ok: finish(commit=sha)` — con gate duro, si el Space está incompleto no se toca.

### GAP-6 — Purga del historial sin resolver

- **Nodo N3 está `CERRADO_CON_FLAG`.** El **árbol** quedó purgado (37 rutas de `build/`) y publicado. El **historial** no: hay commits cuyo pack supera los 2 GiB y GitHub los rechaza con HTTP 500. Alternativas: partir esos commits con rebase, o rehacerlos en un repo nuevo. **Decisión del owner pendiente** (no bloquea el cierre de N6–N10).

### GAP-7 — `main-clean` está 2 commits por detrás de `main`

- `main-clean` = `35470e8b0660`; `main` = `4992c16b3be9` (más los commits posteriores de los agentes paralelos).
- Se resuelve con un **fast-forward con lease** contra el sha remoto real. Sin efectos colaterales, pero sin hacer, la idempotencia del swap (D-142) deja de reflejar el estado real.

### GAP-8 — El gate de cableado reconstruye el grafo en cada job (~8–11 min)

- `j2_graph.build()` recorre 422.731 ficheros: **660 s** medidos. `j9` y luego `j10` lo repiten → +11 min.
- **Corrección preparada (D-149), sin publicar:** el grafo se cachea en disco (`GRAPH_CACHE`) y `wiring_check` lo reutiliza si el árbol es el mismo. La caché ya está generada (283.543.275 B).

### GAP-9 — Otros agentes escriben en `main` en paralelo

- Detectado 3 veces: `main` se movió `f2366baa → 2414b902 → ca79a412 → 7c77a876 → 4992c16b` mientras yo trabajaba.
- Autores: `kernel-cierre`, `yaiwes-hf-combined-engine`, watchdog del owner.
- **Mitigación aplicada:** todo push mío va con `--force-with-lease` contra el **sha remoto real leído en ese momento**, y el árbol se construye sobre `origin/main` actualizado, nunca sobre una base obsoleta. Sin esta regla, un push habría revertido el trabajo ajeno.

### GAP-10 — 16 conexiones del cableado en `pending_audit`

- El umbral ACTIVE del owner exige **7 condiciones** (autenticación válida, conexión real, inferencia ejecutada, respuesta válida, latencia registrada, sin errores críticos, nada superficial). Un `import` no prueba conexión.
- **Estado:** 38 conexiones inventariadas, 12/12 healthchecks con rc=0, sonda HTTP `/health` 200 y **MCP real con 14 tools** verificados en N5. Falta la **prueba de inferencia real** para promover a `active`; el resto queda en `pending_audit` con su evidencia.

---

## 4. Parches preparados y pendientes de publicar

| Parche | Qué hace | Dónde | Estado |
|---|---|---|---|
| **D-145** | Reespejo = rebuild por API de HF (no push de árbol); sha de referencia = `main` remoto real | `ops/j9_remirror.py` | **PUBLICADO** (`2414b9029d`) |
| **D-146** | Blindaje: el clon reutilizado se usa en solo lectura y nunca se registra para borrado | `ops/common.py` | **PUBLICADO** (`2414b9029d`) |
| **D-148** | Gate duro: abortar si al Space le faltan ficheros operativos | `ops/j9_remirror.py` | preparado, **sin publicar** |
| **D-149** | Caché de grafo en disco (eleva ~660 s por job) | `ops/wiring_check.py` | preparado, **sin publicar** |
| **D-149b** | Baseline regenerado sobre árbol íntegro (65.914 entradas) | `connections/baseline_unresolved.json` | regenerado, **sin publicar** |
| **D-148b** | Versión de `ops/wiring_check.py` y `ops/j2_graph.py` de `kernel-cierre` + la caché D-149 encima | ambos | en local, **sin publicar** |

---

## 5. Verificación de ausencia de daño (centinela, fase 1)

Resultado del centinela/sheriff en solo lectura, con 9 flags, **2 bloqueantes procedimentales** (G1 = Space, G2 = evidencia de `j10`) y **0 de seguridad**:

| Comprobación | Resultado |
|---|---|
| `main` remoto con 373.440 ficheros | ✅ |
| 3 anclas de rollback en sus shas (2 tags + 1 rama) | ✅ |
| Parche D-145 sin `read-tree` / `rm --cached` / push al Space | ✅ |
| Space con sus 8 ficheros operativos, RUNNING, `/health` 200 | ✅ (salvo el commit servido: GAP-4) |
| Hashes del contrato (`INPUT_BLOCK.yaml`, `INPUT_BLOCK_YAIWES_CABLEADO.md`, `AGENTS.md`) | ✅ idénticos |
| Tokens literales en `main` o en el Dataset | ✅ 0 (solo por cabecera) |
| Ficheros destruidos / pérdida de datos | ✅ ninguna (366.077 recuperados) |

---

## 6. Secuencia de cierre (lo que queda por hacer, en orden)

1. Publicar D-148 + D-149 + D-149b con lease contra el sha remoto real (1 push, ~2 min).
2. Ejecutar `j9_remirror` con `GRAPH_CACHE` → el gate de cableado pasa en segundos y se dispara el rebuild del Space (~10–15 min de build).
3. Verificar `/health` → `commit` == sha de `main` → **N6 cerrado con prueba real**.
4. Ejecutar `j10_final_audit` con `AUDIT_JOBS` = los 14 jobs → sube `result.json` al Dataset → **N7 cerrado**.
5. Sondas reales de inferencia → promover a `active` las conexiones que cumplan las 7 condiciones; el resto documentado en `pending_audit` → **N8 cerrado**.
6. `kernel/KERNEL.yaml` (11 nodos, `progress_pct` = 100 × CLOSED/11), `kernel/LEDGER.jsonl`, `connections/wiring_changelog.md`, `README.md`, handoffs → **N9 y N10 cerrados**.
7. Fast-forward de `main-clean` a `main` con lease → coherencia de la idempotencia del swap.
8. Segunda pasada del centinela sobre el estado final → veredicto.

**Tiempo estimado:** 35–50 min si el rebuild del Space levanta a la primera. Si el Space no levanta con el árbol reordenado, hay que revertir y el cierre de N6 queda como flag.

---

## 7. Decisiones que necesito del owner

1. **N6 con prueba real o con evidencia declarada?** (rebuild verificado vs. cierre con `/health` sin comprobar el commit servido).
2. **GAP-6, purga del historial:** ¿se acepta quedar en `CERRADO_CON_FLAG`, o se aborda con rebase de los commits pesados / repo nuevo?
3. **N8:** ¿se acepta `pending_audit` para las conexiones sin inferencia real, o se exige una prueba de inferencia por conexión antes de cerrar?

---

## 8. Evidencia y artefactos

- Evidencia de los 14 jobs: `20261104-kernel01/<job>/result.json` en el Dataset (13 PASS, 1 FAIL = `j9_remirror`).
- Bundle de rollback: `backups/20261104-kernel01.bundle` (8.068.832.804 B).
- Investigación: `20261104-kernel01/research/{context.md,guia_code.md,matriz_fuentes.md}`.
- Auditorías: `audit/j6_rewrite/`, `audit/jobs-pendientes/`.
- Paquetes locales: `/workspace/work/output/{AUDIT-JOB-j6_rewrite,AUDIT-PUSH-8,GAP-G7,GAP-G9,GAP-j6_rewrite,JOBS-AUDIT,JOBS-PENDIENTES}`.
- Grafo y baseline nuevos (en local, sin publicar): `/workspace/work/out/graph_cache.json`, `/workspace/work/baseline_new.json`.
- Logs: `/workspace/work/{j9_final.log,regen2.log,wiring_check.log,remirror_push.log}`.

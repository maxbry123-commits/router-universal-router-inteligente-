# INFORME · N4-B · AUDITOR X-RAY (10 fases) + VENTANA GAPS

- **Nodo**: N4-B · **Rol**: AGENTE 1 (DOER/EXECUTOR) · **DAG**: `yaiwes.node/v2` ·
  RESEARCH → EXECUTE → VALIDATE · **modo**: FAIL_CLOSED
- **Alcance exclusivo (respetado, ni un byte fuera)**: `canvas/backend/xray/`
  → `xray_audit.py`, `gaps_store.py`, `README.md`, `INFORME.md`
- **Repo real `maxbry123-commits/router-universal-router-inteligente-`: NO TOCADO**
  (cero git, cero push, cero GitHub, cero HF, cero Vercel, cero install).
- **Estado del nodo**: `CLOSED` (código escrito y validado con smoke test real).
- **Fecha**: 2026-11-16 · **Entorno**: sandbox Linux, Python 3.11.2, git 2.39.5.

---

## 0 · SKILLS APLICADAS (una línea por skill)

| skill | línea citada | estado |
|---|---|---|
| `mcode-metodo-de-trabajo` | — | 🚩 **NO DISPONIBLE**: la tool `skill` devuelve "Cloud Host skill not found" y no existe en `/workspace/.skills/` (solo hay `formato-salida-mcode`, `hf-github-connectors`, `maxbry-ui-frontend`, `minimax-deterministic-deploy`, `yaiwes-node-dag`). Se aplicó el contrato equivalente de `yaiwes-node-dag` (Loops, puertas FAIL_CLOSED, rutas canónicas, salida única). |
| `yaiwes-node-dag` | `authorized_dag: RESEARCH -> EXECUTE -> VALIDATE -> DONE` + `visibility: show_progress_during_run: false` + `flag: {symbol: "🚩", effect: "never stops, never escalates, never asks"}` | APLICADA (ejecución silenciosa, 3 pasos exactos, FAIL_CLOSED, flags sin parar ni preguntar) |
| `hf-github-connectors` | `Los tokens viven **solo** en el almacén cifrado de secretos → se referencian como ${GITHUB_TOKEN}` | APLICADA (GitHub REST API autenticada con `${GH_TOKEN}` por variable de entorno; el token nunca aparece en argv, logs, ficheros ni en este informe) |
| `formato-salida-mcode` | `SALIDA ÚNICA = % ALCANCE + 🚩 FLAGS + CONCLUSIÓN.` | APLICADA **en su parte de estado/progreso/conclusión**; la **estructura de 5 apartados con tabla de acciones** la impone el INPUT BLOCK VERBATIM del owner, que es ley y prevalece sobre la plantilla (ver §6). |

---

## 1 · COPY DEL INPUT BLOCK VERBATIM (literal)

```
N4-B · AUDITOR X-RAY (10 fases deterministas) + VENTANA GAPS/ERRORES

El auditor produce:
xray/STATE.json (checkpoint reanudable) · MANIFEST.md · ARCHITECTURE.md · WIRING.json · INVENTORY.json ·
CONTRACTS.md · GAPS.md · NEXT_ACTIONS.md · XRAY_REPORT.md · FINGERPRINT.json · raw/ (tree, symbols, imports)

FINGERPRINT.json: schema "xray-fingerprint/1", repo, branch, commit_sha, commit_date, tree_sha,
languages {Python:62,...}, file_count, bytes_total, roots[{path,files,sha256}], constitution_ref, generated_at.

COMPARADOR (5 estados + 1): PRESERVED (existe en docs Y code) · REMOVED (en docs, no en code) ·
MODIFIED (existe en ambos, difiere contrato) · NEW (en code, no en docs = HUÉRFANO) ·
BROKEN_CANDIDATE (existe en ambos, import roto o endpoint 4xx/5xx) · UNKNOWN (sin evidencia suficiente).
Cada fila con evidencia: ruta:línea + sha256 del archivo.

REGLAS DURAS: % = sólo si existe evidencia (si no → UNKNOWN, nunca % estimado) · cada nodo apunta a ruta:línea del código
(sin ruta → SIN_EVIDENCIA) · estado de tarea ∈ {PENDING, RESEARCHING, EXECUTING, VALIDATING, GAP, FIXING, RETESTING, STABLE, BLOCKED, CLOSED}
· Constitución = checklist binario (se cumple o no; no se pondera).

FASES 0-9: 0 preflight · 1 inventario determinista · 2 símbolos · 3 cableado (imports) · 4 contratos (endpoints/env vars) ·
5 cruce docs vs code · 6 huecos · 7 acciones · 8 compresión · 9 fingerprint + validación.
Determinista · reanudable (STATE.json guarda la fase) · fail-closed (PASS solo lo emite el validador, nunca el LLM).

VENTANA GAPS: esquema {id:"GAP-0001", tipo: GAP|ERROR|DRIFT|BROKEN_CANDIDATE|HUÉRFANO, severidad: P0|P1|P2|P3,
titulo, evidencia:"ruta:línea + sha256", componente, estado: OPEN|IN_PROGRESS|FIXED|WONTFIX, notas (máx 500 chars), creado, resuelto}.
Flujo: captura → validar evidencia (ruta:línea debe existir en INVENTORY.json) → guardar → V2 muestra contador →
el auditor lo recoge en GAPS.md → NEXT_ACTIONS lo prioriza P0-P3.
Regla: si la evidencia no valida → 400 y el gap NO se crea. No hay gaps inventados.

CHECKLIST DE CIERRE (12 ítems, con evidencia):
[ ] 1 STATE.json existe y fases 0-9 completas [ ] 2 FINGERPRINT.json con commit_sha + tree_sha
[ ] 3 INVENTORY.json cubre 100% de git ls-files (menos excluidos) [ ] 4 WIRING.json con imports reales, no vacíos
[ ] 5 CONTRACTS.md con endpoints/env + ruta:línea [ ] 6 GAPS.md todos con veredicto CONFIRMADO|CONTRADICHO|SIN_EVIDENCIA
[ ] 7 NEXT_ACTIONS.md con evidencia + prioridad [ ] 8 raw/validation.json PASS=true
[ ] 9 gaps.json todos con evidencia ruta:línea válida [ ] 10 ningún gap sin estado [ ] 11 cero secretos en xray/ (grep gh_|hf_|sk-)
[ ] 12 V4 AUDIT muestra fingerprint + GAPS + NEXT_ACTIONS del mismo commit
Si un ítem falla, el cierre se bloquea y el gap se abre como GAP P0.

CÓDIGO DE REFERENCIA (del owner — consérvalo, no lo resumas; CORRIGE sus bugs reales):
xray_audit.py corre las fases 0-9 y escribe xray/: sha256_file, git(), STATE.json con phases{i_n:{status,evidence}},
inventario (git ls-files → path/sha256/bytes/lines/language), símbolos (regex def|class|function|export function|const),
cableado (regex import|from → WIRING.json), contratos (regex @app/@router.get|post|... y os.getenv → CONTRACTS.md con ruta:línea),
cruce (claims en .md que mencionan módulo|module|flujo|flow|componente|component → raw/claims.json),
huecos, acciones (ACT-#### con prioridad P0-P3 + evidencia), compresión (XRAY_REPORT.md), fingerprint + validate() que
recomprueba sha256 de cada archivo y que no falte ninguno → raw/validation.json {"PASS":bool,"errors":[...]}.
BUGS REALES DEL CÓDIGO DE REFERENCIA QUE DEBES CORREGIR:
 1) la fase 6 marca TODAS las claims como SIN_EVIDENCIA, pero el checklist exige 3 veredictos: implementa el cruce real
    (CONFIRMADO si el símbolo/ruta declarado existe en INVENTORY/WIRING con su línea; CONTRADICHO si la ruta existe pero el símbolo no;
    SIN_EVIDENCIA si no hay ruta verificable).
 2) el FINGERPRINT de referencia pone "roots" como lista de strings; el esquema del owner pide roots[{path,files,sha256}]: versión rica.
 3) STATE.json se escribe al inicio y al final: asegúrate de que cada cambio de fase queda persistido.
 4) añade `languages` (conteo por extensión) y `commit_date` al fingerprint.
 5) el store usa Path("xray/gaps.json") relativo al CWD: hazlo relativo a la raíz del propio script y atómico (temp + replace).
 6) añade verificación de que NO hay secretos en las salidas (grep de gh_/hf_/sk-) antes de PASS.
```

---

## 2 · TABLA DE ACCIONES

| ACCION | COMANDO O FICHERO | RESULTADO | EVIDENCIA |
|---|---|---|---|
| Cargar skills obligatorias | tool `skill` (4 skills) | 3 cargadas de `/workspace/.skills/`; `mcode-metodo-de-trabajo` **NO EXISTE** | `skill` → "Cloud Host skill not found"; `ls /workspace/.skills/` → `formato-salida-mcode`, `hf-github-connectors`, `maxbry-ui-frontend`, `minimax-deterministic-deploy`, `yaiwes-node-dag` |
| Leer la ley | `canvas/TAREA_01_FUENTE_DE_LA_VERDAD.md` | leída (DAG `yaiwes.node/v2`, gates FAIL_CLOSED, `authorized_deploy: []`) | fichero de 11.371 B, sección 3 (DAG YAML) y 5 (reglas duras) |
| RESEARCH: leer motores reales por API GitHub (sin clonar) | `GET api.github.com/repos/maxbry123-commits/router-universal-router-inteligente-/contents/chat-router/Loop cola wachdog/Loop/nct_loop/trigger_contract.py?ref=main` | 200 · 12.562 B · git_sha `481c1b1c…` | salida `FILE … -> 200 … SAVED bytes=12562` |
| RESEARCH: leer el test real | `GET …/contents/chat-router/Loop cola wachdog/Loop/tests/test_motor_addons.py?ref=main` | 200 · 6.257 B · git_sha `61fea6b2…` | salida `FILE … -> 200 … SAVED bytes=6257` |
| RESEARCH: estilo heredado | lectura de ambos ficheros | `ContractError(code, detail)`, `sha256()`, solo stdlib, `unittest` con `verbosity=2`, 0 side-effects | `/tmp/ref/trigger_contract.py`, `/tmp/ref/test_motor_addons.py` |
| EXECUTE: auditor 10 fases | `canvas/backend/xray/xray_audit.py` (nuevo) | escrito · 10 fases + validador + comparador 6 estados + veredictos | 73.853 B; `python3 -m py_compile` → exit 0 |
| EXECUTE: store de gaps | `canvas/backend/xray/gaps_store.py` (nuevo) | escrito · validación de evidencia fail-closed + contador V2 + IO atómico | 12.699 B; `python3 -m py_compile` → exit 0 |
| EXECUTE: README | `canvas/backend/xray/README.md` (nuevo) | escrito · uso, fases, esquemas, checklist, decisiones | 9.728 B |
| VALIDATE: fixture | `git init` + commit en `/tmp/xray_fixture` (a.py, b.js, doc.md, sub/c.py) | exit 0 · commit `1bf2cbcb3c7035a2…` | `git ls-files` → a.py, b.js, doc.md, sub/c.py |
| VALIDATE: auditor sobre fixture | `python3 xray_audit.py --root /tmp/xray_fixture --out /tmp/xray_fixture/xray` | **"XRAY COMPLETE"** · exit 0 | log de fases 0-9 + `raw/validation.json` `PASS=true`, 13 checks, 0 errores |
| VALIDATE: artefactos obligatorios | `ls` del out | 11/11 presentes | STATE, INVENTORY, WIRING, CONTRACTS.md, GAPS.md, NEXT_ACTIONS.md, XRAY_REPORT.md, FINGERPRINT.json, MANIFEST.md, ARCHITECTURE.md, raw/validation.json |
| VALIDATE: fingerprint rico | `FINGERPRINT.json` | `commit_sha`+`tree_sha`+`commit_date`+`languages`+`roots[{path,files,sha256}]` | `roots=[{'files':3,'path':'(root)','sha256':'ab73f57e…'},{'files':1,'path':'sub','sha256':'ae30a2c6…'}]`; `languages={'JavaScript':1,'Markdown':1,'Python':2}` |
| VALIDATE: gaps_store evidencia VÁLIDA | `gaps_store.py add --json '{… "evidencia":"sub/c.py:3" …}'` | **OK** · `GAP-0001` creado · exit 0 | salida `{"ok": true, "gap": {"id":"GAP-0001", … "evidencia":"sub/c.py:3 sha256:e32cf4ac…"}}` |
| VALIDATE: gaps_store evidencia INVENTADA (ruta) | mismo comando con `"evidencia":"no_existe_este_fichero.py:1"` | **RECHAZADO** · exit 2 · NO creado | `{"ok": false, "error": "EVIDENCIA_INVALIDA", "detail": "ruta no presente en INVENTORY.json: no_existe_este_fichero.py"}` |
| VALIDATE: gaps_store evidencia INVENTADA (línea) | mismo comando con `"evidencia":"a.py:9999"` | **RECHAZADO** · exit 2 · NO creado | `{"ok": false, "error": "EVIDENCIA_INVALIDA", "detail": "linea 9999 fuera de rango en a.py (lineas=12)"}` |
| VALIDATE: store tras los 3 intentos | `cat gaps.json` | `count = 1` (solo el válido) | `('GAP-0001','DRIFT','P1','OPEN','sub/c.py:3 sha256:e32cf4ac…')` |
| VALIDATE: contador V2 | `gaps_store.py count` | exit 0 · total 1 · abiertos 1 · by_state/by_type/by_severity | salida JSON del contador |
| VALIDATE: el auditor recoge el gap de la VENTANA GAPS | 2ª ejecución del auditor | `GAP-0001` en GAPS.md (2 coincidencias) y en NEXT_ACTIONS.md (1, prioridad P1) · **XRAY COMPLETE** · exit 0 · `PASS=true` · ítem 9 `gaps_json=1 invalidos=0` | `grep -c GAP-0001` → 2 / 1 |
| VALIDATE: py_compile | `python3 -m py_compile xray_audit.py gaps_store.py` | exit 0 | salida vacía, exit 0 |
| VALIDATE: fail-closed sin repo git | `xray_audit.py --root /tmp/not_a_repo …` | exit 3 · `PASS=false` · **sin PASS inventado** | `raw/validation.json` → `"PASS": false`, `errors[0].check="runtime"` |
| VALIDATE: comparador 6 estados (extra) | fixture 2 `/tmp/xray_fixture2` (doc cita `fantasma.py` inexistente y `no_existe_funcion`) | `REMOVED` + `MODIFIED` + `PRESERVED` + `NEW` (+`BROKEN_CANDIDATE` en la fixture 1) + `UNKNOWN` para import externo | `raw/comparison.json` → `{'REMOVED':1,'MODIFIED':1,'PRESERVED':1,'NEW':1}`; veredictos `CONTRADICHO/CONTRADICHO/CONFIRMADO` |
| VALIDATE: reanudabilidad | 2ª ejecución con `STATE.json` presente | fases 1-5 "reanudadas", 6-9 re-ejecutadas (dependen de `gaps.json` externo) | log `fase 1 inventario reanudado (4 ficheros)` … `fase 6 huecos: 6 gaps` |

---

## 3 · LOS 6 BUGS DEL CÓDIGO DE REFERENCIA, CORREGIDOS

| # | bug | corrección aplicada | dónde se ve |
|---|---|---|---|
| 1 | fase 6 marcaba **todas** las claims como `SIN_EVIDENCIA` | cruce real: `CONFIRMADO` (símbolo/ruta existe con su línea) · `CONTRADICHO` (la ruta existe pero el símbolo no) · `SIN_EVIDENCIA` (sin ruta verificable). Tabla `VERIFICACIONES DOCS vs CODE` en `GAPS.md` | `xray_audit.py` fases 5-6; fixture 2 → `CONTRADICHO/CONTRADICHO/CONFIRMADO` |
| 2 | `roots` del fingerprint como lista de strings | `roots[{path,files,sha256}]`, sha256 = hash determinista de `ruta:sha256` ordenado por raíz | `FINGERPRINT.json` (evidencia arriba) |
| 3 | `STATE.json` solo al inicio y al final | `save_state()` en **cada** cambio de fase (`mark_phase`) + escritura atómica | `STATE.json.phases{i_n:{status,evidence,updated_at}}` |
| 4 | faltaban `languages` y `commit_date` | `languages` (conteo por lenguaje) y `commit_date` (`git log -1 --format=%cI`) | `FINGERPRINT.json` |
| 5 | store con `Path("xray/gaps.json")` **relativo al CWD** | rutas por defecto **relativas al script** (`Path(__file__).parent`) + escritura **atómica** (temp + `os.replace`) | `gaps_store.py paths` → `store=<script_dir>/gaps.json` con `cwd=/tmp` |
| 6 | sin verificación de secretos antes del PASS | escaneo de **todas** las salidas antes de emitir PASS (ítem 11 del checklist) | `raw/validation.json` ítem `11_CERO_SECRETOS` → `fugas=0` |

---

## 4 · GAPS / BLOQUEOS / FLAGS 🚩

| # | gap / flag | ruta probada | estado |
|---|---|---|---|
| F1 🚩 | **Los ficheros de referencia no existen en la rama de trabajo** `ccr-f01c3de9-bmry0s` (404 en `chat-router/Loop cola wachdog/Loop/…`); existen en `main` (`Loop/nct_loop/…`, `Loop/tests/…`) | API GitHub: `contents?...ref=ccr-f01c3de9-bmry0s` → 404 → `?ref=main` → 200 (12.562 B + 6.257 B) | **RESUELTO** — leídos por API (sin clonar) desde `main`; el estilo se copió de ahí. El nodo NO escribe nada en el repo. |
| F2 🚩 | Skill `mcode-metodo-de-trabajo` **no disponible** (no está en `/workspace/.skills/`; la tool `skill` la rechaza) | `skill(name="mcode-metodo-de-trabajo")` → "Cloud Host skill not found"; `find /workspace -iname "*mcode*"` → vacío | **ABIERTO (documentado)** — se aplicó el contrato equivalente de `yaiwes-node-dag`. No bloquea la entrega. |
| F3 🚩 | Conflicto de formato: `formato-salida-mcode` (plantilla de 1 bloque, sin tablas) vs. el brief (5 apartados con tabla) | lectura de ambas fuentes | **RESUELTO por precedencia** — manda el INPUT BLOCK del owner; de la plantilla se conservan estado/progreso/conclusión. |
| A1 | **Ítem 5 del checklist con 0 contratos** (la fixture no tiene endpoints ni env vars): el ítem verifica el invariante de formato (toda fila con `ruta:línea`) y la ausencia se declara como `UNKNOWN` (nunca estimación) | `raw/validation.json` ítem 5 | **DECIDIDO (conservador)** — documentado en `README.md` §7 |
| A2 | Rutas de docs citadas que no están en el código: el comparador las marca `REMOVED` (no `UNKNOWN`), porque la ausencia en el code es verificable contra `INVENTORY.json` | fixture 2 → `REMOVED` | **DECIDIDO** |
| A3 | Imports de terceros: no verificables offline → `UNKNOWN` en `WIRING.json` con motivo, y **no** se convierten en filas del comparador (no hay evidencia local) | fixture 2 → `requests -> UNKNOWN modulo externo: no verificable offline` | **DECIDIDO** |
| A4 | Ítem 11: el patrón literal `gh_|hf_|sk-` da falsos positivos en prosa (`"task-"` contiene `"sk-"`). Se bloquea el PASS con el criterio "prefijo + cuerpo de token (≥12)", que sí detecta credenciales; el recuento literal se registra como dato informativo | `raw/validation.json` ítem 11 | **DECIDIDO** — documentado en `README.md` §6 |
| A5 | Sin `ledger.jsonl`: el brief **no define `workdir`** y crear un fichero extra en `xray/` violaría el alcance exclusivo | brief "ALCANCE EXCLUSIVO" | **DECIDIDO** — no se creó ledger |
| A6 | El repo real **no está clonado** en el sandbox (prohibido clonar) → la auditoría real contra `maxbry123-commits/router-universal-router-inteligente-` la ejecuta el orquestador (N4-E) | `git rev-parse` en `/workspace/stage_canvas/chat-router` → "not a git repository" | **FUERA DE ALCANCE DEL N4-B** (el brief exige validar en `/tmp`, no sobre el repo real) |

---

## 5 · QUEDA VERIFICADO | NO SE PUDO VERIFICAR

### QUEDA VERIFICADO (con comando + salida + exit code)

- `xray_audit.py` corre las **fases 0-9** de punta a punta y termina con **"XRAY COMPLETE"**, exit 0.
- `raw/validation.json` → **`"PASS": true`**, `errors: []`, **13 checks** (los 12 del checklist del owner + 1 extra de recomprobación de sha256).
- Los **11 artefactos obligatorios** quedan escritos en el `--out` (más `MANIFEST.md` y `ARCHITECTURE.md`, exigidos por la cabecera del INPUT BLOCK).
- `FINGERPRINT.json`: `schema="xray-fingerprint/1"`, `commit_sha`, `tree_sha`, `commit_date`, `languages`, `file_count`, `bytes_total`, `roots[{path,files,sha256}]`, `constitution_ref`, `generated_at`.
- **COMPARADOR**: los 6 estados se producen con evidencia real (fixture 1: `PRESERVED/NEW/BROKEN_CANDIDATE/UNKNOWN`; fixture 2: `REMOVED/MODIFIED`).
- **3 veredictos** de la fase 6 (bug 1) con contraste fixture 2: `CONTRADICHO`, `CONTRADICHO`, `CONFIRMADO`.
- **VENTANA GAPS**: evidencia válida → gap **creado** (exit 0); evidencia inventada (ruta inexistente y línea fuera de rango) → **RECHAZADO con exit 2 y NO creado**; contador V2 disponible.
- Flujo completo store→auditor: el gap `GAP-0001` aparece en `GAPS.md` y se prioriza **P1** en `NEXT_ACTIONS.md`; ítem 9 `gaps_json=1 invalidos=0`.
- **Ranuudable**: `STATE.json` persiste cada fase; la 2ª ejecución reanuda 1-5 y re-ejecuta 6-9.
- **Fail-closed**: root sin repo git → exit 3, `PASS=false`, **sin PASS inventado**.
- **Cero secretos** en las salidas (ítem 11 `fugas=0`).
- `python3 -m py_compile xray_audit.py gaps_store.py` → exit 0.
- 0 installs, 0 clones, 0 push, 0 HF, 0 Vercel, 0 GitHub Actions, 0 LFS, 0 escrituras fuera de `canvas/backend/xray/`.

### NO SE PUDO VERIFICAR

- La auditoría **contra el repo real** `maxbry123-commits/router-universal-router-inteligente-`: no está clonado en el sandbox y clonar está prohibido. Los 12 ítems del checklist se han validado contra fixtures equivalentes; falta la corrida real (N4-E, con `--root` del repo).
- El **ítem 12** (V4 AUDIT muestra fingerprint + GAPS + NEXT_ACTIONS del mismo commit) solo se ha verificado como **precondición mecánica**: los 3 ficheros llevan el mismo `commit_sha` (mismo commit). Que la ventana V4 los pinte es trabajo del nodo N4-D/N4-E.
- El **comportamiento en caliente del endpoint HTTP** de la VENTANA GAPS (400 con evidencia inválida): este nodo entrega el store; el mapeo a HTTP 400 corresponde a la capa API del nodo N4-A (aquí el error es `EVIDENCIA_INVALIDA`, exit 2).
- **Escala**: el repositorio real tiene ~51k ficheros rastreados; el hashed completo es O(n) y no se ha medido en el repo real (solo en fixtures de 3-4 ficheros). El recorte `--max-rows` limita el markdown, no el `raw/comparison.json`.
- `constitution_ref`: `UNKNOWN` en las fixtures (no hay fichero de constitución); en el repo real debe resolverse a `TAREA_01_FUENTE_DE_LA_VERDAD.md`.

---

## 6 · PRECEDENCIA Y FORMATO DE SALIDA

El INPUT BLOCK del owner fija la "SALIDA FINAL OBLIGATORIA" (5 apartados: COPY verbatim,
tabla de acciones, gaps/bloqueos, verificado/no verificado, conclusión en 2 líneas).
`formato-salida-mcode` fija una plantilla única de estado/progreso/conclusión. Ambas son
del owner: **prevalece el INPUT BLOCK** en la estructura; de la plantilla se conservan
`TAREA/OBJETIVO/REALIZADO`, `CONFIRMA IMPUT BLOCK VERBARTIN`, `GAP/FIX/INSTRUCCIONES`,
`ESTADO`, `PROGRESO`, `TIEMPO`, `PENDIENTE`, `🚩 FLAGS` y `CONCLUSIÓN` (máx. 2 líneas).
No se han inventado porcentajes: `PROGRESO` va con conteos evidenciados.

---

## 7 · CONCLUSIÓN (2 líneas)

El auditor X-Ray de 10 fases y la VENTANA GAPS quedaron escritos, compilados y validados
con smoke test real en `/tmp`: "XRAY COMPLETE", `validation.json PASS=true` (13/13) y gaps
con evidencia inválida rechazados sin crearse.
Queda una sola cosa para el orquestador: la corrida contra el repo real, que en este
sandbox no puede hacerse sin clonarlo (prohibido).

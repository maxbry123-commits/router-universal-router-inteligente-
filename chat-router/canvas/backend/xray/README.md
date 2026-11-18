# X-RAY — auditor determinista + VENTANA GAPS (nodo N4-B)

Nodo **N4-B** del DAG `yaiwes.node/v2` (RESEARCH → EXECUTE → VALIDATE, modo FAIL_CLOSED).
Dos módulos, Python 3.8+ **solo stdlib**, sin dependencias, sin red, sin side effects
al importar:

| fichero | función |
|---|---|
| `xray_audit.py` | auditor de fases 0-9: inventaria, symbola, cablea, extrae contratos, cruza docs vs code, lista huecos y acciones, comprime, sella fingerprint y valida |
| `gaps_store.py` | VENTANA GAPS: captura de gaps con **validación de evidencia** (fail-closed) y contador para la V2 |

---

## 1 · Uso

```bash
# auditor (escribe SOLO dentro de --out)
python3 xray_audit.py --root <repo_git> --out <dir_salida>
# flags: --gaps <gaps.json>  --force  --no-resume  --exclude <glob>  --max-rows N  --quiet

# store de gaps
python3 gaps_store.py paths                      # resuelve rutas por defecto
python3 gaps_store.py add --file gap.json        # crea gap (valida evidencia)
python3 gaps_store.py add --json '{...}'
python3 gaps_store.py list  [--store <path>]
python3 gaps_store.py count [--store <path>]     # contador para la V2
```

Códigos de salida del auditor: `0` = validación PASS · `3` = fallo fail-closed
(root no git, etc.) · `4` = validación con errores (`raw/validation.json` con `PASS=false`).

---

## 2 · Fases 0-9 (deterministas, reanudables, fail-closed)

| fase | nombre | qué hace | artefacto |
|---|---|---|---|
| 0 | preflight | valida raíz, rama, commit, tree, constitución | `STATE.json` |
| 1 | inventario determinista | `git ls-files` → ruta/sha256/bytes/líneas/lenguaje + cobertura | `INVENTORY.json`, `raw/tree.json` |
| 2 | símbolos | regex `def`/`class`/`function`/`export function`/`const` con su línea | `raw/symbols.json` |
| 3 | cableado (imports) | `import`/`from` → resolución real; rotos = BROKEN_CANDIDATE | `WIRING.json`, `raw/imports.json` |
| 4 | contratos | `@app`/`@router.get|post|…` y `os.getenv`/`os.environ`/`process.env` → `ruta:línea` | `CONTRACTS.md`, `raw/contracts.json` |
| 5 | cruce docs vs code | claims en `.md` (módulo/module/flujo/flow/componente/component) + COMPARADOR | `raw/claims.json`, `raw/comparison.json` |
| 6 | huecos | veredictos reales + gaps del comparador + gaps de la VENTANA GAPS | `GAPS.md`, `raw/gaps.json` |
| 7 | acciones | `ACT-####` con prioridad P0-P3, estado y evidencia | `NEXT_ACTIONS.md`, `raw/actions.json` |
| 8 | compresión | informe comprimido + mapa de arquitectura | `XRAY_REPORT.md`, `ARCHITECTURE.md` |
| 9 | fingerprint + validación | fingerprint rico + checklist binario de cierre | `FINGERPRINT.json`, `raw/validation.json`, `raw/closure.json`, `MANIFEST.md` |

**Ranuudable**: `STATE.json` guarda `phases{i_n:{status,evidence}}` y se persiste en
**cada** cambio de fase. Al relanzar, las fases 1-5 se reanudan desde los artefactos
escritos en disco; las fases 6-9 se re-ejecutan siempre (dependen del `gaps.json`
externo o validan el resultado final).

**Fail-closed**: `PASS` lo emite **solo** el validador de la fase 9. El análisis nunca
declara PASS. Si el root no es un repo git, el auditor escribe `raw/validation.json` con
`PASS=false` y sale con código 3.

---

## 3 · Esquemas

### FINGERPRINT.json (`xray-fingerprint/1`)

```json
{"schema":"xray-fingerprint/1","repo":"…","branch":"…","commit_sha":"…","commit_date":"…",
 "tree_sha":"…","languages":{"Python":62},"file_count":N,"bytes_total":N,
 "roots":[{"path":"chat-router","files":N,"sha256":"…"}],
 "constitution_ref":"…","generated_at":"2026-…Z"}
```

`roots` es la **versión rica** (`{path,files,sha256}`), no una lista de strings: el
sha256 de cada raíz es el hash determinista de la lista `ruta:sha256` ordenada de sus
ficheros.

### COMPARADOR (5 estados + 1)

| estado | significado |
|---|---|
| `PRESERVED` | existe en docs **y** en code |
| `REMOVED` | está en docs, no en code |
| `MODIFIED` | existe en ambos, difiere el contrato (símbolo declarado ausente) |
| `NEW` | está en code, no en docs → **HUÉRFANO** |
| `BROKEN_CANDIDATE` | existe en ambos, import roto (relativo local no resoluble) |
| `UNKNOWN` | sin evidencia suficiente (p. ej. módulo externo no verificable offline) |

Cada fila lleva evidencia `ruta:línea` + `sha256` del fichero. Los imports de terceros
no verificables offline se registran en `WIRING.json` como `UNKNOWN` con su motivo, y
**no** se convierten en filas del comparador (no hay evidencia local).

### Veredictos docs vs code (fase 6)

| veredicto | regla |
|---|---|
| `CONFIRMADO` | el símbolo/ruta declarado existe en INVENTORY/WIRING **con su línea** |
| `CONTRADICHO` | la ruta existe pero el símbolo declarado **no** (o la ruta no existe en code) |
| `SIN_EVIDENCIA` | no hay ruta/símbolo verificable |

### VENTANA GAPS (store)

```json
{"id":"GAP-0001","tipo":"GAP|ERROR|DRIFT|BROKEN_CANDIDATE|HUÉRFANO",
 "severidad":"P0|P1|P2|P3","titulo":"…","evidencia":"ruta:línea sha256:<hex>",
 "componente":"…","estado":"OPEN|IN_PROGRESS|FIXED|WONTFIX","notas":"≤500 chars",
 "creado":"ISO-8601","resuelto":null}
```

Flujo: captura → **validación de evidencia** (la `ruta:línea` debe existir en
`INVENTORY.json`) → guardado → la V2 muestra el contador → el auditor lo recoge en
`GAPS.md` → `NEXT_ACTIONS.md` lo prioriza P0-P3.
**Regla dura**: si la evidencia no valida → error (`EVIDENCIA_INVALIDA`, que la capa API
traduce a 400) y **el gap NO se crea**. No hay gaps inventados.

---

## 4 · Rutas (bug 5 del código de referencia, corregido)

Las rutas por defecto son **relativas a la raíz del propio script**
(`Path(__file__).resolve().parent`), **nunca** al CWD:

- store: `<script_dir>/gaps.json`
- inventario: `<script_dir>/INVENTORY.json`

`gaps_store.py paths` las imprime para verificarlo. `--store` / `--inventory` permiten
apuntar a otro sitio (tests sobre `/tmp`). Toda escritura es **atómica**
(`tempfile.mkstemp` en el mismo directorio + `os.replace`).

---

## 5 · CHECKLIST DE CIERRE (binario, con evidencia)

Lo emite `raw/closure.json` (y se refleja en `XRAY_REPORT.md`):

| # | ítem | verificación implementada |
|---|---|---|
| 1 | STATE.json existe y fases 0-9 completas | `STATE.json` + `phases[*].status` |
| 2 | FINGERPRINT.json con commit_sha + tree_sha | regex hex 40/64 + `commit_date` |
| 3 | INVENTORY.json cubre 100% de `git ls-files` (menos excluidos) | re-ejecuta `ls-files` y compara |
| 4 | WIRING.json con imports reales, no vacíos | cada import con `from_path` + `line` |
| 5 | CONTRACTS.md con endpoints/env + ruta:línea | cada fila de tabla con `ruta:línea` |
| 6 | GAPS.md todos con veredicto CONFIRMADO/CONTRADICHO/SIN_EVIDENCIA | parseo de tablas markdown |
| 7 | NEXT_ACTIONS.md con evidencia + prioridad | `prioridad ∈ P0..P3` y evidencia `ruta:línea`/`SIN_EVIDENCIA` |
| 8 | raw/validation.json PASS=true | el propio fichero, escrito y releído |
| 9 | gaps.json todos con evidencia ruta:línea válida | re-validación contra INVENTORY |
| 10 | ningún gap sin estado | `estado ∈ OPEN/IN_PROGRESS/FIXED/WONTFIX` |
| 11 | cero secretos en `xray/` | escaneo de todas las salidas (ver §6) |
| 12 | V4 AUDIT muestra fingerprint + GAPS + NEXT_ACTIONS del mismo commit | los 3 ficheros llevan el mismo `commit_sha` |
| 13 | (extra) sha256 de cada fichero inventariado recomprobado | `sha256_file()` sobre todo INVENTORY |

Si un ítem falla, el cierre se bloquea: `raw/validation.json` queda con `PASS=false` y
`errors[]` con el detalle.

---

## 6 · Cero secretos (ítem 11)

El escaneo recorre **todas** las salidas y bloquea el PASS si encuentra un token con
forma de credencial: prefijo de proveedor seguido de **≥12 caracteres de token**.

Motivo de la regla estricta: el patrón literal del owner (`gh_` / `hf_` / `sk-`)
produce falsos positivos sobre prosa normal — `"task-"` contiene `"sk-"` y `"|hf_"` es
un patrón alterno, no un token. Se aplica el criterio "prefijo + cuerpo de token", que
detecta credenciales reales sin marcar texto legítimo. El número de coincidencias
literales del prefijo se registra como dato informativo en el ítem 11 (no bloquea).

---

## 7 · Decisiones documentadas (ambigüedades resueltas hacia lo conservador)

1. **Ítem 5 con 0 contratos**: si el repo no tiene endpoints ni env vars, `CONTRACTS.md`
   lo dice explícitamente ("sin evidencia, UNKNOWN, no estimación") y el ítem pasa: se
   verifica el **invariante de formato** (toda fila con `ruta:línea`), no la cantidad.
2. **Comparador de rutas**: una ruta mencionada en docs que no está en `INVENTORY.json`
   se clasifica `REMOVED` (no `UNKNOWN`): la ausencia en el código es verificable.
3. **HUÉRFANOs**: un fichero de código que ningún `.md` menciona es `NEW`/HUÉRFANO. En
   repos grandes el número crece; el recorte por estado (`--max-rows`, 200 por defecto)
   se aplica solo al markdown, y la evidencia completa queda en `raw/comparison.json`.
4. **Id namespaces**: `AUD-####` = gaps derivados por el auditor · `GAP-####` = gaps
   capturados por la VENTANA GAPS · `CLM-####` = verificaciones de claims.
5. **Sin ledger**: el brief no define `workdir` para `ledger.jsonl`, y crear un fichero
   extra en `xray/` violaría el alcance exclusivo (`xray_audit.py`, `gaps_store.py`,
   `README.md`, `INFORME.md`).

---

## 8 · Pruebas ejecutadas (reales, en `/tmp`, nunca sobre el repo real)

Ver `INFORME.md` (nodo N4-B) para las salidas completas con exit codes:
fixture `/tmp/xray_fixture` (a.py con def+class, b.js con function, doc.md con
"el modulo X hace cosas y el flujo Y", sub/c.py con imports) → `XRAY COMPLETE`,
`raw/validation.json PASS=true`; store: gap con evidencia válida → creado; gap con
evidencia inventada → RECHAZADO y **no** creado.

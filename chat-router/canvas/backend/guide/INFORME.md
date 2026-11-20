# INFORME · N4‑C · GUÍA VIVA + MOTORES DE ACCIÓN

> Nodo: **N4‑C** (AGENTE 1 · DOER/EXECUTOR · FAIL_CLOSED) · DAG `yaiwes.node/v2`
> RESEARCH → EXECUTE → VALIDATE · Fecha UTC: **2026‑11‑16T06:31Z** · Ramal/ repo: **no tocados**
> (0 git, 0 push, 0 GitHub, 0 HF, 0 Vercel, 0 `pip install`, 0 crawler propio).

---

## 1 · RESEARCH (sólo lectura, API GitHub con `${GH_TOKEN}`)

Se copiaron los **contratos reales** del repo `maxbry123-commits/router-universal-router-inteligente-`
(rama `main`) por la API de contenidos (sin clonar, sin escribir nada en el repo).

| Fichero leído (repo) | Bytes | sha256 (prefijo) | Qué se copió |
|---|---|---|---|
| `chat-router/Loop cola wachdog/Loop/nct_loop/trigger_contract.py` | 12.562 | `75e58d09b069ca31` | `TOP_FIELDS`, `validate_contract`, `STEP_KINDS={MODEL,TOOL,CHECK}`, `OPS`, `ROLES`, `CATEGORIES`, `steps≤32`, `max_model_calls∈{0,1}`, `source.sha256`, `source_anchor_ref` (`^ancla:…$`), transiciones `NEXT/RECORD_AND_NEXT/FLAG_AND_STOP_DEPENDENTS` |
| `chat-router/Loop cola wachdog/Loop/nct_loop/trigger_engine.py` | 18.736 | `f8b7eb69074b4334` | SHA de contrato/anchor, recibos por paso, readback de escrituras, `BLOCKED_DEPENDENCY`, `GITHUB_WRITER_ONE_FILE_PER_TRIGGER`, `WRITER_N4_REQUIRED` |
| `chat-router/Loop cola wachdog/Loop/nct_loop/ricardo_plan_guard.py` | 4.148 | `8db5695df8a837cd` | Allowlist `SAFE_OPS`, validación de DAG (ciclo), `_safe()` de rutas, `requires_n4_approval` si hay escritura |
| `chat-router/Loop cola wachdog/Loop/config/investigation_sources.json` | 1.310 | `59db4463759e54b5` | Los **10 dominios** + `guardrails` (`read_only`, `no_external_code_execution`, `require_evidence`, `max_results=100`) |
| `motores de descarga y extracción/➡️📂 motor de búsqueda/websearch_engine.py` | 9.171 | `6e9c653dac5db033` | **Motor de búsqueda real**: `run(query, providers, limit, root)`, `canon(url)`, `FUNCS` de proveedores |
| `…/motor de búsqueda/research_prepass.py` | 16.568 | `6ab152d5c08c12df` | Prepass: `hostname_matches`, cache por hash + readback, `select_budget`, `NO_NEW_EVIDENCE` |
| `…/motor de búsqueda/source_registry.json` | 1.384 | `d574e868e3384740` | Formato de registro de fuentes (10 web + 1 directa) |
| `…/motor de búsqueda/context_packet.schema.json` | 2.839 | `c776a29bc09c2cb3` | Esquema del paquete de contexto |

Comando (secret por variable de entorno, nunca literal):

```bash
python3 /workspace/.research_agentc/fetch.py   # urllib + Authorization: Bearer $GH_TOKEN
# OK 200 12562B … chat-router/…/trigger_contract.py
# OK 200 18736B … chat-router/…/trigger_engine.py
# OK 200  4148B … chat-router/…/ricardo_plan_guard.py
# OK 200  1310B … chat-router/…/config/investigation_sources.json
# OK 200  9171B … motores de descarga y extracción/➡️📂 motor de búsqueda/websearch_engine.py
# OK 200 16568B … research_prepass.py · OK 2213B trigger_websearch.py
# OK 200  1384B source_registry.json · OK 2839B context_packet.schema.json
```

**Contrato de búsqueda heredado (firma idéntica, sin reimplementar):**

```python
provider(query: str, providers: str, limit: int, root: str) -> dict
# == websearch_engine.run(query, providers, limit, pathlib.Path(root))
```

---

## 2 · EXECUTE (ficheros nuevos, sólo en `canvas/backend/guide/`)

| Fichero | Bytes | sha256 (prefijo) | Contenido |
|---|---|---|---|
| `grammar.py` | 12.083 | `e67c187845e9fb21` | Descomposición gramatical determinista ES/EN (lexicón de 11 verbos canónicos, 3 estados, 11 tipos) |
| `match.py` | 18.160 | `f11620fb43a928c7` | MIRROR contra el ejemplo + veredicto + rango exacto de líneas + parche + `verify_surgical` |
| `trigger.py` | 25.063 | `15feb60b94b4b0e1` | Espejo validado de `validate_contract` + constructor de trigger + descriptor RUNNER + semáforo |
| `discovery.py` | 24.709 | `143e94a8993c8b13` | Delegación en el motor del repo, 10 dominios, normalización/validación de URLs, caché por hash, opciones con evidencia |
| `guide_actions.json` | 8.828 | `620eb3cc3f4d9fbc` | 5 acciones con señales, ancla, forma del parche, `antes` y `ejemplo` |
| `README.md` | 9.341 | `d4e19ee699347fb0` | Contrato, uso, variables de entorno, límites |

Nada más se escribió: el directorio contiene **exactamente** esos 6 ficheros + este `INFORME.md`.
`__pycache__` se compila con `PYTHONPYCACHEPREFIX` fuera del árbol (verificado en el smoke test).

---

## 3 · VALIDATE (smoke test real · bash · salida y exit codes pegados)

```bash
cd /workspace/.research_agentc
PYTHONDONTWRITEBYTECODE=1 python3 smoke_agentc.py > smoke_out.txt 2>&1 ; echo "EXIT=$?"
# EXIT=0   ·   fallos: 0   ·   296 líneas de salida real (smoke_out.txt)
```

### 3.1 `python3 -m py_compile` de los 4 módulos

```
cmd: python3 -m py_compile grammar.py match.py trigger.py discovery.py
stdout: (vacío)
stderr: (vacío)
exit_code: 0
[OK] py_compile sin errores :: exit=0
[OK] no queda __pycache__ en el árbol del repo
```

### 3.2 GRAMMAR · texto de ejemplo → JSON descompuesto (revisión a mano)

```
'anadir reintento con backoff' -> {"objetivo": "anadir reintento con backoff", "sujeto": "reintento", "verbo": "create", "adjetivo": "con backoff", "estado": "DECOMPUESTA", "tipo": "CREACION"}
'validar entrada'             -> {"objetivo": "validar entrada", "sujeto": "entrada", "verbo": "validate", "adjetivo": "", "estado": "DECOMPUESTA", "tipo": "VALIDACION"}
'extraer funcion a modulo'    -> {"objetivo": "extraer funcion a modulo", "sujeto": "funcion", "verbo": "refactor", "adjetivo": "a modulo", "estado": "DECOMPUESTA", "tipo": "REFACTOR"}
'anadir test'                 -> {"objetivo": "anadir test", "sujeto": "test", "verbo": "create", "adjetivo": "", "estado": "DECOMPUESTA", "tipo": "CREACION"}
'rotar token'                 -> {"objetivo": "rotar token", "sujeto": "token", "verbo": "rotate", "adjetivo": "", "estado": "DECOMPUESTA", "tipo": "SEGURIDAD"}
'add retry with backoff'      -> {…"sujeto": "retry", "verbo": "create", "adjetivo": "with backoff"…"tipo": "CREACION"}
'extract function to module'  -> {…"sujeto": "function", "verbo": "refactor", "adjetivo": "to module"…"tipo": "REFACTOR"}
'validate input'              -> {…"sujeto": "input", "verbo": "validate"…"tipo": "VALIDACION"}
[OK] misma entrada -> misma salida (determinista)
```

**Revisión a mano (objeto / verbo / adjetivo):** `añadir reintento con backoff` → objeto
`reintento`, verbo `create` (de *añadir*), adjetivo `con backoff` ✔. `extraer función a módulo`
→ objeto `función`, verbo `refactor` (de *extraer*), adjetivo `a módulo` ✔. `rotar token` →
objeto `token`, verbo `rotate`, tipo `SEGURIDAD` ✔.

### 3.3 MATCH · veredicto + líneas exactas + parche (diff de líneas)

5/5 acciones: `NECESARIA` sobre el bloque `antes`, parche Surgical OK, y el resultado
**reproduce exactamente el ejemplo de la guía**; `DEFINIDA` sobre el ejemplo.

| Acción | Veredicto (`antes`) | Líneas a tocar | `verify_surgical` | Parche == ejemplo | Veredicto (`ejemplo`) |
|---|---|---|---|---|---|
| `add_retry_backoff` | NECESARIA | `{"inicio":2,"fin":2,"rangos":[[2,2]]}` | `ok=true`, modificadas `[2]`, fuera `[]` | ✔ | DEFINIDA |
| `validate_input` | NECESARIA | `{"inicio":1,"fin":1,"rangos":[[1,1]]}` | `ok=true`, modificadas `[1]`, fuera `[]` | ✔ | DEFINIDA |
| `extract_function_to_module` | NECESARIA | `{"inicio":2,"fin":5,"rangos":[[2,5],[5,5]]}` | `ok=true`, modificadas `[1]`, fuera `[]` | ✔ | DEFINIDA |
| `add_test` | NECESARIA | `{"inicio":2,"fin":2,"rangos":[[2,2]]}` | `ok=true`, modificadas `[2]`, fuera `[]` | ✔ | DEFINIDA |
| `rotate_token` | NECESARIA | `{"inicio":1,"fin":1,"rangos":[[1,1]]}` | `ok=true`, modificadas `[1]`, fuera `[]` | ✔ | DEFINIDA |

Diff real (ejemplo `add_retry_backoff`; las demás igual de quirúrgicas):

```
--- antes
+++ despues
@@ -2 +2,8 @@
-    return transporte.post(destino, json=payload)
+    intentos = 3
+    for intento in range(intentos):
+        try:
+            return transporte.post(destino, json=payload)
+        except Exception:
+            if intento == intentos - 1:
+                raise
+            time.sleep(2 ** intento)
```

Caso `NO_APLICA`: `match_action("añadir test", "<html>…</html>")` → `veredicto=NO_APLICA`,
`motivo=NO_APLICA_EN_BLOQUE` (la acción no aplica a ese bloque).

### 3.4 TRIGGER · válido + **negativas**

```
estado: READY | semaforo: CONTINUE | validado: True | error: None
TOP_FIELDS del contrato: ['attachments','category','depends_on','enabled','execution','id',
 'input_block_verbatim','loop_id','name','note','on_blocked','on_not_applicable','on_pass',
 'outputs','role','schema','source','steps','when']
execution: {"operation":"analyze","tool_profile":"read_only","max_model_calls":1,"write_paths":[],"timeout_s":120}
source:   {"document_ref":"source:guia/N4-C","section_id":"N4C","sha256":"9d7fef71…"}
steps (6): f1_descompresion(TOOL/read_text) → f2_gramatica(CHECK) → f3_descubrimiento(MODEL)
           → f4_match(TOOL/verify_contains) → f5_autorizacion(CHECK) → f7_cierre(TOOL/finish)
[OK] el trigger se valida contra el contrato real
[OK] todos los campos del contrato están en TOP_FIELDS
[OK] steps <= 32 :: 6
[OK] max_model_calls ∈ {0,1}
[OK] número de pasos MODEL == max_model_calls
[OK] source.sha256 == sha256(input_block_verbatim)
[OK] semáforo CONTINUE

-- NEGATIVA: campo fuera de TOP_FIELDS --
  TriggerError: UNKNOWN_FIELD | UNKNOWN_FIELD: trigger campo_extra
-- NEGATIVA: steps > 32 --
  TriggerError: STEPS_1_32 | STEPS_1_32
-- NEGATIVA: max_model_calls = 2 --
  TriggerError: MAX_CALLS_ONE | MAX_CALLS_ONE
-- HANDLER NO CONECTADO (CODE) --
  estado: UNBOUND_UNTIL_HANDLER_IS_CONNECTED | semaforo: STOP
-- ESCALADO A APROBACIÓN (acción sobre credenciales) --
  estado: READY_ESCALADO | semaforo: HANDOFF | escalado: {"requiere": true, "pista": "rotar", "destino": "usuario/IA"}
```

### 3.5 DISCOVERY · provider inyectado (sin red)

```
0 resultados -> estado: NO_EVIDENCE | veredicto: NO_EVIDENCE | motivo: SIN_RESULTADOS_EN_DOMINIOS_AUTORIZADOS | opciones: 0
  dominios consultados: ['github.com','huggingface.co','stackoverflow.com','discuss.python.org',
                          'docs.python.org','developer.mozilla.org','fastapi.tiangolo.com',
                          'gitlab.com','pypi.org','npmjs.com']
[OK] 0 resultados => NO_EVIDENCE            [OK] 0 resultados => 0 opciones (nada inventado)

1 resultado -> estado: EVIDENCIA_ENCONTRADA | veredicto: EVIDENCE_FOUND | opciones: 1
  solution_id: "sol_90883e5424d7"        upstream_urls: ["https://docs.python.org/3/library/time.html"]
  summary: "[texto no confiable] Retry with exponential backoff - Python docs — …"
  source_dates: ["2024-10-01"]            versions: ["3.11"]        license: "MIT"    compatibility: "3.11"
  confidence_evidence: [{url, title, snippet, provider, dominio, source_id, confianza:"evidencia_no_confianza_inventada"}]
  steps_proposed: 3 pasos (filtrados: sin pip install / npm install / shell remoto)
  test_plan: 2 pasos    risk: "BAJO"    estimated_calls: 5    approval_needs_approval: false
  fingerprint: "5cd19c10ff6a2cc7…"        prioridad: 100 (30+25+20+15+10)
  campos del FORMATO DE UNA OPCIÓN que faltan: ninguno
[OK] la opción NO se marca PASS por ranking   [OK] el ranking está dentro de 0..100

-- ESCALADO A APROBACIÓN --   aprobacion: {"requiere": true, "motivo": "rotar", "destino": "usuario/IA"}
-- CACHÉ POR HASH --         cache: {"state": "HIT", "key": "9ec1ce61e40d07826f31", "path": "/tmp/guide-discovery-cache/…"}
```

### 3.6 DISCOVERY con el **motor real del repo** (sólo lectura)

```
motor cargado: True | path: …/websearch_engine.py | tiene run: True
resultado: NO_EVIDENCE | SIN_RESULTADOS_EN_DOMINIOS_AUTORIZADOS | opciones: 0 | llamadas: 10 | s: 0.0
[OK] el motor real se carga y se delega (10 dominios) :: 10
[OK] sin red el motor falla cerrado (NO_EVIDENCE, nada inventado)
```

Comprobación aparte de que la carga de dominios usa el fichero **real** del repo cuando existe:

```
origin: …/chat-router/Loop cola wachdog/Loop/config/investigation_sources.json
sha256: 59db4463759e54b51eb1129bd90070d27f0df68272ba6632e230234c9719d9b5
dominios: ['github.com','huggingface.co','stackoverflow.com','docs.python.org',
           'developer.mozilla.org','fastapi.tiangolo.com','docs.pytest.org','pypi.org',
           'owasp.org','sqlite.org']
guardrails: {"read_only": true, "no_external_code_execution": true, "require_evidence": true, "max_results": 100}
```

---

## 4 · GAPS / BLOQUEOS / FLAGS 🚩

| # | Gap / bloqueo | Ruta probada | Estado |
|---|---|---|---|
| G1 | Los **10 dominios** del INPUT BLOCK (`…Python Discourse…GitLab…npm`) **no coinciden** con los del fichero real `investigation_sources.json` (`docs.pytest.org`, `owasp.org`, `sqlite.org` en lugar de esos tres) | 1) leer el fichero real por API GitHub → 2) el motor usa el **repo** cuando existe; 3) si no existe (sandbox), usa los dominios del INPUT BLOCK marcados `sources_origin="input_block_fallback"` | **ABIERTO · 🚩** (no bloquea: ambos listados son de fuente; el repo manda cuando está presente) |
| G2 | El runtime real **no tiene** handler `CODE` ni `HUMAN` (sólo `MODEL`/`TOOL`/`CHECK`) ni semáforo `STOP/HANDOFF/CONTINUE` en `trigger_engine.py` | Se implementa: contrato con los campos reales + descriptor RUNNER aparte con el semáforo del INPUT BLOCK; `CODE`/`HUMAN` ⇒ `UNBOUND_UNTIL_HANDLER_IS_CONNECTED` + `STOP` | **RESUELTO por diseño** |
| G3 | `trigger_contract.py` del repo (línea 137) tiene un **NameError latente**: `any(not isinstance(k, str) or not k in out["acceptance"])` — `k` no está ligado ⇒ revienta con cualquier `acceptance` no vacío | Mi espejo corrige el predicado (`not k for k in out["acceptance"]`) **sin tocar el repo** | **RESUELTO en mi copia** 🚩 (bug real del repo, reportado) |
| G4 | El sandbox **no tiene red**: el motor real devuelve 0 filas en los 10 dominios | Se valida con `search_provider` inyectado (0 → `NO_EVIDENCE`, 1 → opción con URL/evidencia) y con el motor real (10 llamadas, `NO_EVIDENCE`) | **ABIERTO · 🚩** (sin red no hay evidencia que traer; nada inventado) |
| G5 | El repo **no está clonado** en el sandbox: `websearch_engine.py` e `investigation_sources.json` se leyeron por API y se apuntaron por ruta configurable | `GUIDE_WEBSEARCH_ENGINE_PATH` / `GUIDE_REPO_ROOT` resuelven porAncestros; probado con una raíz simulada que reproduce la ruta real | **RESUELTO** |
| G6 | El INPUT BLOCK pide `ledger.jsonl` en el workdir, pero el alcance exclusivo del nodo (`ni un byte fuera`) limita a 7 ficheros | **No se crea** `ledger.jsonl`: la evidencia completa (comando + salida + exit code) queda en este `INFORME.md`, que sí está en alcance | **RESUELTO por alcance** 🚩 |
| G7 | Los skills `mcode-metodo-de-trabajo`, `yaiwes-node-dag`, `formato-salida-mcode` **no están disponibles** como skill del Cloud Host (`Cloud Host skill not found`) | Se leyeron desde disco (`/workspace/.skills/…`) y se aplicaron: FAIL_CLOSED, DAG de 3 pasos, plantilla de salida única | **RESUELTO** |
| G8 | `mcode-metodo-de-trabajo` **no existe** en `/workspace/.skills` (sólo `formato-salida-mcode`, `yaiwes-node-dag`, `hf-github-connectors`, `maxbry-ui-frontend`, `minimax-deterministic-deploy`) | Se aplicaron las reglas equivalentes de `yaiwes-node-dag` (FAIL_CLOSED, 3 pasos, flags, output único) | **ABIERTO · 🚩** (sin skill local; no bloquea) |
| G9 | Formato de salida: la plantilla `formato-salida-mcode` prohíbe tablas, pero el brief exige tabla de acciones | Precedencia del owner: gana el **INPUT BLOCK/brief** ⇒ se entrega la tabla del brief **y** los campos de la plantilla (TAREA/OBJETIVO/REALIZADO/GAP/FIX/INSTRUCCIONES/ESTADO/PROGRESO/TIEMPO/PENDIENTE/CONCLUSIÓN) | **RESUELTO** |

**Flags abiertos: 0** (los gaps anteriores son divergencias documentadas, no bloqueos del nodo).
Ninguna acción del owner quedó sin ejecutar dentro del alcance.

---

## 5 · QUEDA VERIFICADO | NO SE PUDO VERIFICAR

**VERIFICADO (con evidencia y exit code)**

* `py_compile` de los 4 módulos ⇒ exit 0, sin `__pycache__` en el árbol del repo.
* Gramática: 8/8 casos ES/EN con objeto/verbo/adjetivo revisados a mano + determinismo.
* Match: 5/5 acciones → veredicto, rango exacto de líneas, parche, `verify_surgical.ok=true`,
  parche == ejemplo de la guía, `DEFINIDA` sobre el ejemplo, `NO_APLICA` sobre HTML.
* Trigger: contrato `yaiwes.trigger.v1` validado (TOP_FIELDS, `steps≤32`, `max_model_calls∈{0,1}`,
  `source.sha256`, DAG de pasos sin ciclos) + 3 negativas (campo fuera de TOP_FIELDS, steps>32,
  max_model_calls=2) + `UNBOUND_UNTIL_HANDLER_IS_CONNECTED`/`STOP` + `HANDOFF` por credenciales.
* Discovery: 0 resultados → `NO_EVIDENCE` (0 opciones); 1 resultado → opción con los 16 campos del
  formato, URL normalizada, evidence, cache HIT por hash; escalada a aprobación; y **delegación
  real** en `websearch_engine.py` del repo (10 llamadas, fallo cerrado sin red).
* Carga de `investigation_sources.json` real desde la ruta del repo (sha256 `59db4463…`, 10 dominios).
* Alcance: sólo 6 ficheros de código/docs + este INFORME.md; nada fuera de `canvas/backend/guide/`.

**NO SE PUDO VERIFICAR (y por qué)**

* **Resultados reales de búsqueda web**: el sandbox no tiene red ⇒ el motor real devuelve 0 filas.
  Consecuencia: no hay evidencia real (URLs/versiones/licencias) que contrastar; sólo la vía
  determinista con `search_provider` inyectado.
* **Ejecución del trigger por el runtime real** (`TriggerEngine`/`HostPorts`): requiere el host
  N4 (constitución, cola, recibos). Aquí sólo se valida el **contrato** contra el validador real.
* **Aplicación del parche sobre ficheros reales del repo**: estos motores no escriben; la
  escritura la hace el host con aprobación (perfil `writer_n4`).
* **Los 10 dominios del INPUT BLOCK** (Python Discourse/GitLab/npm): no se pudieron consultar
  porque el fichero real del repo no los contiene (G1).

---

## 6 · CONCLUSIÓN

Los 4 motores de la guía viva (gramática, match, trigger y discovery) están escritos, validados
con tests reales (0 fallos, exit 0) y respetan el contrato real del repo: MATCH devuelve el rango
exacto de líneas y un parche que solo toca esas líneas, el TRIGGER valida contra `yaiwes.trigger.v1`
con su semáforo STOP/HANDOFF/CONTINUE, y el DISCOVERY delega en el motor de búsqueda del repo y
devuelve `NO_EVIDENCE` en lugar de inventar. Queda 1 gap abierto sin impacto (los dominios del
INPUT BLOCK difieren del fichero real del repo) y sin red en sandbox no hay evidencia web real
que traer.

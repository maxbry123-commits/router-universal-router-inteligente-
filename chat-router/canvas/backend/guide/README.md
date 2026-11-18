# GUÍA VIVA + MOTORES DE ACCIÓN (N4‑C)

Motor Python de la ventana **V2 · Diff + editor quirúrgico**. Cada punto de la guía es un
motor (mini‑ingeniero) que replica la acción: **decide si esa acción YA ESTÁ DEFINIDA o si es
NECESARIA** y produce **la ADICIÓN o REFACTORIZACIÓN de SÓLO las líneas necesarias**.

Todo es **determinista** (sin LLM dentro de los motores de decisión), **FAIL‑CLOSED**
(sin evidencia ⇒ `NO_EVIDENCE` / `NEEDS_REVIEW`, nunca PASS) y **stdlib‑only**.

---

## 1 · FICHEROS

| Fichero | Función |
|---|---|
| `grammar.py` | Descomposición gramatical determinista de una acción → `{objetivo, sujeto, verbo, adjetivo, estado, tipo}` |
| `match.py` | MIRROR del bloque de código contra el EJEMPLO de la guía → veredicto + **líneas exactas** + parche quirúrgico + verificación de que el parche no toca nada más |
| `trigger.py` | Acción → contrato JSON `yaiwes.trigger.v1` (validado) + descriptor RUNNER con fases/pasos independientes y semáforo `STOP｜HANDOFF｜CONTINUE` |
| `discovery.py` | Búsqueda de la acción en los dominios autorizados, **delegando en el motor de búsqueda real del repo**; devuelve OPCIONES con evidencia o `NO_EVIDENCE` |
| `guide_actions.json` | Catálogo vivo de acciones: señales, ancla, forma esperada del parche y ejemplo (`antes` / `ejemplo`) |
| `INFORME.md` | Detalle de ejecución, evidencia (comando + salida + exit code) y gaps |

---

## 2 · CONTRATOS

### 2.1 `grammar.decompose(texto) -> dict`

```json
{"objetivo":"añadir reintento con backoff","sujeto":"reintento","verbo":"create",
 "adjetivo":"con backoff","estado":"DECOMPUESTA","tipo":"CREACION"}
```

* `verbo` = verbo **canónico** (create, remove, refactor, validate, convert, render, audit,
  deploy, test, document, rotate). La forma en superficie (añadir/add/…) está en
  `grammar.VERB_LEXICON` y se expone con `grammar.lexicon()`.
* `adjetivo` = calificador final (`con backoff`, `a módulo`, `de acceso`). Vacío si la acción
  no lleva calificador.
* `estado` = `DECOMPUESTA` (verbo+sujeto) · `PARCIAL` (verbo, sin sujeto) · `AMBIGUA` (sin verbo).
* `tipo` = `CREACION｜ELIMINACION｜REFACTOR｜VALIDACION｜CONVERSION｜RENDER｜AUDITORIA｜DEPLOY｜TEST｜DOCS｜SEGURIDAD`.
* ES y EN. Sin LLM, sin red, sin I/O. Misma entrada ⇒ misma salida.

### 2.2 `match.match_action(accion, codigo) -> dict`

```json
{"veredicto":"NECESARIA","motivo":"NINGUNA_SENAL_PRESENTE",
 "lineas":{"inicio":2,"fin":2,"rangos":[[2,2]]},
 "lineas_originales":["    return transporte.post(destino, json=payload)"],
 "lineas_nuevas":["    intentos = 3","    for intento in range(intentos):", "…"],
 "parche":{"operaciones":[…],"diff_unificado":"@@ -2 +2,8 @@ …"}}
```

| Veredicto | Significado |
|---|---|
| `DEFINIDA` | Todas las `senales_requeridas` del ejemplo aparecen en el bloque |
| `PARCIAL` | Aparecen algunas ⇒ hay que completar |
| `NECESARIA` | No aparece ninguna ⇒ hay que añadir |
| `NO_APLICA` | La acción no aplica a ese bloque (lenguaje/dominio) |

`match.apply_match(codigo, resultado)` aplica el parche y `match.verify_surgical(antes, despues, resultado)`
comprueba con un **diff de líneas** que **sólo** se han tocado las líneas declaradas
(`ok`, `lineas_modificadas`, `lineas_fuera_de_rango`). El parche **nunca** reescribe el bloque entero.

### 2.3 `trigger.build_trigger(accion, …) -> dict`

Devuelve `{"contrato", "runner", "estado", "semaforo", "validado", "error", "gramatica"}`.

* El **contrato** usa **exclusivamente** los `TOP_FIELDS` del runtime real
  (`chat-router/Loop cola wachdog/Loop/nct_loop/trigger_contract.py`):
  `schema, id, loop_id, name, category, enabled, note, role, source, input_block_verbatim,
  attachments, depends_on, when, execution, steps, outputs, on_pass, on_not_applicable, on_blocked`.
* `steps` entre 1 y 32 · `execution.max_model_calls ∈ {0,1}` (y debe coincidir con el nº de
  pasos `kind=="MODEL"`) · `source.sha256 = sha256(input_block_verbatim)` ·
  `source_anchor_ref` real (`ancla:…`) cuando se declara `original_document_sha256`.
* `trigger.validate_trigger(contrato)` lanza `TriggerError` con código estable
  (`UNKNOWN_FIELD`, `STEPS_1_32`, `MAX_CALLS_ONE`, `SOURCE_SHA_MISMATCH`, `PATH_OUT_OF_SCOPE`, …).
* El **RUNNER** (descriptor, fuera del contrato para no añadir campos) trae las fases
  independientes del pipeline y el **semáforo**:

| Semáforo | Cuándo |
|---|---|
| `CONTINUE` | Todo conectado y sin escalado |
| `HANDOFF` | La acción o la evidencia habla de AUTORIZACIÓN / ADVERTENCIA / credenciales ⇒ se escala a usuario/IA |
| `STOP` | No existe handler conectado (`CODE`, `HUMAN`) ⇒ `UNBOUND_UNTIL_HANDLER_IS_CONNECTED` + bloqueo. Nunca una cadena vacía `MODEL → inspect_workspace → CHECK` |

Mapeo del vocabulario del INPUT BLOCK al contrato real:
`node_id→id`, `depends_on→depends_on`, `condition→when`, `inputs→source + steps[].args`,
`tool/handler→steps[].kind + steps[].tool`, `outputs→outputs.required_fields`,
`acceptance→outputs.acceptance`.

### 2.4 `discovery.discover(accion, …) -> dict`

* **NO hay crawler propio**: delega en `motores de descarga y extracción/➡️📂 motor de búsqueda/websearch_engine.py`
  (import por ruta configurable) o en un `search_provider` **inyectado con la misma firma**
  `provider(query, providers, limit, root) -> dict`.
* Dominios: los 10 de `chat-router/Loop cola wachdog/Loop/config/investigation_sources.json`.
  Máximo 10 dominios por ciclo, 2–5 resultados por dominio, timeout y presupuesto configurables.
* Normaliza URLs (mismo criterio que `websearch_engine.canon`), filtra por relevancia de dominio,
  cachea por hash (sha256 de query+dominios+providers+límite) y **revalida** al releer.
* Devuelve **OPCIONES** con los 16 campos del formato:
  `solution_id, gap_ids, summary, steps_proposed, upstream_urls, source_dates, versions,
  confidence_evidence, compatibility, license, files_affected, risk, test_plan, estimated_calls,
  approval_needs_approval, fingerprint`.
* Sin evidencia ⇒ `NO_EVIDENCE` (0 opciones, nada inventado). Con evidencia incompleta ⇒ `NEEDS_REVIEW`.
* Priorización `0..100` = 30 reproducibilidad + 25 evidencia oficial/upstream + 20 compatibilidad
  + 15 tests propuestos + 10 coste/impacto. **El ranking NO marca PASS** (el estado es
  `EVIDENCIA` / `NEEDS_REVIEW`).

---

## 3 · USO

```python
import sys; sys.path.insert(0, "chat-router/canvas/backend/guide")
import grammar, match, trigger, discovery

grammar.decompose("añadir reintento con backoff")

cat = match.load_catalog()
res = match.match_action("añadir reintento con backoff", codigo_antes, catalog=cat)
nuevo = match.apply_match(codigo_antes, res)
assert match.verify_surgical(codigo_antes, nuevo, res)["ok"]

built = trigger.build_trigger(
    "añadir reintento con backoff",
    input_block_verbatim=texto_del_bloque,      # literal
    document_ref="source:guia/N4-C",
    section_id="N4C",
    target_path="chat-router/canvas/backend/guide/ejemplo.py",
)
trigger.validate_trigger(built["contrato"])      # levanta TriggerError si algo no cuadra

discovery.discover("añadir reintento con backoff")            # motor del repo
discovery.discover("…", provider=mi_provider_de_prueba)       # sin red
```

---

## 4 · VARIABLES DE ENTORNO

| Variable | Por defecto | Para qué |
|---|---|---|
| `GUIDE_WEBSEARCH_ENGINE_PATH` | auto (ruta del repo) | Ruta exacta de `websearch_engine.py` |
| variable GUIDE_REPO_ROOT | auto (ancestros del módulo) | Raíz del repo; el motor de búsqueda y su catálogo de fuentes se resuelven desde backend/guide/discovery.py |
| variable GUIDE_INVESTIGATION_SOURCES | auto | Ruta de investigation_sources.json (vive en la configuración del LOOP, fuera del árbol del canvas) |
| variable GUIDE_ACTIONS_CATALOG | backend/guide/guide_actions.json | Ruta del catálogo de acciones |
| `GUIDE_SEARCH_PROVIDERS` | `duckduckgo,ddgs` | Proveedores del motor de búsqueda |
| `GUIDE_SEARCH_TIMEOUT_SECONDS` | `15` | Timeout de red |
| `GUIDE_DISCOVERY_BUDGET_TOKENS` | `5000` | Presupuesto de contexto por ciclo |
| `GUIDE_DISCOVERY_CACHE_DIR` | `$TMPDIR/guide-discovery-cache` | Caché por hash (fuera del repo) |
| `GUIDE_DISCOVERY_CACHE_TTL_SECONDS` | `21600` | TTL de la caché |

---

## 5 · LÍMITES Y GUARDRAILS

* **Cero red obligatoria**: los motores de decisión son deterministas; sólo `discovery` usa red
  y siempre a través del motor autorizado del repo.
* **Cero credenciales**: los tokens viajan por variable de entorno; el motor nunca imprime,
  escribe ni guarda secretos; las URLs con `user:pass@` se descartan.
* **Sin `pip install` / `npm install` / shell remoto**: `discovery` filtra esos pasos y los
  sustituye por "revisar manualmente la fuente".
* **Texto web no confiable**: cada `summary` va marcado como `[texto no confiable]` y
  `confidence_evidence` contiene **evidencia**, nunca una confianza inventada.
* **FAIL‑CLOSED**: ancla no encontrada, extracción no equivalente, parche que exceda
  `lineas_max`, motor ausente o proveedor caído ⇒ `NEEDS_REVIEW` / `NO_EVIDENCE` + motivo exacto.
* **Alcance de escritura**: estos módulos NO escriben en disco. El parche se devuelve como
  estructura (`parche.operaciones` + `diff_unificado`); la escritura la hace el host con
  aprobación (perfil `writer_n4`, un único `write_text` por trigger).
* **No toca el repo**: los módulos son nuevos y viven en `canvas/backend/guide/`.

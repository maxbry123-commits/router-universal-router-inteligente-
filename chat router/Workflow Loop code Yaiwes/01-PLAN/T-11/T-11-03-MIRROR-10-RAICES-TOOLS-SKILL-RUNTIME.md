# T-11 — MIRROR FACTORY + 10 RAÍCES + TOOLING NATIVO

## 1. Mirror Factory

Objetivo:
`NEW PROJECT/TASK → MIRROR PLAN → ISOLATED TEAM → EXECUTION → CENTRAL SUPERVISION`

Schema:

```yaml
schema: yaiwes.mirror/v1
mirror_id:
parent_project:
parent_task:
base_sha:
created_at:
orchestrator:
children:
  hermes:
    parent_id:
    child_id:
  openclaw:
    parent_id:
    child_id:
roles:
  - researcher
  - sentinel
  - supervisor
authority:
  sheriff: central
  judge: central
write_scopes: []
state_path:
evidence_path:
```

Reglas:
- Orquestador central crea y destruye mirrors.
- Hermes/OpenClaw centrales controlan sus hijos.
- Los hijos no cambian políticas globales.
- Sheriff/Judge siguen siendo código/autoridad central; el mirror consume sus gates.
- Un mirror no escribe fuera de sus scopes.
- Todo mirror tiene TTL/lease/heartbeat y handoff.

## 2. Separación en 10 raíces

El Director enumeró diez dominios. Se implementan como **destinos lógicos obligatorios** y solo se materializan cuando existe contenido real.

```text
chat router/
├── 01 Chat frontend/
├── 02 Plugins Hermes harness/
├── 03 Agente/
├── 04 Input y buscadores/
├── 05 Workflow/
├── 06 Memoria/
├── 07 Formato de salida/
├── 08 Componentes asociados/
├── 09 Tools y pools/
└── 10 Otros/
```

### Regla anti-ruptura

No hacer:

`mv masivo → arreglar después`

Hacer:

`INVENTARIO → DEPENDENCY MAP → MOVE 1 LOTE → UPDATE REFERENCES → TEST → COMMIT → NEXT`

Cada archivo en `ROOT-MAP-T11.yaml`:

```yaml
- source:
  destination:
  reason:
  owner:
  imports_in:
  imports_out:
  runtime_refs:
  tests:
  status: KEEP|MOVE_CANDIDATE|MOVED|COMPAT
```

## 3. Ubicación funcional

### 01 Chat frontend
Shell, paneles, assets, cliente API, browser test adapters del chat.

### 02 Plugins Hermes harness
Adapters/contratos de Hermes/OpenClaw/DeepSeek harness y enchufe; no duplicar motores centrales.

### 03 Agente
Schemas de workers, bootstrap, mirror children, role/capability contracts.

### 04 Input y buscadores
InputParser, QueryCompiler, SearchFanout, Extractor, Ranker, EvidencePacket.

### 05 Workflow
DSL/DAG, templates LOCKED, scheduler/orchestrator adapters, finalize pipeline.

### 06 Memoria
State Hub adapters, task persistence, reducers, HF bridge, DB adapters ya reales.

### 07 Formato de salida
Result schemas, Claim schemas, ResearchResult, receipts, renderers.

### 08 Componentes asociados
Componentes OSS integrados, manifests, source metadata; no runtime core si solo son vendor/source.

### 09 Tools y pools
Tool registry, typed tool adapters, worker pools reales, motor búsqueda/descarga como tools.

### 10 Otros
Solo artefactos que no encajen tras justificarlo. No es un vertedero.

## 4. Hermes/OpenClaw: tool nativo de búsqueda y descarga

T-11 no adivina rutas. El agente debe:

```text
SEARCH REPO
→ LOCATE REAL ENGINE
→ READ CONTRACT
→ IDENTIFY ENTRYPOINT
→ WRAP AS TYPED TOOL
→ SHERIFF POLICY
→ TEST
→ REGISTER
```

Contrato ejemplo:

```json
{
  "tool_id": "repo.search_engine",
  "entrypoint": "<REAL_PATH>",
  "inputs_schema": {},
  "outputs_schema": {},
  "side_effects": [],
  "permissions": [],
  "evidence": true
}
```

Para descarga/extracción:
- conservar la vía RDC/autorizada del baseline;
- Hermes/OpenClaw invocan el motor;
- NO implementan su propio downloader;
- resultado exige evidence/hash/read-back.

## 5. Enchufe Fables / DeepSeek harness

Antes de cualquier movimiento:
1. localizar ruta real;
2. leer archivos/contrato;
3. registrar dependencias;
4. decidir destino lógico;
5. mover solo si imports y runtime pueden actualizarse sin ruptura;
6. test completo;
7. compat shim solo si necesario.

## 6. Conversión genérica SKILL → runtime ejecutable

```text
SKILL.md
→ PARSE SPEC
→ SKILL CONTRACT
→ JSON/YAML SCHEMA
→ PYTHON ADAPTER
→ TOOL REGISTRY
→ SHERIFF POLICY
→ CONTRACT TESTS
→ EXECUTABLE
```

Schema base:

```yaml
schema: yaiwes.skill-runtime/v1
id:
source:
version:
inputs:
outputs:
preconditions:
capabilities:
tools:
side_effects:
permissions:
forbidden:
timeouts:
retries:
evidence:
tests:
entrypoint:
status: DOCUMENTATION_ONLY|ADAPTER_READY|EXECUTABLE|BLOCKED
```

Reglas:
- Nunca borrar el SKILL.md original.
- El SKILL.md no es autoridad ejecutable por sí solo.
- Cada side effect debe estar declarado.
- El adapter no amplía permisos.
- Si el skill contiene decisiones ambiguas, el schema las convierte en estados/condiciones o las deja como `requires_reasoning`; no fingir determinismo.
- SALIDA 3 aplicará este método a los skills concretos indicados por el Director.

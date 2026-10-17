# T-11-I+ — AUTONOMOUS SKILL INGEST
## Hermes / Hitman + OpenClaw / Ovni
### SKILL → SCHEMA → CODE → FABLES/DEEPSEEK HARNESS → TEST → REGISTRY → EXECUTABLE

---

# 0. AUDITORÍA DEL CHAT — 4 PASADAS

## PASADA 1 — ¿Qué sí quedó explicado?

Sí quedó definido:

- `NUEVO-01 … NUEVO-19`.
- Skill Runtime Contract.
- `SKILL.md → SCHEMA → ADAPTER → SHERIFF → REGISTRY → TEST → EXECUTABLE`.
- Skills concretos:
  - ECC
  - Task Observer
  - Local Ultra Review
  - UltraReview
  - Claude-Mem
  - GSD
  - Superpowers
  - Find Skills
  - Agent Skills como `PENDING_VERIFICATION`
- Mirror Factory.
- aislamiento de workers.
- State Hub.
- Evidence.
- Judge/Sheriff.
- separación DISPATCH / FINALIZE.

## PASADA 2 — ¿Qué faltó explicar con suficiente detalle?

Faltó explicar claramente:

1. cómo Hermes/OpenClaw detectan automáticamente una skill nueva;
2. cómo la descargan/adquieren sin ejecutarla;
3. cómo inspeccionan su estructura;
4. cómo crean automáticamente el contrato;
5. cómo generan el schema;
6. cómo generan el adapter Python;
7. cómo deciden si integrar por Fables o por DeepSeek Harness;
8. dónde vive cada archivo nuevo;
9. cómo registran la skill;
10. cómo prueban la skill antes de activarla;
11. cómo hacen rollback;
12. cómo impiden que una skill se dé permisos a sí misma;
13. cómo evitan instalar dos veces la misma skill;
14. cómo registran versión/source SHA;
15. cómo actualizan State/Bitácora/Handoff.

## PASADA 3 — Restricciones del sistema que no se pueden perder

La incorporación automática debe respetar:

```text
reuse > patch > adapt > generate
```

y:

```text
LLM propone
→ SHERIFF autoriza
→ TOOL ejecuta
→ RECEIPT demuestra
→ JUDGE decide
```

Además:

```text
NO_PASS_WITHOUT_EVIDENCE
NO_MUTATION_WITHOUT_AUTH
NO_STATE_WRITE_OUTSIDE_STATE_HUB
NO_TWO_WRITERS
NO_MODEL_OUTSIDE_OUR_ROUTER
```

La skill nunca obtiene autoridad por existir.

## PASADA 4 — Resultado de la auditoría

La pieza que faltaba es un:

```text
AUTONOMOUS SKILL INGEST ENGINE
```

Este motor debe permitir:

```text
HERMES / OPENCLAW
→ ENCONTRAR SKILL
→ SOLICITAR INGEST
→ INSPECCIONAR
→ COMPILAR CONTRATO
→ CREAR ADAPTER
→ REGISTRAR PLUGIN
→ SANDBOX TEST
→ SHERIFF
→ PROMOTE
→ EXECUTABLE
```

pero sin permitir:

```text
ENCONTRAR SKILL
→ EJECUTAR DIRECTAMENTE
```

---

# 1. IDENTIDAD DE LOS AGENTES

Usar estos alias de UI/configuración si ya fueron aprobados por el Director:

```yaml
agents:
  maxbry:
    legacy_name: rowboat
    display_name: "Orquestador Maxbry"

  optimus:
    legacy_name: ruflo
    display_name: "Optimus"

  hitman:
    legacy_name: hermes
    display_name: "Hitman"

  ovni:
    legacy_name: openclaw
    display_name: "Ovni"
```

En este documento:

```text
Hermes = Hitman
OpenClaw = Ovni
```

La lógica interna puede conservar IDs antiguos para no romper compatibilidad.

---

# 2. PRINCIPIO CENTRAL

Hermes y OpenClaw pueden **descubrir y solicitar incorporar** skills.

No pueden:

- instalar directamente;
- ejecutar código no inspeccionado;
- darse permisos;
- modificar Sheriff;
- modificar Judge;
- marcarse PASS;
- escribir fuera del project/write scope;
- saltarse sandbox;
- saltarse tests.

El control real lo hace código determinista.

---

# 3. FLUJO COMPLETO

```text
SKILL FOUND
↓
INGEST REQUEST
↓
SOURCE LOCK
↓
ACQUIRE
↓
ISOLATED SANDBOX
↓
INSPECT
↓
CLASSIFY
↓
COMPILE CONTRACT
↓
GENERATE SCHEMA
↓
BUILD PYTHON ADAPTER
↓
SELECT BRIDGE
├── FABLES
└── DEEPSEEK HARNESS
↓
REGISTER PLUGIN/FICHA
↓
SHERIFF VALIDATE
↓
UNIT TEST
↓
INTEGRATION TEST
↓
NEGATIVE TEST
↓
EVIDENCE
↓
JUDGE
↓
PROMOTE
↓
EXECUTABLE
```

---

# 4. DÓNDE DEBE IR EL CÓDIGO

## 4.1 Rutas existentes que deben reutilizarse

Fables:

```text
router inteligente universal/enchufe/
```

Archivos existentes del contrato Fables:

```text
universal_plugin_bus_v2_integrated.py
ficha_contract_v2.py
validator_v2.py
+ 2 MD de especificación
```

Ejecutor DAG existente:

```text
router inteligente universal/integration/chat_mvp/router.py
```

Plugin host existente:

```text
router inteligente universal/integration/plugin_host/
```

Fichas existentes:

```text
router inteligente universal/plugins/*/ficha.json
```

Runtime/control existente:

```text
chat router/runtime/
```

Estado:

```text
chat router/Workflow Loop code Yaiwes/03-ESTADO/
├── STATE.json
├── CRAZY_WALL.json
├── BITACORA.jsonl
└── HANDOFF.md
```

Agentes:

```text
chat router/Workflow Loop code Yaiwes/05-AGENTES/AGENTES.yaml
```

Contrato general:

```text
chat router/Workflow Loop code Yaiwes/01-PLAN/PLAN-DSL-DAG-00-CONTRATO.yaml
```

---

# 5. NUEVO MÓDULO A CREAR

Si todavía NO se materializó la refactorización de las 10 raíces:

```text
chat router/runtime/skills_runtime/
```

Crear:

```text
skills_runtime/
├── compiler.py
├── inspector.py
├── classifier.py
├── schema_validator.py
├── adapter_factory.py
├── bridge_selector.py
├── registry.py
├── installer.py
├── promoter.py
├── rollback.py
├── models.py
├── schemas/
│   ├── skill-runtime-v1.schema.json
│   ├── skill-ingest-v1.schema.json
│   └── skill-result-v1.schema.json
├── registry/
│   └── skills.yaml
├── skills/
│   └── <skill_id>/
│       ├── SOURCE.json
│       ├── CONTRACT.yaml
│       ├── adapter.py
│       ├── tests/
│       └── EVIDENCE.json
└── tests/
```

Si las 10 raíces YA existen físicamente, mapear el mismo módulo a:

```text
chat router/03 Agente/skills-runtime/
```

Regla:

```text
NO DUPLICAR LOS DOS ÁRBOLES.
```

Usar uno como canonical path y registrar el otro solo como migration/compat path si existe.

---

# 6. ADAPTERS DE INTEGRACIÓN

Los adaptadores que conectan una skill al Router NO deben mezclarse con el código interno de la skill.

Usar:

```text
router inteligente universal/integration/plugin_host/
```

Ejemplo:

```text
integration/plugin_host/
├── skill_ecc_adapter.py
├── skill_gsd_adapter.py
├── skill_claude_mem_adapter.py
└── skill_<id>_adapter.py
```

Cada skill registrada en Fables debe tener su ficha:

```text
router inteligente universal/plugins/<skill_id>/ficha.json
```

Ejemplo:

```json
{
  "schema": "yaiwes.plugin-ficha/v2",
  "id": "gsd",
  "kind": "skill",
  "adapter": "integration.plugin_host.skill_gsd_adapter",
  "runtime_contract": "chat router/runtime/skills_runtime/skills/gsd/CONTRACT.yaml",
  "enabled": false,
  "permissions": [],
  "healthcheck": true
}
```

`enabled=false` hasta completar tests + Judge.

---

# 7. CUÁNDO USAR FABLES

Usar Fables como integración nativa cuando la skill pueda representarse como:

- Python callable;
- CLI controlado;
- HTTP adapter;
- MCP tool;
- workflow tipado;
- función registrada.

Flujo:

```text
SKILL
→ PYTHON ADAPTER
→ FICHA
→ validator_v2.py
→ universal_plugin_bus_v2_integrated.py
→ ROUTER
```

Fables debe ser el bus.

La skill no habla directamente con el Router.

---

# 8. CUÁNDO USAR DEEPSEEK HARNESS

Usar DeepSeek Harness cuando la capacidad original esté diseñada principalmente como:

- harness de coding;
- workflow de agente de código;
- plugin pensado para un coding agent;
- skill que necesite un ciclo de edición/revisión propio.

Pero:

```text
DEEPSEEK HARNESS
≠ AUTORIDAD
```

Debe quedar detrás de:

```text
SKILL CONTRACT
→ SHERIFF
→ HARNESS ADAPTER
→ TOOL EXECUTION
→ EVIDENCE
```

No copiar ni reescribir el Harness.

El agente debe primero localizar su entrypoint REAL en el repo.

Si no lo encuentra:

```text
status = GAP
reason = DEEPSEEK_HARNESS_ENTRYPOINT_NOT_VERIFIED
```

No inventar la ruta.

---

# 9. SELECCIÓN AUTOMÁTICA DE BRIDGE

Crear:

```python
# bridge_selector.py

from enum import Enum


class Bridge(str, Enum):
    FABLES = "FABLES"
    DEEPSEEK_HARNESS = "DEEPSEEK_HARNESS"
    UNSUPPORTED = "UNSUPPORTED"


def select_bridge(inspected: dict) -> Bridge:
    interfaces = set(inspected.get("interfaces", []))
    category = inspected.get("category")

    native_interfaces = {
        "python_callable",
        "cli",
        "http",
        "mcp",
        "typed_workflow",
    }

    if interfaces & native_interfaces:
        return Bridge.FABLES

    if category in {
        "coding_harness_plugin",
        "coding_agent_workflow",
    }:
        return Bridge.DEEPSEEK_HARNESS

    return Bridge.UNSUPPORTED
```

Regla:

```text
UNSUPPORTED
→ PENDING_REVIEW
```

Nunca:

```text
UNSUPPORTED
→ GENERATE RANDOM INTEGRATION
```

---

# 10. INGEST REQUEST

Cuando Hitman/Hermes u Ovni/OpenClaw encuentran una skill:

```yaml
schema: yaiwes.skill-ingest/v1

request_id:
project_id:
requested_by: hitman|ovni
source:
  url:
  type: git|local|archive
  requested_ref:
skill_hint:
reason:
target_capability:
requested_at:
```

El agente SOLO crea esta petición.

No instala todavía.

---

# 11. SOURCE LOCK

Primero fijar la fuente:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceLock:
    url: str
    requested_ref: str | None
    resolved_sha: str
    source_hash: str
```

Guardar:

```text
skills/<skill_id>/SOURCE.json
```

Ejemplo:

```json
{
  "url": "https://github.com/example/skill",
  "requested_ref": "main",
  "resolved_sha": "abc123...",
  "source_hash": "sha256:...",
  "acquired_at": "..."
}
```

Esto impide que mañana `main` cambie y YAIWES ejecute otro código sin saberlo.

---

# 12. ADQUISICIÓN

La adquisición debe usar el método autorizado por el sistema.

Flujo:

```text
INGEST REQUEST
→ SOURCE LOCK
→ RDC / ACQUISITION ENGINE
→ SANDBOX
→ VERIFY HASH
```

La adquisición no implica instalación.

Estado:

```text
ACQUIRED_NOT_TRUSTED
```

---

# 13. INSPECTOR

Crear:

```python
# inspector.py

from pathlib import Path


KNOWN_MANIFESTS = {
    "pyproject.toml",
    "package.json",
    "requirements.txt",
    "setup.py",
    "Cargo.toml",
    "SKILL.md",
    "README.md",
}


def inspect_source(root: Path) -> dict:
    found = []

    for name in KNOWN_MANIFESTS:
        path = root / name
        if path.exists():
            found.append(name)

    interfaces = []

    if (root / "SKILL.md").exists():
        interfaces.append("skill_spec")

    if (root / "pyproject.toml").exists() or (root / "setup.py").exists():
        interfaces.append("python_package")

    if (root / "package.json").exists():
        interfaces.append("node_package")

    return {
        "root": str(root),
        "manifests": found,
        "interfaces": interfaces,
    }
```

El inspector:

- NO ejecuta setup;
- NO ejecuta hooks;
- NO instala paquetes;
- NO llama binarios del repo.

Solo lee.

---

# 14. CLASSIFIER

Crear clasificación determinista:

```python
def classify_skill(inspected: dict) -> dict:
    manifests = set(inspected["manifests"])
    interfaces = set(inspected["interfaces"])

    if "SKILL.md" in manifests:
        kind = "agent_skill"
    else:
        kind = "component"

    return {
        "kind": kind,
        "interfaces": sorted(interfaces),
        "requires_adapter": True,
    }
```

Cuando la clasificación no sea suficiente:

```text
UNKNOWN
→ PENDING_REVIEW
```

---

# 15. COMPILAR CONTRACT

Crear un contrato nunca más permisivo que la fuente.

```python
# compiler.py

def compile_contract(metadata: dict) -> dict:
    return {
        "schema": "yaiwes.skill-runtime/v1",
        "id": metadata["skill_id"],
        "name": metadata["name"],
        "source": metadata["source"],
        "classification": metadata["classification"],
        "inputs": metadata.get("inputs", {"required": []}),
        "outputs": metadata.get("outputs", {"required": []}),
        "tools_allowed": [],
        "permissions": {
            "read_paths": [],
            "write_paths": [],
            "network_domains": [],
            "commands": [],
        },
        "side_effects": {
            "filesystem": "none",
            "network": False,
            "process": False,
            "git": False,
            "memory": False,
        },
        "forbidden": [
            "bypass_sheriff",
            "self_pass",
            "undeclared_side_effect",
            "privilege_escalation",
        ],
        "status": "SCHEMA_READY",
    }
```

## Regla de mínimo privilegio

Empieza siempre en:

```text
NO WRITE
NO NETWORK
NO PROCESS
NO GIT
```

Los permisos se añaden únicamente si:

1. el funcionamiento real los requiere;
2. quedan declarados;
3. Sheriff los valida;
4. existe test negativo.

---

# 16. GENERAR ADAPTER PYTHON

El adapter traduce el contrato YAIWES a la interfaz real de la skill.

```python
# adapter.py

from typing import Any


class SkillAdapter:
    def __init__(self, backend):
        self.backend = backend

    def execute(self, invocation) -> dict[str, Any]:
        payload = self._build_payload(invocation)

        raw = self.backend.invoke(payload)

        return self._normalize(raw)

    def _build_payload(self, invocation):
        return {
            "task_id": invocation.task_id,
            "project_id": invocation.project_id,
            "input": invocation.input,
        }

    def _normalize(self, raw):
        return {
            "status": "EXECUTED",
            "output": raw,
            "evidence": [],
        }
```

El adapter NO:

- decide permisos;
- decide PASS;
- modifica Sheriff;
- modifica DAG;
- escribe fuera del scope.

---

# 17. FACTORY

Crear:

```python
# adapter_factory.py

def build_adapter(skill_id, bridge, backend):
    if bridge == "FABLES":
        return FablesSkillAdapter(
            skill_id=skill_id,
            backend=backend,
        )

    if bridge == "DEEPSEEK_HARNESS":
        return DeepSeekHarnessSkillAdapter(
            skill_id=skill_id,
            backend=backend,
        )

    raise RuntimeError(
        f"unsupported bridge for {skill_id}"
    )
```

---

# 18. FABLES ADAPTER

```python
class FablesSkillAdapter:
    def __init__(self, skill_id, backend):
        self.skill_id = skill_id
        self.backend = backend

    def execute(self, invocation):
        ficha = {
            "id": self.skill_id,
            "project_id": invocation.project_id,
            "task_id": invocation.task_id,
            "payload": invocation.input,
        }

        return self.backend.dispatch(ficha)
```

La ficha real debe validar contra:

```text
ficha_contract_v2.py
validator_v2.py
```

Si falla:

```text
PLUGIN_VALIDATION_FAILED
```

---

# 19. DEEPSEEK HARNESS ADAPTER

No asumir API que todavía no fue verificada.

Crear una interfaz neutral:

```python
class DeepSeekHarnessSkillAdapter:
    def __init__(self, skill_id, harness):
        self.skill_id = skill_id
        self.harness = harness

    def execute(self, invocation):
        request = {
            "skill_id": self.skill_id,
            "project_id": invocation.project_id,
            "task_id": invocation.task_id,
            "input": invocation.input,
            "write_scope": list(invocation.write_scope),
        }

        return self.harness.execute_skill(request)
```

Durante implementación real:

```text
LOCATE REAL HARNESS
→ READ API
→ MAP execute_skill()
→ TEST
```

Si `execute_skill()` no existe, adaptar al entrypoint real.

No modificar el Harness para que coincida con este ejemplo.

---

# 20. REGISTRY

Crear registry central:

```yaml
schema: yaiwes.skill-registry/v1

skills:

  gsd:
    contract: skills/gsd/CONTRACT.yaml
    adapter: skills/gsd/adapter.py
    bridge: FABLES
    status: EXECUTABLE
    source_sha:
    tested_sha:

  example-harness-skill:
    contract: skills/example/CONTRACT.yaml
    adapter: skills/example/adapter.py
    bridge: DEEPSEEK_HARNESS
    status: ADAPTER_READY
```

---

# 21. ACTIVACIÓN POR HERMES / OPENCLAW

Hermes y OpenClaw reciben un tool:

```text
request_skill_ingest
```

Contrato:

```json
{
  "name": "request_skill_ingest",
  "input": {
    "project_id": "string",
    "source_url": "string",
    "requested_ref": "string|null",
    "reason": "string",
    "target_capability": "string"
  }
}
```

No darles:

```text
install_anything()
enable_without_test()
grant_permission()
```

---

# 22. CÓDIGO DEL SERVICIO DE INGEST

```python
from enum import Enum


class IngestState(str, Enum):
    REQUESTED = "REQUESTED"
    ACQUIRED = "ACQUIRED"
    INSPECTED = "INSPECTED"
    SCHEMA_READY = "SCHEMA_READY"
    ADAPTER_READY = "ADAPTER_READY"
    TESTING = "TESTING"
    VERIFIED = "VERIFIED"
    EXECUTABLE = "EXECUTABLE"
    BLOCKED = "BLOCKED"


class SkillIngestService:
    def __init__(
        self,
        acquirer,
        inspector,
        compiler,
        adapter_factory,
        sheriff,
        tester,
        registry,
        promoter,
        state_hub,
    ):
        self.acquirer = acquirer
        self.inspector = inspector
        self.compiler = compiler
        self.adapter_factory = adapter_factory
        self.sheriff = sheriff
        self.tester = tester
        self.registry = registry
        self.promoter = promoter
        self.state_hub = state_hub

    def ingest(self, request):
        self.state_hub.emit(
            "SKILL_INGEST_REQUESTED",
            request,
        )

        acquired = self.acquirer.acquire(
            request["source"]
        )

        inspected = self.inspector.inspect(
            acquired.workspace
        )

        contract = self.compiler.compile(
            request=request,
            inspected=inspected,
            source_lock=acquired.source_lock,
        )

        if not self.sheriff.validate_contract(contract):
            return self._block(
                request,
                "SHERIFF_CONTRACT_DENY",
            )

        bridge = select_bridge(inspected)

        if bridge == Bridge.UNSUPPORTED:
            return self._block(
                request,
                "NO_SUPPORTED_BRIDGE",
            )

        adapter = self.adapter_factory.build(
            contract=contract,
            bridge=bridge,
            workspace=acquired.workspace,
        )

        tests = self.tester.run_all(
            contract=contract,
            adapter=adapter,
            workspace=acquired.workspace,
        )

        if not tests.all_pass:
            return self._block(
                request,
                "TEST_FAILURE",
            )

        registration = self.registry.stage(
            contract=contract,
            adapter=adapter,
            bridge=bridge.value,
            enabled=False,
        )

        promoted = self.promoter.promote(
            registration=registration,
            source_lock=acquired.source_lock,
        )

        self.state_hub.emit(
            "SKILL_INGEST_VERIFIED",
            promoted.receipt,
        )

        return {
            "status": "NEED_JUDGE",
            "receipt": promoted.receipt,
        }

    def _block(self, request, reason):
        self.state_hub.emit(
            "SKILL_INGEST_BLOCKED",
            {
                "request_id": request["request_id"],
                "reason": reason,
            },
        )
        return {
            "status": "BLOCKED",
            "reason": reason,
        }
```

---

# 23. JUDGE FINAL

Ni Hermes ni OpenClaw activan la skill.

Después de ingest:

```text
TESTS PASS
→ EVIDENCE
→ JUDGE
→ ACTIVATE
```

Ejemplo:

```python
def finalize_skill(
    skill_id,
    evidence,
    registry,
    judge,
):
    verdict = judge.verify(
        skill_id=skill_id,
        evidence=evidence,
    )

    if verdict != "PASS":
        return {
            "status": "BLOCKED"
        }

    registry.enable(skill_id)

    return {
        "status": "EXECUTABLE"
    }
```

---

# 24. TESTS OBLIGATORIOS

Cada skill nueva debe pasar:

```text
T01 schema valid
T02 source SHA pinned
T03 no path traversal
T04 no undeclared network
T05 no undeclared write
T06 no undeclared process
T07 Fables/DeepSeek adapter loads
T08 invalid ficha rejected
T09 invocation produces typed result
T10 evidence generated
T11 cross-project write denied
T12 duplicate install idempotent
T13 crash during install → rollback
T14 failed tests → not enabled
T15 agent cannot self-enable
```

---

# 25. IDEMPOTENCIA

Si Hermes y OpenClaw encuentran la misma skill:

```text
SOURCE URL + SOURCE SHA + SKILL ID
→ INGEST KEY
```

Código:

```python
import hashlib


def ingest_key(skill_id, source_url, source_sha):
    raw = (
        f"{skill_id}|{source_url}|{source_sha}"
    ).encode()

    return hashlib.sha256(raw).hexdigest()
```

Si key ya existe:

```text
RETURN EXISTING RECORD
```

No volver a instalar.

---

# 26. VERSIONADO

Una actualización de una skill es una nueva versión:

```text
skill_id
source_sha_old
source_sha_new
contract_hash_old
contract_hash_new
adapter_hash_old
adapter_hash_new
tests
```

Nunca reemplazar silenciosamente.

Flujo:

```text
CURRENT
→ NEW SANDBOX
→ TEST
→ DIFF
→ JUDGE
→ ATOMIC PROMOTE
```

---

# 27. ROLLBACK

Guardar versión activa anterior.

```python
def promote_atomically(current, candidate):
    verify(candidate)

    backup = current.snapshot()

    try:
        current.replace(candidate)
        healthcheck(current)
    except Exception:
        current.restore(backup)
        raise
```

Si falla healthcheck:

```text
ROLLBACK
→ ACTIVE_VERSION = PREVIOUS
```

---

# 28. QUÉ HACE HERMES / HITMAN

```text
ENCUENTRA SKILL
→ request_skill_ingest()
→ consulta estado
→ recibe VERIFIED/BLOCKED
```

Puede pedir incorporación.

No instala.

No activa.

No asigna permisos.

---

# 29. QUÉ HACE OPENCLAW / OVNI

```text
ENCUENTRA SKILL
→ request_skill_ingest()
→ supervisa health/progreso
→ verifica que exista receipt
→ consulta resultado
```

Puede supervisar.

No cambia Sheriff.

No cambia Judge.

---

# 30. QUÉ HACE EL ORQUESTADOR MAXBRY

```text
INGEST REQUEST
→ DAG
→ LOCK
→ ACQUIRE
→ INSPECT
→ COMPILE
→ TEST
→ REGISTER
→ JUDGE
```

Es la capa de coordinación.

---

# 31. QUÉ HACE OPTIMUS / RUFLO

Puede repartir tareas independientes:

```text
INSPECTION
SCHEMA TEST
ADAPTER TEST
SECURITY TEST
```

en paralelo.

Luego:

```text
FAN-IN
→ EVIDENCE PACKET
```

No declara PASS.

---

# 32. DSL/DAG

```yaml
schema: riu.dag/v1

id: T-11-I-SKILL-AUTO-INGEST

title: "Autonomous Skill Ingest — Hermes/OpenClaw"

needs:
  - T-11-I

input:
  schema: yaiwes.skill-ingest/v1

invariants:
  - NO_DIRECT_SKILL_EXECUTION
  - NO_AUTO_PERMISSION_ESCALATION
  - NO_SELF_PASS
  - SOURCE_SHA_REQUIRED
  - SANDBOX_REQUIRED
  - SCHEMA_REQUIRED
  - ADAPTER_REQUIRED
  - SHERIFF_REQUIRED
  - TESTS_REQUIRED
  - EVIDENCE_REQUIRED
  - JUDGE_REQUIRED

nodes:

  - id: SI-01
    action: REQUEST
    output: INGEST_REQUEST

  - id: SI-02
    action: SOURCE_LOCK
    needs: [SI-01]
    output: SOURCE_LOCK

  - id: SI-03
    action: ACQUIRE_SANDBOX
    needs: [SI-02]
    output: ACQUIRED_NOT_TRUSTED

  - id: SI-04
    action: INSPECT
    needs: [SI-03]
    output: INSPECTION_REPORT

  - id: SI-05
    action: COMPILE_CONTRACT
    needs: [SI-04]
    output: CONTRACT

  - id: SI-06
    action: SELECT_BRIDGE
    needs: [SI-05]
    choices:
      - FABLES
      - DEEPSEEK_HARNESS
      - UNSUPPORTED

  - id: SI-07
    action: BUILD_ADAPTER
    needs: [SI-06]
    output: ADAPTER

  - id: SI-08
    action: SHERIFF_VALIDATE
    needs: [SI-07]
    output:
      - ALLOW
      - DENY

  - id: SI-09
    action: TEST
    needs: [SI-08]
    parallel:
      - CONTRACT_TEST
      - INTEGRATION_TEST
      - NEGATIVE_TEST
      - SECURITY_TEST

  - id: SI-10
    action: REGISTER_DISABLED
    needs: [SI-09]

  - id: SI-11
    action: EVIDENCE
    needs: [SI-10]

  - id: SI-12
    action: JUDGE
    needs: [SI-11]

  - id: SI-13
    action: PROMOTE
    needs: [SI-12]

  - id: SI-14
    action: HEALTHCHECK
    needs: [SI-13]

  - id: SI-15
    action: FINALIZE
    needs: [SI-14]
```

---

# 33. HANDOFF PARA DEVIN

```text
ID:
T-11-I-SKILL-AUTO-INGEST

OBJETIVO:
Permitir que Hermes/Hitman y OpenClaw/Ovni soliciten
automáticamente la incorporación de una nueva skill,
sin que puedan instalarla, habilitarla ni otorgarle
permisos directamente.

IMPLEMENTAR:

1. Crear skills_runtime dentro del runtime canónico.
2. Reusar Fables existente; no crear otro plugin bus.
3. Reusar integration/plugin_host/.
4. Cada skill obtiene CONTRACT.yaml.
5. Cada skill obtiene SOURCE.json con SHA.
6. Cada skill obtiene adapter.py.
7. Cada skill obtiene tests.
8. Cada skill obtiene EVIDENCE.json.
9. Cada skill registrada en Fables obtiene ficha.json.
10. Ficha pasa validator_v2.py.
11. Crear bridge_selector.py.
12. Fables = bridge por defecto para interfaces tipadas.
13. DeepSeek Harness = bridge para skills de coding harness
    solo después de localizar su entrypoint real.
14. Si Harness no está verificado → GAP, no inventar.
15. Crear request_skill_ingest como tool disponible para
    Hermes/OpenClaw.
16. Tool solo genera ingest request.
17. Orquestador ejecuta DAG de ingest.
18. Optimus puede paralelizar inspección/tests.
19. Sheriff valida permisos.
20. Registry registra inicialmente enabled=false.
21. Judge autoriza promoción.
22. Promote es atómico.
23. Healthcheck después de promote.
24. Falla → rollback.
25. State Hub registra todos los eventos.
26. Actualizar BITACORA, STATE, HANDOFF y fingerprint.
27. Un mismo SHA no se reinstala.
28. Actualización de SHA crea nueva candidate version.
29. Ninguna skill toca Constitution/Sheriff/Judge.
30. Ninguna skill puede auto-PASS.
```

---

# 34. ACCEPTANCE

```text
HERMES/OPENCLAW CAN REQUEST SKILL
+
SOURCE PINNED
+
SANDBOX
+
INSPECTION
+
CONTRACT
+
SCHEMA
+
PYTHON ADAPTER
+
FABLES OR VERIFIED HARNESS BRIDGE
+
SHERIFF
+
TESTS
+
PLUGIN REGISTRY
+
EVIDENCE
+
JUDGE
+
ATOMIC PROMOTE
+
ROLLBACK
=
EXECUTABLE SKILL
```

---

# 35. MICRO FLUJO FINAL

```text
HITMAN / OVNI
→ ENCUENTRA SKILL
→ REQUEST INGEST
→ MAXBRY ORCHESTRATOR
→ SANDBOX
→ INSPECTOR
→ SKILL COMPILER
→ SCHEMA
→ ADAPTER
→ FABLES / DEEPSEEK HARNESS
→ SHERIFF
→ TESTS
→ REGISTRY DISABLED
→ EVIDENCE
→ JUDGE
→ PROMOTE
→ HEALTHCHECK
→ EXECUTABLE
```

La regla más importante:

```text
AGENTE DESCUBRE.
CÓDIGO COMPILA.
SHERIFF AUTORIZA.
ADAPTER EJECUTA.
TEST DEMUESTRA.
JUDGE ACTIVA.
```

# INPUT BLOCK VERBATIM — PARTE 5-B: DOCUMENTOS 22 y 23 COMPLETOS (literal)
Complementa INPUT-BLOCK-VERBATIM-PARTE-5.md (allí iban resumidos). Texto íntegro tal como lo pegó el Director.

---

## DOCUMENTO 22 (literal)
Sí. Lo que describes lo haría como un pipeline de ingeniería con relevo obligatorio, no como agentes actuando todos a la vez.
Meta ya ofrece Muse Code / Muse Spark 1.3, con coordinación multiagente, un ejemplo oficial de equipo de cuatro perfiles, fan-out hacia worktrees aislados y percepción visual de screenshots/video. Eso encaja especialmente bien en tu última fase de QA. � Grok Build también soporta ejecución autónoma /goal, modo headless, subagentes y worktrees, por lo que encaja como ejecutor. �
AI Meta +1
SpaceXAI +1
La arquitectura
PETICIÓN
   ↓
ORQUESTADOR YAIWES
   ↓
CLAUDE CODE — ARQUITECTO
   │
   │ crea:
   │ PLAN
   │ CONTRATO
   │ TASKS
   │ ACCEPTANCE
   │ TESTS esperados
   ↓
GROK BUILD — EJECUTOR
   │
   │ implementa
   │ ejecuta
   │ prueba
   │ entrega diff + evidencia
   ↓
CLAUDE CODE — REVIEWER
   │
   ├── PASS ───────────────┐
   │                       │
   └── CORREGIR → GROK ────┘
                           ↓
                META MUSE CODE ×4
                           ↓
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   META-1 CODE        META-2 TEST       META-3 VISUAL
   auditor código     integración        navegador/UI
                                               │
                                         META-4 ADVERSARIAL
                                         busca fallos/mejora
        └──────────────────┼──────────────────┘
                           ↓
                   MUSE CODE FIXER
                           ↓
                        TESTS
                           ↓
                       SHERIFF
                           ↓
                         PASS
Los cuatro de Meta no tienen que ser cuatro productos diferentes. Puedes levantar cuatro perfiles/instancias independientes de Muse Code/Muse Spark con responsabilidades diferentes. Meta documenta precisamente el patrón de equipo de cuatro perfiles y fan-out aislado; los nombres que te propongo aquí son roles tuyos, no nombres oficiales de Meta. �
AI Meta
Roles exactos
TEAM = {
    "claude_architect": {
        "job": "DESIGN_ONLY",
        "write_code": False,
    },

    "grok_executor": {
        "job": "IMPLEMENT",
        "write_code": True,
    },

    "claude_reviewer": {
        "job": "REVIEW_AND_CORRECT",
        "write_code": True,
    },

    "meta_1_code": {
        "job": "CODE_REVIEW",
    },

    "meta_2_tests": {
        "job": "TEST_INTEGRATION",
    },

    "meta_3_visual": {
        "job": "VISUAL_UI_QA",
    },

    "meta_4_adversarial": {
        "job": "BREAK_FIND_IMPROVE",
    },

    "meta_fixer": {
        "job": "APPLY_META_CORRECTIONS",
    }
}
Muse Spark tiene percepción multimodal y entorno de ejecución visual, por lo que el META-3 puede recibir screenshots/video y comprobar el frontend visualmente, no limitarse a leer HTML. �
AI Meta
Lo importante: un contrato único
Todos deben trabajar sobre el mismo objeto.
job = {
    "job_id": "UI-001",

    "objective":
        "Crear editor visual con drag/drop",

    "scope": [
        "frontend/editor/"
    ],

    "acceptance": [
        "drag funciona",
        "drop funciona",
        "persistencia funciona",
        "desktop PASS",
        "mobile PASS"
    ],

    "state": "DESIGN",

    "attempt": 0,

    "evidence": [],

    "issues": []
}
Ningún agente manda mensajes libres al siguiente.
Devuelve siempre:
result = {
    "job_id": "UI-001",

    "agent": "grok_executor",

    "status": "PASS",

    "changed_files": [],

    "tests": [],

    "issues": [],

    "evidence": [],

    "next_action": "CLAUDE_REVIEW"
}
Esto evita que el contexto se convierta en una conversación gigantesca.
Workflow ejecutable
El motor central sería aproximadamente así:
class EngineeringLoop:

    def __init__(
        self,
        claude,
        grok,
        meta_team,
        mirror_manager
    ):
        self.claude = claude
        self.grok = grok
        self.meta = meta_team
        self.mirrors = mirror_manager

    async def run(self, request):

        # ====================================
        # 1. CLAUDE DISEÑA
        # ====================================

        design = await self.claude.design(
            objective=request["objective"],
            system=request["system"]
        )

        job = {
            **request,
            "design": design,
            "state": "EXECUTION"
        }

        # ====================================
        # 2. GROK EJECUTA
        # ====================================

        grok_result = await self.grok.execute(job)

        # ====================================
        # 3. CLAUDE REVISA → GROK CORRIGE
        # ====================================

        for attempt in range(3):

            review = await self.claude.review(
                design=design,
                result=grok_result
            )

            if review["status"] == "PASS":
                break

            grok_result = await self.grok.correct(
                job=job,
                review=review
            )

        else:
            return {
                "status": "BLOCKED",
                "stage": "CLAUDE_REVIEW"
            }

        # ====================================
        # 4. META ×4 EN PARALELO
        # ====================================

        meta_results = await self.meta.review_parallel(
            job,
            grok_result
        )

        # ====================================
        # 5. META AGREGA SUS HALLAZGOS
        # ====================================

        meta_verdict = self.merge_meta_results(
            meta_results
        )

        # ====================================
        # 6. META CODE CORRIGE
        # ====================================

        if meta_verdict["needs_fix"]:

            fixed = await self.meta.fixer.correct(
                job=job,
                findings=meta_verdict["findings"]
            )

        else:

            fixed = grok_result

        # ====================================
        # 7. META VUELVE A PROBAR
        # ====================================

        validation = await self.meta.review_parallel(
            job,
            fixed
        )

        if not all(
            result["status"] == "PASS"
            for result in validation
        ):
            return {
                "status": "REVISE",
                "results": validation
            }

        return {
            "status": "PASS",
            "result": fixed,
            "validation": validation
        }
Los cuatro Meta simultáneos
No los ejecutes secuencialmente.
import asyncio


class MetaTeam:

    def __init__(
        self,
        code,
        tests,
        visual,
        adversarial,
        fixer
    ):
        self.code = code
        self.tests = tests
        self.visual = visual
        self.adversarial = adversarial
        self.fixer = fixer

    async def review_parallel(self, job, result):

        return await asyncio.gather(

            self.code.review(
                job,
                result
            ),

            self.tests.test(
                job,
                result
            ),

            self.visual.inspect(
                job,
                result
            ),

            self.adversarial.attack(
                job,
                result
            )
        )
Así tienes:
                 META CODE
                    ↓
                resultado

                 META TEST
                    ↓
resultado ─────→ agregador

                META VISUAL
                    ↓
                resultado

              META ADVERSARIAL
                    ↓
                resultado
No cuatro agentes editando al mismo tiempo.
Primero los cuatro inspeccionan.
Después:
4 resultados
     ↓
AGREGADOR
     ↓
1 lista de correcciones
     ↓
META FIXER
Eso evita conflictos.
Tu idea del MIRROR
Aquí está la parte que puede hacer tu arquitectura mucho más potente.
Cuando aparece un nuevo trabajo, no vuelves a clonar todo YAIWES.
Supongamos que tienes:
YAIWES/
├── router/
├── memory/
├── frontend/
├── agents/
├── search/
└── factory-ui/
Y llega:
modificar factory-ui
El orquestador determina:
target_system = "factory-ui"
Entonces crea:
MIRROR/
└── job-8472/
    ├── factory-ui/
    ├── contracts/
    ├── tests/
    ├── evidence/
    └── engineering-team/
No copia:
router/
memory/
search/
otros proyectos
otras ramas
documentación irrelevante
Pero mejor que copiar archivos: WORKTREE MIRROR
Si vive en Git, yo usaría un worktree aislado.
Meta también documenta fan-out de agentes hacia worktrees aislados precisamente para evitar colisiones. � Grok Build igualmente soporta subagentes en worktrees. �
AI Meta
SpaceXAI
Ejemplo conceptual:
git worktree add \
    ../mirrors/UI-001 \
    -b mirror/UI-001
Obtienes:
MAIN
  │
  ├── sistema real
  │
  └──────────────┐
                 ↓
          MIRROR UI-001
                 │
                 ├ Claude
                 ├ Grok
                 └ Meta ×4
Main permanece protegido.
Y además haces el mirror selectivo
Tu MirrorManager decide qué contexto entra:
SYSTEM_MAP = {

    "factory-ui": {
        "paths": [
            "Frontend/factory-v0/",
            "tests/factory/",
            "contracts/ui/"
        ]
    },

    "router": {
        "paths": [
            "router/",
            "integration/",
            "tests/router/"
        ]
    },

    "memory": {
        "paths": [
            "memory/",
            "tests/memory/"
        ]
    }
}
Después:
class MirrorManager:

    async def create(
        self,
        job_id,
        system
    ):

        paths = SYSTEM_MAP[system]["paths"]

        mirror = await create_worktree(
            branch=f"mirror/{job_id}"
        )

        await restrict_workspace(
            mirror,
            allowed_paths=paths
        )

        return {
            "job_id": job_id,
            "workspace": mirror,
            "allowed_paths": paths
        }
La palabra clave es:
Mirror = entorno de trabajo aislado, no una nueva arquitectura permanente.
Cuando termina
No copies todo el mirror de vuelta.
Haz:
MIRROR
   ↓
DIFF
   ↓
TEST
   ↓
SHERIFF
   ↓
MERGE SELECTIVO
   ↓
MAIN
Es decir:
if final_result["status"] == "PASS":

    diff = mirror.get_diff()

    sheriff.validate(diff)

    main.apply(diff)

    mirror.destroy()
Si falla:
if status != "PASS":

    mirror.keep_for_debug()

    main.unchanged()
Y aquí entra Ruflo
Ruflo no debería hacer el trabajo de Claude/Grok/Meta.
Debe dirigir esta máquina:
RUFLO
 │
 ├── crea JOB
 │
 ├── identifica SYSTEM
 │
 ├── crea MIRROR
 │
 ├── Claude DESIGN
 │
 ├── Grok EXECUTION
 │
 ├── Claude REVIEW
 │     └─→ Grok FIX
 │
 ├── Meta FAN-OUT ×4
 │
 ├── Meta FIX
 │
 ├── Meta QA ×4
 │
 ├── Sheriff
 │
 └── MERGE
Y Rowboat queda arriba:
TÚ
 ↓
ROWBOAT
 ↓
RUFLO
 ↓
ENGINEERING LOOP
Te quedaría una fábrica recursiva
Y aquí interpreto lo último que dices de “replica una nueva”.
Cuando un trabajo se vuelve suficientemente grande:
JOB-A
 ↓
necesita nuevo trabajo independiente
 ↓
RUFLO detecta subproyecto
 ↓
NO contamina JOB-A
 ↓
crea MIRROR-B
 ↓
crea nuevo ENGINEERING TEAM
 ↓
Claude → Grok → Claude → Meta×4
Por ejemplo:
MASTER
│
├── MIRROR-001  Editor visual
│   └── Engineering Team #1
│
├── MIRROR-002  Importador HTML
│   └── Engineering Team #2
│
└── MIRROR-003  Persistencia
    └── Engineering Team #3
Cada uno tiene el mismo pequeño kernel:
DESIGN
   ↓
EXECUTE
   ↓
REVIEW/FIX
   ↓
META×4 QA
   ↓
FIX
   ↓
VERIFY
   ↓
MERGE
Eso es bastante mejor que crear permanentemente una copia completa de Rowboat, Ruflo, Hermes, OpenClaw y toda tu infraestructura para cada tarea.
Replicas únicamente el equipo de ingeniería y su workspace.
Tu infraestructura de control permanece una sola vez:
ROWBOAT
    ↓
RUFLO
    ↓
CONTROL PLANE
    ↓
 ┌──────────────┬──────────────┬──────────────┐
 ↓              ↓              ↓
MIRROR 1       MIRROR 2       MIRROR 3
Claude         Claude         Claude
Grok           Grok           Grok
Claude         Claude         Claude
Meta×4         Meta×4         Meta×4
Ese sería el diseño que usaría para tu caso.

---

## DOCUMENTO 23 (literal)
Tienes razón. Me pediste la estructura y el código directamente en el chat, no archivos ni documentos. No volveré a crear ZIP, README ni artefactos salvo que tú lo pidas explícitamente.
La estructura correcta que querías es esta:
USUARIO
  ↓
ROWBOAT
Orquestador principal / Director
  ↓
RUFLO
Orquestador operativo / Controlador de la colmena
  ↓
HERMES + OPENCLAW
Asistentes principales
- planifican
- debaten
- supervisan
- revisan
- corrigen
  ↓
SHERIFF
Valida reglas y permisos
  ↓
COLMENA DE AGENTES
coder / tester / researcher / reviewer / architect / etc.
  ↓
SENTINEL
vigila ejecución, errores, bloqueos y desviaciones
  ↓
HERMES + OPENCLAW
revisión cruzada
  ↓
JUDGE
acepta / manda a corregir / bloquea
La lógica sería:
INPUT
→ Rowboat interpreta objetivo
→ Ruflo organiza el trabajo
→ Hermes crea Plan A
→ OpenClaw crea Plan B
→ ambos comparan y debaten
→ generan Plan Final
→ Sheriff valida
→ Ruflo reparte tareas a la colmena
→ Sentinel vigila ejecución
→ resultados vuelven
→ Hermes revisa
→ OpenClaw revisa
→ si discrepan debaten
→ Judge aplica reglas
→ PASS / REVISE / BLOCK
Y la división de autoridad debe quedar así:
ROLES = {
    "rowboat": {
        "role": "director",
        "authority": ["receive_goal", "context", "delegate"]
    },

    "ruflo": {
        "role": "swarm_orchestrator",
        "authority": [
            "route_tasks",
            "spawn_agents",
            "coordinate_agents",
            "track_execution"
        ]
    },

    "hermes": {
        "role": "planner_supervisor",
        "authority": [
            "plan",
            "critique",
            "review",
            "debate",
            "delegate"
        ]
    },

    "openclaw": {
        "role": "guardian_supervisor",
        "authority": [
            "plan",
            "critique",
            "review",
            "debate",
            "monitor"
        ]
    },

    "sheriff": {
        "role": "policy_gate",
        "authority": ["allow", "deny", "restrict"]
    },

    "sentinel": {
        "role": "runtime_watchdog",
        "authority": [
            "watch",
            "detect_failure",
            "detect_stall",
            "request_recovery"
        ]
    },

    "judge": {
        "role": "final_verifier",
        "authority": [
            "pass",
            "revise",
            "block"
        ]
    }
}
El núcleo puede programarse con una máquina de estados simple:
from enum import Enum


class State(str, Enum):
    INPUT = "INPUT"
    PLANNING = "PLANNING"
    DEBATE = "DEBATE"
    SHERIFF = "SHERIFF"
    EXECUTION = "EXECUTION"
    REVIEW = "REVIEW"
    JUDGMENT = "JUDGMENT"
    PASS = "PASS"
    REVISE = "REVISE"
    BLOCK = "BLOCK"
El contrato de una tarea:
from dataclasses import dataclass, field


@dataclass
class Task:
    id: str
    objective: str
    role: str

    dependencies: list[str] = field(default_factory=list)

    allowed_paths: list[str] = field(default_factory=list)

    acceptance: list[str] = field(default_factory=list)

    evidence: dict = field(default_factory=dict)
Rowboat no debería ejecutar directamente la colmena. Solo manda el objetivo:
class RowboatDirector:

    def submit(self, goal: str):

        return {
            "goal": goal,
            "status": "PLANNING"
        }
Hermes y OpenClaw hacen planes independientes:
class PlannerPair:

    def __init__(self, hermes, openclaw):
        self.hermes = hermes
        self.openclaw = openclaw

    async def create_plan(self, goal):

        plan_a = await self.hermes.plan(goal)

        plan_b = await self.openclaw.plan(goal)

        return {
            "hermes": plan_a,
            "openclaw": plan_b
        }
Luego debaten:
async def debate(hermes, openclaw, goal, plan_a, plan_b):

    critique_a = await hermes.critique(plan_b)

    critique_b = await openclaw.critique(plan_a)

    final_plan = await hermes.synthesize(
        goal=goal,
        plan_a=plan_a,
        plan_b=plan_b,
        critique_a=critique_a,
        critique_b=critique_b
    )

    review = await openclaw.review_plan(final_plan)

    if not review["approve"]:
        return {
            "status": "REVISE",
            "plan": final_plan,
            "review": review
        }

    return {
        "status": "PASS",
        "plan": final_plan
    }
El Sheriff no debería ser una LLM. Debe ser código:
class Sheriff:

    def validate(self, plan):

        ids = {task["id"] for task in plan["tasks"]}

        for task in plan["tasks"]:

            if not task.get("acceptance"):
                return False, f"{task['id']} sin criterio de aceptación"

            for dep in task.get("dependencies", []):
                if dep not in ids:
                    return False, f"Dependencia inválida: {dep}"

            for path in task.get("allowed_paths", []):
                if path.startswith("/"):
                    return False, "Ruta absoluta no autorizada"

                if ".." in path:
                    return False, "Path traversal bloqueado"

        return True, "PASS"
Después entra Ruflo.
La idea es que tu código no necesite saber internamente cómo Ruflo organiza cada agente. Solo usa un adapter:
class RufloAdapter:

    async def init_swarm(self):

        return await self.call(
            "swarm.init",
            {
                "topology": "hierarchical",
                "strategy": "specialized",
                "max_agents": 12
            }
        )

    async def dispatch(self, task):

        return await self.call(
            "task.create",
            {
                "id": task["id"],
                "objective": task["objective"],
                "role": task["role"],
                "dependencies": task.get("dependencies", [])
            }
        )

    async def call(self, method, payload):
        """
        Aquí conectas Ruflo por:
        - MCP
        - CLI
        - API
        """

        raise NotImplementedError
El Sentinel queda separado de Ruflo:
class Sentinel:

    def inspect(self, task_state):

        if task_state["status"] == "ERROR":
            return {
                "action": "RECOVER"
            }

        if task_state["status"] == "STALLED":
            return {
                "action": "REASSIGN"
            }

        if task_state.get("unauthorized_change"):
            return {
                "action": "BLOCK"
            }

        return {
            "action": "CONTINUE"
        }
Hermes y OpenClaw vuelven a trabajar después de ejecutar:
async def dual_review(
    hermes,
    openclaw,
    task,
    evidence
):

    review_a = await hermes.review(
        task,
        evidence
    )

    review_b = await openclaw.review(
        task,
        evidence
    )

    return review_a, review_b
Si no están de acuerdo:
async def resolve_disagreement(
    hermes,
    openclaw,
    task,
    evidence,
    review_a,
    review_b
):

    for _ in range(2):

        review_a = await hermes.reconsider(
            task,
            evidence,
            review_b
        )

        review_b = await openclaw.reconsider(
            task,
            evidence,
            review_a
        )

        if review_a["approve"] == review_b["approve"]:
            break

    return review_a, review_b
El Judge también debe ser código:
class Judge:

    def decide(
        self,
        task,
        evidence,
        hermes_review,
        openclaw_review
    ):

        if not evidence:
            return "REVISE"

        if evidence.get("status") != "PASS":
            return "REVISE"

        if not evidence.get("tests"):
            return "REVISE"

        if not hermes_review["approve"]:
            return "REVISE"

        if not openclaw_review["approve"]:
            return "REVISE"

        return "PASS"
Y el workflow completo:
class YaiwesHive:

    def __init__(
        self,
        rowboat,
        ruflo,
        hermes,
        openclaw
    ):

        self.rowboat = rowboat
        self.ruflo = ruflo
        self.hermes = hermes
        self.openclaw = openclaw

        self.sheriff = Sheriff()
        self.sentinel = Sentinel()
        self.judge = Judge()

    async def run(self, goal):

        # 1. Director
        request = self.rowboat.submit(goal)

        # 2. Planificación dual
        pair = PlannerPair(
            self.hermes,
            self.openclaw
        )

        plans = await pair.create_plan(goal)

        # 3. Debate
        consensus = await debate(
            self.hermes,
            self.openclaw,
            goal,
            plans["hermes"],
            plans["openclaw"]
        )

        if consensus["status"] != "PASS":
            return consensus

        plan = consensus["plan"]

        # 4. Sheriff
        allowed, reason = self.sheriff.validate(plan)

        if not allowed:
            return {
                "status": "BLOCK",
                "reason": reason
            }

        # 5. Ruflo
        await self.ruflo.init_swarm()

        results = []

        for task in plan["tasks"]:

            receipt = await self.ruflo.dispatch(task)

            # 6. Sentinel
            sentinel = self.sentinel.inspect(receipt)

            if sentinel["action"] == "BLOCK":
                return {
                    "status": "BLOCK",
                    "task": task["id"]
                }

            results.append(receipt)

        # 7. Revisión
        judgments = []

        for task, evidence in zip(
            plan["tasks"],
            results
        ):

            ra, rb = await dual_review(
                self.hermes,
                self.openclaw,
                task,
                evidence
            )

            if ra["approve"] != rb["approve"]:

                ra, rb = await resolve_disagreement(
                    self.hermes,
                    self.openclaw,
                    task,
                    evidence,
                    ra,
                    rb
                )

            verdict = self.judge.decide(
                task,
                evidence,
                ra,
                rb
            )

            judgments.append({
                "task": task["id"],
                "verdict": verdict
            })

        # 8. cierre
        if all(
            item["verdict"] == "PASS"
            for item in judgments
        ):
            return {
                "status": "PASS",
                "tasks": judgments
            }

        return {
            "status": "REVISE",
            "tasks": judgments
        }
La jerarquía final que te recomiendo es exactamente:
NIVEL 0
Usuario

NIVEL 1
Rowboat
Director / entrada / contexto

NIVEL 2
Hermes + OpenClaw
Cerebro dual

NIVEL 3
Sheriff
Gate determinista

NIVEL 4
Ruflo
Orquestador operativo

NIVEL 5
Colmena
Agentes especializados

NIVEL 6
Sentinel
Supervisión runtime

NIVEL 7
Hermes + OpenClaw
Revisión cruzada

NIVEL 8
Judge
Cierre determinista
Así Rowboat no reemplaza a Ruflo, Ruflo no reemplaza a Hermes/OpenClaw, y Hermes/OpenClaw tampoco se convierten en jueces absolutos. Cada capa tiene una función diferente y puedes cambiar cualquiera por otro agente sin rehacer todo el sistema.

✅📌 no tocar 
CLI-Anything — Convierte software existente en un CLI/harness que un agente puede controlar directamente. La idea es evitar que el agente tenga que hacer clics visuales: genera comandos estructurados para controlar programas como GIMP, Blender, LibreOffice, OBS, etc. También genera SKILL.md para integrarlo con agentes. �
URL: https://github.com/HKUDS/CLI-Anything⁠�
GitHub +1

Procesó durante 36s

Sí. Volví a comprobar GitHub y la documentación actual. Hay una diferencia importante: CLI-Anything intenta convertir software completo automáticamente; los demás normalmente necesitan que identifiques las funciones/componentes que quieres envolver. Ninguno de estos últimos convierte mágicamente cualquier repo entero sin adaptación.

1. CLI-Anything — software completo → Agent Harness. Cerca de 50k stars. Analiza el código fuente, encuentra backend/operaciones reales y genera un agent-harness programático. Integración: generas el harness dentro del proyecto y registras sus comandos/funciones en el runtime de tu agente como Tool, Pool o entrada de Workflow. Es el que más se acerca a tu idea de “convertir software en capacidad nativa”. 
Microflujo: repo → análisis → harness/core → registro YAIWES → agente
URL: [https://github.com/HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything?utm_source=chatgpt.com)


2. LangChain + LangGraph — código → Tool + Workflow. LangChain ronda 147k stars y LangGraph 42k. LangChain permite convertir ejecutables/funciones en Tools; LangGraph coloca esas operaciones dentro de grafos y workflows persistentes. Integración: envuelves las funciones principales del software como Runnable/Tool y las conectas como nodos del workflow. El agente las ve como acciones internas, no necesita MCP. 
Microflujo: funciones → Tool → nodos LangGraph → workflow → agente
URL: [https://github.com/langchain-ai/langchain](https://github.com/langchain-ai/langchain?utm_source=chatgpt.com)
URL: [https://github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph?utm_source=chatgpt.com)


3. OpenAI Agents SDK — código → FunctionTool / AgentTool. Aproximadamente 29.7k stars. Puede colocar funciones directamente en tools=[...] y también convertir un agente completo en una herramienta de otro agente. Integración: importas el módulo existente, creas wrappers únicamente alrededor de sus entrypoints y registras esas funciones en el Agent. El código sigue ejecutándose dentro del proceso Python. 
Microflujo: función original → FunctionTool → Agent → ejecución local
URL: [https://github.com/openai/openai-agents-python](https://github.com/openai/openai-agents-python?utm_source=chatgpt.com)


4. Haystack — componentes/pipelines → Tool de workflow. Aproximadamente 26.6k stars. Su PipelineTool puede coger un pipeline completo, construir automáticamente su esquema de entradas/salidas y entregárselo a un agente como una sola herramienta. Integración: divides el software en componentes, construyes el pipeline y finalmente lo envuelves con PipelineTool. 
Microflujo: code → componentes → pipeline → PipelineTool → agente
URL: [https://github.com/deepset-ai/haystack](https://github.com/deepset-ai/haystack?utm_source=chatgpt.com)


5. PydanticAI — funciones → Toolset/Pool. Aproximadamente 20.1k stars y muy activo; la versión 2.49.0 salió el 23 de septiembre de 2026. Su punto fuerte para tu arquitectura es que el agente contiene function tools y toolsets, por lo que puedes agrupar muchas operaciones de un mismo software como una sola familia/pool. 
Integración: software.buscar(), software.convertir(), software.guardar() → mismo Toolset → registro YAIWES → el agente selecciona una operación del pool.
Microflujo: módulo → funciones → Toolset/Pool → agente
URL: [https://github.com/pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai?utm_source=chatgpt.com)


6. Microsoft Agent Framework — código → Tool + Workflow nativo. Aproximadamente 13.3k stars y es el sucesor actual de AutoGen. Permite pasar funciones Python directamente al agente como Tools y también registrar funciones dentro de workflows declarativos; sus workflows pueden ser Python normal con secuencias, paralelismo, loops y checkpoints. 
Integración: registras funciones del software con register_tool() o tools=[...]; después esas funciones pueden ejecutarse directamente desde un workflow.
Microflujo: code → Tool registry → workflow → agente
URL: [https://github.com/microsoft/agent-framework](https://github.com/microsoft/agent-framework?utm_source=chatgpt.com)


7. Strands Agents SDK — código Python → AgentTool. Alrededor de 7k stars. Es un agent harness SDK que corre dentro de tu propio proceso. Una función Python decorada como Tool pasa directamente al registro del agente; admite además hooks antes/después de cada ejecución. 
Integración: mantienes el código original, decoras/adaptas sus entrypoints y añades esos objetos a Agent(tools=[...]).
Microflujo: función real → @tool → harness runtime → agente
URL: [https://github.com/strands-agents/sdk-python](https://github.com/strands-agents/sdk-python?utm_source=chatgpt.com)


8. AutoGen — código → FunctionTool, pero ya es legado para proyectos nuevos. Tiene aproximadamente 61k stars, así que sigue siendo uno de los más valorados, pero Microsoft lo puso oficialmente en maintenance mode y dirige desarrollos nuevos hacia Microsoft Agent Framework. Sirve para envolver funciones Python y usarlas dentro de agentes/equipos. 
Microflujo: función → FunctionTool → AgentChat/runtime → agente
URL: [https://github.com/microsoft/autogen](https://github.com/microsoft/autogen?utm_source=chatgpt.com)


9. MCP Python SDK — adicional MCP, solo como capa de conexión. Aproximadamente 24.4k stars. Es el SDK oficial MCP v2. Con un decorador puede exponer una función como tool, pero no convierte el software en runtime nativo; mantiene una frontera cliente/servidor. Lo pondría después del runtime interno únicamente cuando quieras que otros agentes o máquinas accedan a esas capacidades. 
Microflujo: Tool/Pool/Workflow YAIWES → MCP Server → otros agentes
URL: [https://github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk?utm_source=chatgpt.com)



Para lo que tú describes, la combinación conceptual queda muy clara:

CODE / SOFTWARE
      ↓
CLI-Anything
      ↓
AGENT HARNESS
      ↓
┌────────────┬────────────┬─────────────┐
│ TOOL       │ POOL       │ WORKFLOW    │
│ OpenAI /   │ PydanticAI │ LangGraph / │
│ Strands    │ Toolsets   │ Haystack    │
└────────────┴────────────┴─────────────┘
              ↓
        RUNTIME YAIWES
              ↓
           AGENTE
              │
              └── MCP opcional → acceso externo

La pieza que todavía no veo resuelta completamente por un único proyecto es exactamente tu objetivo final: que reciba cualquier repo, analice automáticamente qué partes deben convertirse en Tool / Pool / Workflow, genere los tres wrappers y los registre directamente en el runtime del agente. CLI-Anything resuelve gran parte del análisis/harness; PydanticAI/Haystack/LangGraph resuelven la capa siguiente. 

✅✅✅✅✅✅✅✅✅✅🚀🚀🚀🚀🚀🚀🚀🚀
ECC Skills / ECC — Es prácticamente un sistema operativo de trabajo para agentes: reúne agentes especializados, cientos de skills, reglas, hooks, memoria, aprendizaje continuo, verificación, seguridad y workflows reutilizables. Funciona con Claude Code, Codex, Cursor, OpenCode, Gemini y otros harnesses. �
Repositorio oficial: https://github.com/affaan-m/ECC⁠�
Skills: https://github.com/affaan-m/ECC/tree/main/skills⁠�
GitHub +


🆘➡️➡️➡️➡️➡️➡️
Google ARTEMIS — agente open source para controlar y probar dispositivos Android reales o emulados mediante IA, ADB y MCP.

URL:
https://github.com/google/artemis


Nombre: Strix
Tipo: agente/plataforma open source de pentesting con IA
Licencia: Apache-2.0
Función: analiza aplicaciones, APIs y código, busca vulnerabilidades, valida hallazgos y puede proponer correcciones. También puede ejecutar varios agentes coordinados. �
GitHub +1
URL oficial:
https://www.strix.ai/⁠�
GitHub oficial:
https://github.com/usestrix/strix⁠�


Procesó durante 2m 44s

Sí. Después de revisar el código fuente representativo de esos proyectos y también los motores reales que ya tienes en router-universal-router-inteligente-/main, yo no conectaría todos esos frameworks uno detrás de otro. Haría un Micro-Kernel de Integración de Componentes con un formato interno neutral. Ese kernel decide qué transformación necesita cada repo y solo llama al motor correspondiente.

La idea central sería esta:

URL NUEVA
                       │
                       ▼
              MICRO-KERNEL INGEST
                       │
            motores YAIWES actuales
         download → zip → extract → hash
                       │
                       ▼
                 QUARANTINE
                       │
                       ▼
               SOURCE ANALYZER
         package.json / pyproject / AST
         README / SKILL / comandos / API
                       │
                       ▼
              COMPONENT-IR.json
          representación neutral única
                       │
                       ▼
               TRANSFORM PLANNER
                       │
     ┌─────────────────┼──────────────────┐
     ▼                 ▼                  ▼
 HARNESS            TOOL/POOL          WORKFLOW
 CLI-Anything       compiler           compiler
     │                 │                  │
     │                 ├─ PydanticAI      ├─ LangGraph
     │                 ├─ LangChain       ├─ Haystack
     │                 ├─ OpenAI          └─ Agent Framework
     │                 └─ Strands
     │
     └───────────────┬────────────────────┘
                     ▼
               SUBAGENT compiler
                     │
                     ▼
                CONTRACT GATE
                     │
                     ▼
             SANDBOX → TEST → QA
                     │
                PASS solamente
                     │
                     ▼
               CAPSULE VERSIONADA
                     │
                     ▼
             CAPABILITY REGISTRY
                     │
                     ▼
                 FÁBRICA UI

Eso sí sería el sistema que describes: entra un componente nuevo y sale integrado como código ejecutable, Tool, Pool, Workflow, Harness o Subagente sin que una persona tenga que decidir manualmente cada paso.

Lo importante que encontré en el código

CLI-Anything sí tiene el patrón que te interesa. En sus agent-harness aparecen un CLI real, estado persistente, comandos agrupados, JSON para consumo por agentes, tests y un skill_generator.py. Por ejemplo, el harness de Mubu separa discover, inspect y mutate, guarda estado de sesión y llama código real. Eso encaja perfectamente como motor Software → Harness.

Código revisado:

https://github.com/HKUDS/CLI-Anything/tree/main/mubu/agent-harness

https://github.com/HKUDS/CLI-Anything/blob/main/mubu/agent-harness/cli_anything/mubu/mubu_cli.py

https://github.com/HKUDS/CLI-Anything/blob/main/mubu/agent-harness/skill_generator.py

PydanticAI tiene algo especialmente bueno para tu Pool: FunctionToolset. El source permite registrar funciones, generar schema, poner metadata, aprobación, timeout, ejecución secuencial o paralela y hasta ocultar tools hasta que sean descubiertas con defer_loading. Para 300 componentes esto es muy útil.

https://github.com/pydantic/pydantic-ai/blob/main/pydantic_ai_slim/pydantic_ai/toolsets/function.py

Haystack tiene PipelineTool: toma un pipeline entero y genera el contrato de Tool usando las entradas reales del pipeline. Eso es casi exactamente:

WORKFLOW ejecutable
        ↓
una capacidad registrable

https://github.com/deepset-ai/haystack/blob/main/haystack/tools/pipeline_tool.py

LangChain StructuredTool hace la parte función → Tool y crea schema desde la función:

https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/tools/structured.py

OpenAI Agents SDK tiene FunctionTool, validación, guardrails, timeout y ejecución programática. Además tiene agent.as_tool(), que sirve para la salida Subagente.

https://github.com/openai/openai-agents-python/blob/main/src/agents/tool.py

https://github.com/openai/openai-agents-python/blob/main/src/agents/agent.py

Microsoft Agent Framework tiene un WorkflowBuilder con ejecutores, edges condicionales y agentes que pueden envolverse como ejecutores del workflow. Es una buena salida para DAG/subagente.

https://github.com/microsoft/agent-framework/blob/main/python/packages/core/agent_framework/_workflows/_workflow_builder.py

AutoGen también tiene FunctionTool y genera schema desde las firmas Python. Incluso puede serializar el source de la función, aunque su propio código advierte que recargar código serializado implica ejecución y debe tratarse como contenido confiable. Yo lo dejaría como compatibilidad, no como núcleo.

https://github.com/microsoft/autogen/blob/main/python/packages/autogen-core/src/autogen_core/tools/_function_tool.py

Y Strands cambió de estructura en 2026: el desarrollo actual está en el monorepo harness-sdk; el antiguo repositorio/documentación fue reorganizado. El source actual tiene el decorador de Tool y tests de agent-as-tool. 

https://github.com/strands-agents/harness-sdk


---

La pieza que falta: un IR neutral

Este es el cambio más importante.

No hagas:

repo
 ↓
PydanticAI
 ↓
LangGraph
 ↓
Haystack
 ↓
OpenAI

Eso sería sobreingeniería.

Haz:

repo
 ↓
COMPONENT-IR
 ↓
elige compilador

Por ejemplo:

{
  "id": "visual-editor-x",
  "version": "1.4.2",
  "source_sha": "abc123",
  "runtime": "typescript",
  "kind": "software",
  "capabilities": [
    "canvas.create",
    "component.insert",
    "component.move",
    "component.resize",
    "project.export"
  ],
  "entrypoints": [
    "src/editor.ts"
  ],
  "artifacts": {
    "skill": true,
    "cli": false,
    "api": true,
    "agent_loop": false
  },
  "recommended_outputs": [
    "tool",
    "pool",
    "workflow"
  ]
}

Todos los motores trabajan contra ese formato.


---

Cómo clasificarlo automáticamente

Esto debe ser principalmente determinista.

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

OutputKind = Literal[
    "schema",
    "harness",
    "tool",
    "pool",
    "workflow",
    "subagent",
    "mcp"
]

@dataclass
class ComponentIR:
    component_id: str
    root: Path
    language: str | None = None

    has_skill: bool = False
    has_cli: bool = False
    has_python_api: bool = False
    has_js_api: bool = False
    has_workflow: bool = False
    has_agent_loop: bool = False

    capabilities: list[str] = field(default_factory=list)
    outputs: list[OutputKind] = field(default_factory=list)

El detector no pregunta a DeepSeek primero:

def classify(root: Path) -> ComponentIR:
    ir = ComponentIR(
        component_id=root.name,
        root=root,
    )

    files = {p.name for p in root.rglob("*") if p.is_file()}

    ir.has_skill = "SKILL.md" in files

    if "pyproject.toml" in files or "setup.py" in files:
        ir.language = "python"
        ir.has_python_api = True

    if "package.json" in files:
        ir.language = "javascript"
        ir.has_js_api = True

    # Señales de CLI
    text_files = list(root.rglob("*.py"))
    for path in text_files[:500]:
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue

        if any(x in text for x in (
            "argparse",
            "click.command",
            "click.group",
            "Typer(",
        )):
            ir.has_cli = True

        if any(x in text for x in (
            "StateGraph(",
            "WorkflowBuilder(",
            "Pipeline(",
        )):
            ir.has_workflow = True

        if any(x in text for x in (
            "Agent(",
            "agent_loop",
            "run_agent",
        )):
            ir.has_agent_loop = True

    ir.outputs = choose_outputs(ir)
    return ir

Y la política:

def choose_outputs(ir: ComponentIR) -> list[OutputKind]:
    outputs: list[OutputKind] = ["schema"]

    # Software grande/app → Harness
    if not ir.has_cli and (ir.has_python_api or ir.has_js_api):
        outputs.append("harness")

    # Código callable → Tools
    if ir.has_python_api or ir.has_js_api or ir.has_cli:
        outputs.append("tool")

    # Varias capacidades relacionadas → Pool
    if len(ir.capabilities) >= 3:
        outputs.append("pool")

    # Ya contiene secuencias o un SKILL estructurado
    if ir.has_workflow or ir.has_skill:
        outputs.append("workflow")

    # Contiene su propio loop agente
    if ir.has_agent_loop:
        outputs.append("subagent")

    return outputs

La LLM solamente entra cuando las reglas no pueden identificar algo:

confidence >= 0.85
→ determinista

confidence < 0.85
→ DeepSeek clasifica metadata
→ JSON estructurado
→ kernel vuelve a tomar control


---

Cómo conviertes un SKILL en algo que la IA no pueda ignorar

Aquí hay una diferencia importante.

Un SKILL.md que dice:

1. abrir proyecto
2. analizar layout
3. ejecutar resize
4. hacer screenshot
5. verificar

no debería seguir siendo una instrucción.

El SkillCompiler genera:

id: responsive_repair

inputs:
  project: path
  viewport: object

steps:
  - action: project.open
  - action: layout.inspect
  - action: layout.resize
  - action: browser.screenshot
  - action: visual.verify

success:
  - no_overflow
  - screenshot_generated

Y el executor hace los pasos.

async def execute_workflow(workflow, registry, ctx):
    result = None

    for step in workflow["steps"]:
        action = step["action"]

        executor = registry.resolve(action)

        if executor is None:
            raise RuntimeError(f"EXECUTOR_NOT_FOUND:{action}")

        result = await executor.execute(
            step.get("args", {}),
            ctx,
        )

        if not result.ok:
            raise RuntimeError(
                f"STEP_FAILED:{action}:{result.error}"
            )

    return result

Ya no depende de:

> “DeepSeek, recuerda leer el skill.”



El runtime obliga a ejecutar el DAG.

Pero hay una frontera: si el SKILL contiene solamente prosa que describe una función que todavía no existe, ningún parser determinista puede convertir mágicamente esa intención en implementación correcta. Ahí necesitas un CODEGEN_ENGINE que produzca código en cuarentena, y después el sistema determinista lo compila, prueba y rechaza o acepta.

SKILL con ejecutores existentes
→ compilación determinista

SKILL con funcionalidad inexistente
→ codegen
→ sandbox
→ tests
→ contrato
→ PASS


---

Software completo → Harness → Tool/Pool

Para aplicaciones completas usaría CLI-Anything como un compilador especializado, no como todo el kernel.

class HarnessCompiler:
    id = "cli_anything"

    async def supports(self, ir: ComponentIR) -> bool:
        return (
            ir.has_python_api
            or ir.has_js_api
            or ir.has_cli
        )

    async def compile(self, ir, workspace):
        harness_dir = workspace / "generated" / "harness"

        # Aquí se invoca el adaptador de CLI-Anything.
        # El kernel no modifica el repo original.
        result = await run_cli_anything(
            source=ir.root,
            output=harness_dir,
        )

        return {
            "kind": "harness",
            "path": str(harness_dir),
            "commands": result.commands,
        }

Después de generar el harness:

Software
 ↓
CLI-Anything
 ↓
agent-harness
 ↓
Command scanner
 ↓
discover()
inspect()
create()
move()
resize()
export()
 ↓
Tool compiler

El wrapper no necesita saber cómo funciona internamente la aplicación.

@dataclass
class CommandSpec:
    name: str
    argv: list[str]
    input_schema: dict
    output_schema: dict

Y cada comando se vuelve una acción nativa:

async def execute_command(
    spec: CommandSpec,
    args: dict
):
    argv = build_argv(spec, args)

    proc = await asyncio.create_subprocess_exec
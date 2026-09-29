# AI-AGENT — Diseño integral de la UI del Router Inteligente

**Versión:** 1.0  
**Fecha:** 2026-08-22  
**Estado:** Diseño consolidado  
**Objetivo:** Definir la interfaz y el modelo de control del Router Inteligente para administrar fichas/conexiones, modelos, plugins, apps, herramientas, memoria, investigación, plantillas DAG, ejecución y configuración interna.

---

# 1. Principio central

El Router Inteligente **no diseña arquitecturas durante la ejecución**.

La arquitectura de cada plantilla es predefinida y queda protegida.

El router solamente:

1. Analiza la entrada.
2. Identifica la plantilla aplicable.
3. Activa una plantilla registrada.
4. Valida el DSL/schema.
5. Ejecuta el DAG fijo.
6. Controla modelos, herramientas y conexiones autorizadas.
7. Consolida los resultados.
8. Entrega una salida estructurada a la API/agente.

La IA **no puede** durante una ejecución:

- crear nodos;
- eliminar nodos;
- reordenar nodos;
- inventar conexiones;
- inventar una arquitectura;
- inventar modelos;
- cambiar el DAG de una plantilla.

Los cambios estructurales pertenecen al **Panel de Configuración de Ingenieros**.

---

# 2. Arquitectura visual general

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI-AGENT ROUTER                                  │
│                                                                         │
│ RUN | TEMPLATES | CONNECTIONS | MODELS | RESEARCH | MEMORY | API       │
├───────────────┬─────────────────────────────────────────────────────────┤
│               │                                                         │
│ NAVEGACIÓN    │                  PANEL CENTRAL                          │
│               │                                                         │
│ Templates     │       ┌────────────┐       ┌────────────┐              │
│ Connections   │       │ ENTRADA    │──────▶│ MODELO     │              │
│ Models        │       └────────────┘       └─────┬──────┘              │
│ Plugins       │                                  │                     │
│ Apps          │                                  ▼                     │
│ Research      │                            ┌────────────┐              │
│ Memory        │                            │ VERIFIER   │              │
│ Engineers     │                            └─────┬──────┘              │
│ Settings      │                                  │                     │
│               │                                  ▼                     │
│               │                            ┌────────────┐              │
│               │                            │ OUTPUT     │              │
│               │                            └────────────┘              │
├───────────────┴─────────────────────────────────────────────────────────┤
│ CPU | RAM | GPU | MODELS | CONNECTIONS | API | MCP | SENTINEL | RUN    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# 3. Panel central: fichas conectadas

El centro de la UI es un **canvas visual de fichas**.

Una ficha representa cualquier recurso conectado al Router:

- Modelo.
- Agente.
- API.
- MCP Server.
- Plugin.
- App.
- HTTP service.
- Web service.
- GitHub.
- Hugging Face.
- Storage.
- Database.
- Filesystem.
- Teléfono.
- Red externa.
- Web.
- RAG.
- Memory.
- Tool.
- Workflow.

Ejemplo:

```text
┌──────────────────────────────┐
│ GitHub                       │
│ ● CONNECTED                  │
│                              │
│ Input:  1–100                │
│ Output: 1–100                │
│                              │
│ API ✓   MCP ✓   HTTP ✓       │
│ Storage ✓                    │
└──────────────────────────────┘
```

---

# 4. Puertos universales 1–100

Cada ficha puede tener:

```text
INPUT  01 ... INPUT 100
OUTPUT 01 ... OUTPUT 100
```

Ejemplos de entradas:

```text
IN-01  prompt
IN-02  context
IN-03  memory
IN-04  files
IN-05  image
IN-06  URL
IN-07  API response
IN-08  previous result
...
IN-100
```

Ejemplos de salidas:

```text
OUT-01  model result
OUT-02  memory
OUT-03  API
OUT-04  UI
OUT-05  next node
OUT-06  evidence
...
OUT-100
```

Esto permite conectar una ficha con múltiples sistemas sin crear una arquitectura especial para cada integración.

---

# 5. Connection Engine

La UI debe disponer de un motor de conexiones separado del Router Core.

```text
router/
└── connection_engine/
    ├── connector_registry
    ├── input_ports
    ├── output_ports
    ├── protocol_adapter
    ├── auth_manager
    ├── health_checker
    └── connection_validator
```

Protocolos/tipos:

```text
HTTP
HTTPS
REST
WebSocket
MCP
OAuth
API Key
Local Socket
CLI
Filesystem
Database
Git
Cloud Storage
Plugin
App
Webhook
```

Conectores concretos:

```text
GitHubConnector
HuggingFaceConnector
PhoneConnector
StorageConnector
DatabaseConnector
MCPConnector
HTTPConnector
WebConnector
```

La ficha representa el recurso; el adapter conoce cómo comunicarse con él.

---

# 6. Panel de conexiones

Vista propuesta:

```text
CONNECTIONS

[ + NEW CONNECTION ]

CATEGORY

○ API
○ MCP
○ HTTP
○ APP
○ STORAGE
○ DATABASE
○ GITHUB
○ HUGGING FACE
○ PHONE
○ SOCIAL
○ LOCAL
○ REMOTE
```

Cada conexión muestra:

```text
┌────────────────────────────────────┐
│ GitHub                             │
├────────────────────────────────────┤
│ Status:       ● Connected          │
│ Protocol:     API / HTTPS          │
│ Inputs:       12                   │
│ Outputs:      18                   │
│ Authentication: OAuth              │
│ Permissions: READ / WRITE          │
│ Health:       ✓                    │
│                                    │
│ [TEST] [CONFIGURE] [DISABLE]       │
└────────────────────────────────────┘
```

---

# 7. Panel de configuración de ingenieros

Debe ser independiente de la configuración normal del Router.

```text
ENGINEERING CONTROL

SYSTEM
├── Router Core
├── Connection Engine
├── Template Engine
├── DAG Engine
├── Model Registry
├── Memory
├── Research
└── API Gateway

PLUGINS
├── Installed
├── Available
├── Enabled
├── Disabled
└── Permissions

APPS
├── Connected
├── Authentication
├── Tokens
├── Webhooks
└── Events

TOOLS
├── MCP
├── HTTP
├── CLI
├── Browser
├── Files
└── Database
```

---

# 8. Administración completa de plugins

Ejemplo:

```text
┌──────────────────────────────────────┐
│ GitHub                               │
├──────────────────────────────────────┤
│ Status         CONNECTED             │
│ Version        1.4                   │
│                                      │
│ READ             ✓                   │
│ WRITE            ✓                   │
│ CREATE           ✓                   │
│ DELETE           ☐                   │
│ ACTIONS          ✓                   │
│ WEBHOOKS         ✓                   │
│                                      │
│ Permission: ENGINEERING              │
│                                      │
│ [ ENABLE ] [ DISABLE ] [ TEST ]      │
└──────────────────────────────────────┘
```

La UI debe permitir administrar permisos por plugin.

---

# 9. Panel de configuración interna del Router

```text
ROUTER CONFIG

ROUTING
☑ Template selection
☑ Task classification
☑ Model registry
☑ Model switching
☑ Connection routing

REASONING
☑ R3
☑ R4
☑ R6
☑ R8
☑ R12

RESEARCH
☑ Basic
☑ Professional
☑ Advanced

MULTI-AGENT
☑ Council
☑ Debate
☑ Consensus
☑ Decision

VALIDATION
☑ Schema
☑ Validator
☑ Sentinel
☑ Verifier
☑ Judge

MEMORY
☑ Short term
☑ Long term
☑ RAG
☑ Retrieval

EXECUTION
☑ Parallel
☑ Sequential
☑ Retry
☑ Escalation
☑ Repetition detection

API
☑ Input schema
☑ Output schema
☑ Run state
☑ Trace
```

Estos controles activan capacidades permitidas; no reescriben el DAG protegido.

---

# 10. Biblioteca de plantillas

Propuesta inicial:

```text
REASONING
├── R3
├── R4
├── R6
├── R8
└── R12

RESEARCH
├── Basic
├── Professional
└── Advanced

SPECIALIZED
├── Code
├── Debug
├── Architecture
├── Frontend
└── Planning

MULTI-AGENT
├── Ask Council
├── Debate
├── Consensus
└── Decision

SYSTEM
├── Verification
└── Escalation
```

La UI permite:

```text
ON / OFF
```

pero cada plantilla conserva su arquitectura fija.

---

# 11. Ficha de plantilla

Ejemplo:

```text
┌────────────────────────────────────┐
│ RESEARCH — ADVANCED                │
├────────────────────────────────────┤
│ Status:        ON                  │
│ Version:       1.2                 │
│ Nodes:         12                  │
│ Models:        7                   │
│ Inputs:        8                   │
│ Outputs:       6                   │
│ Web:           ON                  │
│ MCP:           ON                  │
│ RAG:           ON                  │
│ Sentinel:      ON                  │
│ Judge:         ON                  │
│ DAG:           LOCKED              │
└────────────────────────────────────┘
```

---

# 12. Vista DAG de una plantilla

```text
                    INPUT
                      │
                      ▼
                QUERY ANALYZER
                      │
                      ▼
                 RESEARCH PLAN
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
         WEB         CODE        RAG
        AGENT       AGENT       AGENT
          │           │           │
          └───────────┼───────────┘
                      ▼
                EVIDENCE MERGE
                      │
                      ▼
                  RED / BLUE
                      │
                      ▼
                    JUDGE
                      │
                      ▼
                 SYNTHESIZER
                      │
                      ▼
                    OUTPUT
```

La UI debe mostrar un candado:

```text
🔒 DAG IMMUTABLE
```

---

# 13. Investigación: tres niveles

## R1 — Basic

```text
INPUT
 ↓
QUERY ANALYZER
 ↓
WEB SEARCH
 ↓
SOURCE FILTER
 ↓
EVIDENCE EXTRACTOR
 ↓
SYNTHESIZER
 ↓
CITATION CHECK
 ↓
OUTPUT
```

Para preguntas que necesitan información actual pero no una investigación exhaustiva.

## R2 — Professional

```text
INPUT
 ↓
QUERY ANALYZER
 ↓
RESEARCH PLAN
 ↓
WEB
 ├── OFFICIAL SOURCES
 ├── REPOSITORIES
 ├── CODE
 ├── COMMUNITY
 └── FORUMS
 ↓
LOCAL RAG
 ↓
SOURCE NORMALIZER
 ↓
EVIDENCE DATABASE
 ↓
CONTRADICTION CHECKER
 ↓
SYNTHESIZER
 ↓
CITATION CHECK
 ↓
OUTPUT
```

Debe poder utilizar un registro de fuentes especializadas por dominio.

## R3 — Advanced

```text
INPUT
 ↓
RESEARCH PLAN
 ↓
RESEARCH COUNCIL
 ├── WEB AGENT
 ├── CODE/REPO AGENT
 └── PAPERS/RAG AGENT
 ↓
EVIDENCE MERGE
 ↓
GAP DETECTOR
 ↓
RESEARCH AGAIN
 ↓
RED TEAM
 ↓
BLUE TEAM
 ↓
JUDGE
 ↓
SYNTHESIS
 ↓
VERIFIER
 ↓
OUTPUT
```

La prioridad puede ser calidad sobre latencia, pero el bucle debe tener condiciones de salida y protección contra ciclos infinitos.

---

# 14. Source Registry

```text
research/sources/

├── programming.yaml
├── ai_models.yaml
├── github.yaml
├── python.yaml
├── javascript.yaml
├── frontend.yaml
├── architecture.yaml
├── security.yaml
├── databases.yaml
├── linux.yaml
├── robotics.yaml
├── mathematics.yaml
└── research.yaml
```

Una plantilla profesional puede exigir, por ejemplo:

```text
Official documentation
Official repository
Source code
GitHub issues
Developer forums
Community
Local RAG
Web search
```

---

# 15. Research Monitor

```text
RESEARCH MONITOR

QUERY
──────────────────────────────────
¿Cómo implementar X?

SOURCES

WEB                  17
GITHUB               12
DOCUMENTATION         8
COMMUNITY             6
LOCAL RAG            21
PAPERS                4

TOTAL                 68
```

Estado:

```text
✓ Official documentation
✓ Source code
✓ GitHub issues
✓ Developer discussion
⚠ Contradiction detected
✓ Resolved
```

---

# 16. Evidence Graph

```text
                 QUESTION
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
       GitHub      Docs       Web
         │          │          │
         ▼          ▼          ▼
       FACT A     FACT B     FACT C
         │          │          │
         └──────────┼──────────┘
                    ▼
               COMPARISON
                    │
              ┌─────┴─────┐
              ▼           ▼
           SUPPORT    CONTRADICTION
              │           │
              └─────┬─────┘
                    ▼
                  JUDGE
```

Cada evidencia debe tener:

```text
Source
Type
Relevance
Verification
Claim
Location
```

---

# 17. Ask Council

```text
QUESTION
   │
   ├── AI ARCHITECT
   ├── AI ENGINEER
   ├── SECURITY
   ├── PERFORMANCE
   └── RESEARCHER
   │
   ▼
COUNCIL
   │
   ▼
JUDGE
   │
   ▼
PROPOSALS
```

La UI debe permitir visualizar cada especialista y su estado.

---

# 18. Debate

```text
             PROPOSAL
                 │
        ┌────────┴────────┐
        ▼                 ▼
      BLUE               RED
   defender           atacar
        │                 │
        └────────┬────────┘
                 ▼
               JUDGE
                 │
        ┌────────┴────────┐
        ▼                 ▼
      REJECT            ACCEPT
        │                 │
        ▼                 ▼
 RESEARCH AGAIN         OUTPUT
```

---

# 19. Decision Package

La UI debe poder presentar varias alternativas:

```text
┌────────────────────────────────────┐
│ PROPOSAL A                         │
│                                    │
│ Pros: ...                          │
│ Cons: ...                          │
│ Evidence: 14                       │
│ Score: 91%                         │
│                                    │
│ [ ELEGIR A ]                       │
└────────────────────────────────────┘

┌────────────────────────────────────┐
│ PROPOSAL B                         │
│                                    │
│ [ ELEGIR B ]                       │
└────────────────────────────────────┘

┌────────────────────────────────────┐
│ PROPOSAL C                         │
│                                    │
│ [ ELEGIR C ]                       │
└────────────────────────────────────┘
```

---

# 20. Run Monitor

```text
RUN #000183
Template: RESEARCH-PROFESSIONAL

● Input                         DONE
● Classifier                    DONE
● Research Planner              DONE
● Web Research                  RUNNING
● GitHub Research               12 sources
● RAG                           8 documents
○ Evidence Merge                WAITING
○ Critic                        WAITING
○ Judge                         WAITING
○ Synthesizer                   WAITING
```

Información de recursos:

```text
RAM 14.8 / 32 GB
CPU 63%
Models: 4 loaded
```

---

# 21. Model Registry

```text
LOCAL MODELS

● Gemma
  RAM: ...
  Status: READY

● Qwen
  RAM: ...
  Status: READY

● HRM
  RAM: ...
  Status: READY

● HRM-Text
  RAM: ...
  Status: UNLOADED

● Coder
  RAM: ...
  Status: READY
```

Roles:

```text
REASONER  → model
CODER     → model
RESEARCHER → model
VERIFIER  → model
JUDGE     → model
```

El rol es parte de la plantilla; el modelo concreto puede cambiar dentro de los modelos autorizados.

---

# 22. Selector de profundidad

```text
REASONING DEPTH

[ SIMPLE ] [ 3 ] [ 4 ] [ 6 ] [ 8 ] [ 12 ]
```

Esto selecciona plantillas:

```text
R3  → plantilla R3
R4  → plantilla R4
R6  → plantilla R6
R8  → plantilla R8
R12 → plantilla R12
```

No construye dinámicamente una cadena.

---

# 23. WHY THIS TEMPLATE?

Botón:

```text
[ WHY THIS TEMPLATE? ]
```

Resultado:

```text
Template selected:
RESEARCH-PROFESSIONAL

Reason:
• Current information required
• Technical subject detected
• External sources required
• Local knowledge insufficient

Template is fixed.
Router did not modify DAG.
```

Esto permite auditar la selección.

---

# 24. Sentinel

```text
SENTINEL ● ACTIVE
```

Supervisa:

```text
✓ schema
✓ model permissions
✓ DAG integrity
✓ tool permissions
✓ loops
✓ token limits
✓ output format
✓ source requirements
```

Si se intenta una transición no autorizada:

```text
⚠ EXECUTION BLOCKED

Expected:
critic → verifier

Received:
critic → unknown_node

Action:
BLOCKED
```

---

# 25. Repetición / Escalation

El sistema puede registrar:

```text
question_hash
problem_id
previous_attempts
failed_templates
missing_information
sources_consulted
```

Si la misma pregunta sigue sin resolverse:

```text
attempt 1
 ↓
failed
 ↓
attempt 2
 ↓
same problem detected
 ↓
ESCALATION
 ↓
RESEARCH-PROFESSIONAL
o
RESEARCH-ADVANCED
```

El router activa una plantilla existente; no inventa una nueva.

---

# 26. Run State

Cada ejecución debe tener un estado estructurado:

```text
RUN STATE

├── input
├── context
├── plan
├── candidates[]
├── critiques[]
├── evidence[]
├── verification[]
├── consensus
├── judge
└── final_package
```

Cada nodo devuelve un paquete estructurado:

```json
{
  "run_id": "R123",
  "template": "T05",
  "node": "critic",
  "status": "ok",
  "result": {},
  "confidence": 0.87,
  "errors": [],
  "evidence": [],
  "next": "verifier"
}
```

---

# 27. Consolidación de la API

El flujo final:

```text
12 nodos / múltiples resultados
            ↓
        RUN STATE
            ↓
           JUDGE
            ↓
       SYNTHESIZER
            ↓
       OUTPUT SCHEMA
            ↓
           API
            ↓
          AGENT
```

El `SYNTHESIZER` recibe:

```text
candidates
+
critiques
+
verification
+
judge
+
evidence
```

Y produce:

```json
{
  "answer": "...",
  "alternatives": [
    "...",
    "...",
    "..."
  ],
  "recommendation": "...",
  "confidence": 0.91,
  "verification": {
    "status": "passed"
  },
  "sources": [],
  "reasoning_trace_id": "R123"
}
```

---

# 28. Las cinco áreas principales de la UI

```text
1. CENTRAL CANVAS
   Fichas + puertos + conexiones + DAG.

2. CONNECTION CENTER
   API / MCP / HTTP / apps / storage / GitHub /
   Hugging Face / teléfono / servicios.

3. ENGINEERING CONTROL
   Apps / plugins / permisos / herramientas /
   conectores / sistema.

4. ROUTER CONFIG
   Templates / reasoning / research / memory /
   validation / execution / API.

5. RUN + OBSERVABILITY
   Estado / logs / trazas / RAM / CPU / GPU /
   Sentinel / Judge / resultados.
```

---

# 29. Estructura conceptual del Router

```text
                         USER / AGENT
                              │
                              ▼
                       ROUTER CORE
                              │
                              ▼
                      CLASSIFIER
                              │
                              ▼
                    TEMPLATE REGISTRY
                              │
                              ▼
                       DSL SCHEMA
                              │
                              ▼
                         VALIDATOR
                              │
                              ▼
                    PREDEFINED DAG
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
     MODELS                TOOLS                 MEMORY
        │                     │                     │
        ├── local             ├── MCP              ├── RAG
        ├── HRM              ├── HTTP             ├── vector DB
        ├── HRM-Text         ├── API              └── external
        └── other            └── apps
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                          SENTINEL
                              │
                              ▼
                            JUDGE
                              │
                              ▼
                         SYNTHESIZER
                              │
                              ▼
                       OUTPUT SCHEMA
                              │
                              ▼
                             API
                              │
                              ▼
                            AGENT
```

---

# 30. Paquetes open source para estudiar/fusionar en el backend

Los siguientes son **enlaces de descarga ZIP del repositorio completo**, no enlaces a archivos individuales.

## 1. LangGraph

https://github.com/langchain-ai/langgraph/archive/refs/heads/main.zip

## 2. Open Deep Research

https://github.com/langchain-ai/open_deep_research/archive/refs/heads/main.zip

## 3. GPT Researcher

https://github.com/assafelovic/gpt-researcher/archive/refs/heads/master.zip

## 4. Deep Research — dzhng

https://github.com/dzhng/deep-research/archive/refs/heads/main.zip

## 5. Agents Deep Research

https://github.com/qx-labs/agents-deep-research/archive/refs/heads/main.zip

## 6. LlamaIndex

https://github.com/run-llama/llama_index/archive/refs/heads/main.zip

## 7. Haystack

https://github.com/deepset-ai/haystack/archive/refs/heads/main.zip

## 8. LiteLLM

https://github.com/BerriAI/litellm/archive/refs/heads/main.zip

## 9. PydanticAI

https://github.com/pydantic/pydantic-ai/archive/refs/heads/main.zip

## 10. MCP Servers

https://github.com/modelcontextprotocol/servers/archive/refs/heads/main.zip

## 11. MCP Python SDK

https://github.com/modelcontextprotocol/python-sdk/archive/refs/heads/main.zip

## 12. Ollama

https://github.com/ollama/ollama/archive/refs/heads/main.zip

## 13. vLLM

https://github.com/vllm-project/vllm/archive/refs/heads/main.zip

## 14. Qdrant

https://github.com/qdrant/qdrant/archive/refs/heads/master.zip

## 15. Chroma

https://github.com/chroma-core/chroma/archive/refs/heads/main.zip

## 16. Guardrails AI

https://github.com/guardrails-ai/guardrails/archive/refs/heads/main.zip

## 17. Phoenix

https://github.com/Arize-ai/phoenix/archive/refs/heads/main.zip

## 18. CrewAI

https://github.com/crewAIInc/crewAI/archive/refs/heads/main.zip

## 19. Microsoft AutoGen

https://github.com/microsoft/autogen/archive/refs/heads/main.zip

## 20. n8n

https://github.com/n8n-io/n8n/archive/refs/heads/master.zip

---

# 31. Arquitectura de integración propuesta

No se deben fusionar los 20 proyectos completos indiscriminadamente.

La idea es estudiar/fusionar componentes:

```text
ORCHESTRATION
├── LangGraph
├── Haystack
├── CrewAI
└── AutoGen (referencia)

RESEARCH
├── Open Deep Research
├── GPT Researcher
├── Deep Research
└── Agents Deep Research

RAG / MEMORY
├── LlamaIndex
├── Qdrant
└── Chroma

MODEL GATEWAY
├── LiteLLM
├── Ollama
└── vLLM

CONNECTIVITY
├── MCP Servers
├── MCP Python SDK
└── n8n

SCHEMA / CONTROL
├── PydanticAI
└── Guardrails

OBSERVABILITY
└── Phoenix
```

---

# 32. Regla final del diseño

```text
ROUTER POLICY

1. El Router selecciona plantillas.
2. Las plantillas tienen DAG fijo.
3. El DAG no cambia durante una ejecución.
4. Los modelos ocupan roles autorizados.
5. Las conexiones utilizan adapters.
6. Los plugins tienen permisos.
7. Las herramientas pasan por validación.
8. Research utiliza niveles predefinidos.
9. Council/Debate/Consensus son plantillas.
10. Sentinel controla la ejecución.
11. Judge valida el resultado.
12. Synthesizer consolida.
13. API recibe un Output Schema.
14. Toda ejecución tiene Run ID y trace.
15. La configuración estructural pertenece al panel de ingenieros.
```

---

# 33. Resultado esperado

La UI final no será solamente un "selector de modelos".

Será un:

**AI-AGENT CONTROL CENTER**

con:

```text
FICHAS
+
CONEXIONES
+
MODELOS
+
PLUGINS
+
APPS
+
MCP
+
API
+
MEMORY
+
RAG
+
RESEARCH
+
DAG
+
TEMPLATES
+
SENTINEL
+
JUDGE
+
OBSERVABILITY
```

y el Router actuará como **orquestador determinista de arquitecturas preprogramadas**.

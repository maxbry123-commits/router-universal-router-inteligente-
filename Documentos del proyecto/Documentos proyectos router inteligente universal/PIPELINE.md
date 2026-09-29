# PIPELINE — ROUTER INTELIGENTE UNIVERSAL

**Versión:** 1.0
**Estado:** BASE DE ARQUITECTURA / INTEGRACIÓN
**Repositorio:** `maxbry123-commits/router-universal-router-inteligente-`

---

## 1. OBJETIVO

Este documento fija la arquitectura de fusión para el Router Inteligente Universal. El objetivo es integrar software open-source reutilizable como infraestructura ejecutable, manteniendo un **Control Plane determinista** y evitando que un modelo de IA pueda modificar la arquitectura de ejecución durante una ejecución.

Regla central:

```text
INPUT
  ↓
CLASSIFIER / ROUTING INTELLIGENCE
  ↓
TEMPLATE REGISTRY
  ↓
DSL + SCHEMA
  ↓
VALIDATION
  ↓
REGISTERED TEMPLATE
  ↓
FIXED DAG
  ↓
EXECUTION
  ↓
MODEL / TOOL / RESEARCH / CONNECTOR
  ↓
OUTPUT SCHEMA
  ↓
VALIDATION / GUARDRAILS
  ↓
SENTINEL / JUDGE
  ↓
SYNTHESIZER
  ↓
FINAL OUTPUT
```

El Router **selecciona** una plantilla registrada; no crea nodos, no elimina nodos, no reordena nodos, no inventa modelos y no modifica el DAG durante la ejecución.

---

# 2. INVENTARIO BASE — 24 COMPONENTES

Los siguientes componentes ya fueron consolidados y no deben volver a investigarse como si fueran nuevos.

## A. Ejecución / DSL / DAG

1. **Dagu** — DAG declarativo, YAML, scheduler, retries, ejecución, workers e historial.
2. **Microsoft Prompt flow** — flows orientados a LLM, prompts, Python, herramientas, inputs/outputs y evaluación.
3. **Temporal** — ejecución durable, recuperación, retries y estado persistente.
4. **Open Workflow Specification** — especificación, DSL y schemas de workflow.
5. **Argo Workflows** — ejecución de workflows/DAG.
6. **Kestra** — workflow orchestration declarativo.

## B. Gateway / comunicación / modelos

7. **LiteLLM** — gateway multi-modelo y normalización de proveedores.
8. **Bifrost** — AI gateway, routing y conectividad de modelos/MCP.
9. **MCP Servers** — conectividad mediante Model Context Protocol.
10. **Apache Camel** — integración entre sistemas y protocolos.
11. **Apache APISIX** — API Gateway.
12. **Envoy AI Gateway** — gateway para servicios de IA.

## C. Investigación

13. **SearXNG** — metabuscador.
14. **GPT Researcher** — investigación profunda y recopilación de fuentes.
15. **STORM** — investigación estructurada y síntesis basada en fuentes.
16. **Vane** — búsqueda/investigación web.

## D. Control de prompt, salida y política

17. **PydanticAI** — contratos Python/Pydantic y salidas estructuradas.
18. **Guardrails AI** — validación y control de outputs.
19. **Promptfoo** — pruebas, evaluación y regresión de prompts/modelos/outputs.
20. **OpenFGA** — autorización y relaciones de acceso.

## E. Runtime transversal añadido

21. **Blinker** — dispatcher/eventos internos ligeros en Python.
22. **OpenTelemetry Python** — tracing, spans, métricas e instrumentación.
23. **Pluggy** — PluginManager, hooks, registro y ejecución de plugins.
24. **OpenBao** — secretos, credenciales, autenticación, leases y auditoría.

---

# 3. CAPA DE ROUTING INTELIGENTE — 3 CANDIDATOS ADICIONALES

Estos tres repositorios se incorporan al diseño como **fuentes de código/algoritmos de routing**, no como agentes ni como nuevos orquestadores. La integración final debe seleccionar las partes útiles y evitar duplicación.

## 25. Aurelio Semantic Router

Repositorio: `aurelio-labs/semantic-router`

Función principal: routing semántico de baja latencia mediante representaciones vectoriales para decidir qué ruta debe recibir una entrada.

Uso propuesto:

```text
INPUT
 ↓
SEMANTIC ROUTER
 ↓
INTENT / ROUTE
 ↓
TEMPLATE REGISTRY
```

Aporta una base Python reutilizable para clasificación/routing semántico sin convertir el Router en un agente.

## 26. vLLM Semantic Router

Repositorio: `vllm-project/semantic-router`

Función principal: routing inteligente de inferencia con señales de solicitud, complejidad, estado/capacidad y selección de destino. Su configuración puede expresarse declarativamente.

Uso propuesto:

```text
REQUEST
 ↓
ROUTING SIGNALS
 ↓
MODEL / ENDPOINT SELECTION
 ↓
MODEL GATEWAY
```

Se estudiará especialmente para extraer mecanismos de routing, scoring, filtros y configuración que puedan integrarse en el Control Plane.

## 27. UIUC LLMRouter

Repositorio: `ulab-uiuc/LLMRouter`

Función principal: biblioteca de algoritmos de LLM routing, incluyendo estrategias basadas en KNN, SVM, MLP, Matrix Factorization, Elo, grafos, BERT y métodos híbridos.

Uso propuesto:

```text
REQUEST FEATURES
 ↓
ROUTING MODEL
 ↓
SCORE CANDIDATE MODELS
 ↓
MODEL SELECTION
```

Se utilizará principalmente como fuente de algoritmos/estrategias de selección, no como sustituto completo del Control Plane.

---

# 4. ARQUITECTURA DE FUSIÓN

```text
                         ┌──────────────────────────────┐
                         │          INPUT API           │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │       INPUT CONTRACT         │
                         │ YAML / Python / Pydantic    │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                ┌──────────────────────────────────────────────┐
                │             INTELLIGENT ROUTER               │
                │                                              │
                │ Aurelio Semantic Router                     │
                │ vLLM Semantic Router                         │
                │ UIUC LLMRouter algorithms                    │
                │                                              │
                │ classifier + scoring + policy               │
                └─────────────────────┬────────────────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────────┐
                         │       TEMPLATE REGISTRY      │
                         │ ID / VERSION / ROLE / ACL   │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │        DSL + SCHEMA          │
                         │ Open Workflow Specification  │
                         │ Prompt flow YAML             │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │          VALIDATOR            │
                         │ PydanticAI + Guardrails      │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │       FIXED DAG TEMPLATE      │
                         │ Dagu / Temporal / Kestra /   │
                         │ Argo / Prompt flow           │
                         └──────────────┬───────────────┘
                                        │
                 ┌──────────────────────┼──────────────────────┐
                 │                      │                      │
                 ▼                      ▼                      ▼
       ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
       │   MODEL PLANE    │   │   TOOL / MCP     │   │    RESEARCH      │
       │ LiteLLM/Bifrost  │   │ MCP/Camel/APIs   │   │ SearXNG/Vane      │
       │ model providers  │   │ connectors       │   │ GPT-R/STORM       │
       └────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘
                │                      │                      │
                └──────────────────────┼──────────────────────┘
                                       │
                                       ▼
                         ┌──────────────────────────────┐
                         │       OUTPUT CONTRACT        │
                         │ Pydantic schema             │
                         │ Guardrails validators       │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │       SENTINEL / JUDGE       │
                         │ deterministic policy checks  │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │         SYNTHESIZER           │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                              ┌────────────────────┐
                              │    FINAL OUTPUT     │
                              └────────────────────┘
```

---

# 5. CAPAS TRANSVERSALES

Estas capas no deben quedar dentro de un único DAG ni mezclarse con la lógica del Router.

## Seguridad

```text
OpenFGA → autorización / relaciones de acceso
OpenBao → secretos / credenciales / claves
```

Las plantillas deben referenciar credenciales mediante IDs, nunca contener secretos directamente.

Ejemplo:

```yaml
credentials:
  provider_ref: github-production
```

## Eventos

Blinker proporciona el mecanismo interno para eventos del proceso:

```text
RUN_STARTED
NODE_STARTED
NODE_COMPLETED
NODE_FAILED
RESEARCH_COMPLETED
VALIDATION_FAILED
JUDGE_COMPLETED
RUN_COMPLETED
RUN_FAILED
```

## Plugins

Pluggy proporciona el mecanismo de hooks/registro para extensiones controladas:

```text
Plugin Registry
 ↓
Manifest
 ↓
Permission Check
 ↓
Hook Registration
 ↓
Execution
```

## Observabilidad

OpenTelemetry debe envolver las operaciones relevantes:

```text
RUN
 ├── ROUTING
 ├── TEMPLATE
 ├── NODE
 ├── MODEL
 ├── TOOL
 ├── CONNECTOR
 ├── VALIDATION
 ├── JUDGE
 └── OUTPUT
```

Cada ejecución debe poder correlacionarse mediante `run_id` y contexto de trace.

---

# 6. SYSTEM PROMPT COMO CONTRATO EJECUTABLE

El sistema debe soportar un contrato de prompt definido en YAML y/o Python, de forma que **cada entrada y salida tenga un esquema verificable**.

No se debe tratar el system prompt como un bloque libre aislado. Se debe representar como datos estructurados y versionados.

## Contrato conceptual

```text
PROMPT CONTRACT
│
├── id
├── version
├── role
├── objective
├── system.rules[]
├── input.schema
├── input.constraints[]
├── model.policy
├── tools.allowed[]
├── output.schema
├── output.constraints[]
├── validators[]
├── retry_policy
└── permissions
```

## Ejemplo YAML

```yaml
prompt_contract:
  id: research_verifier
  version: "1.0"

  role: verifier
  objective: verify_claims_with_evidence

  system:
    rules:
      - verify_each_claim
      - use_evidence
      - never_invent_sources
      - return_only_declared_schema

  input:
    schema:
      question:
        type: string
        required: true
      findings:
        type: array
        required: true

  model:
    role: verifier
    allowed_models:
      - verifier_model_a
      - verifier_model_b

  output:
    schema:
      verified:
        type: boolean
        required: true
      corrections:
        type: array
        required: true
      evidence:
        type: array
        required: true

  validation:
    - pydantic
    - guardrails
```

## Equivalente Python

```python
from pydantic import BaseModel

class VerificationInput(BaseModel):
    question: str
    findings: list

class VerificationOutput(BaseModel):
    verified: bool
    corrections: list
    evidence: list
```

Flujo:

```text
SYSTEM ROLE
 ↓
INPUT SCHEMA
 ↓
MODEL
 ↓
OUTPUT SCHEMA
 ↓
PYDANTIC VALIDATION
 ↓
GUARDRAILS
 ↓
SENTINEL / JUDGE
 ↓
FINAL OUTPUT
```

Esto permite que cada nodo tenga su propio contrato:

```text
NODE
├── system.role
├── system.rules
├── input.schema
├── execution policy
├── output.schema
├── validators
└── permissions
```

---

# 7. PROGRAMACIÓN DEL ROUTER

El código propio del Router debe ser pequeño y actuar como Control Plane.

Módulos previstos:

```text
router/
├── classifier/
├── routing_engine/
├── scoring/
├── template_registry/
├── contract_registry/
├── policy/
├── model_registry/
├── connector_registry/
├── execution_dispatcher/
├── validation/
└── run_context/
```

El Router recibe un input estructurado, calcula/obtiene señales de routing, selecciona un template autorizado y entrega un `RunSpec` al motor de ejecución.

Ejemplo conceptual:

```python
run_spec = router.route(request)

assert run_spec.template_id in template_registry
assert policy.can_execute(run_spec)
assert schema.validate(run_spec.input)

execution.submit(run_spec)
```

El resultado del Router no debe ser texto libre. Debe ser un objeto estructurado equivalente a:

```yaml
run_spec:
  run_id: generated
  template_id: research_verifier
  template_version: "1.0"
  route:
    intent: research
    complexity: high
  model_policy: verifier
  input: validated_input
  permissions: validated_permissions
```

---

# 8. FUSIÓN DE LOS 3 ROUTERS

No se deben ejecutar los tres como tres routers independientes en producción.

La fusión propuesta es:

```text
                     REQUEST
                        │
                        ▼
              ┌──────────────────┐
              │ FEATURE EXTRACTOR│
              └────────┬─────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
     SEMANTIC      ROUTING      LEARNED /
      SIGNALS       RULES       ALGORITHMS
          │            │            │
     Aurelio       vLLM SR       UIUC
          └────────────┼────────────┘
                       ▼
                 SCORE / POLICY
                       ▼
                ROUTE DECISION
                       ▼
               TEMPLATE REGISTRY
```

La decisión final pertenece al **Router propio**. Los tres proyectos aportan mecanismos, modelos o algoritmos reutilizables; no sustituyen el contrato central.

Regla de precedencia:

1. seguridad/policy;
2. template permitido;
3. capacidad requerida;
4. compatibilidad de input/output;
5. calidad esperada;
6. latencia;
7. coste;
8. disponibilidad/health;
9. decisión final de routing.

---

# 9. CONTROL DE INPUT Y OUTPUT

Cada frontera entre módulos debe tener contrato.

```text
INPUT
 ↓ schema validation
 ↓ normalization
 ↓ routing features
 ↓ route decision
 ↓ template input schema
 ↓ node execution
 ↓ output schema
 ↓ validation
 ↓ guardrails
 ↓ policy checks
 ↓ final package
```

Nunca se debe asumir que una salida de modelo es válida solamente porque el modelo terminó correctamente.

Estados mínimos:

```text
VALID
INVALID_SCHEMA
VALIDATION_FAILED
RETRY_REQUIRED
POLICY_DENIED
EXECUTION_FAILED
COMPLETED
```

---

# 10. RESEARCH PIPELINE

La capa de investigación queda integrada como capacidad del Model/Tool Plane:

```text
RESEARCH REQUEST
 ↓
RESEARCH TEMPLATE
 ↓
SearXNG / Vane
 ↓
SOURCE COLLECTION
 ↓
GPT Researcher / STORM
 ↓
EVIDENCE / CITATION OBJECTS
 ↓
VERIFICATION
 ↓
JUDGE
 ↓
SYNTHESIS
```

Los resultados de investigación deben conservar procedencia y evidencia; no deben mezclarse con texto de modelo sin distinguir fuente y generación.

---

# 11. MODEL PLANE

```text
Router
 ↓
Model Policy
 ↓
Model Registry
 ↓
LiteLLM / Bifrost
 ↓
Provider / Local Model
```

El Router no debe codificar directamente cada proveedor. Los gateways y adapters aíslan esa variabilidad.

---

# 12. CONNECTIVITY PLANE

```text
Core
 ↓
Connector Registry
 ↓
Adapter
 ↓
Camel / APISIX / Envoy / MCP
 ↓
External System
```

Las credenciales se resuelven mediante `credential_ref` y OpenBao. OpenFGA controla si la ejecución está autorizada.

---

# 13. EJECUCIÓN Y ESTADO

Los motores de workflow existentes proporcionan la infraestructura de ejecución. El sistema propio debe mantener un contrato común sobre ellos y no permitir que cada motor cambie el modelo lógico del Router.

Conceptualmente:

```text
RunSpec
 ↓
Execution Adapter
 ↓
DAG / Workflow Engine
 ↓
Node Execution
 ↓
Run State
```

El estado mínimo debe contemplar:

```yaml
run:
  id: ...
  status: ...
  template_id: ...
  template_version: ...
  input: ...
  nodes: ...
  outputs: ...
  evidence: ...
  validation: ...
  judge: ...
  trace_id: ...
```

---

# 14. DEPENDENCIAS Y PRINCIPIO DE MINIMALIDAD

No se deben instalar automáticamente los 27 proyectos completos como una única aplicación.

La arquitectura debe distinguir:

```text
CORE PROPIO
 ↓
LIBRERÍAS REUTILIZADAS
 ↓
SERVICIOS EXTERNOS OPCIONALES
 ↓
ADAPTERS
```

Los proyectos deben incorporarse solamente cuando el código auditado aporte una función necesaria.

Los 3 routers adicionales son especialmente candidatos a **extracción selectiva de algoritmos/código**, no necesariamente dependencias runtime obligatorias.

---

# 15. SEGURIDAD

Reglas obligatorias:

- ningún secreto dentro de YAML de templates;
- ningún token dentro de código fuente;
- `credential_ref` en lugar de credenciales reales;
- OpenFGA para autorización;
- OpenBao para secretos;
- permisos por template, modelo, herramienta, connector y plugin;
- auditoría de acciones sensibles;
- validación antes de ejecutar herramientas externas.

---

# 16. TESTING

Promptfoo debe utilizarse para regresión de prompts y routing. Los tests del código propio deben comprobar contratos y determinismo.

Matriz mínima:

```text
INPUT CONTRACT
OUTPUT CONTRACT
ROUTING DECISION
TEMPLATE SELECTION
MODEL POLICY
TOOL POLICY
SCHEMA VALIDATION
GUARDRAILS
FAILURE / RETRY
PERMISSION DENIAL
TRACE CREATION
PLUGIN ISOLATION
SECRET REFERENCE
```

---

# 17. OBSERVABILIDAD

Cada ejecución debe producir como mínimo:

```text
run_id
trace_id
span_id
route
selected_template
selected_model
node_id
start_time
end_time
status
validation_status
error
```

OpenTelemetry es la capa estándar de instrumentación. Blinker se limita a eventos internos; no debe utilizarse como sustituto de tracing.

---

# 18. PRINCIPIOS DE INTEGRACIÓN

1. **Router ≠ agente.**
2. **Router ≠ workflow engine.**
3. **Template ≠ prompt libre.**
4. **Prompt ≠ permiso.**
5. **Model selection ≠ execution.**
6. **Authentication/secrets ≠ authorization.**
7. **Evidence ≠ model output.**
8. **Trace ≠ event bus.**
9. **Plugin ≠ arbitrary code execution.**
10. **Cada frontera tiene schema.**
11. **Cada ejecución tiene Run ID.**
12. **El DAG registrado permanece fijo durante la ejecución.**
13. **No se añade software si el código existente ya cubre la función.**

---

# 19. OBJETIVO FINAL DEL BACKEND

La fusión completa debe permitir:

```text
REQUEST
 ↓
STRUCTURED INPUT
 ↓
INTELLIGENT ROUTING
 ↓
AUTHORIZED TEMPLATE
 ↓
SYSTEM ROLE + INPUT SCHEMA
 ↓
FIXED DAG
 ↓
MODEL / TOOL / RESEARCH / CONNECTORS
 ↓
STRUCTURED OUTPUT
 ↓
PYDANTIC
 ↓
GUARDRAILS
 ↓
SENTINEL / JUDGE
 ↓
SYNTHESIZER
 ↓
TRACE + AUDIT
 ↓
FINAL CONTRACTED OUTPUT
```

El resultado es un backend modular donde el Router propio controla **qué plantilla se ejecuta**, mientras que los proyectos open-source proporcionan infraestructura especializada para ejecución, modelos, conectividad, investigación, validación, seguridad, plugins, eventos y observabilidad.

---

# 20. ESTADO DEL PIPELINE

**Base:** 24 componentes consolidados.

**Capa de investigación de routing:** 3 candidatos adicionales.

**Total de arquitectura documentada:** 27 componentes/referencias.

**Regla:** los 3 candidatos de routing deben someterse a auditoría de código antes de convertirse en dependencias definitivas.

**Siguiente checkpoint:** auditoría fuente por fuente de Aurelio Semantic Router, vLLM Semantic Router y UIUC LLMRouter para identificar código reutilizable, dependencias, licencias, solapamientos con LiteLLM/Bifrost y partes que deben permanecer como código propio.

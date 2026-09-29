# Handoff — índice de componentes — Router Inteligente Universal

## 0. Fuente de verdad y propósito

Este documento es el índice operativo para saber **qué existe, qué está parcial, qué falta y cómo debe integrarse** en `maxbry123-commits/router-universal-router-inteligente-`.

Reglas heredadas de los documentos de arquitectura:
- backend Python **95% determinista / 5% LLM**;
- el Router **NO inventa DAGs**: clasifica la tarea y activa una plantilla DAG fija previamente validada;
- todo destino/origen entra como `Conector` con contrato común `async enviar(payload)->dict` + `async sondear()->bool`;
- todo conector debe pasar por **Enchufe Gate v2.0**, preservando compatibilidad v1.5;
- arquitectura hexagonal; `REUSE > PATCH > ADAPT > GENERATE`;
- secretos solo por entorno/Vault, nunca hardcodeados;
- archivo presente ≠ integrado; componente descargado ≠ cableado.

## 1. Flujo objetivo

`USUARIO/API -> Alcabala -> Enchufe Gate -> Router/RedUniversal -> selector/worker pool -> DAG fijo T01-T12 -> conectores -> destinos reales -> ledger/monitoring/storage`

Destinos: IA/LLM, MCP, GitHub, Hugging Face, bases de datos, dispositivos, VPS/SSH, agentes A2A/ACP, mensajería y futuros conectores compatibles.

## 2. Componentes de arquitectura C01-C23

| ID | Componente | Estado de diseño | Acción de integración |
|---|---|---|---|
| C01 | API Gateway REST/WS | MISSING | GENERATE; routers Paneles 1-5 sin lógica de negocio |
| C02 | InboundGatekeeper / Alcabala | MISSING | GENERATE; firma, tokens, schema, fail-closed |
| C03 | Config inmutable | MISSING | GENERATE; env única fuente de configuración |
| C04 | SecretVault | MISSING | GENERATE; cifrado/rotación/BYOK |
| C05 | Enchufe Schema Pydantic v2 | NEW diseñado | MATERIALIZE + WIRE desde validator_v2 |
| C06 | DAGParser | MISSING | GENERATE; parser + detección de ciclos |
| C07 | Templates T01-T12 | MISSING | GENERATE; DAGs fijos, no improvisables |
| C08 | DAGOrchestrator | MISSING | GENERATE; checkpoints por nodo |
| C09 | Worker Pool / selección / cola | MISSING | GENERATE; capability-driven |
| C10 | Resilience | MISSING | GENERATE/ADAPT; retry + circuit breaker temporal |
| C11 | Semantic Cache | MISSING | GENERATE/ADAPT sobre Redis/vector similarity |
| C12 | Cost Optimizer | MISSING | GENERATE; presupuesto/policy |
| C13 | CodeSandbox dual | MISSING | GENERATE/ADAPT; Docker + subprocess con paridad |
| C14 | Windows Chain 1-100 | NEW diseñado | MATERIALIZE; ventanas encadenables configurables |
| C15 | Enchufe Gate | EXISTING_COMPLETE v1.5 | PATCH mínimo para v2.0; conservar firma pública |
| C16 | Conectores | EXISTING_PARTIAL | PATCH/ADAPT; ampliar catálogo v6 sin reescribir bases |
| C17 | RedUniversal | EXISTING_COMPLETE | REUSE; namespaces + rutas fnmatch + modos de envío |
| C18 | Storage protocol/adapters | MISSING | GENERATE; Postgres/Redis detrás de plugin |
| C19 | Backup / respaldo | EXISTING_COMPLETE | REUSE tal cual |
| C20 | Auth | MISSING | GENERATE; integración Vault/credenciales |
| C21 | Audit Ledger hash-chain | MISSING | GENERATE; append-only |
| C22 | Monitoring | MISSING | GENERATE/ADAPT; métricas/health/tracing |
| C23 | WebSocket/SSE events | MISSING | GENERATE; eventos de progreso |

### Resumen de estado
- **Existente completo reutilizable:** C15, C17, C19.
- **Existente parcial:** C16.
- **Diseño nuevo ya especificado pero aún debe materializarse:** C05, C14.
- **Faltantes de implementación según DOC-A02:** C01-C04, C06-C13, C18, C20-C23.

## 3. Código/raíces REUSE identificados por ROOT_ID

- `R-001 red/enchufe_gate.py` — existente; PATCH v1.5→v2.0.
- `R-002 red/conectores.py` — existente parcial; ampliar conectores v6.
- `R-003 red/red_universal.py` — existente completo; no mover ni reescribir.
- `R-004 infrastructure/backup/respaldo.py` — existente completo; REUSE.
- `R-005 enchufe/validator_v2.py` — diseño completo disponible; materializar + conectar.

## 4. Componentes open source físicamente disponibles

Raíz física consolidada:
`Componente open soure router inteligente universal/`

Inventario observado en `main`:
`Chart.js`, `Durable-Task-Python`, `Durable-Workflow-Server`, `LiteLLM`, `MCP-Python-SDK`, `Prefect`, `PyGithub`, `RouterArena`, `SGLang`, `Sentence-Transformers`, `Temporal-Python-SDK`, `TypeScript`, `agents-deep-research`, `aiomysql`, `asyncpg`, `autogen`, `chroma`, `crewAI`, `cryptography`, `docker-py`, `dzhng-deep-research`, `fastapi`, `gpt-researcher`, `grafana`, `guardrails`, `gunicorn`, `haystack`, `httpx`, `huggingface_hub`, `langgraph`, `litellm`, `llama.cpp`, `llama_index`, `lucide`, `n8n`, `ollama`, `open_deep_research`, `phoenix`, `plex`, `postgres`, `prometheus`, `pydantic-ai`, `pydantic-settings`, `pydantic`, `python-dotenv`, `python-sdk`, `pyyaml`, `qdrant`, `react`, `redis-py`, `redis`, `ruflo`, `servers`, `starlette`, `tailwindcss`, `uvicorn`, `vLLM-Router`, `vLLM-Semantic-Router`, `vite`, `vllm`, `zustand` y artefactos auxiliares.

**Estado de integración:** disponibilidad física únicamente. Ninguno se considera integrado por estar descargado. Cada uso exige adapter/wiring/test/evidencia.

## 5. Mapa de integración recomendado por capacidad

| Capacidad del Router | Donantes/reuse candidatos ya disponibles | Regla |
|---|---|---|
| API REST/WS | FastAPI, Starlette, Uvicorn, HTTPX | adaptar detrás de `api/`; no meter lógica de negocio |
| Validación/contratos | Pydantic, pydantic-settings | Enchufe v2.0 como contrato canónico |
| MCP | MCP-Python-SDK, `servers` | adapter `ConectorMCP`; no segundo core |
| GitHub | PyGithub | `ConectorGitHub`; secretos por Vault/env |
| Hugging Face | huggingface_hub | `ConectorHuggingFace`; reutilizar puente HF↔GitHub existente cuando aplique |
| Routing LLM | LiteLLM/litellm, vLLM-Router, vLLM-Semantic-Router, SGLang | donors detrás del Router; no propietarios paralelos del workflow |
| Workflows/durabilidad | Prefect, Temporal-Python-SDK, Durable-* | donor/adapters; el DAG del Router sigue siendo contrato fijo |
| Storage/cache | Postgres, Redis/redis-py, Qdrant, Chroma | detrás de `storage_protocol`, nunca llamadas dispersas |
| Sandbox | docker-py | backend Docker + fallback subprocess obligatorio |
| Seguridad | cryptography, guardrails | Vault/validación; secrets nunca en logs |
| Observabilidad | Prometheus, Grafana, Phoenix | integrar después del ledger/monitoring base |
| Investigación/agentes | autogen, crewAI, langgraph, haystack, llama_index, research repos | donor opcional dentro de nodos permitidos; no pueden modificar el DAG |

## 6. Análisis de integración

### 6.1 Núcleo que debe permanecer único
`Enchufe Gate -> RedUniversal -> DAGParser/DAGOrchestrator -> WorkerPool -> Conectores`.

No ejecutar Prefect, Temporal, LangGraph, CrewAI, AutoGen o similares como orquestadores paralelos que puedan alterar el DAG estructural. Si se reutilizan, deben vivir como adapters/donors dentro de un nodo autorizado.

### 6.2 Integración por fases del DAG de construcción
1. **Foundation:** Config + Enchufe Schema v2 + Gate v1.5/v2 + validator.
2. **Base services:** Vault + storage + backup; en paralelo ampliar Red y crear templates/parser.
3. **Core:** Auth + Ledger + Monitoring + Resilience + Cache + Cost.
4. **Execution:** WorkerPool + Sandbox dual.
5. **Integration:** DAGOrchestrator + Windows Chain + Alcabala + WS/SSE.
6. **API:** routers de Paneles 1-5 y E2E.

### 6.3 GAP principal actual
El repositorio tiene una biblioteca open source amplia, pero el **backend objetivo C01-C23 no debe darse por construido** solo por esos vendors. Antes de generar cada módulo se debe inspeccionar donor local y decidir `REUSE/PATCH/ADAPT/GENERATE` con evidencia.

### 6.4 Contratos que bloquean desviaciones
- DAG templates fijas: el LLM no crea/elimina/reordena nodos.
- UI puede activar/desactivar configuración autorizada y cambiar `model_id`, no la estructura del DAG.
- Compatibilidad Enchufe v1.5→v2.0 obligatoria.
- 0 secretos hardcodeados.
- Backend actual; frontend/UI queda fuera de esta fase salvo contrato API.
- Evidencia final por ruta + SHA/diff + read-back + test.

## 7. Plan de trabajo existente

La descomposición de arquitectura define 11 tasks:
`TASK-01` Foundation A → `TASK-02/03/04` paralelas → `TASK-05/06` → `TASK-07/08` → `TASK-09/10` → `TASK-11` integración API final.

No cambiar este orden sin un conflicto demostrado y registrado.

## 8. Fuentes de proyecto

- `Documentos proyectos router inteligente universal/` — misión, arquitectura, DAG, root map, dependency map, task decomposition y prompts Chat B.
- `Readme arquitectura router inteligente universal/` — método/arquitectura operacional.
- `Componente open soure router inteligente universal/` — biblioteca donor física.
- `coneccion huggueface Github/` — infraestructura HF↔GitHub ya validada, reutilizable como integración externa cuando corresponda.

## 9. Estado de handoff

`HANDOFF_STATUS: READY_FOR_COMPONENT_GAP_AUDIT`

Siguiente acción correcta antes de programar: cruzar **C01-C23 / R-IDs** contra el árbol físico actual y contra cada donor local, marcando por componente `REUSE | PATCH | ADAPT | GENERATE`, con URL/SHA/destino y test esperado.
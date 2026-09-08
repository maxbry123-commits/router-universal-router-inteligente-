# Índice de componentes — Router Inteligente Universal

Fuente física: `Componente open soure router inteligente universal/`.
Regla: componente presente ≠ integrado. Cada componente debe pasar provenance + adapter + wiring + test antes de considerarse activo.

| Componente | Para qué sirve |
|---|---|
| Chart.js | Visualización de métricas, routing, latencia, costes y estados. |
| Durable-Task-Python | Ejecución de tareas durables y reanudables en Python. |
| Durable-Workflow-Server | Backend durable para workflows, estado y recuperación. |
| LiteLLM | Gateway/unificación de múltiples proveedores y modelos LLM. |
| MCP-Python-SDK | Implementación Python de Model Context Protocol para tools/resources. |
| Prefect | Orquestación de workflows, tareas, retries y observabilidad. |
| PyGithub | Cliente Python para GitHub API. |
| RouterArena | Evaluación/benchmark de estrategias de routing. |
| SGLang | Serving y ejecución eficiente de LLM. |
| Sentence-Transformers | Embeddings semánticos y similitud. |
| Temporal-Python-SDK | Workflows durables y recuperación mediante Temporal. |
| TypeScript | Tipado/compilación para componentes JS/TS del router. |
| agents-deep-research | Patrón/agente de investigación profunda. |
| aiomysql | Cliente MySQL asíncrono. |
| archives | Archivo de paquetes/snapshots preservados del inventario. |
| asyncpg | Cliente PostgreSQL asíncrono de alto rendimiento. |
| autogen | Framework multiagente y coordinación entre agentes. |
| chroma | Vector store para memoria/recuperación semántica. |
| crewAI | Orquestación de equipos de agentes por roles/tareas. |
| cryptography | Primitivas criptográficas, firmas y manejo seguro de credenciales. |
| docker-py | Control de Docker desde Python. |
| dzhng-deep-research | Patrón open source de deep research. |
| fastapi | API HTTP del router y servicios internos. |
| gpt-researcher | Agente de investigación y generación de informes. |
| grafana | Dashboards y observabilidad. |
| guardrails | Validación/guardrails de entradas y salidas de IA. |
| gunicorn | Servidor de procesos para aplicaciones Python web. |
| haystack | Pipelines RAG, retrieval y componentes LLM. |
| httpx | Cliente HTTP síncrono/asíncrono para adapters y proveedores. |
| huggingface_hub | API/SDK para Hub, Spaces, Jobs, modelos y datasets de Hugging Face. |
| langgraph | Grafos/estado para flujos de agentes y ejecución controlada. |
| litellm | Variante/copia del gateway LiteLLM presente en el inventario; requiere dedup antes de wiring. |
| llama.cpp | Inferencia local de modelos GGUF/LLM. |
| llama_index | Indexación, RAG, conectores y recuperación de contexto. |
| lucide | Iconos para UI/telemetría visual. |
| n8n | Automatización visual y workflows de integración. |
| ollama | Runtime local de modelos y API local. |
| open_deep_research | Implementación open source de deep research. |
| phoenix | Observabilidad/evaluación de aplicaciones LLM y trazas. |
| plex | Componente auxiliar preservado del inventario; revisar README/provenance antes de integrarlo. |
| postgres | Base de datos relacional y persistencia durable. |
| prometheus | Métricas, scraping y alertas del router. |
| pydantic-ai | Agentes tipados y validación estructurada con Pydantic. |
| pydantic-settings | Configuración tipada desde entorno/secrets. |
| pydantic | Contratos, schemas y validación de datos. |
| python-dotenv | Carga de variables de entorno en desarrollo. |
| python-sdk | SDK Python auxiliar del inventario; verificar provenance exacta antes de wiring. |
| pyyaml | Lectura/escritura de configuración YAML. |
| qdrant | Vector database para memoria/retrieval semántico. |
| react | UI declarativa del dashboard/router. |
| redis-py | Cliente Python para Redis. |
| redis | Cache, cola, locks y estado efímero/distribuido. |
| ruflo | Orquestación/flujo de agentes preservado como componente donor. |
| servers | Colección de servidores/adapters incluida en el inventario. |
| starlette | Capa ASGI/web ligera para APIs y WebSocket/SSE. |
| tailwindcss | Estilos utilitarios para UI. |
| uvicorn | Servidor ASGI para FastAPI/Starlette. |
| vLLM-Router | Router especializado para backends vLLM. |
| vLLM-Semantic-Router | Routing semántico hacia modelos/endpoints vLLM. |
| vite | Build/dev server para frontend. |
| vllm | Serving de LLM con batching y gestión eficiente de GPU. |
| zustand | Estado ligero para frontend React. |

## Reglas de integración

1. Mantener cada componente aislado en su carpeta.
2. Registrar URL + SHA + licencia antes de usarlo.
3. Reutilizar código mediante adapter/plugin; no crear monolito.
4. No activar duplicados equivalentes sin dedup explícito.
5. Exigir test real y read-back antes de `VERIFIED_CLOSED`.

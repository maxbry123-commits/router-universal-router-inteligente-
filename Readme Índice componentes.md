# Readme Índice componentes — Router Inteligente Universal

## Estado por arquitectura C01-C23
| ID | Componente | Estado actual |
|---|---|---|
| C01 | API Gateway REST/WS | PENDING |
| C02 | InboundGatekeeper / Alcabala | PENDING |
| C03 | Config inmutable | PENDING — donor pydantic-settings disponible |
| C04 | SecretVault | PENDING |
| C05 | Enchufe Schema Pydantic v2 | INTEGRADO/VERIFICADO |
| C06 | DAGParser | PENDING |
| C07 | Templates T01-T12 | PENDING |
| C08 | DAGOrchestrator | PENDING |
| C09 | Worker Pool | PENDING |
| C10 | Resilience | TRABAJO PREVIO / verificar cierre físico antes de PASS global |
| C11 | Semantic Cache | PENDING |
| C12 | Cost Optimizer | PENDING |
| C13 | CodeSandbox dual | PENDING |
| C14 | Windows Chain 1-100 | DISEÑADO / materialización pendiente |
| C15 | Enchufe Gate | INTEGRADO v1.5 + PATCH v2 |
| C16 | Conectores | PARTIAL — HF/DB/GitLab/MCPApp/VPS/Memoria trabajados |
| C17 | RedUniversal | INTEGRADO/REUSE |
| C18 | Storage protocol/adapters | PENDING |
| C19 | Backup/respaldo | SOURCE_PDF_FOUND / EXTRACTION_PENDING |
| C20 | Auth | PENDING |
| C21 | Audit Ledger hash-chain | PENDING |
| C22 | Monitoring | PENDING |
| C23 | WS/SSE events | PENDING |

## Componentes open source disponibles físicamente
Raíz: `router inteligente universal/Componente open soure router inteligente universal/`.

Inventario observado incluye: Chart.js, Durable-Task-Python, Durable-Workflow-Server, LiteLLM, MCP-Python-SDK, Prefect, PyGithub, RouterArena, SGLang, Sentence-Transformers, Temporal-Python-SDK, TypeScript, agents-deep-research, aiomysql, asyncpg, autogen, chroma, crewAI, cryptography, docker-py, fastapi, gpt-researcher, grafana, guardrails, gunicorn, haystack, httpx, huggingface_hub, langgraph, litellm, llama.cpp, llama_index, n8n, ollama, phoenix, postgres, prometheus, pydantic-ai, pydantic-settings, pydantic, qdrant, redis/redis-py, starlette, uvicorn, vLLM-Router, vLLM-Semantic-Router, vllm y otros donors del árbol.

## Regla de integración
`DISPONIBLE != INTEGRADO`.

Cada donor debe clasificarse `REUSE | PATCH | ADAPT | GENERATE`, cablearse detrás de Enchufe Universal y tener evidencia real.

## Mapa funcional
- API: FastAPI/Starlette/Uvicorn/HTTPX.
- Contratos: Pydantic/pydantic-settings.
- MCP: MCP Python SDK.
- GitHub: PyGithub.
- Hugging Face: huggingface_hub.
- Routing LLM: LiteLLM/vLLM Router/vLLM Semantic Router/SGLang.
- Workflows: Prefect/Temporal/Durable-* solo como donors/adapters, nunca como segundo core.
- Storage: Postgres/Redis/Qdrant/Chroma detrás de storage protocol.
- Sandbox: docker-py + subprocess fallback.
- Seguridad: cryptography/guardrails.
- Observabilidad: Prometheus/Grafana/Phoenix.

## Pendiente inmediato
1. Cerrar índice real de modelos HF + adapters/FastAPI.
2. Continuar C01-C23 en orden del DAG y podar duplicación.
3. Test E2E + API keys agentes.

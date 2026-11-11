# Mapa de organización (de dónde → a dónde)
Estado: **Fase 1 hecha** (carpetas, mapa, enlaces). Nada se movió. Cada fila se mueve solo con su fase aprobada, un enlace de compatibilidad y verificación.

| Pieza (hoy) | Destino | Fase | Riesgo | Enlace de compatibilidad |
|---|---|---|---|---|
| `chat-router/chat/` (con `mvp/`), `router-mvp/{mvp,router,fichas,raiz_router,raiz_fichas_prompt}` | se quedan | — | — | — |
| `plugins/puente_chat` | se queda (lo usa fichas_qwen) | — | alto | — |
| `plugins/agentes` | `chat-router/agentes/` | 2 | bajo | no |
| `plugins/chat-router/09-CLAUDE-CODE` | `chat-router/agentes/claude-code/` | 2 | bajo | no |
| `plugins/orquestador`, `plugins/parallel` | `chat-router/agentes/` | 2 | medio | `plugins/<nombre>` → destino |
| `plugins/motores`, `plugins/motores-descarga` | `chat-router/motores/` | 2 | bajo | opcional |
| `plugins/chat-router/{11-EVIDENCIA,12-FABRICA-MOTORES}` | `chat-router/motores/` | 2 | bajo | no |
| `plugins/workflow-loop-yaiwes`, `plugins/hf_skills` | `chat-router/workflow-loop-code-yaiwes/` | 2 | bajo | `plugins/<nombre>` → destino |
| `componentes/skills/workflow-loop-yaiwes` | `chat-router/workflow-loop-code-yaiwes/skills/` | 3 | bajo | no |
| `componentes/chat-bot/{OpenBot-*,web-llm,transformers.js,wllama,pglite,sqlite-wasm}` | `chat-router/chatbot/` | 3 | bajo | no |
| `componentes/chat-bot/{OpenHands,OpenManus,Agent-S,agent-zero,strix,artemis,rea,browser-use,CLI-Anything,…}` | `chat-router/agentes/agentes-listos/` | 3 | medio | `componentes/chat-bot` (lo cita puente_chat) |
| `componentes/{n8n,Prefect,Temporal-*,Durable-*,ruflo,rowboat,autogen,crewAI,langgraph,pydantic-ai,microsoft-agent-framework,haystack,agents-deep-research,open_deep_research,dzhng-deep-research,gpt-researcher}` | `chat-router/agentes/` | 3 | bajo | no |
| `componentes/{open-webui,react,vite,tailwindcss,zustand,lucide,Chart.js,TypeScript,plex,ollama,vllm,llama.cpp,SGLang,guardrails,docker-py,grafana}` | `chat-router/chatbot/` | 3 | bajo | no |
| `componentes/{memanto,graphiti,graphify,chroma,qdrant*,Sentence-Transformers,llama_index,redis*,postgres,asyncpg,aiomysql,prometheus,PyGithub,phoenix}` | `Memoria/` | 3 | bajo | no |
| `plugins/chat-router/{10-CHAT-FUNCIONES,13-CHAT-UI-SUITE,chat_space,space,frontend-yaiwes}` | `chat-router/chatbot/` | 4 | bajo | opcional (2 Dockerfile) |
| `plugins/memoria`, `plugins/hf_datasets` | `Memoria/` | 5 | medio | `plugins/<nombre>` → destino |
| `plugins/{chat,chat-router/espejos}`, `Prueba/` | `chat-router/otros/` | 5 | bajo | no |
| `componentes/OmniRoute` (vacío) | eliminar | 3 | ninguno | — |
| LiteLLM, pydantic-settings, vLLM-Router, vLLM-Semantic-Router, RouterArena, gunicorn, python-dotenv | descartados | 3 | ninguno | — |

Fase 6 (backend, requiere autorización expresa): herramientas de memoria y de motores en MCP, permisos y Harness; buzón del proceso.

## Punto de entrada único y registro maestro de cableado (D-112)

| Artefacto | Ruta | Qué es |
|---|---|---|
| **Índice de navegación del código** | [`CODE_INDEX.md`](../CODE_INDEX.md) | Las 11 entradas del sistema con enlaces relativos a la **ubicación real** (no copia ni mueve nada) |
| **Registro maestro de cableado e integraciones (CIWR)** | [`SYSTEM_WIRING_REGISTRY.yaml`](../SYSTEM_WIRING_REGISTRY.yaml) | Centro de distribución: componentes, servicios, conexiones, contratos, healthchecks, fallback, estados y el **umbral de 7 condiciones** para `ACTIVE` |
| Handoffs por área | [`handoff/docs/`](../handoff/docs/) | FRONTEND · AGENTS · MODELS · MEMORY · HARNESS (el maestro no los copia: los referencia) |
| Bitácora central de cableado | [`connections/wiring_changelog.md`](../connections/wiring_changelog.md) + [`connections/wiring_history.jsonl`](../connections/wiring_history.jsonl) | Historia de movimientos del cableado (verificada contra el Dataset) |
| Topología y verificaciones | [`connections/topology.yaml`](../connections/topology.yaml) · [`connections/endpoints.yaml`](../connections/endpoints.yaml) · [`connections/healthchecks.yaml`](../connections/healthchecks.yaml) | Topología, endpoints y cómo se comprueba cada conexión |

Reglas: una conexión no pasa a `ACTIVE` sin las 7 condiciones (autenticación válida, conexión real,
inferencia ejecutada, respuesta válida, latencia registrada, sin errores críticos y nada superficial).
Motor `research_prepass.py`: **no autorizado, intacto**. Claves: **intactas, no se tocan**.

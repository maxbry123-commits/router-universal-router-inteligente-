# Mapa de organización (de dónde → a dónde)
Estado: **Fase 1 hecha** (carpetas, mapa, enlaces). Nada se movió. Cada fila se mueve solo con su fase aprobada, un enlace de compatibilidad y verificación.

| Pieza (hoy) | Destino | Fase | Riesgo | Enlace de compatibilidad |
|---|---|---|---|---|
| `mvp/`, `chat/`, `router/`, `fichas/`, `raiz_router/`, `raiz_fichas_prompt/` | se quedan | — | — | — |
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
| `componentes/{memanto,graphiti,graphify,chroma,qdrant*,Sentence-Transformers,llama_index,redis*,postgres,asyncpg,aiomysql,prometheus,PyGithub,phoenix}` | `chat-router/memoria/` | 3 | bajo | no |
| `plugins/chat-router/{10-CHAT-FUNCIONES,13-CHAT-UI-SUITE,chat_space,space,frontend-yaiwes}` | `chat-router/chatbot/` | 4 | bajo | opcional (2 Dockerfile) |
| `plugins/memoria`, `plugins/hf_datasets` | `chat-router/memoria/` | 5 | medio | `plugins/<nombre>` → destino |
| `plugins/{chat,chat-router/espejos}`, `Prueba/` | `chat-router/otros/` | 5 | bajo | no |
| `componentes/OmniRoute` (vacío) | eliminar | 3 | ninguno | — |
| LiteLLM, pydantic-settings, vLLM-Router, vLLM-Semantic-Router, RouterArena, gunicorn, python-dotenv | descartados | 3 | ninguno | — |

Fase 6 (backend, requiere autorización expresa): herramientas de memoria y de motores en MCP, permisos y Harness; buzón del proceso.

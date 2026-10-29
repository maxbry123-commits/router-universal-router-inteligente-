# Chat — dos raíces

| Raíz | Carpeta | Qué contiene |
|---|---|---|
| **Frontend** | `chat-router/chat/frontend/` | Módulos ES que sirve Vercel (Root Directory `chat-router/chat/frontend`) |
| **Backend** | `chat-router/chat/backend/` | `mvp/` (Router FastAPI), `deepseek_harness/` (Harness), `router_api_cliente.py` |

Apoyo: `chat-router/chat/e2e/` (pruebas en navegador), `chat-router/chat/auditoria/` (cableado, índices, cambios), `chat-router/chat/docs/frontend/` y `chat-router/chat/docs/backend/` (HANDOFF, INDICE, CAMBIOS).

**Compatibilidad:** el Space arranca `python -m mvp.run` y otros plugins importan `plugins.deepseek_harness` y `plugins.router_api_cliente`. Por eso hay tres enlaces simbólicos: `router-mvp/mvp -> ../chat-router/chat/backend/mvp`, `chat-router/plugins/deepseek_harness -> ../chat/backend/deepseek_harness` y `chat-router/plugins/router_api_cliente.py -> ../chat/backend/router_api_cliente.py`. El código vive solo en `chat-router/chat/backend/`.

Entorno de pruebas: `export PYTHONPATH=<repo>/router-mvp:<repo>/chat-router`.
Revisión: `python3 chat-router/chat/auditoria/cableado.py` · batería: `bash chat-router/chat/e2e/todo.sh` · tests: `python -m pytest router-mvp/mvp -q`.

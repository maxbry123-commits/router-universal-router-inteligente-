# Chat — dos raíces

| Raíz | Carpeta | Qué contiene |
|---|---|---|
| **Frontend** | `chat/frontend/` | Módulos ES que sirve Vercel (Root Directory `chat/frontend`) |
| **Backend** | `chat/backend/` | `mvp/` (Router FastAPI), `deepseek_harness/` (Harness), `router_api_cliente.py` |

Apoyo: `chat/e2e/` (pruebas en navegador), `chat/auditoria/` (cableado, índices, cambios), `chat/docs/frontend/` y `chat/docs/backend/` (HANDOFF, INDICE, CAMBIOS).

**Compatibilidad:** el Space arranca `python -m mvp.run` desde la raíz del clon y otros plugins importan `plugins.deepseek_harness` y `plugins.router_api_cliente`. Por eso en la raíz hay tres enlaces simbólicos: `mvp -> chat/backend/mvp`, `plugins/deepseek_harness -> ../chat/backend/deepseek_harness`, `plugins/router_api_cliente.py -> ../chat/backend/router_api_cliente.py`. El código vive solo en `chat/backend/`.

Revisión: `python3 chat/auditoria/cableado.py` · batería: `bash chat/e2e/todo.sh` · tests: `python -m pytest mvp -q`.

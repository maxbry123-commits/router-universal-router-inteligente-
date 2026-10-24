# Harness DeepSeek, chat backend y frontend

- **Harness** (`server.py`): bucle de herramientas de hasta 8 pasos. Recibe el chat del Router por HTTP, llama al modelo y ejecuta las herramientas del catálogo MCP del Router (`github_*`, `almacen`, `pendientes`, `sala`, `agente`, `llm`, `yaiwes_md`, `mcp__*`). No importa nada de `mvp/`. En HF corre montado en el mismo Space en `/plugins/deepseek_harness`.
- **Chat backend** (`mvp/app.py`): `/chat/send` arma los mensajes (capas del prompt, anclados, contexto) y llama al Harness; `/plugins/puente_chat/call/<accion>` sirve las acciones del panel.
- **Frontend** (`plugins/chat-router/frontend/`): módulos ES servidos por Vercel (`riu-jev-bridge`, Root Directory `plugins/chat-router/frontend`). Solo muestra y pide; ver `docs/CHAT_CONTROLES.md`.
- **Botones del chat:** IA, Agentes, System prompt (ON/OFF en el servidor), herramientas (clic derecho o mantener), Conexiones, ROOM, Pendientes, Servidor.
- **Flujo:** navegador ➡️ Vercel (`/api/...` reescribe al Router) ➡️ Router ➡️ Harness ➡️ modelo ➡️ herramientas por MCP ➡️ Router.

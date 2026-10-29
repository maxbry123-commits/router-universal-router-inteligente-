# Chatbot (tipo GrokBot)
Solo componentes para crear una UI web y local con modelos pequeños embebidos y almacenamiento local. **Sin agentes.**
Destino: `componentes/chat-bot/{OpenBot-ashhart, OpenBot-nightly-labs, web-llm, transformers.js, wllama, pglite, sqlite-wasm}` (ya descargados con el motor 2), `open-webui`,
interfaz web (react, vite, tailwindcss, zustand, lucide, Chart.js, TypeScript, plex), modelos locales (ollama, vllm, llama.cpp, SGLang), Guardrails, docker-py, Grafana.
Arquitectura pendiente de análisis: `componentes/chat-bot/ARQUITECTURA-CHATBOT.md`.

## Movido desde `plugins/chat-router/` (mismo nombre, sin enlaces de vuelta)
`10-CHAT-FUNCIONES` · `13-CHAT-UI-SUITE` · `chat_space` · `space` · `frontend-yaiwes`.
Siguen en `plugins/chat-router/` (otros agentes): `09-CLAUDE-CODE`, `11-EVIDENCIA`, `12-FABRICA-MOTORES`, `espejos`. `frontend` ya vive en `chat/frontend`.
Los Dockerfile de `chat_space/` y `space/` usan solo rutas relativas a su propia carpeta (no cambian). `chat_space` hace `COPY riu`, carpeta que ya no existía antes del movimiento.

- Arquitectura (README + input literal de Antonio): `arquitectura/`.

# Raíz CHAT ROUTER — mapa de la organización

El **Router** (`router/`, `fichas/`, `raiz_router/`, `raiz_fichas_prompt/`, `router-componentes/`, `componentes/`) vive en `../router-mvp/`, **fuera** de esta carpeta. `router-mvp/mvp` es un enlace a `../chat-router/chat/backend/mvp` (el código real está aquí).
Esta carpeta (`chat-router/`) agrupa todo lo demás del chat.

```
chat-router/
├── chat/                                          ✅ cableado: frontend + backend (mvp, harness, cliente)
├── harness/    → chat/backend/deepseek_harness    ✅ cableado
├── plugins/                                       plugins del Harness/Edificio 2 (enlaces a deepseek_harness y router_api_cliente.py)
├── memoria/                                       sistema de memoria y almacenamiento (lo cableado hoy sigue en chat/backend/mvp)
├── chatbot/                                       solo lo que sirve para crear algo tipo GrokBot
├── agentes/                                       agentes, frameworks, orquestación, Claude Code
├── workflow-loop-code-yaiwes/                     code, contratos y sus skills (ECC, frontend, calidad)
├── motores/                                       descarga, extracción, búsqueda, copiar, mover, fábrica de motores
└── otros/                                         plugin chat de prueba, espejos, pruebas por modelo
```

## Regla de oro: lo cableado NO se mueve
Protegido (funciona y está conectado): `chat-router/chat/` (frontend, backend con `mvp/`, harness, cliente), `router-mvp/` (`mvp` enlace, `router/`, `fichas/`, `raiz_router/`, `raiz_fichas_prompt/`),
el system prompt y sus motores, el MCP, el banco, `puente_chat` (lo usa `fichas_qwen`), y la memoria y almacenamiento ya cableados
(`chat-router/chat/backend/mvp/memoria.py`, `hf_store.py`, `trabajos.py`, `chat-router/plugins/hf_storage`).

Lo demás no está conectado y se organiza por fases (ver `MAPA.md`). Cada fase se verifica con:
`python3 chat-router/chat/auditoria/cableado.py` · `python -m pytest router-mvp/mvp -q` · `bash chat-router/chat/e2e/todo.sh`. Si algo falla, se deshace esa fase y no se sigue.

Los plugins con `ficha.json` deben seguir siendo hijos directos de `plugins/`: el cargador (`router/integration/plugin_host/host.py`) descubre por nombre de carpeta (`RIU_PLUGINS_DIR` debe apuntar a `chat-router/plugins`).
Por eso, al moverlos, se deja un enlace simbólico en `plugins/`, igual que ya se hizo con `mvp`, `deepseek_harness` y `router_api_cliente.py`.

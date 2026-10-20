# Router Universal - Router Inteligente

Repositorio organizado en dos edificios que solo hablan por HTTP.

- `router/`  Edificio 1: el Router (api, gateway, engine, seguridad, banco, mcp, router_updater).
- `fichas/`  Edificio 1: fichas del Router, system-prompt y SDK (`fichas_qwen`, `plugin_fichas`, `sdk`).
- `plugins/` Edificio 2: Harness DeepSeek y sus plugins (chat-router, workflow-loop-yaiwes, agentes, memoria, almacenamiento, motores, puente_chat, etc.).
- `componentes/` Codigo de terceros. No se toca.
- `docs/` Esta documentacion.

Leer en orden: `ARQUITECTURA.md` y luego `HANDOFF.md`.
Pruebas: `router/mcp/test_mcp.py` (22 pruebas), `router/router_updater/tests`, `fichas/fichas_qwen/tests`, `router/tests`.
Reglas fijas: sin GitHub Actions, sin LFS, el computo corre en Hugging Face, los secretos viven solo en el banco de claves del Router.
No hay secretos en este repo.

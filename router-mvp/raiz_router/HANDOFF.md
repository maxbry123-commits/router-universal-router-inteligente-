# Handoff del Router

**Estado:** `main` contiene el MVP completo (170 pruebas pasan en local con modelo simulado). Space HF y Vercel: **NO VERIFICADO** en vivo.

**Cómo probar:** reanudar y reiniciar el Space `COMAND-CENTER-1/riu-router` y ejecutar `docs/PRUEBAS_SOL.dag.json` por MCP (`/mcp?key=<CLAVE>`).

**Variables del Space:** `GITHUB_TOKEN`, `RIU_API_KEY` (clave de acceso; las cuatro variantes iguales) y la que abre el banco.
**Vercel (`riu-jev-bridge`):** `RIU_ROUTER_API_KEY`, `RIU_CHAT_PASSWORD`, `RIU_ROUTER_URL`, `HF_TOKEN_1` (botón Servidor).

**Pendiente de decisión:** claves NVIDIA y Groq en el banco (ventana Conexiones); revocar el HF token pegado en el chat; conectar los motores movidos a `mvp/herramientas/` (`prompt_layouts`, `loop_controller`, `motor_objetivo`…).

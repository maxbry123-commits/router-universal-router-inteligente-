# SWE CODE free · Pruebas reales del puente MCP · 2026-11-02

## Alcance
Rama main, entrada MCP ya conectada a ChatGPT (`chat` y `resultado`), sin infraestructura nueva.
`chat(ficha_qwen="swen-code-free", modelo="<id>", message="...")` no debe pasar al plan de Qwen Token Plan.
IDs aceptados: `web-qwen38max`, `web-claude-sonnet`, `web-qwen37max`, `web-dsv4-flash`, `swecode-consulta`.

## Evidencia LIVE (no simulada)
- **Puente MCP:** PASS. El chat acepta los cinco IDs y entrega `swen_<uuid>`; se consulta con `resultado`.
- **Salud bridge:** PASS. Respuesta exacta: `bridge_ok:true`, `cuentas_configuradas:true`, `cantidad_cuentas:10`. No confirma logins.
- **Qwen web:** FAIL. `@swen/sesiones` devolvió `caido:SESSION_EXPIRED`. `@swen/diag` confirmó `auth_url:true`, `login_visible:true`, `editor_visible:false`, `modelo_selector_visible:false`. Por tanto no hay sesión autenticada operativa.
- **DeepSeek web:** FAIL. Una inferencia real devolvió `SWE_CODE_SESSION_EXPIRED` (y otra durante reinicio `SWE_CODE_ROUTER_SIN_CONEXION`). Un `refresh_session` previo marcó `vivo`, pero no fue suficiente para corroborar una inferencia real; se endureció la detección de login modal.
- **Claude Sonnet:** FAIL. Inferencia real devolvió `SWE_CODE_CLAUDE_AGENTE_NO_INSTALADO`; `@swen/claude` informó `gateway_disponible:false` y `CLAUDE_GATEWAY_NO_DISPONIBLE`.
- **Ask Cónsil:** no puede acreditarse en vivo porque necesita Qwen 3.8 Max como árbitro, con la sesión actualmente expirada.
- **Estado de trabajo tras reinicio:** se guardan procesos en la carpeta de estado existente y se informa `SWEN_PROCESO_REINICIADO_ANTES_DE_TERMINAR` sin fingir finalización.

## Cambios técnicos verificados
1. Nuevo `router-mvp/router/integration/chat_mvp/swen_mcp.py`: cliente asíncrono del Harness y Bridge existentes, whitelist exacta, ID de proceso y checkpoint.
2. `chat-router/chat/backend/mvp/mcp_route.py`: distingue explícitamente `ficha_qwen=swen-code-free` de fichas Qwen y evita el rechazo `modelo no permitido`.
3. `router-mvp/router/integration/chat_mvp/mcp_fichas.py`: adapta la otra puerta MCP con el mismo contrato.
4. `chat-router/SWE CODE/web-bridge/src/sites.js` y `motor.js`: verificación del modelo elegido, control de login SPA y no presentar respuestas anteriores como si fueran nuevas.
5. `chat-router/SWE CODE/web-bridge/src/browser.js`: diagnóstico seguro de indicadores sin revelar DOM, correos, cookies o capturas.
6. `chat-router/SWE CODE/web-bridge/src/server.js`: plazo WEB ampliado a 250 s y endpoint de diagnóstico autenticado.
7. `chat-router/SWE CODE/web-bridge/src/claude_gateway.js`: clasificación de salud Gateway sin secretos.

## Objetivo de archivo 500 líneas
**PENDIENTE: ninguno de los modelos WEB produjo todavía código validado.**
No se creó un archivo atribuido falsamente a Qwen, DeepSeek, Claude o Ask Cónsil.
La solicitud de generar 500 líneas por modelo tampoco pudo completarse desde el conector: la llamada adicional quedó bloqueada por controles de la plataforma.
No se debe publicar una prueba sintética como si fuera una ejecución real.

## Bloqueos para cierre
- Restaurar por vías oficiales una sesión legítima de Qwen y DeepSeek que permita generar respuestas.
- Comprobar configuración, habilitación y acceso del Gateway OpenClaw al agente Sonnet.
- Cuando haya respuestas reales, exigir 500 líneas de Python válidas, comparar salida con modelo efectivo y registrar un commit con evidencia.
- No reiterar cambios en el repositorio durante pruebas largas: el autopull puede reiniciar el servidor e interrumpir los procesos.

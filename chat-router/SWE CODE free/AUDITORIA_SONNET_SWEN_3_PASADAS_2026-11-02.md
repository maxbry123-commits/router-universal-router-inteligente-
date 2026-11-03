# SWE CODE free · Auditoría X-Ray de 3 pasadas (2026-11-02 Colombia)

## Alcance
Sólo SWE CODE free + conexiones existentes con Harness DeepSeek, Gateway OpenClaw,
selector central y archivo de arranque de la misma raíz. Código en GitHub main;
no se modificó manualmente Hugging Face ni se crearon espacios o raíces nuevas.

## Pasada 1 — Arquitectura, modelos y compilación sintáctica
- 28/28 módulos `chat-router/SWE CODE/web-bridge/src/*.js` revisados mediante
  parseo sintáctico (no equivale a test de ejecución).
- Selector **swen-code-free**: Ask Cónsil, Qwen 3.8 Max, Claude Sonnet 5.5 MAX,
  Qwen 3.7 Max y DeepSeek V4 Flash; sólo cuentas web, otros selectores intactos.
- Corregido GAP crítico: `web-claude-sonnet` figuraba en la UI pero faltaba
  en GET `/v1/models` y era rechazado por MODELO_INVALIDO.
- Corregido GAP: el plan de Sonnet MAX y el consejo eran cortados por deadline
  genérico. 320 s Sonnet, 415 s consejo; otros modelos conservan plazos.
- Corregido GAP: `tools:true` del chat no llegaba al catálogo JSON WEB;
  ahora se obtiene `tools/list` real del Router con identidad y timeouts.
  Tool calls siguen pendientes hasta ejecución/recibos del Harness.

## Pasada 2 — Seguridad, contratos, persistencia y continuidad
- 18 operaciones del contrato nativo `swe-selector`, sin duplicados y con
  handler para cada una; el archivo contract.ts previo estaba roto y se reconstruyó.
- Integración Claude *exclusiva*: consejero `openclaw/swen-council`;
  `anthropic/claude-sonnet-5-5`, `thinkingDefault:max`,
  `fallbacks:[]`, perfil mínimo sin tools de ejecución.
- Orden consejo: DeepSeek, **Claude segundo**, Qwen 3.7 y Qwen 3.8; Qwen 3.8
  arbitra la decisión final. Fallo de Claude produce 🚩 visible y no cancela
  las demás opiniones del consejo.
- Rotación de credenciales: ÚNICAMENTE el mecanismo nativo de OpenClaw entre
  perfiles Anthropic **autorizados en ese agente**. No crear cuentas ni suplantar
  verificaciones ni inventar saldo. Perfiles del agente `main` no están
  automáticamente disponibles en `swen-council`; requiere configuración
  autorizada desde el Gateway. La existencia del agente no certifica cuota.
- El arranque conservaba mal la configuración existente: podía borrar providers
  Anthropic y la allowlist. Ahora fusiona, mantiene `main` como agente del
  resto del chat, configura el consejo aislado y activa endpoint HTTP autenticado.
- Se retiró un parche inseguro de pairing que extendía tokens a diez años;
  se mantiene el vencimiento oficial. Los controles de edad requieren gestión
  legítima por su titular, sin automatizar datos falsos o saltarlos.
- Checkpoints: escritura previa a inferencia, último contexto, HASH, tool_calls
  WAIT_TOOLS, no reejecución automática de efectos pendientes.
- El runner Python sólo relanza el **mismo bridge Node** si el 7870 no está
  escuchando después de que el arranque externo tuvo prioridad. Sin nuevo Space.

## Pasada 3 — Pruebas mock y MCP instalado
- 8/8 casos mock JS del consejero/consenso aprobados:
  1. Sonnet visible en el catálogo del Gateway.
  2. Identidad `openclaw/swen-council` + modelo Sonnet estricto.
  3. Pensamiento MAX y sesión estable.
  4. Interpretación de respuesta.
  5. Sin perfiles -> flag `CLAUDE_CUENTAS_AGOTADAS`.
  6. HTTP 503 temporal no se confunde con cuota agotada.
  7. Qwen 3.8 conserva arbitraje.
  8. El consejo sigue cuando Claude falla.
- Suite de regresión publicada en
  `chat-router/SWE CODE/web-bridge/test/claude_gateway.test.mjs`.
  El mock no usa Internet, cuentas ni cargos.
- MCP conectado `riu_router_github`: lecturas reales de GitHub main PASS.
  Test chat #1: pidió `qwen3.8-max` y respondió `RIU_TEST_OK`, pero
  **modelo_respuesta fue `lfm2.5-350m`** tras
  `Bridge URLError [Errno 111] Connection refused`.
  Test chat #2: pidió `qwen3.8-max`, respondió `QWEN_HEALTH_OK`,
  pero **modelo_respuesta volvió a ser `lfm2.5-350m`**.
  Ninguno certifica Qwen web ni Claude.
- Intentos de test directo `web-claude-sonnet` y `swecode-consulta`:
  MCP rechazó los IDs por catálogo restringido de su ficha personal.
  Este MCP conectado **NO ofrece** endpoints de prueba de los cuatro
  selectores de SWE CODE free. Es un límite de la herramienta conectada,
  no un resultado de inferencia de esos modelos.
- Las URLs `/health` y `/web/health` del Space no fueron accesibles para
  la herramienta de navegación. No se verificó despliegue del Gateway.

## Bloqueos reales para cerrar al 100 % (🚩)
1. 🚩 **No hay prueba de inferencia real Sonnet en el Gateway con perfiles
   Anthropic autorizados para `swen-council`**.
2. 🚩 **Bridge real**: se observó Connection refused, y luego el modelo
   solicitado fue reemplazado por LFM local en el plugin de fichas Qwen.
   El watchdog de mismo-bridge ha sido corregido, pero falta confirmar el
   arranque efectivo tras actualización del Space.
3. 🚩 El plugin MCP instalado sólo admite modelos de la ficha de Qwen, no
   permite invocar directamente la UI/backend de SWE CODE free ni sus
   cuatro selectores. No afirmar pruebas reales individuales sin otro
   canal autorizado.
4. 🚩 Plugin nativo `swe-selector`: contrato y handlers se alinearon, pero
   falta compilar/instalar en el Gateway real y verificar su activación.
5. 🚩 Las acciones OpenAI image/deep research requieren opt-in y credenciales
   válidas de API; no se probaron con consumo real ni se fingió que ChatGPT
   suscripción fuese API.

## Reglas de cierre
NO declarar PASS por pruebas mock o por una respuesta de respaldo. Se necesita
`/web/health` atendiendo, GET `/v1/models` mostrando los IDs, sonda de
Gateway `openclaw/swen-council`, petición real Sonnet MAX y decisión Ask
Cónsil con Qwen final, todo con identidades registradas. No insertar secretos
en commits, respuestas, herramientas ni logs.

Referencia de comportamiento nativo: docs.openclaw.ai/concepts/model-failover
y docs.openclaw.ai/gateway/openai-http-api.

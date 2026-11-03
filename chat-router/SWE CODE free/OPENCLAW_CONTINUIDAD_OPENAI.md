# SWE CODE free · Continuidad OpenClaw, Ask Cónsil y OpenAI API

## Alcance y fuente de verdad

Este documento describe el cableado añadido **dentro de la raíz existente**. No crea un servicio nuevo.
El flujo normal es `chat YAIWES / OpenClaw → Harness DeepSeek → SWE CODE web-bridge → cuenta web seleccionada`.
Cuando se necesita ejecutar herramientas, el agente elegido se usa mediante
`agentes/adaptadores/` y sus permisos y aprobaciones. El modelo local **no es un traductor de JSON**.

## Cuentas web y ejecución

El selector SWE CODE free contiene únicamente:
- Ask Cónsil (DeepSeek, Claude Sonnet 5.5 MAX, Qwen 3.7 y Qwen 3.8; árbitro Qwen 3.8 Max);
- Qwen 3.8 Max web;
- Claude Sonnet 5.5 MAX vía OpenClaw;
- Qwen 3.7 Max web;
- DeepSeek V4 Flash web.

Los modelos y agentes de los otros selectores no deben modificarse por esta restricción.
Una respuesta web común se muestra como texto. Si el consumidor proporciona una lista
`tools: [{type:"function",function:{name,parameters,...}}]`, el bridge añade al prompt
un **contrato explícito** de JSON, valida que la respuesta íntegra cumpla ese contrato y
genera `tool_calls` de OpenAI. Una llamada inválida **NO** se ejecuta.
No se interpreta prosa como un comando. No se permite una herramienta ausente del catálogo.

**Distinción:** `tool_calls` devueltas por el chat en modo no agéntico son
**PENDIENTES, NO EJECUTADAS**. Para ejecución agéntica del chat YAIWES se usa
`modo_agentico=ON` + `workflow=individual` + un agente disponible
(comprobado por el Harness). Los pasos con efectos exigen aprobación y recibo.
El bridge nunca publica un PASS sin un recibo válido.

## Reintentos

El browser bridge tiene perfiles persistentes, salud de sesión y cuentas configuradas.
El mecanismo existente intenta restablecer sesiones autorizadas y puede elegir
otra cuenta previamente configurada cuando la sesión expiró realmente.
No debe reintentar cambios con efectos sin consultar su checkpoint ni alternar cuentas
para eludir verificaciones de edad, identidad, CAPTCHAs, suspensiones, límites o 429.
El `SESSION_EXPIRED` no demuestra por sí solo que se completó el prompt anterior;
comparar el checkpoint antes de volver a enviar.

## Handoff y checkpoint sin LLM

En el bridge, `contexto_handoff.js` escribe archivos JSON de manera atómica en la
carpeta **existente** `BRIDGE_STATE_DIR/checkpoints/`:
- identificador de conversación y propietario hash;
- objetivo original y modelo activo;
- últimos ocho turnos, última salida, modo y proyecto;
- `WAIT_TOOLS` con IDs pendientes hasta que llegue el recibo;
- recibos guardados (sin repetir operaciones confirmadas);
- SHA-256 para verificar integridad antes de recuperar;
- estado CONTINUAR antes de comenzar una llamada, estado final al responder.

Mismo `conv_id` con otro modelo: el handoff se antepone automáticamente si el modelo
cambió. Chat nuevo: en el selector SWE CODE free utiliza **ID del chat anterior**
(`contexto_de`) o usa **↺ Usar última sesión**. El nuevo modelo recibe datos del
objetivo y último resultado, no órdenes nuevas. El historial completo de mensajes
continúa bajo el sistema de memoria YAIWES original, no se sustituye.

Endpoints autenticados del bridge:
- `GET /v1/contexto/{id}` — consultar.
- `POST /v1/contexto/transferir` `{"origen":"A","destino":"B"}` — copiar sin pisar.
- `POST /v1/chat/completions` con `contexto_de:"A"` — recuperar/transferir y continuar.

OpenClaw plugin `swe-selector` expone `swen_contexto` y
`swen_contexto_transferir` desde el Gateway, sin otro LLM para leer el JSON.

## Ask Cónsil

Participantes configurados actualmente: DeepSeek V4 Flash, **Claude Sonnet 5.5 (segundo)**, Qwen 3.7 Max y Qwen 3.8 Max.
Árbitro de la decisión: **Qwen 3.8 Max**; su fallo no se disfraza con otro árbitro.
La respuesta incluye `consenso_detalle` (opiniones individuales, decisión, árbitro);
el chat despliega un control para ver cada opinión, adoptar una como criterio humano y
editar alcance/objetivo. Adoptar opinión crea un **borrador**, no ejecuta código.
Claude se conecta al **Gateway OpenClaw existente**, con el agente aislado
`openclaw/swen-council`, selección estricta `anthropic/claude-sonnet-5-5`,
`thinkingDefault:max` y sin fallback a Opus/Haiku/u otro modelo. Se utiliza
el orden/rotación **nativa** de perfiles Anthropic válidamente autorizados
de OpenClaw, sin copiar claves, automatizar verificaciones de identidad o
crear cuentas. Los perfiles son propios del agente y deben estar autorizados
para `swen-council`; la existencia de perfiles del agente `main` no garantiza
que el consejero pueda utilizarlos. Al agotarse todos los perfiles elegibles,
la salida del consejero lleva 🚩 `CLAUDE_SONNET_SIN_CUENTA_DISPONIBLE`.
**Ask Cónsil no se detiene:** conserva la opinión faltante y Qwen 3.8 Max
decide utilizando las demás respuestas confirmadas. Una solicitud exclusiva
a Claude registra la incidencia y permite retomar la tarea posteriormente,
sin atribuirle una respuesta de otro modelo.
`GET /v1/claude/estado` sólo comprueba que el agente figure en el Gateway;
**no certifica inferencia ni saldo**. Se requiere una prueba real y perfiles
Anthropic configurados en el Gateway para marcarlo Disponible.

## OpenAI opcional: servicio distinto de la suscripción ChatGPT

No existe un acceso automático a herramientas pagadas del chat ChatGPT por medio de
cookies, suscripción o scraping. La integración oficial usa la **OpenAI API**
independiente y sólo está disponible con variables en el backend:
`OPENAI_API_KEY` y `RIU_OPENAI_ACCIONES_ON=1`.
Sin ambas, los endpoints responden `OPENAI_API_NO_CONFIGURADA`.
La UI pide confirmación antes de cada solicitud que pueda generar cargos.

- **@ Investigación profunda**:
  `POST /v1/openai/research` con `{"prompt":"..."}` usa Responses API,
  modelo `gpt-5.6-sol`, `web_search`, `background:true` y devuelve un ID.
  `GET /v1/openai/research/{id}` comprueba progreso sin iniciar otra inferencia.
  El estado se guarda en `BRIDGE_STATE_DIR/openai_api/`. La API puede mantener
  los trabajos en segundo plano por tiempo limitado y puede haber costes.
- **📷 Crear imagen**:
  `POST /v1/openai/image` con `{"prompt":"..."}` usa `gpt-image-2.5-flare`;
  la imagen PNG se guarda en `BRIDGE_STATE_DIR/openai_api/`.
  `GET /v1/openai/image/{id}` devuelve PNG para descargar;
  `GET /v1/openai/image/{id}/data` devuelve JSON base64 para visualización.
  Nunca se publican claves en frontend o repositorio.
- Las rutas pasan por el Harness `/modelos/v1/openai/*` para que YAIWES
  use su entrada **existente** `/plugins/deepseek_harness/modelos/v1/openai/*`.

Plugin OpenClaw `swe-selector` tiene operaciones de estado,
crear/consultar investigación, generar imagen y guardar PNG en su workspace.
Para autorizar acciones *desde el modelo agente* se requiere además
`RIU_OPENAI_AGENTE_ON=1` en el **Gateway OpenClaw**, deshabilitado por defecto.
El usuario debe aprobar el uso facturable explícitamente según su configuración.

**Nota de alcance:** sin OPENAI_API_KEY y las banderas correspondientes la UI
muestra el acceso no configurado; no se pueden generar imágenes ni usar
investigación profunda consumiendo la cuota personal de ChatGPT.

## Pruebas de cierre

El código tiene pruebas sintácticas y del parser JSON, pero **no hay certificación
de producción** sin un arranque real del Space/Gateway con sus credenciales y
comprobación de ejecución: consulta WEB → tool_call → ejecución → recibo →
estado DONE. No convertir `WAIT_TOOLS` en DONE por una pantalla bonita.

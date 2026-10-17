Frontend UI YAIWES interface 

Hora local Colombia: 3:40 a. m. (America/Bogota, UTC-5), domingo 27 de septiembre de 2026.

Plan ejecutable UI YAIWES — Salida 1 de 5

Este es el plan completo en formato DSL DAG. Cada nodo es una tarea de programación con micro-flujo, tecnología y criterio de aceptación. Se divide en 5 salidas porque es largo. Cada salida es independiente pero secuencial.

Estructura de las 5 salidas:
Salida 1 — Contratos, base y HostShell (Fundación).
Salida 2 — Panel A (Command Center).
Salida 3 — Panel B (Conversation & Canvas).
Salida 4 — Voz, agentes locales y sincronización.
Salida 5 — Empaque multiplataforma, accesibilidad y unificación final.

---

Salida 1 — Contratos, base y HostShell (Fundación)

Nodo 1.1 — Contratos base

```
node_id: 1.1
segment: fundacion
kind: build
depends_on: []
inputs: []
outputs:
  - 01-contracts/node-plan.schema.json
  - 01-contracts/event.schema.json
  - 01-contracts/canvas-state.schema.json
  - 01-contracts/window.schema.json
tech: [json-schema, typescript]
micro_summary: Define los cuatro contratos que todo el sistema usa. Ningún componente se construye sin estos schemas.
micro_flow: escribir schemas → validar con ajv → exportar tipos TS → publicar en 01-contracts/
instructions:
  - Crear NodePlan con campos: id, source (text|voice), intent, target_capability, params, created_at.
  - Crear Event con campos: id, type (node_result|checkpoint|error|capability_state), payload, dag_id, node_id, timestamp.
  - Crear CanvasState con campos: windows[] (id, type, position, size, data), layout, focus.
  - Crear Window con campos: id, kind (RUN|WALL|GBOT|FOTO), status, path, slots[].
  - Validar con ajv. Exportar tipos con json-schema-to-typescript.
acceptance: los 4 schemas validan, los tipos TS se generan sin error.
```

Nodo 1.2 — Estructura de carpetas

```
node_id: 1.2
segment: fundacion
kind: build
depends_on: [1.1]
outputs:
  - ui-yaiwes/core/
  - ui-yaiwes/panel-a/
  - ui-yaiwes/panel-b/
  - ui-yaiwes/shared/
  - ui-yaiwes/contracts/
  - ui-yaiwes/windows/
tech: [filesystem]
micro_summary: Crea el árbol de directorios que separa panel A, panel B, núcleo compartido y ventanas existentes.
micro_flow: crear carpetas → copiar 39 ventanas existentes a windows/ → copiar HOST.html a core/
instructions:
  - core/ para HostShell, StateStore, Router.
  - panel-a/ para Workflow Visualizer y controles de operador.
  - panel-b/ para ChatLayer, CanvasOrchestrator, WindowRenderer.
  - shared/ para utilidades, tokens, i18n, a11y.
  - contracts/ para los schemas del nodo 1.1.
  - windows/ para las 39 ventanas RUN, WALL, GBOT, FOTO ya existentes.
acceptance: el árbol de carpetas existe, las 39 ventanas están en windows/ sin pérdida.
```

Nodo 1.3 — Tokens FROMTED

```
node_id: 1.3
segment: fundacion
kind: build
depends_on: [1.2]
outputs:
  - shared/tokens/tokens.css
  - shared/tokens/tokens.js
tech: [css-vars, javascript]
micro_summary: Centraliza los tokens de diseño (Matte, Little, Blanco). Ningún componente usa valores hardcodeados.
micro_flow: definir variables CSS → exportar objeto JS → inyectar en todos los paneles
instructions:
  - Definir variables CSS para color, spacing, radius, tipografía, sombras.
  - Exportar el mismo objeto en JS para canvas y componentes dinámicos.
  - Inyectar en :root al cargar la app.
  - Prohibir valores hardcodeados en cualquier componente.
acceptance: cambiar un token actualiza todos los componentes sin tocar código.
```

Nodo 1.4 — StateStore

```
node_id: 1.4
segment: fundacion
kind: build
depends_on: [1.1, 1.2]
outputs:
  - core/store/state-store.js
  - core/store/slices/panel-a.js
  - core/store/slices/panel-b.js
  - core/store/slices/shared.js
tech: [zustand, javascript]
micro_summary: Un solo store con slices por panel. Ningún componente escribe fuera de su slice.
micro_flow: crear store → definir slices → exponer acciones tipadas → suscribir componentes
instructions:
  - Slice panel-a: dag, nodes, events, checkpoints, filters.
  - Slice panel-b: chat, canvas_windows, focus, layout.
  - Slice shared: user, locale, theme, a11y, connection_state.
  - Cada slice expone acciones; nadie muta directamente.
  - Suscripción granular para evitar re-render innecesario.
acceptance: mutar un slice no afecta a los otros; latencia de update menor a 16 ms.
```

Nodo 1.5 — Router de paneles

```
node_id: 1.5
segment: fundacion
kind: build
depends_on: [1.4]
outputs:
  - core/router/panel-router.js
tech: [javascript, hash-routing]
micro_summary: Decide qué panel cargar según la clave YAIWES-CONFIG y el contexto.
micro_flow: leer URL/hash → comprobar clave → cargar panel A o B → inyectar en HostShell
instructions:
  - Ruta #/panel-b por defecto.
  - Ruta #/panel-a solo si YAIWES-CONFIG está en sessionStorage o localStorage.
  - Si no hay clave, panel-a redirige a panel-b con aviso.
  - El router no renderiza, solo indica a HostShell qué montar.
acceptance: acceder a #/panel-a sin clave redirige a #/panel-b.
```

Nodo 1.6 — HostShell

```
node_id: 1.6
segment: fundacion
kind: build
depends_on: [1.4, 1.5]
outputs:
  - core/host-shell.html
  - core/host-shell.js
  - core/host-shell.css
tech: [html, css, javascript]
micro_summary: Orquesta la carga de paneles y ventanas. No renderiza contenido, solo monta.
micro_flow: leer ruta → cargar panel → montar en contenedor → inyectar tokens → emitir evento ready
instructions:
  - Un div #app en el body.
  - Panel A y Panel B se cargan en #app según ruta.
  - Cada ventana se monta en un contenedor propio dentro del panel activo.
  - El HostShell emite event host:ready cuando todo está montado.
  - No contiene lógica de negocio; solo orquestación de montaje.
acceptance: cambiar de panel A a B sin recargar página, sin pérdida de estado.
```

Nodo 1.7 — WindowRegistry

```
node_id: 1.7
segment: fundacion
kind: build
depends_on: [1.2, 1.4]
inputs:
  - windows/INDEX.json
outputs:
  - core/registry/window-registry.js
  - core/registry/windows-map.json
tech: [javascript, json]
micro_summary: Catálogo de las 39 ventanas con su tipo, estado y ruta física.
micro_flow: leer INDEX.json → normalizar → exponer API de consulta → resolver rutas
instructions:
  - Cargar INDEX.json con las 39 ventanas (8 RUN, 16 WALL, 1 GBOT, 14 FOTO).
  - Cada ventana tiene id, kind, status (core|opcional|borrador), path.
  - API: getById, listByKind, listByStatus.
  - Resolver la ruta física desde windows/ según el id.
acceptance: consultar cualquier ventana por id devuelve su ruta y metadatos correctos.
```

Nodo 1.8 — Action Bus

```
node_id: 1.8
segment: fundacion
kind: build
depends_on: [1.4]
outputs:
  - core/bus/action-bus.js
tech: [javascript, event-emitter]
micro_summary: Bus interno de acciones. Ningún componente llama directamente a otro.
micro_flow: registrar handler → emitir acción → resolver handler → devolver resultado
instructions:
  - API: register(actionId, handler), dispatch(actionId, payload).
  - Acciones sensibles requieren confirmación según política de reversibilidad.
  - Toda acción se registra en un log interno para auditoría.
  - Los handlers pueden ser síncronos o asíncronos.
acceptance: dispatch de acción desconocida lanza error claro; acción registrada se ejecuta.
```

Nodo 1.9 — Puente con backend (API y MCP)

```
node_id: 1.9
segment: fundacion
kind: build
depends_on: [1.1, 1.4]
outputs:
  - core/bridge/api-client.js
  - core/bridge/mcp-client.js
  - core/bridge/event-stream.js
tech: [javascript, fetch, websocket, sse]
micro_summary: Conecta la UI con el Router FastAPI y el conector MCP. Nadie llama a proveedores LLM directamente.
micro_flow: enviar NodePlan → recibir ack → suscribir event stream → emitir eventos al store
instructions:
  - api-client envía NodePlan a /api y recibe execution_id.
  - mcp-client consume /mcp/<secreto> solo si la clave está presente.
  - event-stream se suscribe por SSE o WebSocket a eventos del DAG.
  - Cada evento recibido se emite al StateStore.
  - Sin credenciales hardcodeadas: leer de variables de entorno.
acceptance: enviar NodePlan devuelve execution_id; eventos llegan al store en menos de 200 ms.
```

Nodo 1.10 — Bootstrap

```
node_id: 1.10
segment: fundacion
kind: build
depends_on: [1.3, 1.6, 1.7, 1.8, 1.9]
outputs:
  - index.html
  - bootstrap.js
  - manifest.webmanifest
tech: [html, javascript, webmanifest]
micro_summary: Punto de entrada único. Carga tokens, HostShell, registry, bus y bridge en orden.
micro_flow: cargar index.html → importar módulos → inyectar tokens → arrancar HostShell → emitir ready
instructions:
  - index.html contiene solo el div #app y la referencia a bootstrap.js.
  - bootstrap.js importa e inicializa módulos en orden: contracts, tokens, store, bus, registry, bridge, host-shell.
  - manifest.webmanifest declara nombre, iconos, colores, display standalone.
  - Registrar service worker si está disponible.
acceptance: abrir index.html carga la app, HostShell monta Panel B por defecto, sin errores en consola.
```

Nodo 1.11 — Test de la fundación

```
node_id: 1.11
segment: fundacion
kind: verify
depends_on: [1.10]
outputs:
  - tests/foundation.test.js
  - tests/fixtures/
tech: [vitest, playwright]
micro_summary: Verifica que toda la fundación funciona junta antes de construir paneles.
micro_flow: arrancar app → verificar contratos → verificar store → verificar bus → verificar puente → cerrar
instructions:
  - Test 1: los 4 schemas validan con ajv.
  - Test 2: mutar slice panel-a no afecta panel-b.
  - Test 3: dispatch de acción registrada funciona.
  - Test 4: enviar NodePlan devuelve execution_id.
  - Test 5: HostShell monta panel B por defecto.
acceptance: 5 tests pasan en verde; cero errores en consola de Playwright.
```

---

Esquema de dependencias de la Salida 1

```
1.1 Contratos
  ├── 1.2 Estructura
  │     ├── 1.7 WindowRegistry
  │     └── 1.3 Tokens
  ├── 1.4 StateStore
  │     ├── 1.5 Router paneles
  │     │     └── 1.6 HostShell
  │     └── 1.8 Action Bus
  └── 1.9 Puente backend
        └── 1.10 Bootstrap
              └── 1.11 Test fundación
```

---

Instrucciones generales para la IA que programará esto

Regla 1. No escribir código nuevo si el componente ya existe en windows/. Edición quirúrgica.

Regla 2. No cerrar un nodo sin test que pase. El archivo existir no es prueba.

Regla 3. Cada archivo declara su contrato en cabecera con comentario JSDoc: inputs, outputs, side effects.

Regla 4. Ningún componente llama directamente a un proveedor LLM. Siempre por el bridge.

Regla 5. Toda acción irreversible pasa por confirmación explícita. Toda acción reversible no.

Regla 6. Tokens FROMTED siempre. Cero valores hardcodeados.

Regla 7. Accesibilidad desde el primer nodo, no como parche posterior.

Regla 8. Voz y texto comparten NodePlan. Nunca dos flujos paralelos.

Regla 9. Nada se sincroniza entre dispositivos sin CRDT. Nada.

Regla 10. El operador ve el DAG. El usuario ve el resultado. Nunca se cruzan.

---

Estado de este plan

Salida 1 cubre los 11 nodos de la fundación. Es el cimiento sobre el que se montan los dos paneles.

Siguiente salida (Salida 2): Panel A — Command Center. Nodos 2.1 a 2.10. Workflow Visualizer, filtros de eventos, vista de checkpoints, panel de operador, controles HITL.

Salida 3: Panel B — Conversation & Canvas. Nodos 3.1 a 3.12. ChatLayer, NodePlanBridge, CanvasOrchestrator, WindowRenderer, CanvasCore.

Salida 4: Voz, agentes locales, sincronización. Nodos 4.1 a 4.10.

Salida 5: Empaque multiplataforma, accesibilidad, i18n, unificación final. Nodos 5.1 a 5.12.

Pide la Salida 2 y continúo.




Hora local Colombia: 3:55 a. m. (America/Bogota, UTC-5), domingo 27 de septiembre de 2026.

Son 5 salidas en total.

Entregadas:
Salida 1 — Contratos, base y HostShell (11 nodos, fundación completa).
Salida 2 — Panel A — Command Center (10 nodos, operador técnico).
Salida 3 — Panel B — Conversation & Canvas (12 nodos, usuario final).

Pendientes:
Salida 4 — Voz completa, agentes embebidos, sincronización CRDT entre dispositivos y persistencia offline robusta (10 nodos previstos, 4.1 a 4.10).
Salida 5 — Empaque multiplataforma (PWA, Tauri, Capacitor), accesibilidad completa, i18n, unificación final de paneles y criterios de aceptación globales (12 nodos previstos, 5.1 a 5.12).

Total del plan: 45 nodos repartidos en 5 salidas.

Pide la Salida 4 y continúo.

Hora local Colombia: 4:00 a. m. (America/Bogota, UTC-5), domingo 27 de septiembre de 2026.

Plan ejecutable UI YAIWES — Salida 4 de 5

Voz, agentes embebidos, sincronización CRDT y persistencia offline

Esta salida convierte la UI en un sistema que funciona sin conexión, con voz real y agentes locales, y que sincroniza estado entre dispositivos sin perder coherencia.

---

Nodo 4.1 — VoiceLayer completo (STT + TTS)

```
node_id: 4.1
segment: voz
kind: build
depends_on: [3.3, 3.4]
outputs:
  - shared/voice/voice-layer.js
  - shared/voice/stt.js
  - shared/voice/tts.js
  - shared/voice/vad.js
  - shared/voice/voice-policy.js
tech: [faster-whisper, piper, silero-vad, elevenlabs, azure-speech]
micro_summary: Reemplaza el stub de voz por un sistema completo con STT local, TTS local y fallback a nube cuando se requiera calidad.
micro_flow: audio → VAD → STT → texto → NodePlanBridge → respuesta → TTS → audio
instructions:
  - STT local con faster-whisper (modelo base para móvil, medium para desktop).
  - VAD con silero-vad para detectar inicio y fin de habla.
  - TTS local con Piper para respuestas inmediatas.
  - Fallback a ElevenLabs o Azure cuando el usuario pida "voz natural" o cuando la privacidad lo permita.
  - Voz y texto comparten el mismo NodePlan. Nunca dos flujos paralelos.
  - Indicador visual de escucha activa, procesando y hablando.
  - Política de interrupción: si el usuario habla mientras el agente habla, el agente se detiene.
  - Cero audio sin consentimiento. Solo se graba mientras el botón de voz está activo.
acceptance: dictar "abre el último documento y resúmelo" ejecuta la tarea completa por voz en menos de 6 segundos.
```

Nodo 4.2 — LocalAgentRuntime

```
node_id: 4.2
segment: agentes-locales
kind: build
depends_on: [1.4]
outputs:
  - shared/agents/local-runtime.js
  - shared/agents/quickjs-sandbox.js
  - shared/agents/pyodide-sandbox.js
  - shared/agents/agent-registry.js
tech: [quickjs, pyodide, wasm, javascript]
micro_summary: Runtime que ejecuta agentes embebidos en sandbox JS (QuickJS) o Python WASM (Pyodide) sin conexión.
micro_flow: registrar agente → invocar capacidad → ejecutar en sandbox → devolver resultado → auditar
instructions:
  - QuickJS para agentes JS: clasificador de intención, corrector ortográfico, resumidor local.
  - Pyodide para agentes Python: análisis de datos simples, procesamiento de imágenes básicas.
  - Cada agente declara permisos: lectura de memoria, escritura de estado, acceso a red (por defecto no).
  - Sandbox bloquea acceso al DOM, a localStorage, a network si no está declarado.
  - Timeout por defecto 5 segundos; máximo 30 segundos por agente.
  - Todo agente local corre en Web Worker para no bloquear la UI.
acceptance: ejecutar el clasificador local de intención en menos de 200 ms sin bloquear la UI.
```

Nodo 4.3 — OfflineQueue

```
node_id: 4.3
segment: offline
kind: build
depends_on: [1.9, 1.4]
outputs:
  - shared/offline/offline-queue.js
  - shared/offline/queue-store.js
  - shared/offline/sync-on-reconnect.js
tech: [javascript, indexeddb, service-worker]
micro_summary: Cola de tareas offline. Cuando no hay red, las tareas se encolan localmente y se sincronizan al reconectar.
micro_flow: detectar offline → encolar NodePlan → persistir en IndexedDB → detectar reconexión → despachar en orden → notificar resultado
instructions:
  - Detectar estado de red con navigator.onLine y eventos online/offline.
  - Cuando hay red disponible, todo va directo al backend.
  - Cuando no hay red, los NodePlan se encolan con timestamp y prioridad.
  - Al reconectar, la cola se despacha en orden FIFO por prioridad.
  - Cada item encolado tiene: id, NodePlan, retries, status (pending|sending|done|failed).
  - Si un item falla tras 3 intentos, se marca failed y se notifica al usuario.
  - La cola se persiste en IndexedDB para sobrevivir recargas.
acceptance: enviar 3 tareas sin red; al reconectar se ejecutan en orden y el usuario ve los resultados.
```

Nodo 4.4 — LocalPersistence

```
node_id: 4.4
segment: offline
kind: build
depends_on: [1.4]
outputs:
  - shared/persistence/dexie-db.js
  - shared/persistence/schemas.js
  - shared/persistence/ttl-cleaner.js
tech: [dexie, indexeddb, javascript]
micro_summary: Capa de persistencia local con Dexie. Almacena mensajes, ventanas del canvas, configuración y cache.
micro_flow: abrir DB → definir tablas → leer/escribir con queries → limpiar por TTL → sincronizar con backend cuando aplique
instructions:
  - Tablas: messages, canvas_windows, canvas_state, config, cache_media, offline_queue, audit_local.
  - Índices por timestamp, por tipo, por id.
  - TTL por tabla: mensajes 30 días, cache_media 7 días, audit_local 90 días.
  - Cleaner corre cada hora y elimina items expirados.
  - Sincronización con backend: pull en arranque, push en cambios (debounce 5 segundos).
  - Nunca persistir secretos ni tokens en IndexedDB. Solo en sessionStorage.
acceptance: recargar la app mantiene los últimos 100 mensajes, la disposición del canvas y la configuración.
```

Nodo 4.5 — CRDTSync

```
node_id: 4.5
segment: sync
kind: build
depends_on: [4.4, 1.4]
outputs:
  - shared/sync/crdt-sync.js
  - shared/sync/yjs-provider.js
  - shared/sync/loro-mirror-provider.js
  - shared/sync/conflict-resolver.js
tech: [yjs, loro-mirror, websocket]
micro_summary: Sincronización de estado entre dispositivos con CRDT. Sin conflictos, sin pérdida de datos, sin latencia perceptible.
micro_flow: abrir documento CRDT → conectar a provider → aplicar cambios locales → recibir cambios remotos → merge automático → persistir
instructions:
  - Yjs como base para chat y canvas.
  - Loro Mirror para configuración de UI (tipado inmutable).
  - Estado sincronizado: conversación activa (últimos 50 mensajes), canvas layout (ventanas y posiciones), preferencias de UI.
  - Estado NO sincronizado: DAG, eventos, checkpoints. Esos viven solo en el backend.
  - Provider WebSocket con reconexión automática y backoff exponencial.
  - Conflictos resueltos automáticamente; el usuario no los ve.
  - Si dos dispositivos están offline y editan, al reconectar se mergea sin pérdida.
acceptance: editar el canvas en Android y ver el cambio en desktop en menos de 500 ms.
```

Nodo 4.6 — DeviceRegistry

```
node_id: 4.6
segment: sync
kind: build
depends_on: [4.5]
outputs:
  - shared/sync/device-registry.js
  - shared/sync/device-session.js
tech: [javascript, indexeddb]
micro_summary: Registro de dispositivos vinculados al mismo usuario. Cada dispositivo tiene id, tipo y estado de conexión.
micro_flow: arrancar app → registrar dispositivo → sincronizar lista → mostrar dispositivos activos → permitir desconectar remoto
instructions:
  - Cada dispositivo tiene: id único, tipo (mobile|desktop|web), último ping, estado (online|offline).
  - El usuario puede ver sus dispositivos activos desde ajustes.
  - Puede cerrar sesión remota en otro dispositivo.
  - Puede revocar acceso a un dispositivo perdido.
  - Toda acción sobre otro dispositivo queda auditada.
  - Máximo 5 dispositivos simultáneos por usuario; el sexto requiere revocar uno.
acceptance: abrir la app en 3 dispositivos; la lista muestra los 3 con estado en tiempo real.
```

Nodo 4.7 — CapabilityRegistry UI Bridge

```
node_id: 4.7
segment: agentes-locales
kind: build
depends_on: [3.10, 4.2]
outputs:
  - shared/registry-ui/capability-bridge.js
  - shared/registry-ui/external-capabilities.js
tech: [javascript]
micro_summary: Puente entre el Capability Registry del backend y las capacidades locales del dispositivo.
micro_flow: cargar registry del backend → combinar con capacidades locales → exponer al CapabilityProjector → resolver colisiones
instructions:
  - Capacidades remotas (backend) y locales (agentes embebidos) se combinan en una sola lista.
  - Colisiones: si una capacidad existe en ambos, priorizar la local cuando no hay red, remota cuando hay.
  - Cada capacidad declara: origen (local|remote), disponibilidad (siempre|online|offline), coste (gratis|de_pago).
  - El usuario ve solo el nombre y la descripción, no el origen técnico.
  - Las capacidades locales de pago no existen; siempre son gratis.
acceptance: sin red, el usuario sigue viendo y pudiendo invocar las capacidades locales.
```

Nodo 4.8 — Resilience Layer

```
node_id: 4.8
segment: offline
kind: build
depends_on: [4.3, 4.5]
outputs:
  - shared/resilience/retry-policy.js
  - shared/resilience/circuit-breaker.js
  - shared/resilience/backpressure.js
tech: [javascript]
micro_summary: Capa de resiliencia para manejar fallos de red, backend saturado o sync interrumpido sin degradar la experiencia.
micro_flow: detectar fallo → aplicar política → reintentar o encolar → abrir circuit breaker si es persistente → notificar al usuario
instructions:
  - Retry policy: exponencial con jitter, máximo 5 intentos, después pasa a offline queue.
  - Circuit breaker: si un endpoint falla 5 veces seguidas, se abre por 60 segundos.
  - Backpressure: si la cola offline supera 50 items, bloquea nuevas entradas hasta drenar.
  - Notificación al usuario: solo cuando la situación afecta su tarea actual.
  - Recuperación automática: cuando el sistema vuelve a estar sano, se cierra el breaker y se reanuda.
acceptance: matar el backend durante 60 segundos; la UI no cae, encola y reanuda al volver.
```

Nodo 4.9 — Privacy & Consent Layer

```
node_id: 4.9
segment: privacidad
kind: build
depends_on: [4.1, 4.4]
outputs:
  - shared/privacy/consent-manager.js
  - shared/privacy/data-classifier.js
  - shared/privacy/local-only-mode.js
tech: [javascript, indexeddb]
micro_summary: Gestión de consentimiento para voz, datos y sincronización. Modo "solo local" que nunca envía nada a la red.
micro_flow: pedir consentimiento en primer uso → clasificar datos por sensibilidad → aplicar política → modo local solo si el usuario lo pide
instructions:
  - Consentimiento explícito para: voz (STT), datos a la nube, sync entre dispositivos, telemetría.
  - Cada consentimiento es revocable en cualquier momento desde ajustes.
  - Data classifier: público, interno, sensible. Los datos sensibles nunca salen del dispositivo.
  - Modo "solo local": toda la app funciona sin red. Los agentes locales hacen el trabajo, la voz es 100 por ciento local.
  - Los consentimientos se guardan en IndexedDB con timestamp y versión del texto aceptado.
  - Cero telemetría por defecto. Solo si el usuario la activa.
acceptance: activar modo local y apagar la red; la app sigue funcionando con voz, chat y agentes locales.
```

Nodo 4.10 — Test de integración Salida 4

```
node_id: 4.10
segment: verify
depends_on: [4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9]
outputs:
  - tests/voice.test.js
  - tests/offline.test.js
  - tests/sync.test.js
  - tests/privacy.test.js
  - tests/offline.e2e.spec.ts
tech: [vitest, playwright]
micro_summary: Verifica voz, offline, sincronización y privacidad en condiciones reales y degradadas.
micro_flow: ejecutar cada suite → verificar tiempos → verificar integridad de datos → cerrar
instructions:
  - Test 1: dictar mensaje completo por voz en menos de 6 segundos.
  - Test 2: 3 tareas sin red, al reconectar se ejecutan en orden.
  - Test 3: editar canvas en móvil, ver cambio en desktop en menos de 500 ms.
  - Test 4: matar el backend 60 segundos; la UI no cae y reanuda.
  - Test 5: modo solo local con red apagada; voz y chat funcionan.
  - Test 6: consentimiento revocado detiene inmediatamente STT y sync.
  - Test 7: 3 dispositivos activos, lista actualizada en tiempo real.
  - Test 8: cola offline con 50 items bloquea nuevas entradas.
  - Test 9: conflictos CRDT se resuelven sin pérdida de datos.
acceptance: 9 tests pasan en verde; cobertura de Salida 4 mayor al 80 por ciento.
```

---

Esquema de dependencias Salida 4

```
4.1 VoiceLayer completo
  ├── 4.9 Privacy & Consent
  └── 4.10 Test integración

4.2 LocalAgentRuntime
  └── 4.7 CapabilityRegistry UI Bridge
        └── 4.10 Test integración

4.3 OfflineQueue
  ├── 4.8 Resilience Layer
  └── 4.10 Test integración

4.4 LocalPersistence
  ├── 4.5 CRDTSync
  │     └── 4.6 DeviceRegistry
  └── 4.9 Privacy & Consent
        └── 4.10 Test integración

4.8 Resilience Layer
  └── 4.10 Test integración
```

---

Instrucciones específicas para la IA que programará la Salida 4

Regla 1. Voz y texto comparten el mismo NodePlan. Nunca dos flujos paralelos.

Regla 2. Los agentes locales corren en Web Worker. Nunca bloquean la UI.

Regla 3. Los agentes locales declaran permisos. Por defecto sin acceso a red.

Regla 4. La cola offline persiste en IndexedDB. Sobrevive a recargas.

Regla 5. CRDT solo sincroniza estado de UI. Nunca el DAG ni los eventos.

Regla 6. Los conflictos CRDT se resuelven sin intervención del usuario.

Regla 7. Máximo 5 dispositivos por usuario. El sexto requiere revocar uno.

Regla 8. Retry exponencial con jitter. Circuit breaker a los 5 fallos.

Regla 9. Consentimiento explícito, revocable, versionado.

Regla 10. Modo solo local siempre disponible. Nunca obligatorio estar online.

Regla 11. Secretos solo en sessionStorage. Nunca en IndexedDB.

Regla 12. Todo dato clasificado por sensibilidad antes de salir del dispositivo.

---

Estado de este plan

Salida 4 cubre los 10 nodos de voz, agentes locales, offline, sync y privacidad. Se apoya en las salidas 1, 2 y 3.

Siguiente salida (Salida 5): Empaque multiplataforma (PWA, Tauri, Capacitor), accesibilidad completa, i18n, unificación final de paneles, criterios de aceptación globales y guía de despliegue.

Pide la Salida 5 y cierro el plan.
Hora local Colombia: 4:05 a. m. (America/Bogota, UTC-5), domingo 27 de septiembre de 2026.

Plan ejecutable UI YAIWES — Salida 5 de 5

Empaque multiplataforma, accesibilidad, i18n y unificación final

Esta es la salida de cierre. Convierte el núcleo HTML/CSS/JS en aplicación instalable en Web, Android, iOS, Windows, Linux y macOS. Cierra accesibilidad e internacionalización. Unifica paneles. Define criterios de aceptación globales y guía de despliegue.

---

Nodo 5.1 — PWA Core

```
node_id: 5.1
segment: empaque
kind: build
depends_on: [1.10]
outputs:
  - dist/manifest.webmanifest
  - dist/service-worker.js
  - dist/workbox-config.js
  - dist/icons/ (múltiples tamaños)
tech: [workbox, webmanifest, service-worker]
micro_summary: Convierte la app en PWA instalable. Base universal para web, Android add-to-home, iOS add-to-home y Windows Edge.
micro_flow: definir manifest → configurar Workbox → precache app shell → runtime cache para API → registrar SW en bootstrap
instructions:
  - manifest.webmanifest: name, short_name, start_url, display standalone, theme_color, background_color, icons (192, 512, maskable).
  - Workbox en modo injectManifest con precache del app shell.
  - Runtime cache: network-first para API, cache-first para assets estáticos, stale-while-revalidate para imágenes.
  - Service worker registrado solo en HTTPS o localhost.
  - Actualización automática del SW con notificación de "nueva versión disponible".
  - Modo offline funcional desde el día uno.
acceptance: la app instala desde Chrome Android, Safari iOS (añadir a inicio) y Edge Windows sin errores.
```

Nodo 5.2 — Tauri Desktop

```
node_id: 5.2
segment: empaque
kind: build
depends_on: [1.10, 5.1]
outputs:
  - src-tauri/tauri.conf.json
  - src-tauri/Cargo.toml
  - src-tauri/src/main.rs
  - dist/desktop/ (AppImage, deb, exe, msi, dmg)
tech: [tauri-2, rust, webview2, webkitgtk]
micro_summary: Empaca la app como binario nativo para Windows, Linux y macOS. Peso objetivo menor a 15 MB.
micro_flow: configurar Tauri → definir permisos → cargar dist/ → compilar binarios por plataforma → firmar
instructions:
  - Tauri 2 con webview nativo (WebView2 en Windows, WebKitGTK en Linux, WKWebView en macOS).
  - Permisos declarados en capabilities: solo filesystem (con scope), notifications, dialog, shell (bloqueado por defecto).
  - Sidecar opcional para agentes locales pesados (Python embebido si se necesita).
  - Updater nativo con firma de releases.
  - Instaladores: AppImage + deb para Linux; exe + msi para Windows; dmg para macOS.
  - Auto-update desde GitHub Releases.
acceptance: instalar en Windows, Linux y macOS; el binario pesa menos de 15 MB; auto-update funciona.
```

Nodo 5.3 — Capacitor Mobile

```
node_id: 5.3
segment: empaque
kind: build
depends_on: [1.10, 5.1]
outputs:
  - capacitor.config.ts
  - android/ (proyecto Gradle)
  - ios/ (proyecto Xcode)
  - dist/mobile/ (APK, AAB, IPA)
tech: [capacitor-6, android-studio, xcode]
micro_summary: Empaca la app como aplicación nativa Android e iOS. Reutiliza el mismo núcleo HTML/CSS/JS.
micro_flow: configurar Capacitor → añadir plataformas → configurar plugins → compilar APK/AAB e IPA → firmar
instructions:
  - Capacitor 6 con plugins oficiales: Filesystem, Share, Notifications, Preferences, Network, Camera, Microphone.
  - Android: minSdk 24, targetSdk 34, firma con keystore propio.
  - iOS: deployment target 15.0, firma con provisioning profile.
  - Back button de Android mapeado a navegación interna, no a cerrar la app.
  - Deep links para abrir la app desde URL externa.
  - Splash screen con logo YAIWES, adaptativo a tema claro y oscuro.
  - Publicación: Play Store (AAB) e App Store (IPA). PWA como fallback si no hay cuenta Apple.
acceptance: instalar APK en Android y ver misma experiencia que web; IPA compila sin errores en Xcode.
```

Nodo 5.4 — Native Bridges

```
node_id: 5.4
segment: empaque
kind: build
depends_on: [5.2, 5.3]
outputs:
  - shared/native/bridge.js
  - shared/native/fs-bridge.js
  - shared/native/share-bridge.js
  - shared/native/notifications-bridge.js
  - shared/native/biometrics-bridge.js
tech: [javascript, capacitor-plugins, tauri-api]
micro_summary: Capa única que abstrae las APIs nativas. La UI llama a bridge.js, no a Capacitor ni Tauri directamente.
micro_flow: detectar plataforma → resolver bridge correspondiente → exponer API unificada → UI consume sin saber plataforma
instructions:
  - API unificada: fs.read, fs.write, share.send, notifications.schedule, biometrics.verify.
  - En web: fallback a File System Access API o descarga tradicional.
  - En desktop Tauri: usa las APIs de Tauri 2.
  - En móvil Capacitor: usa los plugins oficiales.
  - La UI nunca importa Capacitor ni Tauri directamente.
  - Cada bridge declara permisos y los pide al usuario cuando corresponde.
acceptance: guardar un archivo funciona igual en web, desktop y móvil sin cambiar código de UI.
```

Nodo 5.5 — Accessibility Layer

```
node_id: 5.5
segment: accesibilidad
kind: build
depends_on: [2.1, 3.1]
outputs:
  - shared/a11y/keyboard-nav.js
  - shared/a11y/screen-reader-announcer.js
  - shared/a11y/focus-manager.js
  - shared/a11y/preferences.js
tech: [javascript, aria, wai-aria]
micro_summary: Accesibilidad completa desde el diseño. Navegación por teclado, lector de pantalla, contraste AA, reducción de movimiento.
micro_flow: detectar preferencias del sistema → aplicar perfil → exponer atajos → anunciar cambios al lector → gestionar foco
instructions:
  - Navegación por teclado completa en panel A y B: Tab, Shift+Tab, Enter, Esc, flechas.
  - Focus visible en todos los controles interactivos.
  - Lector de pantalla: aria-live para cambios importantes, aria-label en iconos, roles correctos.
  - Contraste AA mínimo en todos los textos; AAA cuando sea posible.
  - Respetar prefers-reduced-motion: pausar animaciones si el usuario lo pide.
  - Respetar prefers-color-scheme: tema claro, oscuro o sistema.
  - Atajos: Ctrl/Cmd+K para chat, Ctrl/Cmd+/ para comandos, Esc para cerrar canvas.
  - Perfil de accesibilidad guardado en IndexedDB y sincronizado vía CRDT.
acceptance: usuario con lector de pantalla completa tarea en panel B sin usar el ratón.
```

Nodo 5.6 — i18n / l10n

```
node_id: 5.6
segment: internacionalizacion
kind: build
depends_on: [3.2, 2.1]
outputs:
  - shared/i18n/i18n.js
  - shared/i18n/locales/es.json
  - shared/i18n/locales/en.json
  - shared/i18n/locales/pt.json
  - shared/i18n/format.js
tech: [javascript, intl-api]
micro_summary: Internacionalización completa. Español y inglés de base, portugués opcional. Cero strings hardcodeados.
micro_flow: detectar locale del sistema → cargar locale → aplicar a toda la UI → formatear fechas y números → permitir override manual
instructions:
  - Uso de Intl API para fechas, números, monedas, plurales.
  - Detección automática del locale del navegador o sistema.
  - Override manual desde ajustes.
  - Todos los textos visibles pasan por t('clave').
  - Fechas siempre en zona horaria del usuario por defecto; America/Bogota como override configurable.
  - TTS y STT respetan el locale del usuario.
  - Añadir nuevo idioma es solo añadir un JSON; cero cambios de código.
  - Plurales y géneros manejados por Intl o por reglas declaradas.
acceptance: cambiar idioma a inglés actualiza toda la UI y los mensajes de voz sin recargar.
```

Nodo 5.7 — Design System final

```
node_id: 5.7
segment: diseno
kind: build
depends_on: [1.3, 5.5, 5.6]
outputs:
  - shared/design/components.js
  - shared/design/button.js
  - shared/design/input.js
  - shared/design/window-frame.js
  - shared/design/stories/ (Storybook)
tech: [javascript, css, storybook]
micro_summary: Biblioteca de componentes compartidos entre panel A y B. Tokens FROMTED, accesibilidad e i18n integrados por defecto.
micro_flow: definir componente → aplicar tokens → aplicar a11y → aplicar i18n → publicar story → usar en paneles
instructions:
  - Componentes base: Button, Input, Select, Toggle, Modal, Window, Card, Badge.
  - Cada componente: tokens FROMTED, ARIA correctos, teclado, i18n, tema claro/oscuro.
  - Storybook para ver todos los componentes y sus estados.
  - Cero valores hardcodeados. Todo por token.
  - Componentes reutilizables en panel A y B sin duplicar código.
  - Versionado semver para cambios que rompen.
acceptance: Storybook muestra todos los componentes con todos los estados y temas.
```

Nodo 5.8 — Unified Build Pipeline

```
node_id: 5.8
segment: build
kind: build
depends_on: [5.1, 5.2, 5.3, 5.4]
outputs:
  - build/scripts/build-all.js
  - build/scripts/build-web.js
  - build/scripts/build-desktop.js
  - build/scripts/build-mobile.js
  - .github/workflows/release.yml
tech: [nodejs, vite, github-actions]
micro_summary: Un solo comando genera todos los artefactos. Un solo workflow publica todos los releases.
micro_flow: build:web → build:desktop → build:mobile → firmar → publicar en GitHub Releases → publicar PWA en hosting
instructions:
  - Comandos: pnpm build:web, pnpm build:desktop, pnpm build:mobile, pnpm build:all.
  - Pipeline CI/CD en GitHub Actions: en push a main, compila, testea y publica a releases.
  - Artefactos por release: dist/ web, AppImage/deb/exe/msi/dmg desktop, APK/AAB/IPA móvil.
  - Versión unificada por semver. Cero versiones diferentes por plataforma.
  - Firma obligatoria de artefactos con Sigstore/Cosign.
  - Changelog automático desde commits convencionales.
acceptance: un push a main genera release completo con todos los artefactos en menos de 30 minutos.
```

Nodo 5.9 — Deployment Guide

```
node_id: 5.9
segment: deploy
kind: build
depends_on: [5.8]
outputs:
  - docs/DEPLOY.md
  - docs/ARCHITECTURE.md
  - docs/CONTRIBUTING.md
  - docs/OPERATIONS.md
tech: [markdown, mermaid]
micro_summary: Guía completa de despliegue, arquitectura, contribución y operación. Todo lo que un nuevo dev necesita.
micro_flow: escribir guía → validar comandos → publicar en repo → mantener actualizada
instructions:
  - DEPLOY.md: cómo desplegar web (Vercel/Netlify/Cloudflare Pages), desktop (releases GitHub), móvil (Play Store, App Store).
  - ARCHITECTURE.md: diagrama de paneles, flujo de datos, contratos, decisiones tomadas.
  - CONTRIBUTING.md: cómo contribuir, estándares de código, cómo correr tests, cómo abrir PR.
  - OPERATIONS.md: cómo monitorear, cómo recuperar de fallo, cómo rotar secretos, cómo auditar.
  - Diagramas en mermaid para que se rendericen en GitHub sin herramientas externas.
  - Ejemplos copiables de cada comando.
acceptance: un dev nuevo puede desplegar la app en su máquina siguiendo solo la documentación.
```

Nodo 5.10 — Telemetry & Crash Reporting (opt-in)

```
node_id: 5.10
segment: telemetria
kind: build
depends_on: [4.9, 5.5]
outputs:
  - shared/telemetry/telemetry.js
  - shared/telemetry/crash-reporter.js
  - shared/telemetry/consent-gate.js
tech: [javascript, sentry, opentelemetry]
micro_summary: Telemetría y crash reporting opcional. Cero datos por defecto. Solo si el usuario lo activa.
micro_flow: pedir consentimiento → activar si acepta → enviar solo datos anónimos → respetar revocación inmediata
instructions:
  - Por defecto: telemetría desactivada. Cero datos al backend.
  - Al activar: enviar solo eventos anónimos (rendimiento, errores, uso de capacidades).
  - Nunca enviar contenido de mensajes, prompts ni resultados.
  - Crash reporting con stack trace sanitizado.
  - El usuario puede ver exactamente qué se envía antes de activarlo.
  - Revocación inmediata: al desactivar, se detiene todo envío en menos de 1 segundo.
  - Datos anonimizados con hash no reversible.
acceptance: activar telemetría envía solo eventos anónimos; desactivar detiene todo en 1 segundo.
```

Nodo 5.11 — Global Acceptance Criteria

```
node_id: 5.11
segment: verify
kind: verify
depends_on: [5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10]
outputs:
  - tests/acceptance.spec.ts
  - tests/acceptance-report.json
tech: [playwright, axe-core, lighthouse]
micro_summary: Verifica los 12 goals de aceptación globales del plan completo. Es el cierre formal de todo el sistema.
micro_flow: ejecutar cada test de goal → registrar resultado → generar reporte → publicar
instructions:
  - Goal 1: 90 por ciento de tareas se completan sin clic (solo chat o voz).
  - Goal 2: voz y texto generan resultados idénticos en 20 tareas aleatorias.
  - Goal 3: el usuario nunca pregunta "¿qué está pasando?" en sesiones observadas.
  - Goal 4: cero cruce de información técnica entre panel A y B.
  - Goal 5: cero acciones destructivas ejecutadas sin confirmación explícita.
  - Goal 6: cero código duplicado por plataforma (mismo núcleo en web, desktop, móvil).
  - Goal 7: latencia de sync menor a 500 ms entre dispositivos.
  - Goal 8: 30 por ciento de tareas completables offline.
  - Goal 9: cero pérdida de contexto de los últimos 10 minutos tras cierre abrupto.
  - Goal 10: primera tarea completada en menos de 60 segundos.
  - Goal 11: el canvas decide foco sin intervención manual del usuario.
  - Goal 12: cobertura a11y completa y multi-idioma funcionando.
acceptance: los 12 goals medidos y documentados con evidencia.
```

Nodo 5.12 — Final Integration Test

```
node_id: 5.12
segment: verify
kind: verify
depends_on: [5.11]
outputs:
  - tests/final.e2e.spec.ts
  - tests/final-report.md
tech: [playwright, vitest]
micro_summary: Test end-to-end del sistema completo. Desde instalar la app hasta completar tareas reales en cada plataforma.
micro_flow: instalar app → ejecutar flujo usuario completo → verificar paneles → verificar voz → verificar offline → verificar sync → cerrar
instructions:
  - Test 1: instalar PWA, completar onboarding, ejecutar tarea real.
  - Test 2: instalar APK Android, ejecutar misma tarea.
  - Test 3: instalar exe Windows, ejecutar misma tarea.
  - Test 4: editar canvas en móvil, ver cambio en desktop.
  - Test 5: apagar red, ejecutar tarea offline, reconectar y ver sincronización.
  - Test 6: acceso con clave a panel A, ver DAG en ejecución, resolver un HITL.
  - Test 7: verificar a11y con axe-core en los 2 paneles.
  - Test 8: verificar i18n cambiando idioma y viendo toda la UI actualizada.
  - Test 9: verificar telemetría desactivada por defecto.
  - Test 10: verificar auto-update desde release anterior.
acceptance: 10 tests end-to-end pasan en verde en todas las plataformas.
```

---

Esquema de dependencias Salida 5

```
5.1 PWA Core
  ├── 5.2 Tauri Desktop
  ├── 5.3 Capacitor Mobile
  │     └── 5.4 Native Bridges
  └── 5.8 Unified Build Pipeline
        └── 5.9 Deployment Guide

5.5 Accessibility Layer
5.6 i18n / l10n
5.7 Design System final
  └── 5.11 Global Acceptance Criteria

5.10 Telemetry & Crash Reporting
  └── 5.11 Global Acceptance Criteria
        └── 5.12 Final Integration Test
```

---

Instrucciones específicas para la IA que cerrará el proyecto

Regla 1. Un solo núcleo HTML/CSS/JS. Cero reescritura por plataforma.

Regla 2. Un solo comando genera todos los artefactos. Cero builds manuales por plataforma.

Regla 3. Accesibilidad y i18n desde el diseño, no como parche.

Regla 4. Cero telemetría por defecto. Solo si el usuario la activa explícitamente.

Regla 5. Firma obligatoria de artefactos. Sigstore o equivalente.

Regla 6. Documentación completa: desplegar, contribuir, operar, recuperar.

Regla 7. Los 12 goals de aceptación son medibles y con evidencia.

Regla 8. Auto-update funciona sin intervención del usuario.

Regla 9. Versión unificada por semver. Cero versiones distintas por plataforma.

Regla 10. Un solo pipeline CI/CD. Un solo release por versión.

---

Cierre del plan completo

El plan UI YAIWES se compone de 5 salidas y 45 nodos:

Salida 1 — Fundación. 11 nodos. Contratos, estructura, tokens, store, router, host shell, registry, action bus, bridge, bootstrap, test.

Salida 2 — Panel A Command Center. 10 nodos. Shell, visualizer, inspector, event stream, checkpoints, HITL, metrics, audit, sandbox, test.

Salida 3 — Panel B Conversation & Canvas. 12 nodos. Shell, chat, voz stub, node plan bridge, canvas orchestrator, window renderer, canvas core, attention scheduler, media pipeline, capability projector, onboarding, test.

Salida 4 — Voz, agentes locales, sync, offline. 10 nodos. Voice completo, local agent runtime, offline queue, local persistence, CRDT sync, device registry, registry UI bridge, resilience, privacy, test.

Salida 5 — Empaque, accesibilidad, i18n, cierre. 12 nodos. PWA, Tauri, Capacitor, native bridges, a11y, i18n, design system, unified build, deploy guide, telemetry, acceptance criteria, final test.

Total: 45 nodos ejecutables, cada uno con contrato, micro-flujo, tecnología, instrucciones y criterio de aceptación.

El plan está completo. Está listo para que la IA empiece a implementar en el orden definido. La fundación primero, después los paneles en paralelo, después voz y sync, y por último el empaque y cierre.

Fin del plan UI YAIWES.


Componentes Open Source y Skills para la UI YAIWES

Hora local Colombia: 4:15 a. m. (America/Bogota, UTC-5), domingo 27 de septiembre de 2026.

Esta es la lista consolidada de piezas open source que puedes fusionar para construir la UI YAIWES sin partir de cero. Están organizadas por dominio, con licencia, para qué sirve y dónde encaja en el plan de 45 nodos.

---

1. Núcleo UI, doble panel y layout

@dojo-ng/split-panel (BSD-3-Clause). Web component de dos paneles redimensionables con divisor arrastrable. Encaja directo en el nodo 3.1 (Panel B Shell) para el layout dual responsive.

SQLRooms Layout (MIT). Composición de paneles React en splits, tabs, grids y docking workspaces. Útil para el nodo 2.1 (Panel A Shell) y su inspector de nodos.

Adw.OverlaySplitView / Adw.NavigationSplitView (LGPL). Referencia de patrón sidebar-contenido o overlay para móvil. Ideal para la versión móvil del nodo 3.1.

UZOR (Rust, licencia por confirmar). Framework headless con Panel System dockable y redimensionable. Referencia conceptual para el layout engine del nodo 3.5.

DrawnUI (.NET, SkiaSharp). Motor de composición UI con gestos, layouts y animaciones aceleradas por hardware. Referencia para el canvas animado del nodo 3.9.

---

2. Canvas y visualización

tldraw (Apache 2.0). Canvas infinito con SDK React, formas custom y colaboración. Base directa del nodo 3.7 (CanvasCore).

React Flow (MIT). Grafo de nodos y conexiones. Base directa del nodo 2.2 (Workflow Visualizer) para renderizar el DAG.

Strudel Flow (MIT). Híbrido que fusiona React Flow con tldraw. Alternativa si quieres un solo motor para DAG y canvas visual.

Excalidraw (MIT). Canvas de bocetos embebible. Referencia para el modo nota libre del usuario.

manim-skill y skill-canvas-video (ya descargados en tu repositorio). Generación de animaciones y vídeo del proceso. Nodo 3.9 (MediaPipeline).

---

3. Estado, sincronización y persistencia

Yjs (MIT). CRDT para colaboración y edición offline. Base del nodo 4.5 (CRDTSync). ~920K descargas semanales, 17K estrellas.

Loro (MIT). CRDT más rápido en benchmarks que Yjs. Loro Mirror mantiene estado tipado inmutable sincronizado con el documento CRDT. Alternativa o complemento del nodo 4.5.

Automerge (MIT). CRDT document-based, líder en colaboración junto a Yjs. Opción para el nodo 4.5 si prefieres modelo JSON puro.

Dexie (Apache 2.0). Wrapper de IndexedDB con queries tipadas. Base del nodo 4.4 (LocalPersistence).

Earthstar (MIT). Toolkit UI para apps offline-first colaborativas. Referencia para el nodo 4.3 (OfflineQueue).

ProseKit (MIT). Integración de Yjs y Loro con ProseMirror para edición colaborativa. Útil si el canvas incluye edición de texto enriquecido.

---

4. Empaque multiplataforma

Tauri 2 (MIT/Apache 2.0). WebView nativo, bundles de 5-10 MB, soporta desktop + iOS + Android desde un solo código. Base del nodo 5.2.

Capacitor 6 (MIT). WebView nativo en Android e iOS, ecosistema de plugins maduro. Base del nodo 5.3.

Workbox (MIT). Service worker y precache para PWA. Base del nodo 5.1.

Capacitor Community Plugins (MIT). Filesystem, Share, Notifications, Preferences, Network, Camera, Microphone. Base del nodo 5.4 (Native Bridges).

Tauri Plugins (MIT/Apache 2.0). fs, dialog, notification, updater, shell. Base del nodo 5.4 para desktop.

Enhance Capacitor UI (skill para agentes, MIT). Skill de separación UI/UX cross-surface para apps híbridas PWA + iOS + Android vía Capacitor o Tauri. Útil para el nodo 5.3 y 5.4.

---

5. Accesibilidad

@compa11y (MIT). Toolkit completo de accesibilidad con componentes React y Web Components, ARIA y teclado gestionados. Base del nodo 5.5.

accessible-kit (MIT). Librería de componentes accesibles sin dependencias, ARIA completo, vanilla JS. Alternativa para el nodo 5.5.

OpenNagish (MIT). Widget de accesibilidad con 20+ funciones asistivas (visual, motor, cognitivo, auditivo). Complemento del nodo 5.5.

akyos-accessibility (MIT). Correcciones ARIA automáticas, skip links, reporte visual con score y export JSON para CI. Útil para los tests del nodo 5.11.

axe-core (MPL 2.0). Motor de testing de accesibilidad. Base de los tests de los nodos 5.11 y 5.12.

---

6. Internacionalización (i18n)

i18next (MIT). Framework de internacionalización más popular, detección de idioma, caché, namespaces. Base del nodo 5.6.

js-lingui (MIT). i18n para JavaScript, 2-3 kb, extracción automática de strings, compatible con React. Alternativa al nodo 5.6.

@dreamer/i18n (MIT). Librería ligera sin dependencias, multi-idioma completo. Opción minimalista para el nodo 5.6.

@yyc3/i18n-core (MIT). Framework i18n basado en plugins, cero dependencias, alto rendimiento. Alternativa para el nodo 5.6.

Intl API (nativa). Fechas, números, monedas, plurales. Base obligatoria del nodo 5.6.

---

7. Design System y tokens

OpenDesigner (MIT). Constructor de design system con IA. Genera tokens DTCG, CSS, Tailwind, Figma variables, DESIGN.md con checks WCAG 2.2. Base del nodo 5.7.

DESIGN.md (formato abierto de Google). Formato para que agentes de IA entiendan tokens y brand visual. Útil para que la IA que programe la UI entienda el sistema.

@p31ca/canon (Apache 2.0). Design system agent-native con export W3C DTCG y DESIGN.md. Referencia para el nodo 5.7.

element-hq/compound-design-tokens (MIT). Tokens con temas claro/oscuro/alto contraste, export a Web, iOS y Android. Modelo para el nodo 5.7.

Veritheme (MIT). CSS design system con generador de temas, export DTCG 2025.10. Opción para el nodo 5.7.

@johnfilipstad/groundwork-tokens (MIT). Tokens accesibles con WCAG AA y soporte de reduced motion. Referencia para el nodo 5.7.

---

8. Runtime de agentes locales

@obsku/tool-code-interpreter-wasm (MIT). Intérprete de código WASM-sandboxed que corre Python (Pyodide) y JavaScript (QuickJS) sin acceso al host. Base del nodo 4.2.

ClamBot (MIT). Asistente con sandbox WASM (QuickJS dentro de Wasmtime) para código generado por LLM. Referencia para el sandbox del nodo 4.2.

byte (MIT). Agente self-hosted con WASM sandbox (Pyodide), RAG híbrido y MCP. Referencia para el nodo 4.2 y 4.7.

OpenAI Agents Python SDK en Wasm (MIT). Correr el SDK de agentes dentro del browser vía Pyodide. Patrón para agentes locales sin backend.

wasmsh-pyodide (MIT). Runtime Pyodide para wasmsh. Alternativa para el nodo 4.2.

---

9. Voz (STT, TTS, VAD)

faster-whisper (MIT). STT local rápido, modelo tiny para móvil y medium para desktop. Base del nodo 4.1.

Piper (MIT). TTS local offline, CPU optimizado, voces ONNX. Base del nodo 4.1.

Silero VAD (MIT). Detección de voz precisa, filtra ruido y falsos positivos. Base del nodo 4.1.

chuchote (MIT). Pipeline completo: Silero VAD → faster-whisper → Ollama → Piper. Referencia para el flujo de voz del nodo 4.1.

Voice Studio (MIT). STT con faster-whisper y TTS con Piper, con timestamps por palabra. Referencia para el nodo 4.1.

AbstractVoice (MIT). Stack local Piper + faster-whisper con AEC. Alternativa para el nodo 4.1.

---

10. Action Bus y plugin architecture

@softize/opus (MIT). Declara acción una vez (input, auth, ejecución, audit, feedback) y adaptadores materializan en UI, cliente, servidor y log. Base del nodo 1.8 (Action Bus).

Cortera Framework (MIT). Action primitive, event log, permisos, blast radius, risk modes, provenance. Modelo para el nodo 1.8 y 2.8 (Audit).

@xeplr/actions (MIT). Registry de acciones con inputs tipados e invocación segura. Componentes React ActionExplorer + ActionRunner. Alternativa para el nodo 1.8.

Open VSX (EPL 2.0). Registry de extensiones con backend Spring Boot y frontend React. Modelo para el nodo 4.7 (Capability Registry UI Bridge).

OpenEverest Hub (Apache 2.0). Registry de plugins con UI genérica. Referencia para el nodo 4.7.

---

11. Skills para agentes de diseño UI

Superdesign (MIT). Skill de diseño para Claude Code, Cursor y cualquier agente. Convierte UI genérica en frontend pulido. Útil para que la IA que programe la UI no genere "AI slop".

UI Sift (MIT). Skill React-first para elegir componentes, encontrar skills y MCP tools, y convertirlos en producto coherente. Base para que la IA seleccione piezas del ecosistema.

Design Workbench Skills (MIT). 11 skills coordinados de diseño y escritura para agentes: investigación visual, interface craft, review enfocado, prosa clara. Complemento para el nodo 5.7.

Open Design (MIT). 31 skills composables y 72 design systems brand-grade. Genera páginas, decks, prototipos, imágenes y vídeo. Alternativa completa para diseño asistido por agente.

Pi Coding Agent (MIT). Disciplina anti-slop UI/UX con DESIGN.md lintable y dirección de diseño. Referencia para el nodo 5.7.

---

12. Offline-first y resiliencia

@whiskeyjack-net/design-system (MIT). Design system Tauri-first con componentes thumb-first, offline-first, un código para desktop y móvil vía Tauri. Referencia para el nodo 5.2 y 5.7.

Hero OS (MIT). Framework de desktop environment con Dioxus (Rust → WASM), window management estilo macOS y theming para apps WASM cargadas dinámicamente. Referencia conceptual para el canvas multi-ventana.

muon (MIT). Plataforma GUI multiplataforma basada en CEF (Chromium Embedded Framework). Alternativa a Tauri si necesitas Chromium completo.

---

13. Herramientas de testing y verificación

Playwright (Apache 2.0). Tests end-to-end en navegador, móvil y desktop. Base de los nodos 2.10, 3.12, 4.10, 5.11 y 5.12.

Vitest (MIT). Tests unitarios rápidos. Base de todos los tests de integración.

axe-core (MPL 2.0). Testing de accesibilidad. Base de los tests del nodo 5.11.

Lighthouse (Apache 2.0). Métricas de rendimiento, PWA y accesibilidad. Complemento del nodo 5.11.

ajv (MIT). Validación de JSON Schema. Base del nodo 1.1 (Contratos).

json-schema-to-typescript (MIT). Genera tipos TS desde schemas. Base del nodo 1.1.

---

14. Stack mínimo para empezar hoy

Si tuvieras que elegir una sola combinación para arrancar la fundación (Salida 1) y el Panel B (Salida 3) sin perder tiempo, sería esta:

Núcleo UI: HTML/CSS/JS + @dojo-ng/split-panel para doble panel.
Estado: Zustand + Dexie + Yjs.
Canvas: tldraw + React Flow.
Empaque: PWA (Workbox) + Tauri 2 + Capacitor 6.
Voz: faster-whisper + Piper + Silero VAD.
Agentes locales: QuickJS + Pyodide (vía @obsku o wasmsh).
i18n: i18next.
A11y: @compa11y + axe-core.
Design System: OpenDesigner + DESIGN.md.
Skills de diseño: Superdesign + UI Sift.
Testing: Playwright + Vitest.

Con estas piezas, los nodos 1.1 a 1.11, 2.1 a 2.10 y 3.1 a 3.12 se pueden implementar sin escribir infraestructura desde cero. Las piezas restantes (Salidas 4 y 5) se añaden sobre esta base sin refactor.

---

15. Dónde NO usar open source

Tres cosas del plan no las cubre ningún proyecto open source tal cual:

El Component-IR neutral (nodo 1.1) es específico de tu arquitectura. Se construye.
El Transform Planner determinista (nodo 3.4) es lógica de negocio. Se construye.
El Semantic Contract Gate (nodo 1.11) valida invariantes y ejemplos ejecutables. Ningún proyecto lo hace genérico. Se construye.

Todo lo demás tiene base open source fusionable.

---

Fin de la lista. Cuando quieras, puedo detallar cómo fusionar dos o más de estas piezas en un nodo específico del plan.





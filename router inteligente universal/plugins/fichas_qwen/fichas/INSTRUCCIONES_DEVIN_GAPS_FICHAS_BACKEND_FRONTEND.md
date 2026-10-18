# YAIWES — HANDOFF PARA DEVIN: 18 GAPs, reparación mínima y aceptación

**Alcance:** fichas 1–5 + backend `fichas_qwen`, `puente_chat` y frontend real. **Base de auditoría:** `main` en `28f6088f3e2b71c50fee2ed6353e433ac4f9c53a` (18-10-2026). Es una **referencia**, no autorización para aplicar un diff obsoleto. Releer HEAD antes de editar. **No modificar GitHub, no hacer commit, push ni deploy sin nueva autorización explícita del Director.** Entregar primero parches en copia local/PR propuesto, evidencias y diff. No confiar en texto de Qwen como prueba de tool ejecutada.

## Reglas inviolables

1. Reutilizar JSON funcional, selector, DAG, scheduler, checkpoints, memoria, capacidades y herramientas **existentes**. 2 y 3: conservar arquitecturas y nodos; 5: conservar MVP directo, sin introducir DAG. 1 y 4: conservar sus selectores propios. No duplicar `dsl`, `loop`, `nodos`, `mode_router`, `governance` ni routers.
2. JSON `YAIWES_PROMPT_1A1_JSON_UNICO.json` + `PARCHE_4_PASADAS_PROMPT_SEGMENTOS_SOLO_FALTANTES.json` + los **cinco JSON originales de Claude** son fuentes de cobertura. Verificar equivalencia semántica con campos existentes y convertir **solo** reglas faltantes. Mantener registro SHA de origen. **No afirmar VERBATIM de contratos adicionales cuyo literal completo no está disponible**.
3. No declarar `max_tokens=unlimited`: proveedor tiene límites por llamada. Resolver volumen de **tarea** con checkpoints y llamadas sucesivas. `Stop` del usuario, permisos de escritura y cuotas siguen vigentes. No crear `while True` sin avance e idempotencia.
4. Para todo GAP: `ruta + línea/función real → causa → hunk mínimo → prueba NEGATIVA + POSITIVA → recibo → PASS/FAIL`. Ante un cambio upstream, recalcular la causa y no aplicar el hunk a ciegas.

## Inventario ejecutable (G01–G18)

| ID / prioridad | GAP / evidencia | Qué cambiar **exactamente** | Prueba de aceptación |
|---|---|---|---|
| **G01 P0** | Frontend `api.js::harness`: referencias a `...extra` sin definir `extra` (error JS). | Restablecer **una** declaración `const extra = Object.assign(...)` antes de su primera expansión. Incluir `sesion`, `anclados` incluso `[]`, `active_anchors_v1:true`, `gobernanza`, `constitucion`, `instrucciones_fijas`, flags de selector y contexto previo; preservar payload existente. | Desde navegador REAL enviar F1/F2/F3/F5; cero `ReferenceError`, request llega al backend con flags correctos. |
| **G02 P0** | `panel-chat.js` usa `mvp` en `mensajeQwen`/`fijasQwen` antes de inicializar `const mvp` (TDZ). | **Mover** la declaración original de `mvp` por encima de esas dos líneas, sin duplicarla. | Browser F1/F2/F3/F5 envía y recibe; cero `Cannot access 'mvp' before initialization`. |
| **G03 P0** | Botón **Think** modifica tokens UI pero no llega fiable al proveedor. | `panel-chat.js` → `api.js` → `fichas_qwen/plugin.py` y `mvp.py` → `puente_chat/plugin.py`: pasar `thinking_mode` estructurado, validado en backend; usar parámetro de razonamiento **compatible con cada proveedor**, también con tools; no duplicar `enable_thinking` y `reasoning_effort` incompatibles. | ON/OFF + tool on/off Qwen/DeepSeek/GLM con payload backend sanitizado y respuesta. En unsupported: `GAP_THINKING_UNSUPPORTED`, no falso ON. |
| **G04 P0** | Complemento JSON del prompt no está conectado al selector code/agente. | Reutilizar **selector ya existente** `RIU_SELECTORES`/`ficha_qwen`, `task_type`, `cap_in` y `perfil`. Aplicar políticas pertinentes en `fichas_qwen/plugin.py` a F1/F2/F3/F4 N4 y en `mvp.py::_mensajes` a F5 MVP, solo para tareas código/agente. No reconstruir DAG F2/F3 ni crear segundo selector/router. | Chat común OFF; tarea code ON; agente ON; F2/F3 N4 ON y otros nodos sin duplicación; F5 MVP ON sin DAG. |
| **G05 P0** | Entrada larga se corta: `_hist_txt` (20 mensajes / ~12k caracteres), `limite_llamada_chars` (60k), posibles `.trim()` del frontend. | Conservar entrada literal UTF-8 íntegra en persistencia **antes** de cualquier ventana, generar SHA, guardar readback. Si no cabe en proveedor, dividir por tareas/nodos con checkpoint + recuperación; el modelo debe consumir todas las partes necesarias. Separar historial abreviado de fuente íntegra. | 80k+ caracteres con Unicode/espacios: SHA exacto original↔readback↔reensamblado, sin truncado silencioso; reporte real de segmentos consumidos. |
| **G06 P0** | Fichas capan salida a 1500 tokens (general), FAST ~500 y UI 512/1024/2048; el modelo devuelve incompleto. | Por nodo, distinguir `max_output_tokens` **permitidos por proveedor**, `task_token_budget` y `fast_lane`. Para trabajo largo usar continuación por múltiples llamadas y checkpoint sin repetir escrituras. No configurar infinito ni eliminar límites de seguridad del transporte. | Respuesta suficientemente larga produce 3+ segmentos unidos con hashes, cero PASS prematuro y coste/tokens registrados. |
| **G07 P0** | `finish_reason=length` y timeouts dan respuesta parcial, sin continuación durable probada. | Reutilizar `puente_chat::_http_stream/_bucle` y detector `length`. Guardar parcial, cursor, receipts de tools y estado antes de terminar request; reanudar exactamente desde último checkpoint. | Forzar `length` dos veces + interrupción SSE; al retomar texto completo, 1 sola ejecución por mutación. |
| **G08 P0** | `api.js::RIU_RETOMAR` puede producir `RESULTADO_VACIO` tras ocho polls sin `estado`, sin saber si backend trabaja. | Distinción `RUNNING`/`DONE`/`BLOCKED`/transporte vacío. `RUNNING` conserva mismo PID, consulta checkpoint/estado real y no crea otro trabajo; error transitorio = `RUNNING_RESUMABLE`, no `DONE`. | 8 respuestas vacías simuladas mientras backend está RUNNING: PID conservado, sin doble ejecución; al completar devuelve respuesta. |
| **G09 P0** | `TIEMPO_TOTAL_AGOTADO`: el frontend termina tras ~560 s aunque el proceso podría seguir. | `api.js::puenteRouter`: agotamiento del polling UI → `RUNNING_RESUMABLE`, conservar PID/base y botón reanudar; corregir backend solo si su deadline también destruye el checkpoint. | Tarea dura más que polling: mismo PID retoma y termina; no burbuja vacía y no se ejecuta tool dos veces. |
| **G10 P0** | LOOP CODA se detiene con nodos pendientes por `loop.max_segundos`, `loop.correcciones` o un request agotado. | `fichas_qwen::_correr`: distinguir **límite de iteración/request** de **fin de tarea**. Guardar nodo pendiente y receipts usando scheduler/checkpoints existentes; reanudar en corridas controladas hasta DONE, GAP bloqueante o Stop explícito. Watchdog contra repetición sin avance. | DAG de varios nodos con pausa/reinicio: pendientes terminan; verificadores pasan; salida no dice DONE antes de tiempo. |
| **G11 P0** | `GAP N4 ... HERRAMIENTA_NO_EJECUTADA`; Qwen simuló lecturas o delegación con texto. | Exigir tool receipt real cuando tarea implica acceso/cambio externo. El LLM **no puede** acreditar una tool diciendo «ejecuté». Si tool falla, retry limitado o GAP con registro. No exigir escritura si usuario solo pidió explicación. | Prueba acceso real: ID de tool, status, payload sanitizado, receipt; fallo real jamás PASS. |
| **G12 P1** | Modelos interpretan nombres/IDs de proyectos como repos en GitHub; conclusiones contradictorias sin evidencia. | Antes de buscar GitHub, resolver `project_id` mediante almacenamiento/memoria YAIWES local; **proyecto no implica repositorio**. Prohibir fabricar estructura de archivos, tareas o tool calls. Buscar GitHub solo cuando corresponda. | Casos: proyecto en memoria sin repo, con repo, ID desconocido: ruta correcta y afirmaciones probadas. |
| **G13 P0** | Desanclar imagen/archivo no siempre elimina su inclusión activa ni el chip visible. | `contexto.js::ampliarAnclados`, `panel-chat.js` y `api.js`: snapshot SOLO fuentes `on`, propagar `active_anchors_v1:true` y `anclados:[]` en OFF, invalidar caché de anclas; en UI quitar chip activo. Mensaje histórico no se borra salvo orden de eliminarlo. | ON→OFF→otro turno→nueva sesión: cero fuente enviada o inyectada, chip desaparece; historial antiguo permanece correctamente. |
| **G14 P1** | Subir 8/25/100/101 imágenes: frontend 2 MB por fichero y vista parcial; la supuesta restricción «7 fotos» no está verificada. | Probar cada ruta real `panel-chat.js`/`almacen-archivos.js`/backend. Subir en lotes acotados; ACK/hash individual; listado paginado y fallos reintentados sin repetir éxitos. No cambiar umbrales sin necesidad. | 8, 25, 100, 101 archivos de prueba dentro de límites, todos visibles/recuperables, sin ACK falso. |
| **G15 P1** | Memoria/historial: `_guardar` pudo recortar pregunta 4k/respuesta 8k; existe vía `chat-full` por verificar. | Conservar resumen corto de búsqueda, PERO persistir original completo con hash en la memoria ya existente; recuperar por ID/cursor en siguientes turnos. | Pregunta/respuesta extensas: lectura posterior byte-a-byte exacta y sesión correcta. |
| **G16 P0** | Botón LOCK agente/tools: `_bucle` consulta sesión en `_IDS_CTX`; `_cablear_graphiti` no la propagaba en ese camino. | Usar `sesion` segura de backend/`_MOTOR_SES` y `_agent_lock_status(sesion)` en **entrada real de delegaciones y tools**, antes de ejecución; LOCK ON devuelve `GAP_AGENT_ACCESS_LOCKED`. **No bloquear chat directo sin tools**. Refrescar estado por sesión en UI. | ON: cero llamadas de agente/tools; chat directo responde; cambio de sesión respeta estado; OFF restablece. |
| **G17 P2** | Ventanas de entrada y salida demasiado pequeñas. | Solo CSS real `chat frontend/shell.css`; `#composer #message` mínimo ~5× altura original dentro de `max-height:80dvh` + `resize`; historial expandible con scroll. Responsive sin ocultar botones/teclado. | Medidas DOM antes/después móvil + PC; input 5× cuando la pantalla lo permite, scroll/stop utilizables. |
| **G18 P1** | Schemas y validadores Claude están en repo pero no demuestran ejecución verdadera del contrato. | Reutilizar `validate_contract.py`, `validate_contract_v11.py`, JSON de Claude, `verificacion_instrucciones`, `gobernanza`; ejecutar pruebas positivas y negativas, asociar receipt/commit+diff+hash a Judge. Resolver rutas relativas solo si fallan. | JSON válido PASS, falso o incompleto FAIL, ejecución real con evidencias; `PASS_SIN_EVIDENCIA` si falta prueba. |

## Código mínimo — dos defectos verificables, sin reescritura

**G02 `panel-chat.js`** — el orden correcto (respetar contenido original de cada línea, solo mover `mvp`):

```js
const soloLiteralQwen = fq === '2' || fq === '3';
const mvp = selAct === 'team-5-mvp'
  ? { plugin: 'fichas_qwen', ficha_qwen: '5', modelo: c.selectorQwen ? c.selectorQwen.label : '', instrucciones_fijas: c.instrucciones || '' }
  : null;
const mensajeQwen = soloLiteralQwen ? rawText : (mvp ? message : A.envolver(message, c.instrucciones));
const fijasQwen = (soloLiteralQwen || mvp) ? (c.instrucciones || '') : '';
```

**G08 `api.js`** — rama cuando no hay `estado` (adaptar dentro del flujo existente; NO sustituir el resto):

```js
if (!p.estado && ++malos >= 8) {
  return {
    estado: 'reanudable', proceso_id: v.pid,
    error: 'GAP_RESULTADO_TEMPORALMENTE_VACIO',
    detalle: 'Reconsultar el mismo PID; no relanzar el trabajo'
  };
}
```

**G17 `shell.css`** — base de estilo adaptativa, medir contra CSS original:

```css
#composer #message { min-height: min(280px, 55dvh); max-height: 80dvh; resize: vertical; overflow-y: auto; }
.chat-history { min-height: min(76dvh, 840px); max-height: 90dvh; overflow-y: auto; }
@media (max-width:480px) {
  #composer #message { min-height: min(280px, 42dvh); }
  .chat-history { min-height:44dvh; max-height:70dvh; }
}
```

**G01 `api.js`** — no insertar un `extra` incompleto. Restaurar objeto `extra` antes del primer `...extra` **con todos los campos vigentes** (señales `anclados` explícitas incluyendo vacío, `sesion`, `instrucciones_fijas`, `active_anchors_v1:true`, `gobernanza`, `constitucion`, `fast_reply`, `motor`, `project_id`, `contexto_previo`, datos del selector `qwen`), y preservar la lógica existente de `harness`.

## Ejecución por fases sin tocar arquitectura

**Fase 0 — baseline:** leer HEAD real y las cinco fichas, comprobar que reversión anterior de `system_prompt_yaiwes_v1` ya ocurrió; SHA backup. `git status` limpio. Prohibido revertir otra vez si ya está.

**Fase 1 — fichas:** comparar JSON único + parche adicional + 5 JSON Claude con campos existentes; dedupe por semántica; insertar **solo** campos faltantes de control para ficha 1/4/5, y solo deltas no cubiertos para 2/3; preservar DSL-DAG 2/3 y MVP sin DAG. Conectar selector code/agente en rutas backend existentes (G04). Verificar parse JSON, claves duplicadas, hashes y diff mínimo.

**Fase 2 — frontend/backend P0:** G01/G02/G03/G05/G06/G07/G08/G09/G10/G11/G13/G16; un microparche+test por GAP, sin tocarlos si HEAD ya los resolvió.

**Fase 3 — restantes y regresión:** G12/G14/G15/G17/G18; pruebas reales de integración entre las 5 fichas, memoria, tools, reconexión, UI móvil.

**Fase 4 — sentencia:** salida `ID | archivo | diff hunk | test ejecutado | evidencia | PASS/FAIL/GAP`. **Nunca** cerrar con `0 GAP` si quedan pruebas sin ejecutar. `HEAD → DIFF → TEST → RECIBO → SIGUIENTE`, STOP solo ante autorización faltante, fallo bloqueante, cancelación explícita o falta de progreso verificable.

**Fuentes de código adjuntas a este handoff** (ya en conversación): `YAIWES_REHACER_5_PASADAS/PASO_2_GAPS_CODIGO/02_XRAY_GAPS_CAMBIOS_Y_CODIGO.md`, `PASO_4_BACKEND_FRONTEND/04_DEVIN_BACKEND_FRONTEND_GAPS_CONECTORES.md`, `PASO_2_GAPS_CODIGO/yaiwes_runtime_helpers.py`. Son propuestas: adaptar al HEAD y verificar; no copy/paste ciego.


---

# ANEXO — Casos adicionales derivados de las salidas de Qwen

## Auditoría cruzada contra las salidas reales citadas por el Director

| Evidencia del Director | GAP existente | Lo que faltaba concretar | Parche obligatorio y prueba |
|---|---|---|---|
| Qwen dice haber leído GitHub y delegado; después incluye «(Simulación...)» y resultados inventados | G11/G18 | Prohibición **operativa** de relatos de tools sin resultados firmados/identificables | Declarar acción `EXECUTED` únicamente con evento real del Harness (`tool_call_id`, nombre, parámetros sanitizados, resultado/estado, timestamp/trace); sin evento `NOT_EXECUTED`, no escribir «encontrado» ni «se delegó». Test: salida textual ficticia debe dar `FAIL_FAKE_TOOL_EVIDENCE`. |
| Primero afirma proyectos ausentes; luego «encontrados» sin evidencia | G12/G18 | Diferenciar verdad de proyecto del registro del chat frente a repos GitHub y resolver contradicciones | Resolver primero `project_id`/sesión/almacenamiento de proyectos; GitHub es fuente **solo** de repositorios. No inferir proyecto inexistente a partir de búsqueda vacía en GitHub. Exigir ubicación real y recibo para «encontrado». Test: mismo input con reportes contradictorios sin receipt → `UNVERIFIED`, nunca PASS. |
| Qwen afirma «PNG truncadas, solo EXIF» | G13/G14 | No estaba exigida prueba de contenido real del adjunto | Antes de describir la imagen: obtener asset original accesible por ID activo, comprobar tipo, tamaño, integridad y **decodificación**; distinguir `IMAGE_READ_OK`, `IMAGE_UNREADABLE` y `IMAGE_NOT_AVAILABLE`. No concluir que contiene solo EXIF por nombre o metadatos. Test: PNG válido, PNG corrupto, asset eliminado/desanclado. El OFF elimina de contexto activo, no borra mensajes históricos. |
| «PASS_SIN_EVIDENCIA» para lista de proyectos sin encargo explícito | G11/G12/G18 | Mezcla entre falta de especificación y falta de prueba de una operación | Clasificar `TASK_UNSPECIFIED` (hay proyecto, no objetivo ejecutable), `PROJECT_NOT_FOUND` (registro real negativo), `TOOL_UNAVAILABLE`, `TOOL_NOT_CALLED`, `TOOL_FAILED`, `PASS_WITH_EVIDENCE`. No usar `PASS_SIN_EVIDENCIA` como demostración de que los proyectos no existen; nunca crear tareas por imaginación. Test por cada estado. |
| `RESULTADO_VACIO` tras recuperación | G08/G09 | Caso `DONE` con texto vacío, ausencia temporal de estado y parcial recuperable | PID estable + lectura de estado persistido. Si `RUNNING` → seguir/retomar; si `DONE` y salida vacía → buscar resultado persistido/último parcial antes de marcar `DONE_EMPTY`; si transporte sin estado → `STATE_UNKNOWN_RESUMABLE` sin duplicar. Test RUNNING vacío, DONE con resultado guardado, DONE genuinamente vacío y timeout UI. |
| «sin límite de tokens» para fichas 1 a 5, **primero** | G05/G06/G07 | Orden de ejecución y distinción demanda de usuario / límite físico | Prioridad funcional de FASE 2: *primero* continuidad de entrada + salida en fichas 1/2/3/4/5. Eliminar solo topes arbitrarios incompatibles con capacidades del proveedor; mantener `max_output_tokens` válido por petición. Persistir texto completo y cursors, continuación durable entre llamadas, presupuestos configurables. Prueba independiente para cada ficha: input largo, `finish_reason=length` dos veces, interrupción, reanudación y misma semántica. |
| «aumentar 5 veces el espacio de input **y salida**» | G17 | El CSS sugerido agranda composer/historial pero no mide explícitamente **salida visible** | Medir alto/ancho útil del editor de INPUT y del panel de **lectura de OUTPUT** antes/después en móvil y escritorio. Intentar 5× la zona útil en ambos con límites de viewport, sin tapar controles de Stop/envío ni el teclado; no prometer 5× cuando la pantalla no lo permite. Prueba con capturas/medidas DOM y scroll. |
| «LOOP CODA sin stop ni escalamiento salvo GAP bloqueante real» | G10 | Distinción entre progreso real y texto de avance simulado | Usar scheduler/estado **existentes**, nodos con `PENDING/RUNNING/BLOCKED/DONE`, checkpoints idempotentes y detector sin progreso. Autocontinuar solo nodos autorizados, no repetir escrituras/commit ni ignorar Stop, permisos o límites proveedor. La UI puede mostrar estado observable sin anunciar éxito. Test: 3 nodos, interrupción tras nodo 1, continuación 2→3, mutaciones únicas y DONE solo con pruebas. |
| «botón thinking activado» | G03 | Distinguir solicitud, parámetro admitido y confirmación del proveedor **con tools** | Propagar `thinking_requested` desde UI, calcular `thinking_effective` en backend según compatibilidad del modelo y disponibilidad con herramientas; mostrar estado real ON/OFF/UNSUPPORTED, sin inventar una prueba de razonamiento interno. Test 5 fichas; modelo con/sin soporte; tool activa e inactiva; comparar solicitudes y telemetría real. |

## Cambios técnicos mínimos para Devin

1. **Evidence gate, sin nueva infraestructura:** en el camino de ejecución de herramientas del `puente_chat/plugin.py`, ligar cada afirmación de tool/lectura/escritura a los `tool_calls` y recibos reales ya retornados por `_chat`. Si una respuesta dice «ejecuté/consulté/encontré/delegué» sin respaldo real, el verificador la marca no comprobada y la respuesta no obtiene PASS. No introducir una segunda capa de herramientas.
2. **Identidad de proyectos:** en la entrada de ficha/backend, consultar el registro/estado existente de proyectos por `project_id` y sesión, no buscar primero un repositorio por coincidencia de nombre. Si no existe registro verificable, decir `NO_VERIFICADO`, no «no existe». Los adjuntos no se convierten en órdenes de crear repos.
3. **Adjuntos:** comprobar bytes/decodificación reales antes de afirmar «PNG truncado». Para OFF aplicar snapshot activo vacío a backend, eliminar chip activo, invalidar contexto cacheado y preservar historial como registro. No interpretar mensajes históricos como anexos activos.
4. **Recuperación:** el frontend no debe transformar timeout de HTTP/polling en estado `DONE`. Backend conserva y devuelve `pid`, `status`, `output_ref`, `cursor`, `last_receipt`; reintenta/retoma **el mismo** trabajo sin crear otro.
5. **Priorización de tokens:** ejecutar primero pruebas de continuidad en las cinco fichas; luego selector/thinking, luego loop/receipts, anclas y UI. Conservar límites efectivos por llamada del proveedor; no usar `null`, `0` o un número gigantesco como sinónimo de infinito.
6. **G17:** documentar valores DOM de input y salida **antes/después**; verificar 5× dentro de restricciones responsivas, no solo añadir `min-height` al historial.

## Contrato de pruebas de cierre

`CASO → REQUEST_ID/PID → ENTRADA_LITERAL_SHA → TOOL_EVENTS_REALES → RESULTADO_PERSISTIDO → VERIFICACIÓN → PASS/FAIL`.

Pruebas adversas obligatorias: (1) LLM inventa una lectura GitHub; (2) outputs contradictorios sobre el mismo proyecto; (3) PNG ilegible; (4) ancla ON→OFF→nuevo turno; (5) DONE sin texto pero con `output_ref`; (6) timeout con PID vivo; (7) output dos veces `length`; (8) loop reanudado tras reinicio; (9) reasoning pedido pero no soportado; (10) input y salida UI 5× medidos. **Sin test ejecutado no hay PASS.**

## Alcance

Los 18 GAPs previos siguen vigentes como inventario de trabajo. Este archivo **agrega condiciones de aceptación omitidas**; no implica que las causas de los errores o su reparación ya estén demostradas en producción. No inventar archivos o servicios. Reutilizar el código real del HEAD y aplicar el diff mínimo por GAP. **No se efectuó ninguna mutación remota.**

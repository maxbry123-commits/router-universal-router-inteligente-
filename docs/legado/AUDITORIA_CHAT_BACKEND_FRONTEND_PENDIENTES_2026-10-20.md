# Auditoría de pendientes — backend y frontend del chat (20-10-2026)

**Repositorio:** `maxbry123-commits/router-universal-router-inteligente-`. **Rama de trabajo real:** `reorganizacion` (la rama `main` de los enlaces antiguos no existe al realizar esta auditoría). **Alcance:** chat, cinco fichas Qwen y pasarela de agentes. **No se modificó Vercel ni se desplegó el Space.**

## Evidencia verificada en código

- Las fichas `fichas/fichas_qwen/fichas/ficha{1..5}*.json` ya poseen `dsl.tokens.max_output_tokens=8192`, `task_budget=10000000` y política `yaiwes_control_code_agent_v3.execution`. La política sola **no** elimina límites de proveedor ni prueba continuación efectiva.
- Fichas 1–4 tienen `motor.limite_llamada_chars=60000` y `fast_lane.max_output_tokens=500`. La ficha 5 utiliza `mvp.py`, sin DAG.
- El backend `fichas/fichas_qwen/plugin.py` ya persistía entrada >12k con SHA/readback; cuando el prompt sobrepasa el límite, devuelve GAP. No está demostrada la ingestión completa de segmentos por la LLM.
- `plugin.py` y `mvp.py` tienen `thinking_mode_resolver` en la pasarela; el frontend no propagaba `thinking_mode` por el envío principal, corregido en commits debajo.
- `api.js` usa PID para continuación pero devolvía salida vacía tras respuestas sin `estado`. Se corrigió el cliente, queda pendiente probar el proceso real.

## Cambios aplicados a la rama (código confirmado, prueba E2E pendiente)

1. **Think:** `plugins/chat-router/frontend/api.js` propaga `thinking_mode` estructurado; `panel-chat.js` envía ON/OFF cuando se elige la ficha Qwen/MVP. `fichas/fichas_qwen/plugin.py` evita enviar preguntas con Think explícito por FAST de 500 tokens. **Cuidado:** modelo con tools no verificado puede responder `GAP_THINKING_UNSUPPORTED` correctamente.
2. **Recuperación:** `api.js` retiene el PID si faltan estados repetidos, devuelve `GAP_RESULTADO_TEMPORALMENTE_VACIO`/reanudable y no declara el proceso terminado por transporte vacío; `RIU_RETOMAR` retiene PID ante errores de consulta sin estado terminal.
3. **Entrada íntegra:** `panel-chat.js` envía texto `rawText` de F2/F3/F5 y dentro del envoltorio de F1, y lo guarda/visualiza sin recortar espacios. `plugin.py` abandona FAST si supera `fast_lane.context_chars` en lugar de cortar el texto con `[:context_chars]`. Para output de los perfiles normal/Think, la UI solicita 4096/8192 tokens por llamada, **sujetos al proveedor**.
4. **Tamaño de ventana:** `plugins/chat-router/frontend/chat-espacio.css` amplía entrada hasta ~280px escritorio y ~200px móvil (capado por `dvh`) y conserva scroll independiente para la salida. **No puede garantizar 5x en input y output simultáneamente cuando el viewport es pequeño.**

## Pendientes extraídos del encargo (solo chat backend/frontend)

| ID | Área | Estado | Resolución concreta | Evidencia de cierre obligatoria |
| --- | --- | --- | --- | --- |
| B01 | Backend/fichas 1–5 — input >60k | **PENDIENTE** | Persistir bytes UTF-8+SHA antes de cortar ventana; consumir segmentos mediante orquestación/checkpoints en secuencia y reensamblado validado. `_fuente_integra_guardar` guarda, pero **no implica** que el modelo leyó todos los fragmentos. Nunca configurar tokens infinitos por llamada. | Caso Unicode 80k+, hash original=readback=reensamblado y recibo de cada segmento consumido. |
| B02 | Backend/fichas 1–5 — output y `finish_reason=length` | **PENDIENTE / PARCIAL PREEXISTENTE** | Persistir respuesta parcial, estado y cursor; detectar `length` y reanudar por llamada adicional con el mismo modelo y contexto mínimo; no duplicar escrituras. Proteger del límite real del proveedor. | Salida de 3+ segmentos, reanudación tras SSE cortado, ninguna tool mutante duplicada. |
| B03 | Backend — Loop CODA/timeout | **PENDIENTE** | Reutilizar scheduler y checkpoints actuales. Deadline por request/nodo no debe significar `DONE`; guardar `PENDING/RUNNING/RESUMABLE/BLOCKED/DONE` y reencolar trabajo autorizado. Respetar Stop del usuario, permisos, cuotas y watchdog de no progreso. | Tarea con 3 nodos, caída tras 1, retoma 2→3 una sola vez. |
| B04 | Backend — ejecución real de tools | **PENDIENTE** | En `puente_chat/plugin.py`, verificar `tool_call_id`, nombre, resultado, estado, duración y recibo antes de declarar lectura/escritura/completado. No aceptar afirmaciones simuladas del modelo. | Salida inventada → FAIL; llamada real con receipt → PASS. |
| B05 | Backend/fichas — Think por modelo y tools | **PARCHE APLICADO; E2E PENDIENTE** | Confirmar que el botón ON/OFF llega a cada proveedor, con `extra_llm` compatible y soporte con/sin herramientas. En no compatible, devolver GAP explícito. | Payload anonimizado y respuesta probada por proveedor/modo/herramientas. |
| B06 | Backend — `RESULTADO_VACIO`/`TIEMPO_TOTAL_AGOTADO` | **FRONTEND PARCHEADO; E2E PENDIENTE** | Verificar durabilidad de resultado y estado tras reinicio de worker; en RUNNING no dar DONE; en DONE vacío recuperar parcial o declarar DONE_EMPTY; nunca lanzar un segundo job al retomar mismo PID. | 8 polls vacíos, >560 s, reinicio y recuperación, sin duplicado. |
| B07 | Backend — identidad de proyectos | **PENDIENTE** | Resolver `project_id` en almacenamiento YAIWES/registro del chat antes de deducir existencia de un repositorio GitHub. `TASK_UNSPECIFIED` distinto de `PROJECT_NOT_FOUND`. | Tres casos: proyecto local, repositorio vinculado, ID desconocido. |
| B08 | Backend — memoria íntegra | **PENDIENTE** | Validar que resumen abreviado de `_hist_txt` no sustituye fuente original de 20+ mensajes; guardar historial íntegro por sesión y recuperar por ID/cursor. | Entradas y salidas extensas recuperadas byte a byte. |
| B09 | Backend — LOCK de agentes/tools | **PENDIENTE** | Verificar `_agent_lock_status(sesion)` en la entrada real de todas las herramientas/delegaciones; bloquear tools, no chat directo. | LOCK ON=0 tools, chat responde, OFF recupera. |
| F01 | Frontend — input sin recorte | **PARCHE APLICADO; E2E PENDIENTE** | `rawText` sustituye `trim()` en envío de F1/F2/F3/F5; probar que proxy/backend conserva caracteres. | Comparar SHA del textarea con el input recibido del backend. |
| F02 | Frontend — botón Think | **PARCHE APLICADO; E2E PENDIENTE** | UI → `harness()` → ficha → pasarela; debe mostrar estado efectivo, no solo token elegido. | ON/OFF en 1,2,3,4,5 y al activar/desactivar tools. |
| F03 | Frontend — ventanas 5× | **CSS APLICADO; MEDICIÓN PENDIENTE** | Capturas con ancho/alto DOM móvil/PC; corregir reglas conflictivas en `shell.css`/`chat-espacio.css`. Mantener Stop, teclado y scroll visibles. | Medir entradas ~5x del mínimo si el viewport lo permite y salida legible. |
| F04 | Frontend — imágenes desancladas | **PENDIENTE** | Emitir snapshot solo de anclas ON, `anclados:[]` incluso vacío y `active_anchors_v1`; invalidar caché/chip activo. **No borrar mensajes históricos** al desanclar. | ON→OFF→nuevo turno: cero archivo inyectado, chip desactivado, historial conservado. |
| F05 | Frontend — recuperación pendiente | **PARCHE PARCIAL; E2E PENDIENTE** | UI debe ofrecer reanudar por mismo PID al recibir `estado=reanudable`; conectar botones con `RIU_RETOMAR` y notificar que se conserva el trabajo. | 8 resultados vacíos y reanudar sin relanzar la tarea. |
| F06 | Frontend — carga de múltiples imágenes | **PENDIENTE** | Procesar 8/25/100/101 archivos en lotes; ACK/hash por archivo y paginación del listado. No alterar límite físico de almacenamiento por suposición. | Total de archivos enviado/recuperado=total autorizado, sin pérdidas ocultas. |
| QA01 | Integración del chat | **PENDIENTE** | Ejecutar pruebas de contrato existentes + negativas: herramientas simuladas, 80k Unicode, `finish_reason=length`, Think incompatible, OFF de anclas, retoma de PID; registro de SHA/commit/prueba. | PASS con recibos de herramientas y resultados E2E, no por texto de modelo. |

**Flujo prioritario:** `fichas 1–5 revisadas → conectividad Think/RAW/FAST parcheada → B01 → B02 → B03 → B04 → B06 → UI E2E → QA01`.

**Estado de publicación:** cambios confirmados en GitHub `reorganizacion`. **No** confirmado su despliegue en `comand-center-1-riu-router.hf.space` ni en el frontend Vercel; no tocar Vercel sin instrucción nueva. Sin evidencia E2E, no declarar 0 GAPs.

# README — Orquestador de modelos (fuentes y hallazgos)

Compendio del análisis aportado por Claude (INPUT 125 + tabla de fuentes) y los hallazgos verificados en vivo por Devin. Rama: `feat/modos-router`.

## 1. Principio central (Qwen, DeepSeek, GLM — los tres igual)
El modelo **propone** la tool_call; la **aplicación** la ejecuta. `tool_calls=[]` + texto "Entendido" es respuesta válida en `tool_choice=auto` — no es ejecución. `tool_choice="required"` no es garantía fiable en Qwen.

## 2. Contrato de éxito estructural
```
ÉXITO = tool solicitado + permitido + despachado + terminado + receipt verificable
if (task.executionRequired && result.executedTools.length === 0) -> RETRYABLE_NO_EXECUTION
```
El regex de ACK sirve para diagnóstico, NO como criterio de integridad.

## 3. Las 7 categorías de fallo (antes colapsadas en HERRAMIENTA_NO_EJECUTADA)
`ACK_ONLY` · `NO_TOOL_DECISION` · `TOOL_IN_REASONING` · `TOOL_PARSE_FAILURE` · `TOOL_DISPATCH_FAILURE` · `TOOL_EXECUTION_FAILURE` · `TOOL_EXECUTED`
Cada una exige un retry distinto (ver §5).

## 4. Matriz por modelo (hallazgos verificados)
| Modelo | Comportamiento real observado | Causa raíz |
|---|---|---|
| glm52 | Ejecuta con evidencia (intermitente) | layout B ayuda; thinking no es el problema |
| qwen38max | Ejecuta con evidencia real (HTTP 200, tool_calls) | estable con prompt corto imperativo |
| qwen36flash | Ejecuta (lento, salida parcial) | ok |
| qwen38flash | Ejecuta con prompt ultra-corto | prompt largo -> texto plano (issue #236 Qwen3.8) |
| dsv4flash | Acusa / timeout | `reasoning_effort:'high'` en perfiles.py -> tools en reasoning, nunca despachan (issue #6548 Qwen Code + DeepSeek V4) |
| dsv4pro | Acusa / salida vacía | misma causa: thinking 'high' forzado |
- DeepSeek V4: thinking activo por defecto; Qwen Code lo desactiva con `thinking:{type:'disabled'}`. DeepSeek soporta tool use con thinking, pero NO insertar tool_calls no generados en el historial -> retry = nuevo intento legítimo con D_solo_tarea, no falsificar el ACK.
- GLM 5.2 vía Qianwen puede requerir `extra_body={"tool_stream": True}` para producir tool_calls (GLM-5.3 la excepción).
- Streaming Qwen: `delta.tool_calls` hay que concatenarlos por index antes de parsear (nombre y arguments llegan en chunks distintos); un adapter que lee solo el último chunk concluye "sin herramienta" en falso.

## 5. Árbol de fallback recomendado
```
TASK
 ├─ ¿requiere ejecución real? no -> respuesta textual permitida
 ├─ intento inicial
 ├─ ¿tool receipt real? sí -> PASS
 ├─ clasificar fallo
 │   ├─ ACK / NO_TOOL      -> retry con D_solo_tarea
 │   ├─ TOOL_IN_REASONING / PARSE_ERROR -> parser/adapter fallback
 │   ├─ HTTP temporal      -> retry técnico
 │   ├─ tool timeout tras dispatch -> verificar idempotencia/estado antes de repetir
 │   └─ segundo fallo      -> model fallback o FAIL explícito
```
Timeout de red NO prueba que una escritura no se ejecutó -> idempotency keys / check de estado antes de reintentar escrituras.

## 6. Tres capas (no sustituibles entre sí)
- layout B -> mejora la instrucción (gobernanza->system, tarea etiquetada->user)
- D_solo_tarea -> reduce interferencia contextual
- executor determinista (`run_node_with_execution_contract`) -> garantiza que respuesta sin ejecución NO se acepta

## 7. Estado aplicado hoy
- prompt_layouts.py + test (7/7 OK) copiados verbatim de Claude en `plugins/fichas_qwen/modos/`
- Parche quirúrgico: gobernanza(rol+ctx)->system, tarea etiquetada->user (línea ~1356 plugin.py), sys_prompt via opts por nodo
- Detector ACK + reintento layout D por nodo (S4)
- Desplegado en el Space; prueba A/B real: antes "entendido", después ejecución con evidencia (PASS línea 28 loop_run)
- `validate_contract.py --exclude ID` (fix §6 ADICIONALES) aplicado

## 8. Executor con contrato de ejecución (INPUT 126, diseño de Claude)
- `classifyResult`: toolExecutions completados => SUCCESS (receipt gana sobre texto). Sin calls + regex ACK => ACK_ONLY. Sin calls pero rawText contiene `<tool_call>|"tool_calls"|function_call` => TOOL_IN_REASONING. Sin calls => NO_TOOL. Calls sin receipt => PARSE_FAILURE.
- Retry reconstruye el prompt entero (no append "continúa" sobre el ACK): SYSTEM ejecutor + tools mínimas + USER tarea sola.
- Routing por nodo: glm52/qwen38max/qwen36/qwen38flash => layout B; **dsv4flash/dsv4pro => D_solo_tarea directo** + thinking toggle en matriz (evita pagar latencia de un B ya sabido malo).
- **Tres relojes**: NODE_TOTAL_DEADLINE (150s sin retry; mayor calibrado P95 con retry) + ATTEMPT_TIMEOUT por intento + TOOL_EXECUTION_TIMEOUT. Deadline dinámico: `attempt_timeout = min(config, deadline - now - reserve)`. Un ACK detectado se reintenta al instante, no espera al tope.
- Timeout de configuración ejemplo dsv4flash: total 205s, 2×D (95s, thinking off → on), reserve 15s.
- **Fix GitHub >1MB**: Contents API devuelve `git_url`/SHA/`download_url` → para archivos grandes usar raw media / download_url / Git Blob por SHA en vez de JSON/base64 (hoy trunca en ~INPUT 022 del fichero de instrucciones).

## 9. Plan P0-P3 de Claude (INPUT 127)
- **P0**: predicate de éxito = receipt real (execution_required && receipts==0 -> no PASS); run_with_fallback determinista; timeout por intento + deadline total; clasificar ACK al finish_reason; GitHub raw/blob para >1MB (contents API trunca a 1MB exactamente).
- **P1**: D_solo_tarea + tools mínimas (allowed_actions directo, no 50 residentes + "usa estas 8"); telemetría raw→parser→dispatch→receipt; thinking por modelo (hecho: dsv4 toggle deployado); tool_stream=True en GLM 5.2 vía Qwen (verificar).
- **P2**: named tool_choice donde compatible (capability matrix por modelo, no `required` universal); DeepSeek strict; fallback de modelo dsv4→qwen38max/glm52; circuit breaker; idempotency keys para escrituras.
- **P3**: suite permanente 10-30 ejecuciones por combinación; métricas execution_success_rate, ack_only_rate, tool_in_reasoning_rate, fallback_recovery_rate, p50/p95/p99.
- Chunking local en el propio tool: fetch raw → indexar → devolver sólo regiones (mejor que mandar 1.1MB al LLM).
- Estado EXECUTION_STATE_UNKNOWN cuando tool_call llegó y dispatch empezó sin confirmación — distinto de NO_TOOL.
- Escrituras: retry solo con idempotencia / verificación de estado tras timeout.

## 10. INPUT 129 — Soluciones A-E de Claude y su estado REAL en el código
- **A — Parser XML→JSON de Qwen**: YA EXISTE — `_calls_texto()` en puente_chat/plugin.py:785 recupera `<tool_call><function=X><parameter=Y>`, `<invoke>` y JSON suelto; aplicado sobre content (L995) y reasoning_content (L997, según política buscar_tool_calls_en). No requiere cambio.
- **B — quitar tool_choice=required con thinking**: YA OK — el código solo usa `tool_choice:'auto'` (puente_chat L648); nunca manda required. Nada que sanear.
- **C — herramientas no diferidas (shouldDefer)**: N/A — el registry del router no difiere herramientas; el catálogo se envía entero según cap_nodo.
- **D — re-inyectar reasoning_content (DeepSeek V4)**: YA EXISTE — L1013-1016 conserva reasoning_content en el assistant con tool_calls cuando la política lo pide; las fichas dsv4 ya declaran `conservar_reasoning_content_con_tools: true`.
- **run_with_fallback + timeout por intento**: APLICADO — detector ack + retry layout D + fallback de modelo (F) + `_per_attempt_s` = 50% del tope del nodo (75s de 150s).
- **GLM tool_stream=True**: PENDIENTE VERIFICAR — soportado en _extras (L525-526) via `con_tools.tool_stream`; la ficha glm52 lo deja en false por nota. Solo activarlo si aparece ReadTimeout>30s de api.z.ai.
- **Telemetría ack por nodo**: PARCIAL — `layout_attempts` registra cada intento (nodo, layout, modelo, ack, why); falta contador persistente MODELO_NO_TOOL_CAPABLE tras 3 acks (exec_dispatch.Profile lo cubre cuando se cablee completo).
- Solución E (npm xml-toolcall/pi-qwen-fix): no aplica, el parser propio ya cubre los 3 formatos.

## lectura_archivo_grande (nota operativa, antes vivia en fichas JSON — DSL N5 la saca de config)
GitHub API trunca lecturas >1MB: leer archivos grandes por rangos/partes, no una sola llamada.

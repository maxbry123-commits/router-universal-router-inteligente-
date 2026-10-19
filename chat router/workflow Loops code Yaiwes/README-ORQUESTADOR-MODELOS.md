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

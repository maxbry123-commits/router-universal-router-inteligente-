# Prueba 02 — Groq, 500 líneas Python | GAP real por MCP

**Rama:** main · **Ruta de chat:** conector MCP existente `chat → resultado`; no se creó otro puente.

## Pruebas realizadas desde el chat YAIWES

| Prueba | Modelo | max_tokens | Proceso | Resultado |
|---|---|---:|---|---|
| Salida de 500 líneas, JSONL/CLI | groq/qwen/qwen3.8-27b | 6500 | `p-test-groq-500lineas-20261103-v1` | **GAP**: `PROVEEDOR_GROQ_HTTP_429: limite_temporal`; presupuesto acumulado 120 s, error 504 |
| Salida compacta de 500 líneas | groq/qwen/qwen3.8-27b | 3300 | `p-groq-500-lines-compact-v2-20261103` | **GAP**: HTTP 429; agotó los reintentos/120 s |
| Control corto de 80 líneas | groq/qwen/qwen3.8-27b | 800 | `p-groq-80-lines-calibration-20261103-v1` | **GAP**: 429 temporal y 503 temporal, resultado final 504 |
| Sonda corta anterior | groq/qwen/qwen3.8-27b | 160 | `p-prueba-mcp-groq-20261103-1` | **PASS**: `GROQ_MCP_PRUEBA_1_OK`, `finish_reason=stop`, 0.6971 s |

No hay 500 líneas generadas en la respuesta completa: **no se publicó código inventado, incompleto ni de otra IA**. No existe commit válido del modelo de 500 líneas que se pueda auditar.

## Diagnóstico OpenClaw mediante el mismo MCP

- `@swen/ocroute` con `chat(ficha_qwen=swen-code-free)`: `/openclaw/v1/models=200`, `/health=200`, `/v1/models=404` (el gateway usa la ruta prefijada).
- `@swen/occonfig`: `chat_completions_habilitado=true`, `openclaw_enable=true`, `gateway_token_configurado=true`, agentes registrados true.
- **Verificado:** configuración y rutas del Gateway accesibles desde MCP. **NO verificado:** hacer clic/escribir/mostrar las 500 líneas en la interfaz navegador de OpenClaw. Este conector no ofrece control del DOM ni sesión del navegador; no confundir diagnóstico de gateway con prueba de interfaz.

## Cierre

**Estado: GAP BLOQUEANTE** del proveedor Groq para tareas largas. No se pasa al siguiente modelo hasta registrar el fallo y verificar su recuperación. Con 500 líneas pendientes, revisar ventana de cuota/rate limit y reintentos; no ajustar frontend sin evidencia ni crear otros puentes.

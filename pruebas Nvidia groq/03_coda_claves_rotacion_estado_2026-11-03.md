# 03 — CODA 500 líneas · Auditoría de claves Groq/NVIDIA (2026-11-03)

## Ruta real probada
- **YAIWES:** MCP existente `chat(ficha_qwen="1") → resultado`; no puente nuevo.
- **OpenClaw (provider):** mismo MCP existente `chat(ficha_qwen="swen-code-free")` → ruta backend SWE web-bridge, `origen=openclaw`, Groq seleccionado explícitamente. **No es prueba de clics/DOM de la UI visual.**
- Todo el código se mantiene dentro de la organización actual de GitHub en `main`; no se modificó Hugging Face directamente ni se creó infraestructura.

## Evidencia de llamadas reales
1. YAIWES / Groq: `p-groq-claves-coda-audit-final-v2` → **PASS** respuesta exacta `GROQ_CLAVES_AUDIT_OK`; `finish_reason=stop`; ~0,586 s.
2. OpenClaw provider / Groq: `swen_4b5949f750b44a719f5f2beeea05c7e3` → **PASS** respuesta exacta `OPENCLAW_GROQ_MCP_OK`; modelo solicitado/usado `groq/qwen/qwen3.8-27b`; sin tool_calls.
3. YAIWES / Groq / 500 líneas: `p-groq-coda-500-verificacion-20261103-v1` → **GAP** final `CODA_MODELO_SIN_TEXTO_FINISH_REASON_length` después de **12/500** líneas estáticas verificadas. No existe salida completa ni commit de 500 líneas.
4. NVIDIA MiniMax Flash anterior: `p-coda-nvidia-500-test-20261103-c3` → **GAP** tras **49/500** líneas verificadas; un segmento devolvió texto vacío.
5. **Sin prueba de 500 líneas completa** ni para Groq, ni NVIDIA ni la interfaz gráfica OpenClaw. No marcar PASS.

## Gaps y medidas aplicadas en código
- Pool Groq/NVIDIA: claves deduplicadas del banco y entorno, rotación en 429 a la siguiente clave del mismo modelo. Se añadieron contadores seguros `credenciales.configuradas`, `probadas`, `rotaciones`, `errores_http`, `retry_after_s`; el Harness ya no los elimina del resultado, y los errores tipados del proveedor transportan estos campos. **No incluyen secretos ni huellas.**
- `Retry-After`: el transporte lo respeta y el bucle CODA toma el máximo entre la pausa fija y el `retry_after_s` del proveedor hasta 600s.
- Código largo: partes de hasta 50 líneas, checkpoint persistente con SHA/input, reducción adaptativa del tamaño de bloque tras respuestas vacías, AST/compile y validación del total antes de PASS.
- El fallo real Groq es `finish_reason=length` con texto vacío (tokens gastados en razonamiento). Se cambió **solo en generación CODA de Groq** a `reasoning_effort=none` (soportado por el modelo), manteniendo el ajuste normal del chat para otras tareas. **Pendiente verificación real tras despliegue de este commit.**
- OpenClaw: el conector MCP existente acepta Groq/NVIDIA y usa el provider original, mismo Router `chat_async/resultado` y checkpoint. Los tests unitarios del bridge prueban la ruta con stub, pero no son pruebas de proveedor real.

## Commits principales
- `9168d6a9e5`: auditoría y conteo anónimo en transporte.
- `0977c48324`: propagar conteos seguros en errores de Router.
- `649988db46`: segmentos adaptativos + Retry-After.
- `16b10e061c`: MCP de OpenClaw acepta proveedor Groq/NVIDIA por bridge existente.
- `ff736db37b`, `c4e04b80d1`: pruebas deterministas de rotación, Retry-After, respuesta vacía.
- `f0f9ab59d5`: el Harness permite la métrica segura.
- `6166cb1d6d`, `e34f87d827`: pruebas del Harness y error 429 tipado.
- `b14d95f0a5`: diagnóstico de recuento de claves configuradas, no necesariamente válidas.
- `96a4482fda`: comando MCP de ejecución de pruebas fijas `@swen/codatest`.
- `5b5fcc26e3`: Groq CODA desactiva reasoning para evitar `content="" / finish_reason=length`.

## Pendiente para cerrar
- Verificar que el commit de `main` esté **activo** en `/health`; el autopull puede diferir reinicios mientras hay tareas.
- Ejecutar por el **mismo MCP** `@swen/claves` para conocer números reales de claves; `@swen/codatest` para ejecutar pruebas deterministas; no inferir estos números.
- Repetir 500 líneas con Groq después de desplegar `5b5fcc26e3`, inspeccionar cada segmento, AST y SHA; luego repetir con MiniMax NVIDIA y OpenClaw provider.
- No saltar a otro modelo sin revisar el resultado del primero. Evitar llamadas excesivas a una organización con cuota compartida.

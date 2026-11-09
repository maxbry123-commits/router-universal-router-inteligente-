# Contrato del Harness DeepSeek

Fuente: `chat-router/chat/backend/deepseek_harness/server.py` (rutas en líneas ~689 a 1014). Este documento describe el código; no define comportamiento nuevo.

## Autenticación

- Cabecera: `X-API-Key`.
- Valor esperado: variable de entorno `RIU_API_KEY`. Comparación con `hmac.compare_digest`.
- Sin `RIU_API_KEY` configurada, o clave incorrecta: respuesta `401` con `{"status": "error", "error": "clave de acceso invalida"}`.
- Ninguna clave se escribe en archivos ni en respuestas.

## Sobre de respuesta

- Éxito: `{"status": "ok", "result": <dato>}`.
- Error: `{"status": "error", "error": "<mensaje>"}`. El código de HTTP es `200` por defecto; `401`, `400`, `404` y `503` solo en los casos que lo indican el código.

## Rutas

| Método | Ruta | Acción |
|---|---|---|
| POST | `/invoke` | Cuerpo `{"action": "status" \| "invoke" \| "llm", ...}`. Ver abajo |
| GET | `/modelos/v1/models` | Lista de modelos |
| GET | `/modelos/v1/disponibilidad` | Disponibilidad de modelos |
| POST | `/modelos/v1/chat/completions` | Chat compatible con OpenAI |
| POST | `/credenciales/{accion}` | Gestión de credenciales (`404` si la acción no está permitida; `503` si el banco no está disponible) |

### `/invoke`

- `action: "status"`: devuelve `{"servicio": "deepseek_harness", "acciones": ["status", "invoke", "llm"], "swe": ...}`.
- `action: "invoke"`: ejecuta la herramienta `tool` del diccionario `HERRAMIENTAS`. Si `tool` no está permitida, responde `tool no permitida`. `args` debe ser un objeto; si no lo es, se usa `{}`.
- `action: "llm"`: llama a `llm(cuerpo)`.
- Otra acción: `accion no permitida`.
- Excepciones `ValueError` y `RuntimeError` se devuelven como error con su mensaje. Cualquier otra excepción se devuelve como error con solo el nombre del tipo.

## Variables de entorno usadas

- `RIU_API_KEY`: clave de acceso del harness.
- `BRIDGE_TOKEN`: token del puente.
- `PORT`: puerto de escucha.
- `RIU_ROUTER_URL`: URL del router.
- `RIU_SWE_BRIDGE_URL`: URL del puente SWE.
- `RIU_SWE_TIMEOUT_S`: timeout del puente SWE (por defecto 450 s).
- `RIU_SWE_LOCAL_MODELO`, `RIU_CONTEXTO_MAX_CHARS`, `RIU_HARNESS_PAUSA_S`: parámetros de ejecución.

## No incluido

Los nombres `AGENT_HARNESS_URL`, `MCP_MEMORY_URL` y un endpoint `/health` no aparecen en el código del harness. No se documentan aquí.

## Pendiente

- Los timeouts por herramienta no están declarados en un solo lugar. Solo se conoce el del puente SWE.
- La lista exacta de herramientas de `HERRAMIENTAS` debe extraerse del código en una pasada propia.

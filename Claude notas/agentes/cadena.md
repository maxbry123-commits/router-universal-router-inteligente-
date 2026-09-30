# Agente cadena (Bloque 3, Paso 2) - 2026-09-30
Rama: bloque3-cadena (desde main 3c512e4).

## Hecho
- Las cadenas (default, code, minor, g2) viven ahora en `integration/chat_mvp/policies.json`. `resilience.py` las lee al arrancar; si el archivo falta, es JSON invalido o un grupo es invalido, usa el diccionario en codigo (`CODE_POLICY`) y el Router no cae. `DEFAULT_POLICY` sigue existiendo (mismo nombre, mismo uso en route_api y tests).
- Grupo nuevo `chat_nvidia` (chat, Hermes, OpenClaw): Kimi K3 (nvidia) -> GLM 5.3 (nvidia) -> DeepSeek V4 Flash (hf, deepseek:true, se salta en horas pico 01-04 y 06-10 UTC L-V) -> Groq qwen/qwen3.8-27b como cola de emergencia. SIN Nemotron. Cada opcion tiene `timeout: 90` propio en el JSON (no usa la base de 30 s de los otros grupos; tope prov.CHAT_TIMEOUT).
- Grupo `sdk` vacio (lista pendiente del Director): responde ROUTER_NO_ROUTE_AVAILABLE, no rompe nada.
- `/chat/route` ya acepta `chat_nvidia` sin tocar route_api.py ni model_pool.py (toman los grupos de DEFAULT_POLICY). Cooldown 120 s y horas pico sin cambios.
- Los otros grupos no cambian de comportamiento.

## Pruebas
- `tests/test_policy_config.py` (nuevo, 9 tests): carga del JSON, orden/timeouts de chat_nvidia, sin Nemotron, JSON faltante/invalido, grupo invalido, pico DeepSeek, 90 s por opcion frente a base 5 s, grupo default conserva base, sdk vacio.
- Resultado real (maquina temporal, python3, pytest): test_policy_config + test_resilience + test_model_pool = 48 passed, 8 skipped.
- El CI de GitHub (workflow `tmp-cadena-verify.yml`) NO corrio: "The job was not started because your account is locked due to a billing issue". tests/test_resilience_c10.py prueba engine/resilience.py (otro archivo), no se ejecuto.

## Pendiente / bloqueado
- Bloqueado: GitHub Actions por facturacion de la cuenta.
- Pendiente: lista del grupo `sdk` (Director). No existe grupo `assistants` en main (solo en la rama bloque2), no se anadio.
- El workflow temporal tmp-cadena-verify.yml se puede borrar al cerrar.
- Nota: clonar el repo entero en la maquina temporal pesa ~7 GB y mata la maquina; usar la API de contenidos.

# Handoff: selector unificado y registro de credenciales API/SDK

## Alcance
- Solo `chat-router/`, rama `main`. Las fichas, motor de agentes, OpenClaw independiente, Hugging Face y banco persistente no se modifican manualmente.
- Selector ya existente `chat/frontend/selector-modelos.js`: una sola lista de modelos locales HF, Groq y NVIDIA; elegir cambia el selector ACTIVO y conserva el mismo ID de extremo a extremo. Los modelos sin consulta al catálogo dicen `Sin verificar`, nunca `Disponible` sin prueba.
- Botón `+ API / SDK`: reutiliza `chat/frontend/ventana-claves.js` (el panel actual de Configuración), no duplica formulario ni guarda valores en navegador.
- Ruta de CONTROL, sin modelo LLM: **Chat UI → Harness DeepSeek POST /plugins/deepseek_harness/credenciales/{catalogo,anadir} → HTTP → Router MVP plugin banco_proveedores → HTTP local → SWE CODE /v1/credenciales → banco cifrado existente → mirror cifrado en rama banco-claves de GitHub**. El Harness actúa solo de relé autenticado: jamás expone claves a la IA, prompts, herramientas, logs ni historial.
- Claves con prefijo `gsk_` / `nvapi-`: clasificación automática Groq / NVIDIA. Para tokens sin prefijo reconocible, elegir proveedor en el desplegable. `+ Añadir` SUMA claves sin reemplazar ni borrar las anteriores.
- Otros proveedores / SDK: se guardan por un nombre identificador en el mismo banco. **Estado: registrados, NO operativos para inferencia sin un adaptador compatible**. Ningún sistema puede deducir protocolo, URL y modelo solamente con una clave arbitraria. Esta distinción es explícita en la UI.
- Acceso exclusivamente por `X-API-Key` autenticada, validaciones de longitud y proveedor en las tres capas; jamás enviar claves en query params, localStorage, archivos JS o Github main.

## Pendiente de verificación operativa
1. Confirmar que el Space actual hizo autopull del SHA publicado desde GitHub, que levanta Router MVP :7861, bridge :7870 y proxy existente :7860; no tocar el Space.
2. Desde la interfaz abrir **Selector de modelos** y verificar los 4 NVIDIA, Groq y 4 locales HF. Probar `+ API / SDK` y ver solo conteos, no el valor.
3. Comprobar la escritura cifrada y el mirror en `banco-claves` (sin leer ni revelar el archivo ni sus valores).
4. Probar una respuesta real de un modelo Groq, NVIDIA y HF local en YAIWES y OpenClaw. No declarar DONE hasta pruebas PASS.
5. Ejecutar los tests agregados: `chat/backend/deepseek_harness/test_provider_keys_relay.py`, `chat/backend/mvp/test_proveedor_claves.py`, `SWE CODE/web-bridge/test/test_claves_banco_auto.py`, `chat/frontend/test/selector-api-sdk.test.mjs`.

## Estado actual
Código publicado, sin verificación live de secretos/inferencia. No se han editado agentes.

## Extensión DeepSeek / MiniMax / OpenAI (2026-11-01)
- Estudiadas las configuraciones oficiales de OpenClaw, API de DeepSeek, MiniMax y OpenAI. Reutilizamos el adaptador `openai-completions` del bridge existente, no copiamos librerías ajenas ni creamos un nuevo servidor.
- Base URL fija y autenticación Bearer desde el banco cifrado:
  - `deepseek`: `https://api.deepseek.com`; `deepseek/deepseek-v4-pro`, `deepseek/deepseek-flash`.
  - `minimax`: `https://api.minimax.io/v1`; `minimax/MiniMax-M3`, `minimax/MiniMax-M2.7`. Es compatible con API Chat Completions, aunque OpenClaw recomienda su transporte Anthropic-native para algunas funciones avanzadas.
  - `openai`: `https://api.openai.com/v1`; `openai/gpt-5.6`, `openai/gpt-5.5`.
- Los tres usan `DEEPSEEK_API_KEY`, `MINIMAX_API_KEY` y `OPENAI_API_KEY` (y variantes indexadas) a través de `claves_banco.py`, `clavesbanco.js`, `respaldo.js` y `mvp.externos`. No se almacenan en GitHub main ni en el navegador.
- El control de claves es `/plugins/deepseek_harness/credenciales/anadir` → `/plugins/banco_proveedores/call/anadir` → `http://127.0.0.1:7870/v1/credenciales`. Autentica con las mismas claves de acceso del Chat (no con claves de los modelos).
- Inferencia: YAIWES por el mismo bridge y Router MVP; OpenClaw por `/openclaw/v1/chat/completions`. Ambos exponen el mismo identificador y no sustituyen silenciosamente el modelo elegido. La disponibilidad real requiere clave y `GET /models`; `SIN VERIFICAR` no equivale a `DISPONIBLE`.
- El selector único de modelos añade 6 entradas a las 9 existentes; + API/SDK reutiliza la ventana de claves con proveedor explícito. Los prefijos `sk-...` no permiten deducir correctamente si la clave es OpenAI, DeepSeek o MiniMax, por eso el usuario selecciona su proveedor.
- Un SDK ajeno sin protocolo compatible puede registrar el secreto, pero **no** se afirma que sea ejecutable: necesita un adaptador específico.

### Fuentes técnicas
- https://docs.openclaw.ai/concepts/model-providers/official-provider-plugins
- https://docs.openclaw.ai/minimax
- https://api-docs.deepseek.com/quick_start/agent_integrations/
- https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create

### Verificaciones pendientes
- Los módulos JS modificados `respaldo.js`, `server.js`, `clavesbanco.js`, `selector-modelos.js`, `swe-directo.js` y `ventana-claves.js` pasaron inspección de sintaxis V8 al retirar las declaraciones ESM de import/export (no es una prueba de ejecución).
- Pruebas mock incorporadas: `SWE CODE/web-bridge/test/otros_proveedores.test.mjs`, `chat/backend/mvp/test_externos_multi_api.py`, y cruces de catálogo OpenClaw/YAIWES.
- No se ejecutaron inferencias reales, ni se inspeccionaron secretos de usuario. No certificar el despliegue hasta obtener respuesta real para cada proveedor y ambos chats.

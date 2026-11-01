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

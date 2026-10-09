# Selector Qwen: pendientes para la ficha/plugin (Claude)

Estado: el **Selector Qwen** es solo frontend (`chat-selector-modelos.js`, pastilla `#sel-nuevo`, hoja `#sh-modelos`).
No llama al Router y no envía nada. El selector de ficha `modelo ▾` sigue igual.

## Gancho que deja el frontend
- Evento `window` **`riu:selector-qwen`**, `detail = { modelo_id_slug, label, grupo, sesion }` (o `null` si se deselecciona).
- `window.RIU_SELECTOR_QWEN = { enviar: null, seleccion, modelos }`.
  - `enviar`: lo rellena la ficha/plugin: `async ({ modelo_id_slug, mensaje, sesion }) => respuesta`.
  - Mientras `enviar === null`, el chat sigue por la ficha del chat (harness), igual que hoy.
- Los `modelo_id_slug` son nombres de interfaz (`qwen-3-8-max`…), **no** son ids de proveedor.

## Modelos

| Modelo (slug) | Grupo | Frontend | ID de proveedor |
|---|---|---|---|
| 🧠 Qwen 3.8 Max (`qwen-3-8-max`) | Código y razonamiento | hecho | ID por confirmar |
| ⚡ Qwen 3.8 Flash (`qwen-3-8-flash`) | Código y razonamiento | hecho | ID por confirmar |
| 🧠 Qwen 3.7 Max (`qwen-3-7-max`) | Código y razonamiento | hecho | ID por confirmar |
| ⚡ Qwen 3.7 Plus (`qwen-3-7-plus`) | Código y razonamiento | hecho | ID por confirmar |
| 🚀 Qwen 3.6 Flash (`qwen-3-6-flash`) | Código y razonamiento | hecho | ID por confirmar |
| 🧠 DeepSeek V4 Pro (`deepseek-v4-pro`) | Código y razonamiento | hecho | ID por confirmar (en `/chat/providers/hf/models` aparece `deepseek-ai/DeepSeek-V4-Pro`) |
| 🧠 DeepSeek V4 Pro 0813 (`deepseek-v4-pro-0813`) | Código y razonamiento | hecho | ID por confirmar (aparece `deepseek-ai/DeepSeek-V4-Pro-0813` en hf) |
| ⚡ DeepSeek V4 Flash (`deepseek-v4-flash`) | Código y razonamiento | hecho | ID por confirmar (aparece `deepseek-ai/DeepSeek-V4-Flash` en hf) |
| 🧠 GLM 5.2 (`glm-5-2`) | Código y razonamiento | hecho | ID por confirmar (el Router solo tiene GLM 5.3) |
| 🎨 Qwen Image 3.0 Pro (`qwen-image-3-0-pro`) | Imágenes | hecho | ID por confirmar |
| 🎨 Wan 2.7 Image (`wan-2-7-image`) | Imágenes | hecho | ID por confirmar |
| 🔊 Qwen TTS (`qwen-tts`) | Modo recepción | hecho | ID por confirmar |
| 🎙️ Qwen Realtime (`qwen-realtime`) | Modo recepción | hecho | ID por confirmar |
| 📝 Qwen ASR (`qwen-asr`) | Modo recepción | hecho | ID por confirmar |

## Botones

| Botón | Hecho sin backend | Necesita ficha/backend |
|---|---|---|
| Pastillas `modelo ▾`, `⚖ equilibrado ▾`, `⚙ más ▾`, `⚓ ancla ▾`, `⬇ motor ▾` | Solo estilo Grok | No: la función no cambió |
| Círculos 📎 🗂 🧪 ⧉ ⏹ | Solo estilo Grok | No: la función no cambió |
| Enviar | Píldora azul de marca | Solo si se usa el Selector Qwen (punto 4 abajo) |
| Agentes / Router / Emergencia / Respaldo | Estilo: gris; encendido en azul | No: la función no cambió |
| ✦ Selector Qwen + filas | Elegir, ✓ azul, evento, estado por chat | Sí: ficha + plugin para responder |

## Tareas para Claude
1. Confirmar proveedor, endpoint y **model id exacto** de cada uno de los 14 modelos. El Router hoy no tiene proveedor Qwen/DashScope: `providers` muestra nvidia, hf y groq; `deepseek` aparece con `configured:false`.
2. Crear una ficha por modelo, `modelo-<slug>.json`, en `router inteligente universal/plugins/puente_chat/fichas/`, con el mismo formato que las existentes (`id`, `nombre`, `tipo`, `proveedor`, `modelo`, `timeout_s`). Los ids deben coincidir con los `modelo_id_slug` o con una tabla de mapeo.
3. `puente_chat/plugin.py`: las fichas `modelo-*.json` con `tipo:"api"` ya se cargan solas en `FICHAS`. Si el proveedor es nuevo (Qwen/DashScope, voz o imagen), hay que añadirlo en `_api`/`_llamar_api` y poner su clave en el banco/vault. No poner claves en el repo.
4. Gancho del harness en el frontend: un módulo nuevo escucha `riu:selector-qwen` y rellena `window.RIU_SELECTOR_QWEN.enviar` con la llamada a `puente_chat/chat_async` (`model` = id de la ficha). En `panel-chat.js` hay que añadir 1 línea en el envío: si `enviar` existe y el chat tiene `selectorQwen`, usarlo.
5. Imágenes (Qwen Image 3.0 Pro, Wan 2.7 Image): crear una acción del plugin que devuelva la imagen (`/chat/media/{id}` o base64) y su render en el chat.
6. Modo recepción (voz):
   - TTS: endpoint de texto a audio y reproducción en el chat.
   - ASR: subida de audio desde el micrófono (permiso del navegador) para pasarlo a texto.
   - Realtime: WebSocket/stream de voz en vivo. Requiere decidir si el Router hace de proxy.
7. Probar en vivo cada modelo con una respuesta real (NO MOCK) antes de cerrar.

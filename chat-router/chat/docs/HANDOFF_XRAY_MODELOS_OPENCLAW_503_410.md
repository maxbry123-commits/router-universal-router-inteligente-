# X-Ray: Modelos únicos, salida única, HF 503, GLM 410 y OpenClaw

Fecha: 2026-11-01/02. Fuente de código: GitHub `main`. Restricción: no tocar Hugging Face, no alterar agentes ni crear infraestructura.

## Evidencia del Director (capturas)
- YAIWES **NVIDIA MiniMax M3.1 Flash, Muse Glimmer y Nemotron 3 Ultra**: el Director observó respuestas reales. La app añadía un segundo globo `SWE · <modelo> · respondió nvidia` que no era otra inferencia, sino una **nota de procedencia**.
- YAIWES **Groq**: el Director observó una respuesta real; estado no está certificado para todos los modelos.
- **NVIDIA GLM-5.3**: `EXTERNO_NVIDIA HTTP 410` devuelto por el proveedor/endpoint. La documentación oficial mantiene el ID `z-ai/glm-5.3`: no reemplazar por otro modelo o API de forma silenciosa. La corrección del `410 Gone` depende de comprobar derechos de la clave, respuesta y catálogo con el servicio real; esta sesión no accede a esos secretos.
- **Locales HF**: `HF_LOCAL_FALLO: S1: HTTP 503 | S2: HTTP 503 | S3: HTTP 503`. Los tres servidores responden indisponibilidad (según capturas). Una URL configurada no significa que el modelo esté cargado; el frontend y el bridge NO pueden cargar servidores detenidos desde el Router.
- **SWEN CODE free/web**: `GAP: network error`. Diagnosticar browser Playwright/credenciales web; separado de API.
- **OpenClaw**: `Couldn't sign in to the AI service`; catálogo SWE Code marcado `No disponible`. Auditoría solo-lectura del archivo raíz del Space `swecode_provider.json`: `baseUrl=http://127.0.0.1:7860/v1`, `apiKey=local`, IDs antiguos. Esos valores NO coinciden con las credenciales y rutas del bridge autenticado actual.

## Correcciones GitHub
1. `chat/frontend/selector-modelos.css`: oculta únicamente las filas modelo Groq y NVIDIA heredadas dentro de la misma hoja de selección, y el segundo indicador interno. Conserva su estado y cableado sin mover agentes.
2. `chat/frontend/enviar-mensaje.js`: la procedencia `answer.nota` se conserva en `dataset`/`title` del mensaje, no como otra burbuja: **1 mensaje del modelo por turno**.
3. `chat/frontend/chat-selectores.js`: no duplica el nombre NVIDIA en la indicación.
4. `SWE CODE/web-bridge/src/respaldo.js`: tipifica `HTTP 410 Gone` para el modelo exacto y no activa sustitución automática.
5. `SWE CODE/web-bridge/src/openclaw.js`: si `OPENCLAW_ENABLE=1`, sincroniza de forma idempotente en el mismo contenedor el provider `swecode` desde el catálogo REAL del bridge cada 10 s. Usa la `RIU_API_KEY` ya existente **solo para autenticar la conexión loopback al bridge**; nunca claves externas de Groq/NVIDIA. Añade modelos a allowlist SIN cambiar modelo predeterminado, pairing, workspace ni otros providers. Escritura de config atómica 0600; OpenClaw aplica hot reload de `models.providers` y `agents.defaults.models`.
6. Pruebas regresión: `chat/frontend/test/selector-unico-salida.test.mjs`, `SWE CODE/web-bridge/test/xray_errores_proveedor.test.mjs`, `SWE CODE/web-bridge/test/openclaw_modelos_config.test.mjs`.

## Gate de cierre
- PASS estático GitHub: archivos integrados, código JS compilable sintácticamente; sin acceso a secretos, no se ha ejecutado test runner Node/Python ni inferencia real.
- GAP operacional: `S1-S3 HTTP503`, `GLM HTTP410`, disponibilidad del Gateway OpenClaw real; las capturas no certifican la sincronización del SHA GitHub.
- Para PASS en producción: GET /health y /web/health; comprobación de commit activo; respuesta sin doble metadato en YAIWES; estado de servidores locales S1-S3; prueba del mismo modelo desde OpenClaw tras recarga en caliente (y si falla, logs del gateway sin imprimir claves). No reiniciar ni editar Hugging Face manualmente.
- La preparación de arranque `boot_hf_optimizado.sh` del commit anterior no reemplaza al `boot.sh` HF sin un mirror explícito de archivos raíz. No declararlo desplegado solo por `git pull`.

Referencias:
- https://docs.api.nvidia.com/nim/reference/z-ai-glm-5-3-infer
- https://docs.openclaw.ai/gateway/configuration/hot-reload
- https://docs.openclaw.ai/gateway/config-tools/custom-providers

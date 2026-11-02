# Optimización de arranque HF sin cambiar la arquitectura (GitHub fuente única)

Diagnóstico **en solo lectura** del Space `COMAND-CENTER-1/riu-router`:

- Su archivo raíz **HF** `boot.sh` verifica `WEB_ACCOUNTS` y `WEB_PASS` como **obligatorios** antes de iniciar el Router Python :7861 y el proxy :7860. Si falta cualquiera, `set -euo pipefail` finaliza el arranque completo, aunque los modelos API o HF local no necesiten cuentas web.
- El mismo archivo ejecuta `npm install` y espera `npx playwright install chromium` antes de levantar el bridge Node :7870. Esto afecta la disponibilidad de APIs cuando Chromium tarda o falla.
- El Space usa la imagen Docker propia, no el Dockerfile de `respaldo_space/`; el boot clona el GitHub en `/tmp/repo`. Clonar código **no actualiza** el `boot.sh` raíz ya incluido dentro de la imagen.
- La pantalla **Preparing Space** es un síntoma; sin consultar logs de ejecución o estado del scheduler no se puede certificar que la causa sea el bootstrap.

## Parche preparado

`chat-router/chat/backend/mvp/respaldo_space/boot_hf_optimizado.sh` es un **archivo sustituto de origen en GitHub**, basado en el `boot.sh` HF actual. Conservar la misma imagen, arquitectura, puertos y rutas, sin tocar banco, agentes ni UI.

1. `GITHUB_TOKEN` y `RIU_API_KEY` siguen obligatorios; `WEB_ACCOUNTS`/`WEB_PASS` solo se necesitan al solicitar modelos de navegador, no para API/SDK ni locales.
2. Bridge Node se inicia al instalar el módulo JS, mientras Chromium se prepara **en segundo plano** por la versión instalada de Playwright (sin `npx` de descarga extra). Los modelos navegador requieren Chromium y podrán responder solo cuando esté listo.
3. Proxy :7860, Router :7861, bridge :7870, OpenClaw opcional y puente móvil permanecen inalterados.
4. El Router Python en GitHub también solapa las dos lecturas independientes del estado al inicio, manteniendo los permisos del backend.

## Aplicación (restricción del Director: NO tocar Hugging Face directamente)
**Este commit NO cambia el `boot.sh` en el Space.** La actualización debe realizarla únicamente el **mirror autorizado GitHub → HF** que publique esta plantilla como `boot.sh` raíz del repositorio Space y dispare la reconstrucción de imagen. El simple autopull de GitHub dentro del contenedor no puede reemplazar el propio boot del contenedor.

Mapping de mirror existente a configurar en el mecanismo que ya usa el proyecto:
`chat-router/chat/backend/mvp/respaldo_space/boot_hf_optimizado.sh` → `COMAND-CENTER-1/riu-router:boot.sh`.

**No crear Actions, jobs, servicios, otra raíz o tokens en el repo.** Si ese mirror de archivos raíz no está instalado, dejar el Space sin cambios y marcar **BLOQUEO** en vez de anunciar mejora desplegada.

## Prueba después del mirror
- Verificar estado del Space y consultar los logs de ejecución con `hf spaces logs COMAND-CENTER-1/riu-router --tail 80`, sin mostrar secretos.
- GET `/health` desde el enlace directo, luego GET `/web/health` autenticado; comprobar servicios :7861, :7870 vía proxy.
- Probar conversación con un modelo local HF, Groq y NVIDIA, más OpenClaw; verificar que `Preparing Space` desaparezca y medir tiempos.
- Revertir **solo** la plantilla de arranque si el mirror devuelve RUNTIME_ERROR. No alterar banco cifrado ni modelos ni credenciales.

## Referencias
- https://huggingface.co/docs/hub/spaces-sdks-docker
- https://huggingface.co/docs/huggingface_hub/guides/manage-spaces
- https://playwright.dev/docs/ci

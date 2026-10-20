# Handoff de la reorganizacion (rama `reorganizacion`)

## Estado
- Paso 1 hecho: se borraron documentos sueltos y carpetas obsoletas (fichas/individuales, puente-chat, respaldo-hf, plugins/chatgpt-proyectos, remote_router, _sync_p3.py).
- Paso 2 hecho: `router/mcp/` anadido, 22 pruebas OK.
- Paso 3 parcial: rutas viejas arregladas (prompt_rules.yaml, puente_chat, panel-chat.js, programas.json, URL de constitucion, router_updater, plugin_host, pruebas). Ver pendientes.

## Pendientes (decisiones necesarias)
1. Cruces entre edificios aun por import directo (no convertidos a HTTP): fichas_qwen -> puente_chat (capacidad_de, plugin, hf_storage); puente_chat/herramientas -> fichas_qwen; plugins -> `integration.chat_mvp` (memoria_loader, providers, vault_hook, route_api), `integration.plugin_host`, `integration.hf_worker_pool`. Hace falta definir los endpoints HTTP destino antes de cortar los imports.
2. Cargador de plugins: rechaza entry_points `fichas.` y `router.` (6 fichas: fichas_qwen, plugin_fichas, sdk/openai_sdk_lab, router/banco, fables_enchufe, router_updater) y solo escanea `plugins/`. Ampliar la lista cambia el diseno de seguridad: lo decide el dueno.
3. 4 gitlinks huerfanos viven en `componentes/` (OmniRoute, Jan, LibreChat, big-AGI): zona protegida, sin tocar.
4. `RIU_HANDOFF_REF` y la URL de la constitucion en `plugins/chat-router/frontend/ventana-constitucion.js` apuntan a la rama `reorganizacion`: cambiar a `main` tras el merge.
5. Pruebas que siguen fallando (sin conexion con el cambio de rutas o por el punto 2): router/tests (fables_enchufe, deepseek, conectores, vault, lifeguard por regla HF_JOBS_RETIRADOS) y algunas de fichas_qwen/tests que pasan sueltas pero fallan en bloque por estado compartido.

## Como operar
- Instalar: `pip install -r router/requirements.txt pytest pyyaml`.
- Probar: `PYTHONPATH=<raiz>:<raiz>/router python3 -m pytest -q <carpeta de pruebas>` (mejor archivo por archivo).
- El actualizador en caliente (`router/router_updater`) sincroniza solo `fichas/`; el resto requiere redeploy.
- El Vercel sandbox es solo puente hacia GitHub; no se guarda nada ahi.

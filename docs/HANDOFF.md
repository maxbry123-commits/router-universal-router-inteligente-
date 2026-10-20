# Handoff de la reorganizacion (rama `reorganizacion`)

## Estado
- Paso 1 hecho: se borraron documentos sueltos y carpetas obsoletas (fichas/individuales, puente-chat, respaldo-hf, plugins/chatgpt-proyectos, remote_router, _sync_p3.py).
- Paso 2 hecho: `router/mcp/` anadido, 22 pruebas OK.
- Paso 3 parcial (cruces ed.1/ed.2 convertidos arriba): rutas viejas arregladas (prompt_rules.yaml, puente_chat, panel-chat.js, programas.json, URL de constitucion, router_updater, plugin_host, pruebas). Ver pendientes.

## Pendientes (decisiones necesarias)
1. Cruces entre edificios (HTTP): cliente delgado router/red/http_plugins.py (llamar(plugin, accion, payload); env RIU_ROUTER_URL y RIU_API_KEY).
   - CONVERTIDO: fichas/plugin_fichas/plugin.py (puente a puente_chat, ahora POST /plugins/puente_chat/call/<accion>).
   - CONVERTIDO ed.1 -> ed.2: fichas_qwen (hf_storage list/read/write por HTTP; capacidad_de por la nueva accion `capacidad` de puente_chat) via fichas/fichas_qwen/puente_http.py.
   - PENDIENTE fichas_qwen/plugin.py -> puente_chat por import en proceso (_pc(): _chat, _memoria, _mem_dato, _http_stream, _politica_ficha, proyecto_proceso, thinking_mode_resolver): comparten ContextVars/sesion/tools del mismo proceso; la accion HTTP `chat` no tiene el mismo contrato. No se cablea sin inventar.
   - CONVERTIDO ed.2 -> ed.1: plugin nuevo router/router_api (acciones memoria, env_keys, base_url, provider_keys, chat) + cliente plugins/router_api_cliente.py. Usado por orquestador (deploy, sandbox, plugin), puente_chat (plugin, herramientas: providers, memoria, vault_hook) y parallel (host.call -> HTTP).
   - NO ES CRUCE: fichas/sdk/_plantilla_sdk (vault_hook) y fichas_qwen -> perfiles (ed.1 con ed.1).
   - PENDIENTE plugins/chat (route_api.build_route_router): monta rutas FastAPI en el mismo proceso, no es una funcion llamable por HTTP. plugins/puente_chat -> fichas_qwen (_NODO_CALL, buzon: estado en proceso). plugins/hf_compute (hf_worker_pool) y deepseek_harness: protegidos, no tocados.
   - ATENCION: router_api (entry_point `router.router_api.plugin:handle`) no se cargara hasta resolver el punto 2 (el cargador solo escanea plugins/ y rechaza `router.`). Hasta entonces los plugins convertidos fallan cerrado (degradan) sin la accion. Ademas env_keys/provider_keys devuelven claves por HTTP (protegido por X-API-Key del Router).
   - router/fables_enchufe y router_updater: lecturas internas del propio edificio 1 (no son cruce HTTP).
2. Cargador de plugins: rechaza entry_points `fichas.` y `router.` (6 fichas: fichas_qwen, plugin_fichas, sdk/openai_sdk_lab, router/banco, fables_enchufe, router_updater) y solo escanea `plugins/`. Ampliar la lista cambia el diseno de seguridad: lo decide el dueno.
3. 4 gitlinks huerfanos viven en `componentes/` (OmniRoute, Jan, LibreChat, big-AGI): zona protegida, sin tocar.
4. `RIU_HANDOFF_REF` y la URL de la constitucion en `plugins/chat-router/frontend/ventana-constitucion.js` apuntan a la rama `reorganizacion`: cambiar a `main` tras el merge.
5. Pruebas que siguen fallando (sin conexion con el cambio de rutas o por el punto 2): router/tests (fables_enchufe, deepseek, conectores, vault, lifeguard por regla HF_JOBS_RETIRADOS) y algunas de fichas_qwen/tests que pasan sueltas pero fallan en bloque por estado compartido.

## Como operar
- Instalar: `pip install -r router/requirements.txt pytest pyyaml`.
- Probar: `PYTHONPATH=<raiz>:<raiz>/router python3 -m pytest -q <carpeta de pruebas>` (mejor archivo por archivo).
- El actualizador en caliente (`router/router_updater`) sincroniza solo `fichas/`; el resto requiere redeploy.
- El Vercel sandbox es solo puente hacia GitHub; no se guarda nada ahi.

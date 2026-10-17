# Arquitectura (no cambiar la ruta)

## Ruta obligatoria
COMPONENTE (UI) → HARNESS `puente_chat` → HTTP → FICHA → MODELO.
Toda tarea nueva (Constitución, Graphiti/Graphify, agentes, tools) entra por el canal harness (estilo DeepSeek, plugins), no por puentes directos.

## Superficies
- **HF Space** `COMAND-CENTER-1/riu-router`: backend (plugins, `/plugins`, `/vault`, `/health`, `/resultado`). `host.py`: MAX_INFLIGHT=8 por plugin.
- **Vercel** `riu-jev-bridge` → https://riu-jev-bridge.vercel.app/ . Rewrites `/plugins`, `/vault`, `/health` → Space (no-store, tope 120 s). `chat router/chat frontend/build.sh` añade `?v=<sha>` a shell.html y a los imports JS (basta cerrar y abrir la pestaña). YAIWES en `/yaiwes/`.
- **Repo backend**: `maxbry123-commits/router-universal-router-inteligente-` (main). **Frontend**: `maxbry123-commits/frontend`.

## Flujo del chat
`chat_async` + polling a `/resultado` (long-poll 8 s, máx. 3 concurrentes por plugin), `request_id` idempotente. Un poll fallido se reintenta; solo corta con 401/403 o 12 fallos seguidos. `/resultado` devuelve `parcial` y la burbuja pinta el texto parcial.

## Despliegue (bundle del bucket)
- Bundle: `buckets/COMAND-CENTER-1/yaiwes-memoria-storage/router-inteligente-universal/codigo/router-bundle.tar.gz` + `router-bundle.json` (manifiesto: sha, fecha).
- Pasos: 1) descargar el bundle actual; 2) aplicar cambios encima (desde main); 3) copia de seguridad `router-bundle.tar.gz.bak-<fecha>-<sha>`; 4) subir el bundle nuevo y actualizar `router-bundle.json`; 5) reiniciar el Space (HF API, `HF_TOKEN`); 6) comprobar `/health` = 200 y probar el chat en Android.
- Frontend: push a main del repo → Vercel construye solo.

## Memoria (PARCHE-3)
- SQLite principal: `/tmp/riu-data/riu_chat.sqlite3`.
- Grafo: graph-sqlite-fallback cuando no hay Graphiti/Neo4j.
- State-hub: `chat router/03-ESTADO/` (`BITACORA.jsonl`, eventos con seq/task/status/next).
- Sync al bucket `yaiwes-memoria-storage` (el `/tmp` del Space se pierde al reiniciar: todo debe sincronizarse).
- Graphiti: `chat router/workflow Loops code Yaiwes/code/memoria/motores/graphiti_sidecar.py` y `code/runtime/src/core/graphiti_temporal_adapter.py`.
- Regla de Antonio: nada se puede perder; agentes, chats y proyectos deben persistir en este sistema.

## Fichas y selectores
- Fichas: contrato `ficha_contract_v2.py`; `fichas_qwen` (Qwen Token Plan: siempre stream; `enable_thinking:false` en preguntas simples sin tools de ≤300 caracteres; reintentos solo ante red/5xx/429/timeout con backoff 0.5→1→2 s + jitter; timeouts 5 s connect y 60 s de lectura entre chunks).
- 6 selectores Qwen (Max ~2–4.5 s, Flash ~2 s). Ficha 4: DeepSeek V4 Pro/Flash, NVIDIA (Nemotron), Groq.
- Constitución: botón ON/OFF, OFF por defecto; solo entra si el chat la manda encendida.

# HANDOFF — Almacenamiento y memoria conectados al Harness DeepSeek

Actualizado: 2026-11-09 · Investigación en solo lectura. No se cambió ningún archivo.
Ramas: `main` (harness, memoria del chat, MCP) · `ccr-f01c3de9-bmry0s` (sqlite local de Router 1).

## 1. Cadena de conexión (cómo llega la memoria al modelo)

```
Modelo (DeepSeek / Groq / NVIDIA)
   │ function calling: tools "memoria", "almacen", "yaiwes_md", "pendientes", "sala"
   ▼
Harness DeepSeek  ── server.py (decide qué tools ve cada modelo; registra en el diario las que cambian algo)
   │ HTTP con RIU_ROUTER_URL + clave de agente
   ▼
Router de cómputo (chat/backend/mvp)  ── /memoria/save · /memoria/load · /memoria/search
   │ mvp.hf_store (un JSON por scope)
   ▼
Bucket HF "yaiwes-memoria-storage" (privado, ~1.5 GB) ── memoria/<scope>.json
```

Ruta paralela para herramientas MCP externas: `memoria_mcp_server.py` expone `memoria_*`, `almacenamiento_*` y `orquestador_*` y llama al mismo Router.

## 2. Archivos y función

| Componente | Archivo | Función | Estado |
|---|---|---|---|
| Harness DeepSeek (servidor) | [chat-router/chat/backend/deepseek_harness/server.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/chat/backend/deepseek_harness/server.py) | Expone tools al modelo. `con_efectos` marca qué tools cambian algo (memoria save, almacen guardar, yaiwes_md escribir). Con Groq Qwen 3.8 recorta el catálogo a 8 tools para evitar HTTP 413; conserva `almacen`, `yaiwes_md`, `pendientes` y `sala`. | Activo. |
| Harness DeepSeek (plugin) | [chat-router/chat/backend/deepseek_harness/plugin.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/chat/backend/deepseek_harness/plugin.py) | Registro del plugin en el harness. | Revisado solo por nombre. |
| Memoria del chat (router) | [chat-router/chat/backend/mvp/memoria.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/chat/backend/mvp/memoria.py) | Rutas `/memoria/save`, `/memoria/load`, `/memoria/search`. Un JSON por scope en el bucket. Caché de 50 scopes, tope de 900 KB por scope, candado por scope, oculta credenciales antes de guardar. | Activo. Tiene pruebas en `test_memoria.py`. |
| MCP de memoria | [chat-router/workflow-loop-code-yaiwes/workflow-loop-yaiwes/code/harness-plugins/memoria/memoria_mcp_server.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/workflow-loop-code-yaiwes/workflow-loop-yaiwes/code/harness-plugins/memoria/memoria_mcp_server.py) | Tools MCP: `memoria_health`, `memoria_save`, `memoria_load`, `memoria_search`, `almacenamiento_estado`, `almacenamiento_sync`, `orquestador_*`. Llama al Router con `RIU_ROUTER_URL` y `RIU_API_KEY` (variables de entorno). | Activo. Ver riesgo R-2. |
| Memoria para OpenClaw | [chat-router/SWE CODE/web-bridge/memoria_hf.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/SWE%20CODE/web-bridge/memoria_hf.py) | CLI `save/load/search`. Reutiliza `mvp.memoria`: misma memoria que el chat. Token desde `HF_TOKEN`. | Activo. Ruta de OpenClaw. |
| Memoria del bridge web | [chat-router/SWE CODE/web-bridge/src/memoria.js](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/SWE%20CODE/web-bridge/src/memoria.js) | Lado Node de la memoria del puente web. | Revisado solo por nombre. |
| Memoria del Loop | [chat-router/Loop cola wachdog/Loop/plugin.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/Loop%20cola%20wachdog/Loop/plugin.py) | Checkpoint por misión en `state/memoria/<mission>.json`, local al proceso. | Activo. Separado del bucket. |
| Memoria unificada ECC | [chat-router/Loop cola wachdog/Loop/motores_code/ecc_unified_memory.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/Loop%20cola%20wachdog/Loop/motores_code/ecc_unified_memory.py) | Motor de memoria unificada de ECC. | NO revisado a fondo. Pendiente. |
| Arquitectura OpenClaw | [chat-router/SWE CODE free/ARQUITECTURA.md](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat-router/SWE%20CODE%20free/ARQUITECTURA.md) | Describe `GET /v1/memoria/<sesion>` y el scope `chat-ui:hist:openclaw-<sesion>`. | Documento. |
| SQLite local (Router 1) | [ROUTER MVP v1/system_prompt_py/sqlite_memory.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/sqlite_memory.py) | Memoria clave-valor en `/data/memory.db` con aiosqlite. | SIN USO: ningún módulo lo importa. Duplicado a decidir. |

## 3. Reglas de la memoria (leídas en el código)

- Un scope = un archivo `memoria/<scope>.json` en el bucket. El nombre se limpia con `[^A-Za-z0-9_-]`.
- Las claves de `key` tienen máximo 200 caracteres; los scopes, 120.
- Cada guardado asigna un id creciente. Si el scope pasa de 900 KB, se descartan los registros más viejos (siempre se conserva al menos uno).
- No se cachea un scope vacío cuando la lectura falla: guardar encima borraría el historial. Se devuelve 502.
- Las credenciales se ocultan antes de guardar.
- Las tools que cambian algo quedan en el diario de la tarea (fail-closed en `loop`).

## 4. Riesgos y gaps

- **R-1 Tres memorias distintas.** Bucket HF (router), SQLite local (sin uso) y `state/memoria` del Loop. No hay una fuente única. Propuesta: el bucket HF como única fuente; el resto, a cuarentena.
- **R-2 Valor por defecto del MCP.** `memoria_mcp_server.py` usa `RIU_ROUTER_URL=http://127.0.0.1:8000` por defecto. En el arranque de `riu-router` el router MVP escucha en 7861 (boot.sh). Si no se define la variable, el MCP no llega al router. Hay que verificar en el entorno real.
- **R-3 Sin prueba en vivo.** `test_memoria.py` valida el módulo. Falta probar el ciclo completo: modelo → harness → router → bucket → lectura.
- **R-4 Caché por proceso.** Si hay varias réplicas, la caché de scopes puede quedar desincronizada con el bucket.
- **R-5 Recorte de tools.** Con Groq Qwen 3.8 solo viajan 8 tools; `memoria` no está en esa lista de prioridad. Hay que confirmar si el modelo puede guardar memoria en esa ruta.
- **R-6 Dependencia de la clave del agente.** El MCP usa `RIU_API_KEY`. Debe venir de entorno y nunca de un archivo.

## 5. Pruebas que deben pasar

- [ ] `chat-router/chat/backend/mvp/test_memoria.py`.
- [ ] Guardar en un scope y leerlo desde otra sesión (persistencia real en el bucket).
- [ ] Confirmar que `memoria_mcp_server.py` arranca con `RIU_ROUTER_URL` apuntando al router real.
- [ ] Confirmar que `sqlite_memory.py` no tiene consumidores antes de cuarentena.
- [ ] Prueba en vivo con clave (🚩 hasta que haya llave en el entorno).

## 6. Pendientes para decidir

- Si `sqlite_memory.py` va a cuarentena o se conecta al bucket.
- Si `ecc_unified_memory.py` duplica la memoria del router.
- Si el MCP de memoria se conecta solo por el router o también directo al bucket.

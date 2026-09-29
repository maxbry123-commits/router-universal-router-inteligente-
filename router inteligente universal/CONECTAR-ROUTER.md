# Conectar CUALQUIER repo, MCP o herramienta al Router único
Actualizado: 2026-09-29 (~11:20 Bogotá; segunda pasada ~16:30: las frases afectadas llevan la marca [16:30] y la sección 9 resume los cambios). Regla del Director: **un solo Router, todo centralizado**. No se crea un Router por repo ni por herramienta. El Router es un servicio web; los demás son clientes que le hablan. El chat NO es el centro: es UN plugin más conectado al Router (Director, 10:55).
Solo hechos verificados. Lo que no se probó dice SIN VERIFICAR. Marcas: ✅ VERIFICADO · 🟡 HECHO SIN PROBAR / a medias · 🔴 PENDIENTE · ⛔ BLOQUEADO. Nada de esta guía está ✅: no se ha probado todavía desde otro repo.

## 1. Encontrar la dirección (no se copia a mano)
La dirección del Router vive en un archivo público del repo, línea `LIVE_URL=`:
`https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/main/router%20inteligente%20universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag`
- Si el Job se relanza, la dirección cambia y el lanzador actualiza ese archivo (verificado en `riu-router-job-central.yml`). Por eso cada cliente lo lee cada vez que lo necesita.
- Una dirección copiada a mano (por ejemplo la variable `RIU_ROUTER_URL` de Vercel) se queda vieja al relanzar. Mejor leer el archivo.
- Ese mismo archivo trae `PAUSED=true/false`: con `true` el Router contesta 503 (menos `/health`). Es el interruptor de pausa remoto.

## 2. Cómo se le habla (corregido el 2026-09-29 11:20)
- `POST <LIVE_URL>/chat/send` con cuerpo JSON `{"message": "...", "provider": "auto", "max_tokens": 1200}`.
- **`"provider":"auto"` es obligatorio.** Con `auto` el Router elige el modelo en cada turno con su cadena (Kimi K3 → GLM 5.3 → DeepSeek V4 Flash → Qwen 3.8 → Nemotron último), pasa al siguiente si uno falla y el campo `model` se ignora. Sin `provider` la petición falla (400 `MODEL_REQUIRED` con el código de la rama; 422 por falta de `model` con el código que corre hoy el Router vivo). El cliente NO manda claves de proveedor: en modo automático `X-Provider-Key` se ignora y el Router usa las suyas.
- Cabeceras: `Authorization: Bearer <token de Hugging Face>` y `X-API-Key: <clave del Router>`.
- Respuesta JSON: el texto del modelo viene en **`reply`** (no en `response`, `content`, `text` ni `message`). Trae también `provider` y `model` (el que contestó de verdad), `auto: true`, `trace` (qué opciones se saltaron o fallaron y por qué) y `conversation_id` (mándalo en la petición siguiente para seguir la misma conversación aunque cambie el modelo). `empty: true` = el modelo contestó vacío (no se guarda en el historial).
- Errores del modo automático [16:30 corregido]: 502 con un texto `ERROR | traza ; traza` (máx. 900 caracteres): `ROUTER_ALL_ROUTES_FAILED` (todas las opciones fallaron) o `ROUTER_NO_ROUTE_AVAILABLE` (ninguna opción configurada, por ejemplo sin llaves). **503** con el mismo formato de texto si el Router está ocupado (`ROUTER_SATURATED`: reintentar más tarde; no es que el modelo esté muerto) y 503 también si el Router está en pausa o si el plugin del chat está apagado (`plugin chat apagado`). (Antes, 11:20, esta guía decía que `ROUTER_SATURATED` era un 502: obsoleto, `router.py:243-244`. El texto plano del 502 es de la ronda 2: 🟡 subido a la rama, sin CI propio.) Errores de la petición que NO enfrían el modelo ni prueban otra llave: 400, 413 (demasiado grande) y 422; tampoco 404 ni 410 cambian de llave.
- Otros grupos de cadena: `POST <LIVE_URL>/chat/route` con `{"group": "default" | "code" | "minor" | "g2", "message": "..."}` → `reply`, `route`, `trace`; si falla, 503 (o 409 `NEEDS_DIRECTOR_AUTH` solo si un grupo no tuviera respaldo autorizado; hoy ninguno).
- Comprobación de vida sin gastar modelos: `GET <LIVE_URL>/health`. Estado de las cadenas y del pool de modelos: `GET <LIVE_URL>/chat/router/status`.
- Verificado en vivo contra el Router vivo (smoke 2026-09-29): `/health`, `/chat/models`, `/chat/router/status`. 🟡 `provider:"auto"` se probó SOLO en el runner de CI con llaves reales (código de la rama `bloque1-cadena-chat`). 🔴 En el Router vivo `auto` todavía NO existe (por el código de main daría 400 `PROVIDER_UNKNOWN`; no se probó en vivo) hasta que se una la rama a main y se relance el Job. [16:30] Sigue cierto a las 16:30: la rama no está unida a `main`; la activación la hace otro agente y no consta en el repo. Hasta entonces un cliente debe mandar un proveedor y un modelo reales (SIN VERIFICAR en vivo con NVIDIA o Groq) y NO `provider=hf` (falla siempre).

## 3. Qué necesita cada repo cliente (solo nombres, nunca valores)
- Un secreto con el token de Hugging Face (en el Router se llama `HF_TOKEN_1`; el cliente existente lo lee como `HF_TOKEN`).
- Un secreto `RIU_ROUTER_API_KEY`.
- Opcional: `RIU_LIVE_URL` para fijar la dirección a mano (solo pruebas).
- Los valores nunca van en el repo (es público): van en GitHub Secrets del repo cliente.
- Para repartir esos secretos a los repos del Director ya existe el workflow `.github/workflows/riu-propagate-auth-secrets.yml` (usa `router inteligente universal/scripts/propagate_actions_secrets.py`). No se probó en vivo tras la reorganización.

## 4. El cliente que ya existe [16:30: ya parcheado en la rama; antes decía «necesita dos cambios pequeños antes de servir»]
`chat router/05-AGENTES/colmena/router_cliente.py`, clase `RouterCliente`:
- Lee `LIVE_URL` del archivo público (o de `RIU_LIVE_URL`), llama `/chat/send`, reintenta 3 veces, antepone `[ROL=…]` al mensaje. Uso: `RouterCliente().chat(prompt, rol)`. Con `SIMULADO=1` no toca la red (para pruebas). Es de una sola pieza y solo usa la librería estándar.
- [16:30] 🟡 ARREGLADO EN LA RAMA `bloque1-cadena-chat` (commit `40924286`, 11:45): ahora manda `"provider": "auto"` (línea 107), lee `reply` primero (línea 91) y muestra el detalle plano del error; prueba `chat router/05-AGENTES/colmena/tests/test_router_cliente_live.py` (commit `3ac20597`). Sin corrida de CI que la ejecute (`[skip ci]`) y en `main` sigue el archivo viejo hasta unir la rama. 🔴 `test_colmena.py::test_hive_block_por_sheriff` falla igual antes y después (preexistente, según el archivo de hechos; no lo ejecuté).
- (Texto de las 11:20, ya obsoleto:) 🔴 HOY NO FUNCIONA CONTRA UN ROUTER REAL, verificado leyendo el archivo (líneas 105-108 y 90): (a) el cuerpo que manda no lleva `provider` → la petición falla (ver sección 2); (b) `_extract_text` busca el texto en `response`, `content`, `text` o `message` y el Router lo devuelve en `reply`, así que devolvería el JSON entero. Arreglo: añadir `"provider": "auto"` al cuerpo y `reply` a la lista de claves. No se ha hecho (no se editó código en este checkpoint) y no se ha probado.
- Para usarlo desde otro repo se copia ese archivo (ya corregido).

## 5. MCP u otra herramienta
Cualquier cosa que pueda hacer una llamada web usa el mismo contrato: leer el archivo de dirección y luego `POST /chat/send` con `"provider":"auto"`. No hace falta otro Router ni otro servidor.
- SIN VERIFICAR: que exista un envoltorio MCP del Router. Si se necesita uno, es una tarea aparte y se arma cableando lo ya descargado, no escribiendo desde cero.
- El conector MCP de Claude (Space `claude-github-mcp-backup`) es otra cosa y está protegido: no se toca.

## 6. Reglas
- Nadie relanza el Job del Router salvo el lanzador único y por orden del Director (relanzar apaga el anterior; el lanzador solo cancela el viejo después de que el nuevo responde `/health`).
- Ningún cliente guarda ni imprime claves.
- Modelos solo por el Router. Cadena del chat (grupo `default`; existe en la rama `bloque1-cadena-chat`, el Router vivo aún tiene la anterior): Kimi K3 → GLM 5.3 (NVIDIA, hasta 4 claves) → DeepSeek V4 Flash → Qwen 3.8 (Groq) → Nemotron ÚLTIMO; en hora pico de DeepSeek (01–04 y 06–10 UTC, lunes a viernes) se salta DeepSeek. [16:30] Sin `HF_TOKEN_1` en el Job el proveedor `hf` queda no configurado y DeepSeek también sale de `default`; `code` y `minor` quedan solo con Nemotron. Regla general anterior (03:26): NVIDIA hasta 4 claves → Groq → DeepSeek V4 Flash al final. Sin Cerebras, sin OmniRoute, sin APIs de Anthropic.

## 7. Si el Router se mueve a otro repo
Cambian dos direcciones: `FLAG_URL` en `router_cliente.py` y `REPO_URL` en `agents-yaiwes/common/router_job_persistent.py` (línea 20), más el `git clone` y la URL de la API del archivo de dirección dentro de `.github/workflows/riu-router-job-central.yml`. Los clientes que lean `LIVE_URL` del archivo nuevo siguen funcionando sin más cambios.

## 8. Plugins (el chat es el primero) — 🟡 subido a la rama y probado en CI [16:30; a las 11:20 decía «🟡/🔴 EN CONSTRUCCIÓN»]
Un plugin es cualquier cliente que usa el Router; el chat es solo el primero. [16:30] El Plugin Host YA está en la rama (`integration/plugin_host/`, `plugins/chat/`, `plugins/thinking-modes/`; 🟡, no ✅; ver `HANDOFF-PROVISIONAL-ROUTER.md` 20.D). Diseño (texto de las 11:20, «no funciona todavía: al 11:20 no hay código del Plugin Host en la rama», hoy obsoleto): cada plugin vive en `plugins/<id>/ficha.json` y el Router lo monta UNA vez; cada llamada de un plugin va envuelta por la regla del harness de DeepSeek (removible, sin dependencia dura; si falla o se agota el plazo devuelve un estado `degraded` con el motivo y no tumba el Router); no se ejecuta código de terceros. Un cliente externo sigue conectándose como cliente web normal (secciones 1 a 5); el host solo añade `GET /plugins` y `/plugins/{id}/enable|disable`, y una compuerta que responde 503 «plugin chat apagado» a las rutas `/chat` si el plugin del chat está apagado (encendido por defecto; `thinking-modes` apagado y sin código). Estado y lista roja: `HANDOFF-PROVISIONAL-ROUTER.md`, secciones 15 y 17.

## 9. Cambios de la segunda pasada (~16:30) — resumen
- `ROUTER_SATURATED`: 503 (no 502) también en `/chat/send` con `auto`. 413 se trata como error de la petición (no enfría, no cambia de llave). `RouterCliente` ya está parcheado en la rama. El plugin del chat puede responder 503 «plugin chat apagado». `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` la pone el propio Job; solo falta `HF_TOKEN_1` en los secretos del Job (otro agente está activando el Router; no está hecho en el repo a las 16:30).
- Nada de esta guía está ✅: sigue sin probarse desde otro repo contra el Router vivo, que todavía no corre el código de la rama.

# DEPLOY — destinos de despliegue y cómo subirlos unificados

Inventario hecho sobre `origin/main` (`a0283c4c73`) con `git ls-files`. **Solo nombres de variables: nunca valores.** Las credenciales viven en los secretos de cada servicio, en el banco/vault o en el entorno; jamás en el repo.

Atajo: `bash chat-router/DEPLOY/deploy-unificado.sh` (simulacro, no sube nada) y `... --ejecutar` (merge + push). Operadores: `bash chat-router/DEPLOY/generar-aprobadores.sh <operador> [...]`.

## 1. Tabla única: destino → cómo se actualiza → qué necesita → cómo verificarlo

| # | Destino | Qué es / de dónde sale | Cómo se actualiza | Variables / secretos (solo nombres) | Verificación (URL + SHA) |
|---|---|---|---|---|---|
| 1 | **Vercel** `riu-jev-bridge` (frontend del chat) | `chat-router/chat/frontend/` (`vercel.json`, `build.sh`, `api/power.js`, `api/loop.js`, `api/ecc_motor.py`). `build.sh` versiona los assets con `?v=<sha>` y escribe `version.json` | **Automático** al hacer push a `main` si el proyecto tiene la integración Git conectada (el dominio `riu-jev-bridge-git-main-…vercel.app` y el último deploy READY lo indican; confirmar en el panel que la *Root Directory* es `chat-router/chat/frontend`). Alternativa **manual**: Deploy Hook (`VERCEL_DEPLOY_HOOK`, lo dispara `deploy-unificado.sh`) | En Vercel: `RIU_ROUTER_API_KEY`, `HF_POWER_TOKEN` (o `HF_TOKEN_1`); opcionales `HF_SPACE_ID`, `RIU_ROUTER_URL`. Lo pone Vercel: `VERCEL_GIT_COMMIT_SHA`. Local del script: `VERCEL_DEPLOY_HOOK` | `GET https://riu-jev-bridge.vercel.app/version.json` -> `{"commit":"<sha completo>"}` (debe ser el de `main`). `GET .../health` pasa por el rewrite al Router |
| 2 | **Space del Router** (HF `COMAND-CENTER-1/riu-router`, `https://comand-center-1-riu-router.hf.space`) | Docker (`chat-router/chat/backend/mvp/respaldo_space/Dockerfile` + `boot.sh`): clona `main` al arrancar y ejecuta `python -m mvp.run` (`run.py`) | **Automático cada 60 s**: el autopull de `run.py` hace `git pull --ff-only`; reinicia solo si el cambio toca servidor (no reinicia por frontend/docs/e2e/auditoría, ver `SIN_REINICIO`), espera a que terminen las tareas en curso, y si `import mvp.app` falla deshace el pull. Cambios del propio `boot.sh`/`Dockerfile` o dependencias: **manual** (Factory reboot del Space) | ver bloque ENV-SPACE: obligatorias `RIU_API_KEY`, `GITHUB_TOKEN` y, solo para aprobar acciones con efectos, `RIU_SWE_APROBADORES` (+ `BRIDGE_APROBADORES`, mismo valor); el resto tiene defecto | `GET /health` -> `{"status":"ok","commit":"<10 car.>"}` (comparar con `git rev-parse --short=10 origin/main`) |
| 3 | **Bridge SWE CODE** (`chat-router/SWE CODE/web-bridge`, `:7870`, dentro del Space del Router; el proxy expone `/web/*`) | `node src/server.js` desde el clon. El `Dockerfile` del bridge es solo para build local (el Space real no lo usa) | **Automático cada 60 s** (`src/autoactualizar.js`): si cambia `SWE CODE/`, `SWE CODE free/` o `chat/backend/mvp/prompts/`, hace `node --check` (y `npm install` si cambió `package.json`) y se relanza solo; si no compila, no se relanza. Apagar: `BRIDGE_AUTOACTUALIZAR=0` | `RIU_API_KEY`, `GITHUB_TOKEN`, `BRIDGE_APROBADORES` (solo para aprobar), `WEB_ACCOUNTS`, `WEB_PASS`, `HF_TOKEN`, `BRIDGE_STATE_DIR`; ya NO hacen falta `BRIDGE_TOKEN` (opcional), `SWECODE_URL_S1..S3` ni `RIU_DEEPSEEK_HARNESS_URL` (tienen defecto, ver ENV-SPACE) | `GET /web/health` -> `ok`, `pool`, `respaldo{groq,nvidia,hf_local}`, `banco`. **No devuelve commit** (el SHA del código se comprueba con `/health` del Space; mismo clon) |
| 4 | **Space del Harness DeepSeek** (URL = la de `RIU_DEEPSEEK_HARNESS_URL`) | `chat-router/chat/backend/deepseek_harness/space/{Dockerfile,boot.sh}`: clona `main` al arrancar y lanza `plugins.deepseek_harness.server:app` con `PYTHONPATH=chat-router:router-mvp:repo` | **Manual**: NO tiene autopull. Tras subir a `main` hay que reiniciar/reconstruir el Space (panel HF -> Restart/Factory reboot, o API `POST /api/spaces/<id>/restart` con token de HF). `boot.sh` imprime `HEAD=<sha>` en el log | `GITHUB_TOKEN` (obligatoria en `boot.sh`), `RIU_API_KEY`, `RIU_SWE_APROBADORES` (solo para aprobar; de ahí deriva los operadores), `GROQ_API_KEY*`, `NVIDIA_API_KEY*`, agentes (ver ENV-SPACE) | `POST /invoke {"action":"status"}` con `X-API-Key` -> `result.swe` y `commit`. Log del Space: línea `HEAD=` |
| 5 | **Servidores de modelos locales** `comand-center-1-swe-code-s1/s2/s3` (HF) | Su código **no está en este repo** (sirven GGUF del dataset `COMAND-CENTER-1/swe-code-hf-gguf`) | Fuera de este deploy | — | `GET https://comand-center-1-swe-code-s{1,2,3}.hf.space/v1/models` |
| 6 | **puente-movil** (`chat-router/SWE CODE free/puente-movil`, `node server.js`) | Canal MCP/WebSocket del APK. Comparte el vigilante `autoactualizar.js` | **Automático cada 60 s** una vez que corre como proceso; arrancarlo como proceso del Space es **manual** (pendiente según HANDOFF) | `PUENTE_TOKEN` (obligatorio, `PUENTE_PORT`, defecto 7860) | `GET /health` -> `{"ok":true,"movil":<bool>}` |
| 7 | **APK** (`chat-router/SWE CODE free/apk-movil`, proyecto Gradle `com.swecode.agente`) | No hay CI ni script de build en el repo. Se descarga desde el chat (Configuración -> «Agente móvil (APK)» -> `GET /apk` del Space; esa ruta/proxy **no está en el repo**) | **Manual**: en una máquina con Android SDK/Gradle `gradle assembleDebug` (no hay `gradlew`), publicar el `.apk` donde sirva `/apk`, reinstalar en el móvil | `PUENTE_TOKEN` (la app lo usa para conectar) | `versionName` en `app/build.gradle` (0.1.0); instalar y pulsar «Conectar agente»; `puente-movil /health` -> `movil:true` |
| 8 | **Plugin OpenClaw** `swe-selector` (`chat-router/SWE CODE free/openclaw-ui`) | Plugin nativo de OpenClaw (Node >= 24.22.1) | **Manual**: `npm install && npm run build && npm run validate`, luego `openclaw plugins install .` (o `npm run pack` + `openclaw plugins install ./swe-selector.tgz`) en el Gateway | En el Gateway: `RIU_API_KEY` (el bridge la acepta por Bearer; `BRIDGE_TOKEN` es opcional y solo respaldo), `RIU_SWE_BRIDGE_URL`. `provider-openclaw.json` usa el marcador `${RIU_API_KEY}` | `openclaw plugins inspect swe-selector` y `openclaw models list` dentro del Space (aún NO VERIFICADO según HANDOFF R10) |
| 9 | **Agentes reales del Harness** (`codex`, `opencode`, `sweagent`, OpenHands, `claude-code`, OpenClaw) | `chat-router/agentes/runtime/instalar-agentes.sh` **no existe todavía en el repo** (lo crea otro agente) | **Manual**, dentro del entorno del Harness, cuando exista: `bash chat-router/agentes/runtime/instalar-agentes.sh`. `deploy-unificado.sh` solo avisa si el archivo está | `RIU_CODEX_BIN`, `RIU_CODEX_BASE_URL`, `RIU_OPENCODE_BIN`, `RIU_SWEAGENT_BIN`, `RIU_DOCKER_BIN`, `RIU_SWEAGENT_IMAGE`, `RIU_OPENHANDS_PYTHON`, `RIU_CLAUDE_BIN`, `RIU_CLAUDE_PASARELA_URL`, `RIU_CLAUDE_PASARELA_MODELO`, `OPENCLAW_GATEWAY_TOKEN`, `RIU_OPENCLAW_URL` | `POST /invoke {"action":"status"}` -> `result.swe` (estado por agente: DISPONIBLE / NO INSTALADO / NO CONFIGURADO...) |
| 10 | **GitHub Actions** | En `origin/main` hay **0 workflows** (`.github/` no existe en `main`). Solo `espejo-chat.yml` en las ramas `devin/1792939533-loop-cableado` y `respaldo-cableado-2026-10-25` (no corre porque no está en la rama por defecto). Los `.github/workflows` bajo `agentes-listos/` y `frameworks/` son de terceros en subcarpetas: GitHub no los ejecuta | Nada se dispara por push a `main`. `espejo-chat.yml` (si se llevara a `main`): push a `chat/espejo/**` o manual (`workflow_dispatch`); necesita el secreto de repo `RIU_QA_KEY` | `RIU_QA_KEY` (solo si se activa el espejo) | Pestaña Actions del repo |
| 11 | **Rama `banco-claves`** | No es un destino de código: guarda el banco cifrado `banco-swe.bin` que el bridge publica/lee | Automático (bridge, cada 60 s si el local no existe o no abre) | `GITHUB_TOKEN` | `GET /web/health` (con `x-api-key`) -> `banco.*` |

### Qué dispara cada cosa
- `git push` a `main`: dispara Vercel (integración Git) y, en ≤ 60 s, el autopull del Router y del bridge. **No** actualiza el Harness (reinicio manual), ni S1-S3, ni APK, ni el plugin OpenClaw.
- Deploy Hook de Vercel: manual (POST al hook). Crearlo: Vercel -> proyecto `riu-jev-bridge` -> Settings -> Git -> *Deploy Hooks* -> rama `main`; exportar la URL como `VERCEL_DEPLOY_HOOK` (secreto: no guardarla en archivos del repo).
- Reinicio del Space Router/Harness: panel de HF (Restart / Factory reboot) o `POST https://huggingface.co/api/spaces/<owner>/<space>/restart` con un token de escritura; `api/power.js` de Vercel hace esto para el Router (`POST /api/power {"accion":"reiniciar"}` con `X-API-Key`).

### Avisos detectados en el inventario (no corregidos: fuera del alcance de este encargo)
1. `respaldo_space/boot.sh` (copia del repo) hace `test -f mvp/run.py` y `python -m mvp.run` desde la raíz del clon; hoy la raíz solo tiene `router-mvp/` y `chat-router/` (`mvp` es `router-mvp/mvp` -> enlace a `chat-router/chat/backend/mvp`). Confirmar cuál es el `boot.sh` REAL del Space (el HANDOFF dice que el real no está en el repo). `boot_run.py` (en la misma carpeta) es otra copia vieja (`riu_kernel`).
2. El Harness no tiene autopull: `main` nuevo no llega hasta reiniciarlo.
3. El Space desplegado (último dato del HANDOFF: `6a1d59a616`) iba por detrás de `main`; compruébalo con el paso de verificación de `deploy-unificado.sh`.
4. `GET /apk` y el proxy `/web/*` del Space no están en este repo.

## 2. Bloque ÚNICO `ENV-SPACE` — variables de Space / Harness / bridge

Leyenda: **Dónde** R = Space del Router, B = bridge (mismo Space), H = Harness, V = Vercel. **Estado** = `EXISTE` (según HANDOFF, `/web/health` del 2026-11-01 y los `boot.sh`: el Space ya la usa), `FALTA` (hay que crearla como secreto/variable), `VERIFICAR` (no se puede saber desde el repo: comprobar en Settings del Space). Sin valores.

```
# ---- Acceso y operadores ----
BRIDGE_TOKEN                 [B]     OPCIONAL (ya no hace falta): el bridge acepta cualquier clave de acceso (RIU_API_KEY...) como Authorization: Bearer. Si se define, debe ser DISTINTO de cualquier token de operador.   no crear
RIU_API_KEY                  [R,B,H] OBLIGATORIA. Clave de acceso del chat/Harness/bridge (X-API-Key / Bearer). boot.sh del Router la exige; también es la que usa OpenClaw (${RIU_API_KEY}).   EXISTE
RIU_PUBLIC_CHAT_KEY / RIU_MCP_KEY / RIU_ROUTER_API_KEY   [R,B,V]  Claves de acceso alternativas (cualquiera cifra/abre el banco). RIU_ROUTER_API_KEY además la usa Vercel /api/power.   VERIFICAR (/web/health: "accesos":3)
RIU_SWE_APROBADORES          [R,H]   OBLIGATORIA SOLO para poder aprobar acciones con efectos (YAIWES): operador:sha256(token),operador2:sha256(token2). Generar con generar-aprobadores.sh. Sin ella /chat/swe/aprobar da 503 APROBADORES_NO_CONFIGURADOS (el mensaje nombra esta variable).   FALTA
BRIDGE_APROBADORES           [B]     OBLIGATORIA SOLO para aprobar desde OpenClaw (POST /v1/swe/aprobar y tools con efectos). MISMO valor que RIU_SWE_APROBADORES.                  FALTA
RIU_SWE_OPERADORES           [H]     YA NO hace falta: el Harness deriva los operadores de los nombres de RIU_SWE_APROBADORES / BRIDGE_APROBADORES. Solo si se define manda (vacía = ninguno).   no crear

# ---- Código y persistencia ----
GITHUB_TOKEN                 [R,B,H] Clonar/leer main, publicar el banco en la rama banco-claves (permiso contents). boot.sh de Router y Harness lo exigen.                  EXISTE (/web/health: banco.github.token=true)
HF_TOKEN                     [R,B]   OPCIONAL: memoria compartida / hf_store / checkpoint HF (persistencia entre Spaces). Sin ella el chat y el checkpoint de tareas SWE CAEN a disco local (BRIDGE_STATE_DIR) sin romperse; el catalogo de modelos de OpenClaw/SWE CODE y las tools de GitHub NO dependen de esta variable.   VERIFICAR
HF_BUCKET_ID, RIU_VAULT_SOURCE, RIU_VAULT_PROVIDERS_SOURCE, RIU_VAULT_PATH, RIU_DATA_DIR, RIU_CORS_ORIGINS   [R]  Variables fijas del Dockerfile del Router (no son secretos).   EXISTE (Dockerfile)
RIU_VAULT_PASSPHRASE         [R]     Solo si el boot real usa boot_run.py (vault); secreto.                                                                                       VERIFICAR
BRIDGE_STATE_DIR             [B]     Estado en disco (checkpoints, banco-swe.bin). En el Space: /data/state (almacenamiento permanente).                                         VERIFICAR
BRIDGE_PORT                  [B]     Puerto del bridge (defecto 7870).                                                                                                              defecto
PORT                         [R]     Puerto del Router (7860 / 7861 detrás del proxy del Space).                                                                                  defecto

# ---- Cuentas web del bridge ----
WEB_ACCOUNTS, WEB_PASS       [B]     Cuentas web Qwen/DeepSeek (correos) y su clave; si faltan, /web/health avisa WEB_ACCOUNTS_VACIO y responde el respaldo.                            EXISTE (pool total=10)
BRIDGE_PROXY                 [B]     Proxy opcional de los navegadores.                                                                                                            opcional

# ---- Harness y rutas internas ----
RIU_DEEPSEEK_HARNESS_URL     [R,B]   YA NO hace falta con el Harness del MISMO Space: sin definir, el chat y el bridge usan http://127.0.0.1:$PORT/plugins/deepseek_harness (PORT del Router; 7861 si falta; solo URL local). Solo se define si el Harness corre en OTRO Space (su URL pública https); definida y vacía = desactivado.   defecto
RIU_SWE_WORKSPACE_RAIZ       [H]     YA NO hace falta: defecto <BRIDGE_STATE_DIR o tmp>/swe-workspace, creado 0700. Solo si se quiere otra raíz; definida y vacía = desactivado.   defecto
RIU_SWE_BRIDGE_URL           [H]     Por dónde llegan los modelos hf/* a los agentes (defecto http://127.0.0.1:7870).                                                                defecto
RIU_ROUTER_URL               [B,H,V] URL del Router (tools de OpenClaw -> MCP /mcp); en Vercel, destino de /api/power.                                                          defecto (derivada de HF_SPACE_ID)
HF_SPACE_ID                  [V]     Space a encender/apagar desde /api/power (defecto COMAND-CENTER-1/riu-router).                                                                 defecto
HF_POWER_TOKEN (o HF_TOKEN_1) [V]    Token de HF con permiso de reiniciar/pausar el Space (solo en Vercel).                                                                       VERIFICAR

# ---- Modelos locales HF (URLs públicas, sin secreto) ----
# YA NO hacen falta: sin definir, bridge, Harness y mini_router usan estas URLs públicas. Definida manda; definida y vacía = sin ese servidor.
SWECODE_URL_S1=https://comand-center-1-swe-code-s1.hf.space/v1   [B,H]   Servidor GGUF 1 (entrada).                                                                               defecto
SWECODE_URL_S2=https://comand-center-1-swe-code-s2.hf.space/v1   [B,H]   Servidor 2 (LIQUID 1, lector).                                                                            defecto
SWECODE_URL_S3=https://comand-center-1-swe-code-s3.hf.space/v1   [B,H]   Servidor 3 (LIQUID 2, ejecutor).                                                                          defecto

# ---- Proveedores (la fuente es el banco; el Harness NO las lee del banco) ----
GROQ_API_KEY, GROQ_API_KEY_1..20       [H]  Modelo groq/qwen/qwen3.8-27b para agentes. Copiar los mismos valores del banco como secretos del Harness.                              FALTA (en el bridge ya hay 6 vía banco)
NVIDIA_API_KEY, NVIDIA_API_KEY_1..20   [H]  Modelos nvidia/* para agentes.                                                                                                       FALTA (en el bridge ya hay 5 vía banco)

# ---- Agentes del Harness (solo los que se instalen) ----
RIU_CODEX_BIN, RIU_CODEX_BASE_URL (API Responses; obligatoria), RIU_OPENCODE_BIN, RIU_SWEAGENT_BIN, RIU_DOCKER_BIN, RIU_SWEAGENT_IMAGE, RIU_OPENHANDS_PYTHON,
RIU_CLAUDE_BIN, RIU_CLAUDE_PASARELA_URL, RIU_CLAUDE_PASARELA_MODELO, RIU_CLAUDE_AUTH_TOKEN (opcional), OPENCLAW_GATEWAY_TOKEN, RIU_OPENCLAW_URL    [H]   FALTA (HANDOFF: solo la CLI de claude está instalada y sin configurar)

# ---- Ajustes opcionales (defecto razonable) ----
BRIDGE_EXIGIR_CONFIRMACION (YA NO hace falta: la confirmación del objetivo y de las operaciones previstas está activa por defecto con tools; 0 la desactiva), BRIDGE_AUTOACTUALIZAR (0 apaga), MVP_AUTOPULL (0 apaga el autopull del Router), BRIDGE_AUTORETOMAR, BRIDGE_DEADLINE_MS, BRIDGE_RESPALDO_MS, RIU_SWE_TIMEOUTS,
RIU_SWE_GROQ_MODELO, RIU_SWE_NVIDIA_MODELO, RIU_SWE_SONDA_MODELOS, RIU_AGENTE_TIMEOUT_S, RIU_SWE_TIMEOUT_S, RIU_SWE_HARNESS_TIMEOUT_MS, RIU_HARNESS_TIMEOUT_S, RIU_MAX_HORAS, RIU_DEFER_MAX_S

# ---- Otras de servicios concretos ----
PUENTE_TOKEN, PUENTE_PORT    [puente-movil]  Token (obligatorio) y puerto del puente móvil.                                                                                  FALTA/VERIFICAR
RIU_QA_KEY                   [GitHub Actions] Secreto del repo, solo para el workflow espejo-chat.yml.                                                                          no aplica en main
```

Formato exacto de `RIU_SWE_APROBADORES` / `BRIDGE_APROBADORES` (validado en `swe_rutas.js::aprobadores` y `mvp/app.py::_aprobadores`): pares separados por coma `nombre:huella`, con `nombre` = `[A-Za-z0-9_.@-]{2,64}` y `huella` = 64 caracteres hex = `sha256(token)` en minúsculas (UTF-8, sin salto de línea). Entradas mal formadas se ignoran. Si la huella de algún operador coincide con la de `BRIDGE_TOKEN` (o de una clave de acceso en el Router), la operación responde 503: el token de operador debe ser **distinto** y propio de cada persona. Cada operador manda `x-operador` + `x-operator-token`.

## 3. Orden de trabajo recomendado (Director)
1. `bash chat-router/DEPLOY/generar-aprobadores.sh <tu-operador>`: copia el token (se muestra una sola vez) a tu gestor de secretos y pega la línea (el valor, mismo para las dos) como Secrets `RIU_SWE_APROBADORES` y `BRIDGE_APROBADORES` del Space (y `RIU_SWE_APROBADORES` también en el Space del Harness si es aparte). `RIU_SWE_OPERADORES` ya no hace falta.
2. `bash chat-router/DEPLOY/deploy-unificado.sh` (simulacro) y, si todo OK, `... --ejecutar`.
3. Reiniciar el Space del Harness (no tiene autopull) y comprobar `POST /invoke {"action":"status"}`.
4. Añadir los secretos marcados FALTA en cada servicio; reiniciar donde corresponda.
5. (Opcional) Crear el Deploy Hook de Vercel y exportarlo como `VERCEL_DEPLOY_HOOK`.
6. Pendientes manuales: APK, plugin OpenClaw, agentes reales, puente-movil como proceso.

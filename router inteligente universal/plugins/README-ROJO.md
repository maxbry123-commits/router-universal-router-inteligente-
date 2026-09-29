# 🔴 PLUGINS DEL ROUTER — LO QUE **NO** ESTÁ CABLEADO (README-ROJO)

Regla del Director: UN solo Router; lo que está debajo se conecta como plugin y no se toca más. El chat es UN plugin más.
Nada de esto está ✅ VERIFICADO: lo construido está "hecho y probado localmente (shim)", sin CI, sin auditoría y sin el OK del Director.

## Qué existe hoy (código en `integration/plugin_host/`)
- `host.py` (sin FastAPI): registro de `plugins/<id>/ficha.json`, validación, interruptor on/off en un JSON, y `host.call(plugin, accion, payload, timeout_s)` = envoltura obligatoria: ante excepción, plazo vencido, plugin apagado/inválido, acción no permitida o entrypoint fuera de la lista devuelve `{"status":"degraded","reason":...}` (o `off`) y NUNCA lanza.
- `api.py`: `GET /plugins`, `POST /plugins/{id}/enable`, `POST /plugins/{id}/disable` (misma autenticación que el resto del Router) y la compuerta del chat (503 "plugin chat apagado" si el plugin `chat` está apagado; por defecto ENCENDIDO).
- Montaje: una sola vez, dentro de `try/except`, en `integration/chat_mvp/app.py`. Si el host falla al importarse, el Router arranca igual, sin `/plugins` y sin compuerta.
- Plugins: `chat` (encendido; su salud = la función de `/chat/router/status` llamada en el mismo proceso, sin red) y `thinking-modes` (APAGADO, placeholder).
- Entrypoints: solo módulos que empiezan por `integration.` o `plugins.`, cargados con `importlib`; nada de `exec`/`eval`. La comprobación se hace al cargar la ficha y otra vez justo antes de importar.

## 🔴 NO CABLEADO (de Fables / bus_v2 y del diseño §8) — cada punto es trabajo pendiente
1. 🔴 **Failover declarativo**: la ficha tiene `failover.sustituible_por` pero el host NO lo lee; `call()` no salta a otro plugin. (Fables: `FailoverManager`.)
2. 🔴 **Presupuesto por nivel (n0–n5)**: `presupuesto` de la ficha se ignora; no hay `CostGovernor`; no se cuentan tokens/ms/USD por plugin.
3. 🔴 **Evidencia L1–L4**: no se recolecta evidencia. Solo existen, en memoria, `last_error` y `last_call_ms` de cada plugin (se pierden al reiniciar).
4. 🔴 **Hot-swap / upgrade**: no existe. Las fichas se leen al arrancar el host; cambiar una ficha en disco no hace nada hasta reiniciar (`host.reload()` existe pero NO hay endpoint ni temporizador; el diseño §8 pedía releer cada 60 s: 🔴). No se copió el `HotSwapManager` de Fables (usa `exec`).
5. 🔴 **Sandbox C13**: no existe. El plugin corre DENTRO del proceso del Router, en un hilo con plazo. Un hilo que se pasa de plazo NO se mata (sigue corriendo hasta terminar); solo se limita a 8 llamadas simultáneas por plugin. No hay límite de memoria ni de CPU. La lista de módulos permitidos (`integration.*`, `plugins.*`) bloquea `os`, `subprocess`, `builtins`…, pero NO es un sandbox: `integration.*` incluye todos los módulos del Router y cualquier ficha que llegue al repo puede apuntar a una función suya. Código de terceros NO debe montarse hasta que exista el sandbox.
6. 🔴 **Firma y tribunal**: `firma.gpg_key_id` = `PENDIENTE`; no hay `contract_hash`; ninguna ficha trae `tribunal_case_id`; nada se verifica contra `revocation_list.json`. Por eso las fichas están en `testing`/`draft`, nunca `active`. El "tribunal" = el OK del Director sigue PENDIENTE.
7. 🔴 **Invocación por `RedUniversal`**: el §8 decía "invocación real → RedUniversal". NO se hizo: el host llama al entrypoint directo con `importlib`. `RedUniversal` es asíncrona y trabaja con conectores; unirlos es trabajo aparte.
8. 🔴 **Salud por latido, telemetría (spans OTel), activación por eventos / wake words, perfiles cognitivos, repetición**: la ficha los trae con valores por defecto y el host no los usa. Solo hay `health_action` (una acción de la ficha que `GET /plugins` ejecuta con el mismo `call()`; esa llamada espera como máximo el plazo del plugin).
9. 🔴 **El interruptor NO sobrevive al reinicio del Job**: el Job de Hugging Face es efímero y el archivo de estado (`RIU_PLUGINS_STATE`, por defecto `plugins_state.json` dentro de `RIU_DATA_DIR`, en el Job `/tmp/riu/`) se pierde al relanzar. Hasta anclar el estado en GitHub / almacenamiento de HF, cada relanzamiento vuelve al `enabled_default` de la ficha (chat encendido, thinking-modes apagado). Si la ruta no es escribible, el interruptor vive solo en memoria y `GET /plugins` lo dice (`state.persisted:false`).
10. 🔴 **Compuerta del chat — alcance**: cubre los tres routers de chat (`build_router`: `/chat`, `/chat/providers`, `/chat/send`, agentes, documentos…; `build_jobs_router`: `/chat/jobs/run`; `build_route_router`: `/chat/route`, `/chat/router/status`, `/chat/router/models`, `/chat/jev`). NO cubre: `/health`, `/v1/models`, `/v1/chat/completions` y `/chat/models` (pasarela), `/vault/*`, `/gh/accounts`, `/control/*`, `/groups` (ui_bridge), `/memoria/*`, `/omniroute/*`. Decisión del Director si `/v1/chat/completions` (lo usan agentes) también debe apagarse con el chat.
11. 🔴 **Compuerta — detalles**: responde ANTES de la autenticación (sin llave se ve 503 en vez de 401, o sea, cualquiera puede saber que el chat está apagado). Falla abierta: si el host se rompe, el chat sigue funcionando; una ficha inválida nunca cierra la compuerta. Si el chat se apaga desde el panel, la página `/chat` del propio Router también da 503 (el panel de plugins `/plugins` sigue).
12. 🔴 **Sin roles**: cualquier llave válida del Router puede apagar/encender plugins.
13. 🔴 **Pruebas HTTP sin ejecutar aquí**: no hay `fastapi` en esta máquina. Las 4 pruebas HTTP/compuerta (`tests/test_plugin_host.py`, marcadas con `importorskip`) están escritas pero NO se corrieron con FastAPI real; solo se comprobó el mismo código con un sustituto de FastAPI (solo humo). Necesitan CI.
14. 🔴 **Estado `ready`** = ficha válida + encendido. El módulo se importa en la primera llamada; si falla ese import, el plugin pasa a `degraded` en ese momento.

## 🔴 Las invariantes de la ficha de Fables frente a la ficha del chat
Se ejecutó `validar()` de `enchufe/validator_v2.py` (y la copia de Fables `ficha_contract_v2.py`: mismo resultado) sobre `plugins/chat/ficha.json`:
- Tal cual (`estado: testing`): 0 errores. Pero "0 errores" NO significa "cumple las 36":
  - El validador solo implementa **27** comprobaciones en código (I01–I13 y V01–V14). El encabezado dice "22 v1.5 + 14 v2.0 = 36": **9 invariantes v1.5 no están implementadas** en el validador ni en la copia de Fables (fuente sin recuperar). No se pueden dar por cumplidas ni por falladas: SIN VERIFICAR.
  - V05–V12 (perfiles, repetición, presupuesto, `repite_en`) "pasan" porque el validador les pone valores por defecto; la ficha no declara nada de eso y el host no lo usa (puntos 2 y 8).
- Con `estado: active` la ficha del chat FALLA: `I04_active_requiere_hash` (sin `contract_hash` sha256) y `V13_active_requiere_gpg` (firma `PENDIENTE`). Por eso NO está `active`. Una prueba lo fija.
- Fuera de `validar()`: el `enchufar()` de Fables exige `tribunal_case_id` aprobado; la ficha no lo tiene (punto 6).
- Valores que puso el constructor, sin decisión del Director, y que hay que confirmar: `etapa: "P"` (el valor por defecto; no se comprobó qué significan las letras E/P/S/T/A), `runtime_type: "hybrid"` sin `llm_ratio` medido, `idempotente: true` (la única acción, `status`, solo lee), `sandbox: "none"` (es lo que hay), `timeout_ms: 5000`.
- Además del validador de Fables, el host corre una comprobación pequeña `plugin_host/v1` (H01–H11: bloque `plugin_host`, id = nombre de carpeta, `enabled_default` booleano, versión semver, categoría, entrypoint permitido, `allowed_actions`, `health_action`). Si el validador del repo no se pudiera cargar, `GET /plugins` mostraría `validator: "plugin_host/v1 solo …"` y solo esa comprobación pequeña protegería.

## 🔴 `thinking-modes` (ZIP `yaiwes_subrouters_modulares.zip`)
- Es SOLO una ficha placeholder, APAGADA (`status: off`). El ZIP NO se ha descomprimido, revisado ni importado; según la nota de arquitectura contiene instant/thinking/council/code + `profiles.json` y sus pruebas eran simuladas (SIN VERIFICAR).
- No hay entrypoint. Si alguien lo enciende desde `/plugins/thinking-modes/enable`, queda `degraded` ("placeholder: sin código montado"): encender no hace nada útil.
- Pendiente: revisión de seguridad del ZIP, cablearlo como plugin (con su ficha real) y solo entonces encenderlo desde el chat/panel.

## Cómo se añade un plugin (cuando se autorice)
`plugins/<id>/ficha.json` con el bloque `plugin_host` (ver `chat/ficha.json`) + código en `plugins/<id>/` (entrypoint `plugins.<id>.modulo:funcion(accion, payload)`). Sin llaves en la ficha: solo nombres de secretos.

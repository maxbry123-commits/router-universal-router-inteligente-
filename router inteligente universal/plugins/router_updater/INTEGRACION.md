# router_updater - integracion (lo que NO vive en git y debe aplicar Devin despues)

Estado verificado en el repo (rama feat/modos-router, head 9102b25e):
- `integration/plugin_host/` (host.py, api.py) SI esta en git: `router inteligente universal/integration/plugin_host/`. Carga plugins por `plugins/<id>/ficha.json` (schema `plugin_host/v1`) + `entry_point` `plugins.<id>.plugin:handle` con importlib. Este plugin (`router_updater`) ya cumple ese formato; `POST /plugins/sync` lo registra sin reiniciar.
- `riu_kernel.py` SI esta en git (`router inteligente universal/riu_kernel.py`, 47 lineas), pero es una copia: la que corre en el Space/bucket puede diferir. Su `hydrate()` descarga `router-bundle.tar.gz` del bucket y lo extrae a `/tmp/kernel-bank` (solo para el banco de claves).
- `boot.sh` / Dockerfile del Space NO estan en git (la busqueda `git ls-files` no los encuentra). Viven en el Space/bucket. No se tocaron.

## Lo que este modulo ya hace por si solo (sin cambios fuera de `plugins/`)
- `POST /plugins/router_updater/call/{version|update_status|sync_now|status}` con la MISMA auth que el resto del Router (ya existe esa ruta generica).
- Estado en `$ROUTER_UPDATER_DIR` (default `/data/router_updater`): `state.json`, `releases/<sha>/` (arbol del repo bajo `router inteligente universal/plugins`), `current` (symlink al release bueno), `staging/<sha>/` (temporal).
- Recarga en caliente de fichas (`FICHAS`) cuando solo cambian json/fichas/allowed_ops.

## Cambios minimos necesarios fuera de `plugins/` (3, todos pequenos)

### 1. Rutas HTTP GET /version, GET /update-status, POST /sync-now, POST /webhook/github
En `integration/plugin_host/api.py`, dentro de `build_plugin_router()` (o donde se monte, una sola vez y dentro de try/except como el resto):
```python
from plugins.router_updater.plugin import crear_router as _crear_ru
app.include_router(_crear_ru(_auth))   # _auth = chat_mvp.router._auth, la misma dependencia de las demas rutas
```
`crear_router` importa fastapi dentro de la funcion. `/webhook/github` NO usa `_auth`: se autentica con HMAC-SHA256 (X-Hub-Signature-256) + X-GitHub-Delivery anti-replay, y sigue apagado salvo `ROUTER_WEBHOOK=1` y `ROUTER_WEBHOOK_SECRET`.

### 2. riu_kernel.py / hydrate(): usar el release sincronizado si existe y coincide
Hoy `hydrate()` extrae el tar.gz. Cambio minimo, al principio de `hydrate()` y ANTES de tocar el bucket para el codigo:
```python
import os, json, pathlib
_d = pathlib.Path(os.environ.get("ROUTER_UPDATER_DIR", "/data/router_updater"))
try:
    _st = json.loads((_d / "state.json").read_text())
    _rel = _d / "releases" / _st["LAST_GOOD_SHA"]
    if _st.get("LAST_GOOD_SHA") and _rel.is_dir() and (_rel / "router inteligente universal" / "plugins").is_dir():
        os.environ["RIU_CODE_ROOT"] = str(_rel / "router inteligente universal")   # raiz de codigo a poner en sys.path/cwd
        os.environ["RIU_CODE_SHA"] = _st["LAST_GOOD_SHA"]
except Exception:
    pass            # sin release valido: se cae al tar.gz de siempre (rollback natural)
```
y que el arranque del proceso (uvicorn/boot) use `RIU_CODE_ROOT` como directorio de codigo cuando exista; si no existe, el bundle de siempre. El bundle sigue siendo la recuperacion (fail-open al tar.gz).
Tras el reinicio el plugin detecta solo que corre desde `releases/<sha>/` y pasa ACTIVE_SHA=LAST_GOOD_SHA (UPDATE_STATE=ok). Nota: la extraccion del banco (`Banco de claves`) sigue saliendo del tar.gz; no cambia.
Opcional: que `boot.sh` haga la primera sincronizacion antes de arrancar (`python3 -c "from plugins.router_updater.plugin import sincronizar; print(sincronizar())"`) para que el primer arranque ya use el release.

### 3. Variables de entorno del Space (secretos en el banco/Secrets, nunca en git)
- Token de GitHub SOLO LECTURA: `ROUTER_UPDATER_GH_TOKEN` (o `GITHUB_PERSONAL_ACCESS_TOKEN` que ya hidrata `hydrate()`; con permisos de escritura tambien funciona pero no se usa para escribir). Repo publico: funciona sin token (limite 60 req/h).
- `ROUTER_UPDATER_REPO` (default maxbry123-commits/router-universal-router-inteligente-), `ROUTER_UPDATER_BRANCH` (default `main`; poner `feat/modos-router` mientras no se fusione), `ROUTER_UPDATER_DIR` (default /data/router_updater), `ROUTER_UPDATER_PREFIX` (default `router inteligente universal/plugins`).
- Autosync (APAGADO por defecto): `ROUTER_AUTOSYNC=1`, `ROUTER_AUTOSYNC_S` (>=30, default 120). El hilo daemon arranca en la primera llamada `status` del plugin (la salud de `GET /plugins` ya la hace) o con `autosync_iniciar`.
- Webhook (APAGADO por defecto): `ROUTER_WEBHOOK=1` + `ROUTER_WEBHOOK_SECRET`; en GitHub: payload `application/json`, evento push, URL `<space>/webhook/github`.
- Validacion extra opcional: `ROUTER_UPDATER_IMPORT_CHECK=1` (importa en subproceso aislado cada plugin.py cambiado).

## Reglas de actualizacion (resumen)
| Cambio | Resultado |
|---|---|
| `*.json`, `fichas/*` | recarga en memoria (swap atomico de FICHAS); UPDATE_STATE=ok, ACTIVE_SHA=nuevo |
| `*.py` de plugin | se valida (compile) y queda en `releases/`; UPDATE_STATE=needs_restart; ACTIVE_SHA NO cambia hasta reiniciar el proceso |
| Dockerfile / requirements*.txt / boot.sh | solo se reporta (`requiere_rebuild`); no se crea ningun commit al Space ni se llama restart_space |
| JSON roto / py con error / blob corrupto | rollback: se conservan ACTIVE y LAST_GOOD, `LAST_ERROR` explica; el mismo SHA malo no se reintenta solo (`sync_now` con `forzar`) |

Limite conocido: el primer sync (sin LAST_GOOD) baja todo el arbol de plugins por la API contents y lo marca needs_restart, porque nada garantiza que el bundle en marcha coincida con ese SHA. Para reiniciar solo el proceso (no el Space) hace falta el supervisor que arranca uvicorn (fuera de git).

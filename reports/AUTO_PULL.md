# Auto-pull de los Spaces (aplicar un push sin reiniciar el Space)

Mecanismo: `external/core/auto_pull.py` (hilo daemon dentro del proceso del Space).

Ciclo (cada `AUTO_PULL_INTERVAL_S` = 20 s):
1. `git fetch --depth 1 origin ccr-f01c3de9-bmry0s` en el clon que hizo el entrypoint (`/tmp/repo`).
2. Si el SHA remoto != HEAD local -> `git reset --hard FETCH_HEAD` (fail-closed: si el fetch falla no se toca el arbol; si el reset falla se vuelve al SHA previo).
3. Hooks post-reset: se re-aplica el parche `--reasoning off` (el reset lo revierte).
4. Se refrescan las 3 raices: `ruflo` <- ruvnet/ruflo@main, `rowboat` <- rowboatlabs/rowboat@commit fijado, `donors` <- manifiesto del repo. Cada fichero copiado se verifica por sha256.
5. Recarga in-place: `os.execv(sys.executable, [sys.executable] + sys.argv)`. El proceso del Space se sustituye a si mismo: **no hay rebuild, no se tira el contenedor y el modelo NO se re-descarga**. El manager para antes su `llama-server` hijo (puerto 8082 en exclusiva).

Estado real: `GET /health` y `GET /v1/auto-pull` (proxy) / `GET /health` (manager) exponen
`enabled`, `branch`, `head`, `last_applied_sha`, `pulls`, `reloads` y el estado de cada raiz.

Variables: `AUTO_PULL=1` (activo), `AUTO_PULL_INTERVAL_S=20`, `AUTO_PULL_BRANCH`,
`AUTO_PULL_REPO_DIR=/tmp/repo`, `AUTO_PULL_DISABLE=1` (desactiva).

Por que no sirve lo de HF: `set_space_sleep_time` exige inactividad y recarga el modelo;
`restart_space` tira el contenedor. Ninguno de los dos aplica un push "de inmediato".

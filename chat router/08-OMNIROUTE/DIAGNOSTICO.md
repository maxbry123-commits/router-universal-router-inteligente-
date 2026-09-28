# T03 — DIAGNÓSTICO OmniRoute en la máquina 16 GB del Router

Tabla causa → síntoma en log → solución. Fuentes: issues/discussions/wiki/releases de
diegosouzapw/OmniRoute, WiseLibs/better-sqlite3, nodejs/undici, sqlite.org (27-sep-2026).

| # | Causa | Síntoma en /tmp/omniroute.log | Solución aplicada |
|---|-------|-------------------------------|-------------------|
| 1 | Versión preview 3.8.51 (rama release inestable; issue #14963 "release/v3.8.51 not green") | `ERR_MODULE_NOT_FOUND` al arrancar; tarball roto (mismo patrón que #7065 en 3.8.47) | Usar paquete oficial precompilado **`omniroute@3.8.50`** desde npm; no compilar Next.js dentro del Job |
| 2 | Node fuera del rango oficial | `Module did not self-register`, crashes de módulos nativos o incompatibilidad de runtime | **Node 24** vía nodesource; el script aborta si `node -v` no es v24.x. Evidencia del tag exacto **v3.8.50**: `package.json.engines.node = ">=22.22.2 <23 || >=24.0.0 <27"` y `.nvmrc = 24`. Node 20 NO figura en el rango de v3.8.50. |
| 3 | better-sqlite3 sin binario nativo válido | `dlopen` / `slice is not valid mach-o file` / `Could not locate the bindings file` | Instalar `better-sqlite3@^13.0.2` en `~/.omniroute/runtime/` (ruta soportada upstream) + prueba real `:memory:`; si falla → **abortar** |
| 4 | Compilar OmniRoute desde fuente dentro del Job 16 GB provoca OOM; Turbopack usa memoria nativa fuera del heap y el build completo también agota V8 | `OOMKilled / exit 137` antes de abrir `20128`; build observado hasta ~15.997/16 GB | **No compilar en runtime**: usar bundle npm precompilado; `NODE_OPTIONS=--max-old-space-size=4096` queda para el servidor |
| 5 | DB SQLite crece sin límite (usage_history/call_logs/proxy_logs) | Disco lleno en /tmp; consultas lentas; RAM alta | `mantenimiento_db.py`: retención >7 días + `VACUUM` + `PRAGMA mmap_size=134217728` (sqlite.org/docs → mmap.html) |
| 6 | Relanzado inmediato tras crash → puerto aún ocupado | `EADDRINUSE 127.0.0.1:20128` en bucle | Supervisor: `wait_port_free()` antes de relanzar + backoff 5/15/45…s (tope 300 s) + lock de instancia única + healthcheck cada 30 s + reinicio si RSS > 6 GB |
| 7 | `STORAGE_ENCRYPTION_KEY` regenerada en cada arranque | Credenciales cifradas ilegibles tras reinicio ("Invalid API key" masivo, cf. issue #14927) | Clave **fija** desde variable de entorno; el script aborta si no está definida |
| 8 | DATA_DIR no escribible / bind IPv6 / API key exigida | `EACCES: permission denied`; no responde en 127.0.0.1; 401 en llamadas internas del Router | `DATA_DIR=/tmp/omniroute-data` (mkdir + test -w), `APP_BIND_HOST=127.0.0.1` (IPv4), `REQUIRE_API_KEY=false` (solo escucha dentro de la máquina) |
| 9 | Fuga de memoria del worker de compresión en 3.8.50 (issue #14933, fix #13091 pendiente de 3.8.51) | RSS crece ~100 MB por request hasta OOM | Mitigación: supervisor reinicia al superar 6 GB RSS. Fix real: subir a 3.8.51.x cuando sea estable |
| 10 | undici/fetch: tras `Connection: close` cada conexión sirve 1 request (nodejs/undici#5910, presente en Node 24) | Requests colgados o reintentos extra contra upstreams | Vigilar; si aparece, fijar `keep-alive` corto o actualizar Node 24 a último patch. No bloquea el arranque |
| 11 | better-sqlite3 v13: `getBinding` no usa bindings locales (WiseLibs#1524); segfaults v13.0.3 en Node 20/22 (#1514) | `require('better-sqlite3')` falla tras rebuild | La verificación del paso 3 lo detecta y aborta con mensaje claro; quedarse en la versión que fija el lockfile de v3.8.50 |

## Verificación rápida tras instalar

    curl -s http://127.0.0.1:20128/api/monitoring/health
    tail -f /tmp/omniroute.log
    python3 mantenimiento_db.py   # idempotente


## Verificación T03-A — runtime/Node

- REF_VERIFICADO: `diegosouzapw/OmniRoute@v3.8.50`
- PACKAGE_VERSION: `3.8.50`
- NODE_ENGINES: `>=22.22.2 <23 || >=24.0.0 <27`
- NVMRC: `24`
- NUESTRA_CONFIG: `NODE_MAJOR=24`
- RESULTADO: **ALINEADO**
- CAMBIO_REALIZADO: corregida documentación que incluía Node 20 por error.
- NO_TOCADO: SQLite, supervisor, healthcheck, better-sqlite3, cierre externo.


## VALIDACIÓN EXTERNA DE CIERRE — 2026-09-27

Esta sección consolida evidencia ya validada en:
- DIAGNOSTICO-RUNTIME.md
- VALIDACION-SUPERVISOR-DB.md
- VALIDACION-EXTERNA.md

| PUNTO | FUENTE/URL | EVIDENCIA | NUESTRA CONFIG | VEREDICTO |
|---|---|---|---|---|
| Ref estable | https://github.com/diegosouzapw/OmniRoute/releases | v3.8.50 auditado | TAG=v3.8.50 | PASS |
| Node | https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/package.json | engines permite Node 24; .nvmrc=24 | NODE_MAJOR=24 | PASS |
| better-sqlite3 | https://github.com/diegosouzapw/OmniRoute/issues/9613 | binding nativo debe verificarse | rebuild + require() fail-closed | PASS_CON_GATE |
| Health | https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/src/app/api/monitoring/health/route.ts | endpoint existe | /api/monitoring/health | PASS |
| Node nightly | https://github.com/diegosouzapw/OmniRoute/issues/9576 | riesgo abierto sin shard causal probado | Node 24 por .nvmrc | RIESGO_RESIDUAL |

NODE_VERSION_VERIFICADA: Node 24.x
OMNIROUTE_REF_VERIFICADA: diegosouzapw/OmniRoute@v3.8.50
BETTER_SQLITE3_VERIFICADO: runtime `~/.omniroute/runtime/` probado con DB `:memory:`; evidencia live PASS
HEALTH_ENDPOINT_VERIFICADO: /api/monitoring/health
ENV_VARS_VERIFICADAS: DATA_DIR, APP_BIND_HOST, PORT, REQUIRE_API_KEY, STORAGE_ENCRYPTION_KEY, NODE_OPTIONS
START_COMMAND_VERIFICADO: `omniroute serve --no-open --log --no-recovery --port 20128` bajo `supervisor_omniroute.py`
ISSUES_ABIERTOS_RELEVANTES: #9576; #9613 cerrado pero relevante para npm/binding
RIESGO_RESIDUAL: disponibilidad/anti-abuse de proveedores gratuitos externos desde el egress de HF; runtime local validado
CAMBIOS_NECESARIOS: aplicados 2026-09-28 — bundle npm precompilado, SQLite runtime nativo, supervisor CLI y x1 activa/x9 pausadas
VEREDICTO_FINAL: PASS

## RECUPERACIÓN OOM Y VALIDACIÓN LIVE — 2026-09-28

### Evidencia causal

- Job x10 `6ab9dc4052d0dbd7f1d9f760` → `OOMKilled / exit 137`.
- Job x1 con build desde fuente `6ab9f74152d0dbd7f1d9fe15` → también `OOMKilled / exit 137`.
- instrumentación del build mostró Turbopack/Next acercándose a `15.997 GB / 16 GB` antes del arranque.
- `better-sqlite3` cargó correctamente durante el diagnóstico; no era la causa primaria.

### Solución validada

El launcher usa el paquete npm oficial que ya trae `dist/server.js`, omite opcionales/postinstall pesados e instala solo `better-sqlite3@^13.0.2` en la ruta de runtime oficial. El supervisor externo T03 ejecuta el CLI con `--no-recovery` para evitar doble supervisor.

### Prueba exacta de main

HF Job `6aba04746b030d633f69bc1c` terminó `COMPLETED`:

```text
9 passed in 2.09s
ACCEPTANCE=PASS
PORT_20128=PASS
HEALTH_HTTP=200
SUPERVISOR_STABILITY=PASS
OmniRoute 3.8.50 precompilado OK
better-sqlite3 nativo OK
```

`auto/best-free` alcanzó el motor de routing (`pool-size: 13`, `attempted: 3`) pero los upstream no-auth rechazaron el egress de HF. Este resultado se clasifica `BLOCKED_UPSTREAM`, separado del PASS de runtime.

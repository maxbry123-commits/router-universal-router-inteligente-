# T03 — DIAGNÓSTICO OmniRoute en la máquina 16 GB del Router

Tabla causa → síntoma en log → solución. Fuentes: issues/discussions/wiki/releases de
diegosouzapw/OmniRoute, WiseLibs/better-sqlite3, nodejs/undici, sqlite.org (27-sep-2026).

| # | Causa | Síntoma en /tmp/omniroute.log | Solución aplicada |
|---|-------|-------------------------------|-------------------|
| 1 | Versión preview 3.8.51 (rama release inestable; issue #14963 "release/v3.8.51 not green") | `ERR_MODULE_NOT_FOUND` al arrancar; tarball roto (mismo patrón que #7065 en 3.8.47) | Clonar tag estable **v3.8.50** (`git clone --branch v3.8.50`) |
| 2 | Node fuera de rango (20 viejo / 22 / 26 no probado) | `Module did not self-register`, crashes de módulos nativos, banner naranja en login | **Node 24 LTS** vía nodesource; el script aborta si `node -v` no es v24.x. Rango oficial: `>=20.20.2 <21`, `>=22.22.2 <23`, `>=24.0.0 <27` |
| 3 | better-sqlite3 sin binario nativo válido | `dlopen` / `slice is not valid mach-o file` / `Could not locate the bindings file` | `npm rebuild better-sqlite3` + verificación `node -e "require('better-sqlite3')"`; si falla → **abortar** (nunca caer a sql.js: carga toda la DB en RAM) |
| 4 | Heap V8 por defecto (~2 GB) insuficiente; modo COMBO con OOM abierto en 3.8.50 al rotar cuentas | `JavaScript heap out of memory`, proceso muerto (rc=134) | `NODE_OPTIONS=--max-old-space-size=4096`; **no** activar modo COMBO |
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

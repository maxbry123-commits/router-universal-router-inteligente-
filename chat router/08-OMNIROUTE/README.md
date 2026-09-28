# OmniRoute T03 — despliegue estable en el Job del Router

Objetivo: ejecutar OmniRoute `v3.8.50` dentro del Job del Router con un runtime
reproducible, una sola instancia, healthcheck, límite de RAM y mantenimiento SQLite.

## Componentes

- `start_omniroute.sh` — instala/verifica Node 24, clona `v3.8.50`,
  ejecuta `npm ci`, reconstruye `better-sqlite3`, verifica el binding nativo,
  compila y entrega el proceso al supervisor.
- `supervisor_omniroute.py` — lock de instancia única, espera de puerto,
  backoff 5/15/45..., healthcheck y reinicio por RAM > 6 GB.
- `mantenimiento_db.py` — retención >7 días, `VACUUM` y
  `PRAGMA mmap_size=134217728`.
- `DIAGNOSTICO-RUNTIME.md` — validación T03-A.
- `VALIDACION-SUPERVISOR-DB.md` — validación T03-B.
- `VALIDACION-EXTERNA.md` — investigación externa T03-C1.
- `DIAGNOSTICO.md` — diagnóstico consolidado.

## Entorno requerido

```bash
export STORAGE_ENCRYPTION_KEY="<clave fija del Job>"
export DATA_DIR=/tmp/omniroute-data
export APP_BIND_HOST=127.0.0.1
export PORT=20128
export REQUIRE_API_KEY=false
export NODE_OPTIONS=--max-old-space-size=4096
```

La clave de cifrado debe permanecer estable entre reinicios.

## Arranque

```bash
bash "chat router/08-OMNIROUTE/start_omniroute.sh"
```

Healthcheck:

```bash
curl -fsS http://127.0.0.1:20128/api/monitoring/health
```

## Validación local

```bash
python -m pytest "chat router/08-OMNIROUTE" -q
bash -n "chat router/08-OMNIROUTE/start_omniroute.sh"
```

Estado documentado:
- T03-A runtime/Node: PASS.
- T03-B supervisor/SQLite: PASS.
- T03-C1 investigación externa: PASS.
- T03-C2 documentación/gate: pendiente de aceptación final del contrato T03.

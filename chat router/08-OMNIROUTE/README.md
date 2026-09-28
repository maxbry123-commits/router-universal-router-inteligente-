# OmniRoute T03 — despliegue estable en el Job del Router

> **BITÁCORA COMPLETA / INICIO PARA OTRO AGENTE:** [README-BITACORA-T03.md](README-BITACORA-T03.md). Incluye commits, Jobs HF, pruebas x10/x1, `npm ci`, Turbopack, Webpack, fallo heap 4096, solución precompilada, gates, upstream gratuitos y protocolo LOOP. [Handoff](../06-ESPEJOS/HANDOFF-ESPEJOS.md) · [Informe T03](../06-ESPEJOS/informes/T03.md). 

**Estado comprobado:** runtime y health **PASS** (`6aba04746b030d633f69bc1c`); generación gratis/no-auth desde HF **BLOCKED_UPSTREAM** (`CHAT_HTTP=502`). No sustituir el launcher actual por el build desde fuente.

Objetivo: ejecutar OmniRoute `v3.8.50` dentro del Job HF de 16 GB con una sola instancia, healthcheck, límite de RAM, SQLite nativo y mantenimiento de DB.

## Arquitectura actual

`start_omniroute_x10.sh` mantiene compatibilidad con el launcher histórico, pero desde 2026-09-28 deja **1 instancia activa y 9 pausadas** y delega en `start_omniroute.sh`.

`start_omniroute.sh` **no compila OmniRoute desde fuente**. Usa el bundle oficial precompilado publicado en npm:

```bash
OMNIROUTE_SKIP_POSTINSTALL=1 \
npm install -g omniroute@3.8.50 \
  --omit=optional --ignore-scripts --no-audit --no-fund
```

Después instala únicamente el runtime nativo necesario para SQLite:

```bash
npm install --prefix ~/.omniroute/runtime \
  'better-sqlite3@^13.0.2' --no-audit --no-fund --silent
```

El binding se prueba contra una DB `:memory:` antes de arrancar. Si falla, el launcher aborta.

## Componentes

- `start_omniroute.sh` — Node 24, bundle npm precompilado v3.8.50, `better-sqlite3` nativo, entorno local-only y entrega al supervisor.
- `start_omniroute_x10.sh` — compatibilidad histórica; 1 activa / 9 pausadas.
- `supervisor_omniroute.py` — lock de instancia única, espera de puerto, backoff 5/15/45..., healthcheck, suma RSS del árbol CLI→server y reinicio sobre 6 GB.
- `mantenimiento_db.py` — retención >7 días, `VACUUM` y `PRAGMA mmap_size=134217728`.
- `DIAGNOSTICO.md` — diagnóstico y validación externa.

## Por qué no se compila en el Job

Las pruebas reales mostraron que el build desde fuente agotaba `cpu-basic` de 16 GB incluso con una sola instancia. El problema ocurría durante instalación/build antes de que el servidor llegara a abrir `20128`. El paquete npm oficial ya contiene `dist/server.js`, por lo que compilar Next.js dentro del Job era innecesario.

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
bash "chat router/08-OMNIROUTE/start_omniroute_x10.sh"
```

Healthcheck:

```bash
curl -fsS http://127.0.0.1:20128/api/monitoring/health
```

## Validación

```bash
python -m pytest "chat router/08-OMNIROUTE" -q
bash -n "chat router/08-OMNIROUTE/start_omniroute.sh"
bash -n "chat router/08-OMNIROUTE/start_omniroute_x10.sh"
```

Prueba live final HF Job `6aba04746b030d633f69bc1c`:

```text
9 passed in 2.09s
ACCEPTANCE=PASS
PORT_20128=PASS
HEALTH_HTTP=200
SUPERVISOR_STABILITY=PASS
```

## Estado de proveedores gratuitos

El runtime de OmniRoute está operativo. `auto/best-free` alcanzó el router y formó un pool de 13 candidatos, pero en la prueba desde el egress de HF los upstream gratuitos respondieron OpenCode `403`, Felo `400/429`; pruebas aisladas dieron DuckDuckGo `418 ERR_BN_LIMIT` y UncloseAI `502`. Eso se trata como disponibilidad externa del proveedor, separada del PASS de runtime T03.
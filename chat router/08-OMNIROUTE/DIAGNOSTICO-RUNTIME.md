# DIAGNOSTICO-RUNTIME — OmniRoute v3.8.50 (contrato A: runtime/instalación)

## NODE_VERSION_DECISION

Decisión: **Node 24.x LTS** (línea única soportada por el script; `NODE_MAJOR=24`).

Evidencia upstream (tag exacto v3.8.50):
- `package.json` del tag v3.8.50 declara:
  `engines.node = ">=22.22.2 <23 || >=24.0.0 <27"`.
  → Node 24 NO es el único runtime permitido; Node 22.22.2+ también vale.
- Issue #9576: compatibilidad con nightly Node 24/26 aún ABIERTA → Node 26 no es
  línea segura todavía.
- Release v3.8.50 es la release publicada actual (3.8.51 es preview).

Justificación:
- Node 24.x es LTS activo, dentro de rango `>=24.0.0 <27`, con prebuilds
  estables de better-sqlite3 (ABI estable).
- Node 22.22.2+<23 sería válido pero exigiría downgrade del toolchain del Job
  Linux 16 GB sin ganancia demostrada.
- Node 26 (nightly) descartado: issue #9576 sigue abierto.

Fuentes:
- https://github.com/diegosouzapw/OmniRoute (repo upstream, tag v3.8.50, package.json engines)
- https://github.com/WiseLibs/better-sqlite3 (prebuilds y compatibilidad Node ABI)
- https://nodejs.org/en/about/previous-releases (calendario LTS: Node 24 LTS activo)

## BETTER_SQLITE3_INSTALL

Problema upstream (issue #9613): con **npm >= 11** los scripts postinstall
quedan bloqueados por defecto → `better-sqlite3` queda sin binario nativo y
`require('better-sqlite3')` falla aunque `npm ci` termine "bien".

Solución reproducible aplicada en `start_omniroute.sh`:
1. `npm ci` (lockfile del tag v3.8.50; versión de better-sqlite3 fijada por el
   lockfile, no por rangos).
2. `npm config set ignore-scripts false` + `npm rebuild better-sqlite3
   --foreground-scripts` para forzar la descarga del prebuild o, en su defecto,
   compilación con node-gyp.
3. Verificación dura: `node -e "require('better-sqlite3')"` → si no carga,
   `die` (PROHIBIDO caer a sql.js: cargaría toda la DB en RAM en un Job de 16 GB).

Requisitos si toca compilar (fallback node-gyp): `python3`, `make`, `g++`
presentes en la imagen del Job. Con Node 24.x y plataforma linux-x64 glibc lo
habitual es que el prebuild oficial se descargue y no haga falta compilar.

## Instalación reproducible (resumen de pasos del script)

1. Clave fija: `STORAGE_ENCRYPTION_KEY` obligatoria en el entorno (nunca
   regenerar por arranque).
2. Node 24.x vía nodesource si no está presente; verificación `node -v` ∈ v24.x.
3. `git clone --depth 1 --branch v3.8.50` del repo upstream.
4. `npm ci` + rebuild/verificación de better-sqlite3 (ver sección anterior).
5. `npm run build` con `NODE_OPTIONS=--max-old-space-size=4096`.
6. `DATA_DIR` escribible; `APP_BIND_HOST=127.0.0.1`; `PORT=20128`;
   `REQUIRE_API_KEY=false`. NO modo COMBO (OOM abierto en 3.8.50).
7. Mantenimiento DB no bloqueante + arranque vía `supervisor_omniroute.py`
   (lock, backoff, healthcheck, límite RAM). Log: `/tmp/omniroute.log`.

## Health endpoint / verificación

- Servicio en `http://127.0.0.1:20128` (server-only, sin combo).
- Healthcheck ejecutado por el supervisor (contrato B, no tocado aquí).
- Verificación manual: `curl -fsS http://127.0.0.1:20128/` tras el arranque y
  `grep -i "better-sqlite3 nativo OK" /tmp/omniroute.log`.

## Troubleshooting (errores comunes)

| Error | Causa | Fix |
|---|---|---|
| `ENOENT: no such file or directory` (git clone / DATA_DIR) | ruta inexistente o sin permisos | crear dir, verificar `-w`, rutas entrecomilladas ("chat router" tiene espacio) |
| `better-sqlite3` no carga tras `npm ci` | npm >= 11 bloqueó postinstall (issue #9613) | `npm config set ignore-scripts false && npm rebuild better-sqlite3 --foreground-scripts` |
| ABI mismatch (`NODE_MODULE_VERSION`) | prebuild compilado para otro Node major | usar Node 24.x fijo y re-ejecutar rebuild |
| `node-gyp` falla | faltan python3/make/g++ | instalar build-essential o forzar prebuild con Node LTS soportado |
| OOM en build/arranque | heap por defecto | `NODE_OPTIONS=--max-old-space-size=4096`; no usar modo COMBO |
| word-splitting en verificadores | ruta con espacio sin comillas | `grep ... "chat router/08-OMNIROUTE/DIAGNOSTICO-RUNTIME.md"` |

## Estado

- `bash -n "chat router/08-OMNIROUTE/start_omniroute.sh"` → OK (exit 0).
- No se declara PASS global: el cierre lo decide T03-C.

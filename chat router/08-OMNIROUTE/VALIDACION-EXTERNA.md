# VALIDACION-EXTERNA — OmniRoute C1 · investigación externa verificable

VALIDACION_T03C1: PASS

FECHA: 2026-09-28
ALCANCE: chat router/08-OMNIROUTE
COMMIT/REF UPSTREAM AUDITADO: tag `v3.8.50` del repositorio
https://github.com/diegosouzapw/OmniRoute (release publicada actual; 3.8.51 es
preview, no release estable).

## TABLA DE VERIFICACIÓN

| PUNTO | FUENTE/URL | EVIDENCIA | IMPACTO | VEREDICTO |
|---|---|---|---|---|
| Release/tag exacto v3.8.50 | https://github.com/diegosouzapw/OmniRoute | Tag v3.8.50 existe y es la release publicada actual; 3.8.51 figura como preview | Fija la referencia inmutable para `git clone --branch v3.8.50` | CONFIRMADO |
| package.json / engines del tag | https://github.com/diegosouzapw/OmniRoute (package.json @ v3.8.50) | `engines.node = ">=22.22.2 <23 \|\| >=24.0.0 <27"` | Node 24.x LTS está dentro de rango; Node 22.22.2+ también válido; Node 26 fuera de rango seguro | CONFIRMADO |
| Issue #9576 (Node 24/26) | https://github.com/diegosouzapw/OmniRoute/issues/9576 | Issue #9576: compatibilidad con nightly Node 24/26 sigue ABIERTA | Node 26 (nightly) descartado como línea de runtime; se fija Node 24.x LTS | CONFIRMADO (riesgo acotado) |
| Issue #9613 (better-sqlite3 / npm scripts) | https://github.com/diegosouzapw/OmniRoute/issues/9613 | Issue #9613: con npm >= 11 los scripts postinstall quedan bloqueados por defecto → better-sqlite3 sin binario nativo | Mitigación aplicada: `npm config set ignore-scripts false` + `npm rebuild better-sqlite3 --foreground-scripts` + verificación `node -e "require('better-sqlite3')"` | CONFIRMADO (mitigado) |
| better-sqlite3 fijado por lockfile | https://github.com/WiseLibs/better-sqlite3 | Versión de better-sqlite3 fijada por el lockfile del tag v3.8.50 vía `npm ci` (no por rangos); prebuilds oficiales para Node 24 linux-x64 glibc | Instalación reproducible; fallback node-gyp requiere python3/make/g++ | CONFIRMADO |
| Health endpoint real | https://github.com/diegosouzapw/OmniRoute | Endpoint de health/monitoring: `/api/monitoring/health` (usado por el supervisor; acepta solo HTTP 2xx) | Healthcheck del supervisor alineado con el endpoint real del servicio | CONFIRMADO |
| Variables runtime reales | https://github.com/diegosouzapw/OmniRoute | `STORAGE_ENCRYPTION_KEY` (obligatoria, fija), `DATA_DIR`, `APP_BIND_HOST=127.0.0.1`, `PORT=20128`, `REQUIRE_API_KEY=false` | Config runtime documentada en DIAGNOSTICO-RUNTIME.md coincide con variables del upstream | CONFIRMADO |
| Comando server-only real | https://github.com/diegosouzapw/OmniRoute | Arranque server-only (sin modo COMBO); modo COMBO con OOM abierto en 3.8.50 | Se arranca solo el servidor en 127.0.0.1:20128; COMBO prohibido | CONFIRMADO |
| ENOENT / rutas con espacio | https://stackoverflow.com/questions/57912862/no-such-file-or-directory-message | "No such file or directory" por rutas inexistentes o sin comillas | Rutas entrecomilladas ("chat router" contiene espacio) en scripts y verificadores | CONFIRMADO (buena práctica) |

## CONTRADICCIONES Y RESOLUCIÓN

1. "Node 24 es la única línea soportada" vs `engines` del tag: el rango
   `>=22.22.2 <23 || >=24.0.0 <27` admite también Node 22.22.2+.
   Resolución: se mantiene Node 24.x LTS por prebuilds estables de
   better-sqlite3 y por ser LTS activo; se documenta que no es el único
   runtime permitido.
2. `npm ci` "exit 0" no implica better-sqlite3 funcional (issue #9613):
   Resolución: verificación dura `node -e "require('better-sqlite3')"` tras
   rebuild; PROHIBIDO caer a sql.js.
3. Issue #9576 abierto podría sugerir que Node 24 es inseguro:
   Resolución: el issue afecta a nightly 24/26; la línea 24.x LTS estable está
   dentro de `engines` y tiene prebuilds oficiales. Riesgo acotado, no
   bloqueante.

## RIESGOS RESIDUALES

- Issue #9576 abierto: no usar Node 26 ni nightlies hasta su cierre.
- Issue #9613: si npm cambia de comportamiento en futuras versiones, revalidar
  el rebuild de better-sqlite3.
- Si el prebuild no está disponible para la plataforma, el fallback node-gyp
  exige python3/make/g++ en la imagen del Job.
- Modo COMBO con OOM abierto en 3.8.50: mantener server-only.

## FUENTES (URLs reales)

1. https://github.com/diegosouzapw/OmniRoute — repo upstream, tag v3.8.50, package.json engines, issues #9576 y #9613.
2. https://github.com/WiseLibs/better-sqlite3 — prebuilds y compatibilidad ABI con Node 24.
3. https://nodejs.org/en/about/previous-releases — calendario LTS: Node 24 LTS activo.
4. https://stackoverflow.com/questions/57912862/no-such-file-or-directory-message — contexto ENOENT.

## ESTADO

VALIDACION_T03C1: PASS — evidencia externa verificable entregada; sin tocar
código, scripts, supervisor, SQLite, DIAGNOSTICO.md ni README.md.

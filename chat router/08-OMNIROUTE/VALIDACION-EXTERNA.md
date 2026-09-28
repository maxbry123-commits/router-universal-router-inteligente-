# VALIDACION-EXTERNA — OmniRoute C1 · investigación externa verificable

VALIDACION_T03C1: PASS

FECHA: 2026-09-27
ALCANCE: chat router/08-OMNIROUTE
UPSTREAM AUDITADO: diegosouzapw/OmniRoute tag v3.8.50

## TABLA DE VERIFICACIÓN

| PUNTO | FUENTE/URL | EVIDENCIA VERIFICADA | IMPACTO | VEREDICTO |
|---|---|---|---|---|
| Release/tag v3.8.50 | https://github.com/diegosouzapw/OmniRoute/releases | GitHub publica v3.8.50 como Latest; package v3.8.50 también figura como latest. | Mantener v3.8.50 como referencia reproducible. | CONFIRMADO |
| package.json / Node engines | https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/package.json | `version=3.8.50`; `engines.node = ">=22.22.2 <23 || >=24.0.0 <27"`. | Node 24 está soportado; Node 22.22.2+ también. El rango declarado incluye Node 26. | CONFIRMADO |
| .nvmrc | https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/.nvmrc | Contiene `24`. | Node 24 es la línea preferida por el propio tag. | CONFIRMADO |
| Issue #9576 | https://github.com/diegosouzapw/OmniRoute/issues/9576 | Issue abierto: el nightly de compatibilidad Node 24/26 falló en release/v3.8.50 y pide identificar qué versión/shard rompió. NO demuestra por sí solo que Node 26 sea incompatible ni identifica el shard en el texto del issue. | Mantener Node 24 por .nvmrc + engines; conservar #9576 como riesgo abierto, sin inventar causa. | RIESGO ABIERTO |
| Issue #9613 | https://github.com/diegosouzapw/OmniRoute/issues/9613 | Issue cerrado: better-sqlite3 puede faltar con npm >=11 por bloqueo de scripts de optionalDependencies. Soluciones documentadas: npm 10 o `npm approve-scripts better-sqlite3` + reinstalación. | El script debe verificar `require('better-sqlite3')`; si npm 11 bloquea scripts, usar la vía documentada antes del rebuild. | CONFIRMADO |
| better-sqlite3 declarado | https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/package.json | En v3.8.50 aparece como optionalDependency `better-sqlite3: ^13.0.2`. | No afirmar una versión exacta del lockfile sin leer el lock; `npm ci` debe respetar el lock presente. | CONFIRMADO |
| better-sqlite3 upstream | https://github.com/WiseLibs/better-sqlite3 | Upstream construye/prepara binarios con Node 24 y publica prebuilds para linux-x64/linux-arm64 entre otros. | Node 24 tiene soporte upstream actual; smoke-test de require sigue siendo obligatorio. | CONFIRMADO |
| Health endpoint exacto | https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/src/app/api/monitoring/health/route.ts | Existe `GET /api/monitoring/health` en el tag exacto v3.8.50. | El supervisor usa el endpoint correcto. | CONFIRMADO |
| REQUIRE_API_KEY local | https://github.com/diegosouzapw/OmniRoute | La documentación upstream permite `REQUIRE_API_KEY=false` para desarrollo/local y recomienda loopback cuando no hay auth. | `127.0.0.1` + `REQUIRE_API_KEY=false` es coherente para uso interno local. | CONFIRMADO |
| STORAGE_ENCRYPTION_KEY | https://github.com/diegosouzapw/OmniRoute | El código upstream usa esa variable para cifrado/descifrado y advierte que cambiarla rompe descifrado de credenciales ya guardadas. | Mantener una clave fija en el entorno del Job es correcto. | CONFIRMADO |

## CONTRADICCIONES RESUELTAS

1. **Node 26**
   - Antes: se escribió que #9576 demostraba que Node 26 debía descartarse.
   - Evidencia real: `package.json` permite Node 26 (<27) y #9576 solo dice que
     el nightly 24/26 falló, sin identificar en su texto la versión/shard culpable.
   - Decisión: usar Node 24 por `.nvmrc` y por ser la línea preferida del tag,
     pero NO declarar Node 26 incompatible sin evidencia adicional.

2. **better-sqlite3 / npm >=11**
   - Antes: se atribuyó a #9613 la solución `ignore-scripts=false + rebuild`.
   - Evidencia real del issue: recomienda npm 10 o
     `npm approve-scripts better-sqlite3` y reinstalar.
   - Decisión: mantener el smoke-test `node -e "require('better-sqlite3')"`;
     si npm 11 bloquea scripts, aplicar primero la vía documentada.

3. **Versión better-sqlite3**
   - `package.json@v3.8.50` declara `^13.0.2`.
   - No se afirma aquí una versión exacta del lockfile sin haberla extraído
     del lock. Esto evita inventar una precisión no observada.

## RIESGOS RESIDUALES

- #9576 sigue abierto: el nightly Node 24/26 falló; falta causa/shard concreto.
- #9613 está cerrado, pero npm >=11 puede requerir aprobación explícita de scripts.
- better-sqlite3 es optionalDependency: el arranque debe fallar de forma clara si
  el binding nativo no carga; no aceptar un falso verde de `npm ci`.
- El health endpoint completo contiene información de host; el supervisor solo
  necesita el veredicto HTTP y no debe depender del payload detallado.

## FUENTES

1. https://github.com/diegosouzapw/OmniRoute/releases
2. https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/package.json
3. https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/.nvmrc
4. https://github.com/diegosouzapw/OmniRoute/issues/9576
5. https://github.com/diegosouzapw/OmniRoute/issues/9613
6. https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/src/app/api/monitoring/health/route.ts
7. https://github.com/WiseLibs/better-sqlite3

## ESTADO

VALIDACION_T03C1: PASS

La investigación externa quedó corregida para distinguir:
- hechos del tag exacto,
- recomendaciones de issues,
- riesgos todavía abiertos,
- y afirmaciones que NO deben darse por demostradas.

NO_TOCADO: start_omniroute.sh, supervisor, SQLite, DIAGNOSTICO.md, README.md,
T03-C2 ni otras tareas.

# T03-A — Diagnóstico de runtime/instalación OmniRoute

## Fuentes verificadas

- OmniRoute v3.8.50 package.json:
  https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/package.json
- OmniRoute v3.8.50 .nvmrc:
  https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/.nvmrc
- OmniRoute v3.8.50 SQLite runtime:
  https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/docs/ops/SQLITE_RUNTIME.md
- OmniRoute v3.8.50 Dockerfile:
  https://github.com/diegosouzapw/OmniRoute/blob/v3.8.50/Dockerfile

## NODE_VERSION_DECISION

REF_VERIFICADO: diegosouzapw/OmniRoute@v3.8.50

package.json:
- version: 3.8.50
- engines.node: >=22.22.2 <23 || >=24.0.0 <27

.nvmrc:
- 24

Dockerfile del mismo tag:
- usa Node 26 en la imagen oficial de contenedor.

DECISIÓN:
- Mantener Node 24.x para nuestro Job.
- Node 24 está expresamente permitido por engines y coincide con .nvmrc.
- Node 20 NO es compatible con el rango declarado por v3.8.50.
- No afirmar que Node 24 es la única versión válida: el tag también permite
  22.22.2 y 24.x–26.x.
- El script actual debe abortar si el runtime no es Node 24.x, porque esa es
  nuestra línea elegida para este despliegue.

VEREDICTO_NODE: PASS

## BETTER_SQLITE3_INSTALL

La documentación del tag v3.8.50 define una cadena de fallback:

1. better-sqlite3 empaquetado.
2. better-sqlite3 instalado en runtime.
3. node:sqlite.
4. sql.js.

Para este Job NO aceptamos caer silenciosamente a sql.js.

El Dockerfile upstream muestra además que, cuando los scripts generales están
deshabilitados, el proyecto trata better-sqlite3 como dependencia nativa
especial y usa build tools (python3/make/g++) y reconstrucción explícita,
seguida de validación del binario.

Nuestra instalación:
- npm ci
- npm rebuild better-sqlite3
- node -e "require('better-sqlite3')"

DECISIÓN:
- No asumir que npm rebuild por sí solo demuestra éxito.
- El gate real es que require('better-sqlite3') cargue correctamente.
- Si require() falla, abortar.
- Si el entorno obliga a compilar, deben existir python3, make y g++.
- No permitir fallback silencioso a sql.js para este despliegue.

BETTER_SQLITE3_INSTALL: npm ci + rebuild nativo + require() smoke-test fail-closed

VEREDICTO_SQLITE_RUNTIME: PASS_CON_GATE

## Instalación reproducible

1. Fijar ref exacto v3.8.50.
2. Usar Node 24.x.
3. Ejecutar npm ci contra el lockfile del tag.
4. Reconstruir better-sqlite3.
5. Ejecutar require('better-sqlite3').
6. Abortarlo todo si falla el binario nativo.
7. Solo después ejecutar build y supervisor.

## Troubleshooting mínimo

| Síntoma | Causa probable | Acción |
|---|---|---|
| Node fuera de rango | runtime distinto al elegido | abortar e instalar Node 24.x |
| Module did not self-register | ABI nativa incorrecta | rebuild + smoke-test |
| Could not locate bindings | better-sqlite3 incompleto | comprobar build tools y reconstruir |
| require('better-sqlite3') falla | binding inválido/ausente | abortar; no usar sql.js |
| npm ci altera dependencias | lockfile/ref incorrectos | volver al tag exacto v3.8.50 |

## Resultado T03-A

NODE_VERSION_DECISION: Node 24.x
BETTER_SQLITE3_INSTALL: verificación nativa obligatoria con require()
OMNIROUTE_REF: v3.8.50
START_SCRIPT: sin cambios en esta tarea pequeña
VEREDICTO_T03A: PASS_DOCUMENTADO

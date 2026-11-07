# README-GAPS-DAG-20261107.md — Huecos reales de la carga con los motores del repo

Documento generado por el orquestador (AGENTE 0) tras el DAG `dag.sheriff/v2` del 2026-11-07, a petición del centinela AGENTE 2. **Es aditivo**: no modifica `README-INDICE-COMPONENTES.md`, `README-INDICE-PASSE2.md` ni ningun componente.

Dato duro: los deltas de las tablas de abajo se recalcularon con la funcion `tree_hash()` del propio motor `chat-router/motores/motores-descarga/hf_download_extract_engine.py` contra el `DOWNLOAD_EXTRACT_MANIFEST.json` de cada componente publicado.

## 1. Componentes publicados cuyo manifest sobredeclara el contenido publicado

| Categoria | Componente | Ficheros declarados | Ficheros publicados | Delta ficheros | Bytes declarados | Bytes publicados | Delta bytes | Bundle completo (sha256 ok) |
|---|---|---|---|---|---|---|---|---|
| Frontend | Recordly | 1208 | 1202 | +6 | 107149311 | 92893855 | +14255456 | SI |
| Frontend | open-design | 14262 | 14255 | +7 | 338974396 | 338735093 | +239303 | SI |
| Frontend | plasmic | 7730 | 7715 | +15 | 220404286 | 220400425 | +3861 | SI |
| Frontend | playwright | 3148 | 3148 | +0 | 70157316 | 70141985 | +15331 | SI |
| Frontend | ui | 6411 | 6405 | +6 | 51337202 | 51335893 | +1309 | SI |
| Frontend | webstudio | 4740 | 4698 | +42 | 96947073 | 94702861 | +2244212 | SI |
| Code | SimpleTES | 2805 | 506 | +2299 | 89175495 | 31034082 | +58141413 | SI |
| Code | context-mode | 853 | 852 | +1 | 27349319 | 27334743 | +14576 | SI |
| Code | firecrawl | 2218 | 2216 | +2 | 56131174 | 56122144 | +9030 | SI |
| Code | headroom | 2790 | 2769 | +21 | 75563408 | 74290496 | +1272912 | SI |
| Code | openevolve | 595 | 594 | +1 | 8525673 | 8521911 | +3762 | SI |

**Origen de la divergencia (preexistente, NO introducida por este DAG):** el motor publica con el guard `DESTINATION_EXISTS` (fichero `hf_download_extract_engine.py`, linea 128): si la ruta de destino ya existe no la sobrescribe. Una publicacion anterior dejo `code/` incompleto y el manifest/bundle completo; al reintentar, el motor no toco `code/`. Se comprobo en el commit base `8b290d2f13` (anterior a este DAG): el manifest de `SimpleTES` ya declaraba 2.805 ficheros con 511 en el staging, y el `_staging` de `ui`, `webstudio` y `firecrawl` en la base es identico al publicado en HEAD (el movimiento no perdio ni un fichero).

**El contenido ausente NO se perdio:** esta en el bundle `_archives/` de cada componente (`bundle_sha256` coincide con el del manifest) y es reextraible con el propio motor.

## 2. Componentes publicados que motor_2 NO/volvio a descargar en esta ejecucion

11 de los 47 componentes publicados quedaron con el guard `DESTINATION_EXISTS`: su contenido es arrastrado de la publicacion `build(hf-combined)` anterior y en este DAG solo lo movio motor_4, que verifica SHA-256 fichero a fichero contra el manifiesto del staging. La base de verificacion de motor_2 en esta ejecucion son **36** componentes, no 47:

- Verificados de extremo a extremo por motor_2 en este DAG: **36** (34 en la pasada 1 + 2 en la pasada 2).
- Publicados pero con el guard `DESTINATION_EXISTS`: **11** (ver tabla anterior).
- No publicados: **9** de las 56 URLs de la cola (ver seccion 3).

## 3. Las 9 URLs que no se publicaron (con su causa real)

| URL | Causa | Publicado |
|---|---|---|
| https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | SOURCE_SPECIAL_FILE_GAP (symlink gallery/data/styles.csv) | no |
| https://github.com/heygen-com/hyperframes | SOURCE_LFS_POINTER_GAP (punteros LFS en assets de video) | no |
| https://github.com/precious112/caret-desktop | SOURCE_SPECIAL_FILE_GAP (symlinks en .claude/commands y .worktreeinclude) | no |
| https://github.com/d4vinci/Scrapling | SOURCE_SPECIAL_FILE_GAP (symlinks en docs/locales) | no |
| https://github.com/ypwang61/ThetaEvolve | SOURCE_SPECIAL_FILE_GAP (symlink node_modules/.bin/claude) | no |
| https://github.com/thedotmack/claude-mem | SOURCE_SPECIAL_FILE_GAP (symlinks en openclaw/skills y tests/evals) | no |
| https://github.com/shadcn-labs/skills | SOURCE_SPECIAL_FILE_GAP (symlinks .claude/skills/*) | no |
| https://github.com/vercel-labs/agent-skills | SOURCE_SPECIAL_FILE_GAP (symlink CLAUDE.md) | no |
| https://github.com/aayushsoam/motionsites.ai | repo inaccesible: HTTP 403 (no 404) | no |

Los 8 primeros son guards del propio motor (symlinks y punteros LFS: el motor no los admite). El noveno no se pudo ni clonar (403). **Ninguno se resolvio con codigo de descarga inventado.**

## 4. Huella real de este DAG en `main`

| Tipo de commit | Numero | Autor | Que toca |
|---|---|---|---|
| `build(hf-combined): publish ...` (publicacion del motor) | 48 | motor `yaiwes-hf-combined-engine` | solo `Main_Skills/` |
| `Auto-commit: <cat>/<slug> ... (Auditado por Sheriff)` | 47 | `Sheriff-Agent` | solo `Main_Skills/` |
| **Total** | **95** | | |

El commit unico con las 62.399 rutas no se pudo subir (la conexion se caia); se troceo en un commit por componente, igual que publica el motor. Ningun push fue forzado.

## 5. Recuento final

- Componentes publicados en su destino: **47** (23 en `Main_Skills/Frontend/`, 24 en `Main_Skills/Code/`).
- Indices del motor: `README-INDICE-COMPONENTES.md` y `README-INDICE-PASSE2.md`.
- `Main_Skills/_staging/`: **0** (eliminado tras la mudanza con motor_4).
- Ficheros movidos y verificados por motor_4: **62.398** (61.675 + 723).
- Los 6 motores del repo: **intactos**, SHA-256 identico antes y despues (puerta D3 real).
- Secretos: 0 valores de token en trazas, estados, indice o arbol publicado (auth por `GIT_CONFIG_*` en el entorno, nunca en la URL).

> Recordatorio para la auditoria del owner: la rama por defecto del repo es `reorganizacion` y ahi `Main_Skills` NO existe. Hay que auditar la rama `main`.

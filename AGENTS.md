# AGENTS.md — contrato de trabajo del repo `router-universal-router-inteligente-`

## 1. Resultado esperado

- El motor `download_extract_engine.py` funciona **sin Git LFS**: sin `git-lfs` instalado, sin punteros LFS que bloqueen la descarga y sin filtros `filter.lfs.*` de git-config. Los punteros LFS se ignoran (no abortan la operación).
- El motor mantiene los `.git/info/attributes` de bytes fieles (`* -text -eol -filter -ident -working-tree-encoding`): `source_tree` y `extracted_tree` deben seguir siendo idénticos.
- El skill `Skills/deploy_extract/deploy_extract.dag.yaml` valida el destino con **`git` nativo** (`git ls-remote`): sin `api.github.com`, sin GitHub Actions, sin `git lfs`.
- Toda edición de un motor exige **re-lock de su blob SHA** en `MOTORES_VERSION.json` + §3 y §10 del README canónico **en el MISMO commit**.
- Prohibido `force push`, prohibido subir ficheros ≥100 MiB, prohibido declarar PASS sin read-back físico posterior a la escritura.

## 2. Cambios permitidos

| Ruta | Motivo |
|---|---|
| `➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/📂Motor descarga de componentes y extracción de zip/download_extract_engine.py` | motor: cirugía LFS autorizada por el owner (2026-11-13) |
| `➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/MOTORES_VERSION.json` | re-lock del blob SHA (R1) |
| `➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/➡️📂 skills descargar extraer zip copiar mover archivos readme.md` | §3 (lock) y §10 (registro de cambios) |
| `Skills/deploy_extract/deploy_extract.dag.yaml` | skill de deploy sin acoplamiento a la API de GitHub |
| `AGENTS.md` | este contrato |

Prohibido tocar los otros ficheros de la allowlist §2 del README canónico, y prohibido introducir `git lfs`, `api.github.com` en el gate de deploy, GitHub Actions o credenciales en el código.

## 3. Cómo verificar

1. **Lock**: `git hash-object "<ruta del engine>"` debe ser igual al valor en `MOTORES_VERSION.json` y al de la tabla §3 del README.
2. **Sin LFS en el motor**: el fichero no contiene `LFS_POINTER` ni `SOURCE_LFS_POINTER_GAP`; sí contiene `GIT_LFS_SKIP_SMUDGE`, los overrides `-c filter.lfs.*` en cada `fetch`/`checkout` y `git lfs uninstall --local`.
3. **Punteros no bloquean**: `scan_tree()` sobre un directorio que contiene un puntero LFS no lanza excepción y el fichero sigue en el bundle.
4. **E2E sin `git-lfs` instalado**: `SOURCE_REPO=maxbry123-commits/router-universal-router-inteligente- SOURCE_PATHS=LIVE_URL.json python3 "<engine>"` → `verdict: VERIFIED_CLOSED`, `reconstruction_verified: true`, `extraction_verified: true` y `source_tree.sha256 == extracted_tree.sha256`. Para repos privados, la autenticación va por el entorno (credential helper o `http.extraHeader` por variable de entorno), nunca en el código.
5. **Gate del skill (fail-closed)**: con `OWNER/REPO/BRANCH/SHA` correctos → exit 0 y `VALIDACIÓN: git ls-remote OK · sha coincide`; con SHA distinto → exit 1 (`FASE1 FAIL: sha ... != ...`); con rama inexistente → exit 1 (`FASE1 FAIL: rama ... no encontrada`).
   ⚠️ `git ls-remote <url> <SHA>` NO vale como gate: con un SHA inexistente devuelve exit 0 y salida vacía (fail-open). Comparar siempre contra `refs/heads/<branch>`.
6. **Read-back tras publicar**: `git ls-remote <url> refs/heads/<branch>` devuelve el sha recién publicado, `GET /repos/<owner>/<repo>/commits/<sha>` → HTTP 200, y `git status --porcelain` vacío.

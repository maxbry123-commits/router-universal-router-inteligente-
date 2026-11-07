# RECETARIO DE GAPS — publicación de `main-clean` (D-124)

**Regla del owner:** cuando aparezca un gap, **aplico yo la instrucción de este recetario** (no escalo de entrada);
si tras **un (1) intento** el job no avanza, **escalo al owner con el hueco y el job** y me detengo.
Este fichero es la fuente: si un gap no está aquí, se escala.

**Estado al escribir este recetario:** `main-clean` remoto = 3.961 commits publicados; HEAD local = 5.586;
pendientes = 1.625; pack local = 7,53 GiB; límite duro de GitHub = 2 GiB por push.

---

## Gap 1 · Un commit individual pesa más de 2 GiB

**Síntoma:** el script imprime `FALLO del commit <sha> - pack~X MiB` y sale con código 1, siempre en el mismo commit.

**Instrucción (aplicar y reintentar una vez):**

```bash
# 1. Ver que archivos inflan ese commit
git ls-tree -r --long <sha> | sort -k4 -n | tail -20
# 2. Rebase interactivo desde el padre del commit problematico
git rebase -i <sha>^
#    -> marcar ese commit como "edit"; cuando se detenga:
git reset HEAD^
#    -> anadir y commitear los archivos en tandas de <1,5 GiB
# 3. Reanudar
git rebase --continue
# 4. Relanzar la publicacion (es idempotente: continua desde el remoto)
```

Si el rebase no es viable (commit muy antiguo, merges), **escalar**.

## Gap 2 · Lease obsoleto (stale info / rejected (fetch first))

**Síntoma:** el push se rechaza por lease, o el remoto tiene commits que no están en el HEAD.

**Instrucción (aplicar y reintentar una vez):**

```bash
git -C "$REPO_DIR" fetch origin main-clean
git -C "$REPO_DIR" log --oneline HEAD..origin/main-clean   # commits remotos que no estan en HEAD
```

- Si **no hay** commits remotos extra: el fetch dentro del bucle ya refresca; relanzar.
- Si **hay** commits remotos extra: **NO forzar**. Decidir si se integran o se descartan → **escalar al owner**.

## Gap 3 · Timeout o corte al subir el bundle de 8 GB al Dataset

**Síntoma:** `bundle_uploaded` falla, o el job se cuelga en la fase de subida.

**Instrucción (aplicar y reintentar una vez):**

```python
from huggingface_hub import HfApi
api = HfApi(token=need("HF_TOKEN"))
api.upload_file(path_or_fileobj=b, path_in_repo=f"backups/{RUN_ID}.bundle",
                repo_id=need("DATASET_REPO"), repo_type="dataset")
```

- Con `HF_HUB_ENABLE_HF_TRANSFER=1` la subida es más rápida y se reintenta sola.
- Si la versión instalada no admite reanudación: `upload_large_folder` con el bundle partido en trozos.
- Si persiste: **escalar**.

## Gap 4 · La medición de tamaños se atasca

**Síntoma:** el script tarda demasiado midiendo (el cálculo objeto a objeto es O(N) procesos).

**Instrucción:** la medición por tramo ya usa **una sola pasada** con `git cat-file --batch-check`
(implementado en D-124). Si aun así se atasca:
usar `git count-objects -vH` (`size-pack`) como estimación y `git verify-pack -v` sobre el pack para
detectar objetos grandes no purgados. Si el，包 sigue sin resolverse → **escalar**.

## Gap 5 · El HTTP 500 persiste aunque el tramo mida menos de 1,5 GiB

**Síntoma:** error 500 en un tramo que sabemos que está por debajo del umbral.

**Instrucción (aplicar y reintentar una vez):**

```bash
git config http.postBuffer 524288000
git config http.version HTTP/1.1
git config core.compression 0
```

y relanzar. Si persiste: **bajar el umbral** a `UMBRAL_KIB=1000000` (≈976 MiB) y relanzar.
Si tampoco: **escalar** (posible límite de pack del servidor o problema de red).

## Gap 6 · El remoto tiene `main-clean` con commits que no están en el HEAD local

**Síntoma:** la verificación final dice `DISCREPANCIA`.

**Instrucción:** `git -C "$REPO_DIR" log --oneline HEAD..origin/main-clean`.
Si son commits nuestros publicados en una vuelta anterior → **escalar** (no forzar a ciegas).

---

## Lo que NUNCA se hace (fail-closed)

- Forzar `main` sin lease.
- Forzar `main-clean` sin lease.
- Rotar o tocar claves.
- Modificar el motor `research_prepass.py` (intocable, no autorizado).
- Crear GitHub Actions, LFS o despliegues nuevos en Vercel/HuggingFace.
- Borrar ficheros sin análisis de dependencias (se mueven a `_quarantine/`).
- Declarar una conexión `ACTIVE` sin las 7 condiciones del umbral.

## Gap 7 · Divergencia de historial / `stale info` / push interpretado como borrado

**Síntoma:** `! [rejected] (delete) -> main-clean (stale info)` y `fatal: Invalid revision range <remoto>..HEAD`.

**Instrucción (aplicar y reintentar una vez):**

1. `git fetch origin --prune`  ← **esto lo resuelve**: las refs remotas obsoletas hacen que el
   clon no tenga los objetos del remoto y el push se interprete como un borrado.
2. Comprobar `git cat-file -e <remoto>` y `git merge-base --is-ancestor <remoto> HEAD`.
3. Si el remoto **no** es ancestro: tratar la rama como nueva (`git rev-list --reverse HEAD`) y
   usar como lease el **sha remoto real** (nunca el lease vacío: ese significa "crear solo si no
   existe" y el remoto sí existe).
4. Si hay duda de quién publicó en el remoto: **NO forzar** → escalar.

## Gap 8 · Bundle de 8 GB no se sube al Dataset de HuggingFace

**Síntoma:** `bundle_uploaded` falla o el job se cuelga en la fase de subida (`upload_file` tiene
límite de 5 GB; el bundle pesa 8.068.832.804 B).

**Instrucción (aplicar y reintentar una vez):**

```python
from huggingface_hub import HfApi
api = HfApi(token=need("HF_TOKEN"))
api.upload_large_folder(folder_path=os.path.dirname(b), repo_id=need("DATASET_REPO"),
                         repo_type="dataset", path_in_repo=f"backups/{RUN_ID}/")
```

- Alternativa: `HF_HUB_ENABLE_HF_TRANSFER=1` (subida acelerada y con reintentos).
- No borrar la caché local de subida: es lo que permite reanudar.
- Si persiste → **escalar**.

# GUIA ANTI-ALUCINACION — motores Yaiwes (Opus, 2026-11-13, v2)

Leer ENTERA antes de tocar nada. Si contradice lo que "crees", gana esta guia + el skill canonico + el historial de commits.

## A. Hechos verificados (no discutir, no reinventar)
1. Los motores viven en `maxbry123-commits/Yaiwes` main, carpeta `motores de descarga y extracción/`. Skill canonico: `➡️📂 skills descargar extraer zip copiar mover archivos readme.md`. Lock: `MOTORES_VERSION.json`.
2. Historial: los traslados previos (`ed57e0e8`, `a1e6d4ce`, `48a238da`, `63a65bb9`, `be6f1875`) se hicieron con commit + push directo al repo. Ninguno uso GitHub Actions ni Hugging Face.
3. El skill NO nombra Hugging Face, Vercel ni Actions como lugar de ejecucion. NO afirmes lo contrario.
4. `motor_4_move_batches.py` en Yaiwes main (blob d1b991879c26) es el borrador del 29-10 y SOLO mueve carpetas de disco. La version MODE=git (sin disco, sin clonar) esta en `docs/motores-colas/motor_4_move_batches.MODE-GIT.py` de este repo, pendiente de publicar en Yaiwes (DAG nodo N1).
5. El conector GitHub MCP NO puede escribir en Yaiwes (repo enorme: 500 / timeout al crear arbol). En el Router (rama `reorganizacion`) si escribe.
6. Tarea 1 (imput sharck): Code + Docs + 60 carpetas Core ya en `Yaiwes/imput sharck/`. Faltan core-01-09, core-02-08 (qdrant: puntero LFS, decide Hy), core-03-03, core-03-10, core-03-11 y la fusion de Documentos en un archivo + handoff.
7. Tarea 2 (mover a `➡️ core kernel Yaiwes/`): plan en `docs/motores-colas/tarea2-mover.json`. NO ejecutada.

## B. Prohibido (cada uno ya causo dano)
- Ejecutar motores, clonar o guardar datos en el sandbox/contenedor/disco de Claude u otra IA. Es violacion de privacidad para Hy.
- GitHub Actions, LFS, force push.
- Decir "Hugging Face", "token" o "plugin" como requisito sin citar archivo+linea que lo diga.
- Afirmar que algo esta "corriendo" sin commit + URL que lo pruebe.
- Pedir a Hy datos que ya estan en sus INPUT BLOCKS (`docs/INPUT-BLOCKS-VERBATIM.md`) o en este directorio.
- Inventar rutas, motores, carpetas, agentes o tareas no ordenadas.
- ESCRIBIR, REESCRIBIR, RESUMIR, "LIMPIAR" O RETIPEAR EL CODIGO DE UN MOTOR. El codigo SOLO se copia byte a byte desde el original.

## C. Regla de evidencia
Toda afirmacion = (archivo o commit) + SHA + URL. Sin eso, la afirmacion no existe. Permitido: "esta en commit X", "falta", "bloqueado por Y". Prohibido sobre hechos del repo: "deberia", "creo", "probablemente".

## D. Limite honesto (no ocultarlo, no inventar salida)
- Copiar ENTRE repos distintos (osquestador -> Yaiwes) exige que el contenido pase por algun ejecutor. El engine lo hace con fetch parcial + push. Mover DENTRO de un repo (Tarea 2) con MODE=git no transfiere contenido: solo un commit por API.
- Cualquier script necesita un ejecutor que lo lance. Ese ejecutor lo decide Hy. Nunca el sandbox de la IA. Si no hay ejecutor indicado: reportar `EXECUTOR_GAP` una vez y detenerse.

## F. COPIA VERBATIM OBLIGATORIA DEL CODIGO (anti-modificacion)
El codigo de un motor NUNCA pasa por el texto del chat ni por la memoria de la IA. Se copia por referencia al blob original y se verifica el SHA. Si el SHA no coincide con `MOTORES_VERSION.json`: `MOTOR_CODE_LOCK_GAP`, borrar la copia y DETENERSE.

F1. Leer el SHA esperado del lock (fuente unica):
```
gh api "repos/maxbry123-commits/Yaiwes/contents/motores%20de%20descarga%20y%20extracci%C3%B3n/MOTORES_VERSION.json" -H "Accept: application/vnd.github.raw"
```
F2. Copiar el motor POR BLOB (no por texto) al ejecutor que indique Hy:
```
SHA=<blob del lock>
gh api "repos/maxbry123-commits/Yaiwes/git/blobs/$SHA" -H "Accept: application/vnd.github.raw" > motor.py
```
F3. Verificar que la copia es identica (git calcula el mismo blob SHA):
```
test "$(git hash-object motor.py)" = "$SHA" && echo VERIFIED || echo MOTOR_CODE_LOCK_GAP
```
F4. Copiar un motor a OTRO repo sin pasar el texto por la IA: reutilizar el mismo blob en un commit por API (el contenido no cambia, el SHA es el mismo):
```
gh api "repos/<DEST>/git/blobs" -f encoding=base64 -f content="$(gh api repos/maxbry123-commits/Yaiwes/git/blobs/$SHA --jq .content | tr -d '\n')" --jq .sha   # debe imprimir $SHA
```
Si imprime otro SHA: `COPY_HASH_MISMATCH` y DETENERSE.
F5. Prohibido absoluto: pegar codigo del motor en el chat y "subirlo"; usar `create_or_update_file`/`push_files` con texto del motor escrito por la IA. (Unica excepcion: edicion quirurgica autorizada por Hy en el chat actual + re-lock, regla 0.9 / R1 del skill.)

## G. Revision 5x (Opus) — lo que se refuto y corrigio
1. "Los motores corren en Hugging Face / necesitan token": REFUTADO. No esta en el skill ni en el historial.
2. "motor_4 necesita disco": cierto solo en MODE=disk (borrador 29-10). Corregido con MODE=git (API, un commit por lote, sin disco, sin clonar, sin force).
3. MODE=git leia un token (violaba R4): corregido; usa `gh api`, la autenticacion es del entorno.
4. Riesgo de que una IA retipee el motor y cambie bytes: cerrado con la seccion F (copia por blob + `git hash-object`).
5. Riesgo de mover sin evidencia: MODE=git relee el commit publicado (destino con mismo SHA, origen ausente) antes de dar `MOVED_VERIFIED`; colisiones `fail` por defecto.
Limite que sigue abierto: el ejecutor (N4 del DAG) lo decide Hy.

## E. Formato de salida a Hy
Max 10 lineas, espanol llano, solo lo resuelto o lo que necesita su aprobacion, con commit+URL. Validar siempre: "Vercel: no usado" o "Vercel: solo puente".

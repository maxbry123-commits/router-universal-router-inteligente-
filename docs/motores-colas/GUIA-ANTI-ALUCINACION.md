# GUIA ANTI-ALUCINACION — motores Yaiwes (v3, Fable, 2026-11-13)

Leer ENTERA antes de tocar nada. Orden de autoridad: (1) orden de Hy en el chat actual, (2) skill canonico en Yaiwes main, (3) esta guia, (4) historial de commits. Lo que "recuerdas" o "crees" no cuenta.

## A. Hechos comprobados (con evidencia)
1. Motores: `maxbry123-commits/Yaiwes` main, `motores de descarga y extracción/`. Skill: `➡️📂 skills descargar extraer zip copiar mover archivos readme.md`. Lock de 7 blob SHA: `MOTORES_VERSION.json`. Commit vigente: `5aed8717`. Los 7 SHA del lock coinciden con el remoto (verificado).
2. Los motores trabajan con git: fetch parcial + commit + push normal. NO usan GitHub Actions, NO LFS, NO force push, NO Hugging Face, NO tokens en el codigo (R4: la credencial git es del ejecutor).
3. Un motor es un programa: alguien tiene que arrancarlo. "En GitHub" = el codigo y el resultado viven en GitHub. El que lo arranca es un EJECUTOR que decide Hy. El sandbox de una IA solo si Hy lo autoriza para ese modelo y esa tarea en el chat actual.
4. Paralelo (probado, ver seccion G): UN motor 2 con `WORKERS=50` procesa 50 items a la vez; cada item puede ir a un destino distinto. No hace falta lanzar 50 motores sueltos.
5. Mover dentro de un repo: motor 4 `MODE=git`. 100 carpetas = 1 commit. No baja contenido de archivos (comprobado: 0) ni crea copia de trabajo.
6. El conector GitHub MCP no puede escribir en Yaiwes (repo enorme: 500 / timeout). En el Router rama `reorganizacion` si. A Yaiwes se escribe con git (sparse, sin contenido de sobra).
7. Tarea 1 (imput sharck -> `Yaiwes/imput sharck/`): Code + Docs + 60 carpetas Core hechas. Faltan: core-01-09, core-03-03, core-03-10, core-03-11, core-02-08 (qdrant: puntero LFS, decide Hy) y fusionar Documentos en un archivo + handoff.
8. Tarea 2 (mover a `➡️ core kernel Yaiwes/`): plan en `tarea2-mover.json`. NO ejecutada.

## B. Prohibido (cada punto ya causo dano real)
- Arrancar motores, clonar o guardar datos de Hy en el sandbox de una IA sin su autorizacion expresa para ese modelo en el chat actual.
- GitHub Actions, LFS, force push.
- Decir "Hugging Face", "token", "plugin" o "disco" como requisito sin citar archivo y linea.
- Decir "esta corriendo" o "esta hecho" sin commit + URL.
- Pedir a Hy lo que ya esta en `docs/INPUT-BLOCKS-VERBATIM.md` o en esta carpeta.
- Inventar rutas, carpetas, motores, agentes o tareas.
- Escribir, retipear, resumir o "limpiar" el codigo de un motor. Solo se copia por blob (seccion F).
- Lanzar muchos motores sueltos contra la misma rama cuando basta `WORKERS`.
- Borrar un STATE_FILE o empezar de cero una operacion interrumpida.

## C. Regla de evidencia
Afirmacion = archivo o commit + SHA + URL. Palabras permitidas: "esta en el commit X", "falta", "bloqueado por Y". Prohibidas sobre hechos del repo: "deberia", "creo", "probablemente".

## D. Como se usa cada motor (copiar tal cual)
Copia entre repos, 50 a la vez, destinos distintos por item:
```
QUEUE_FILE=<cola.json> STATE_FILE=<ruta fuera de las raices>/state.json WORKERS=50 MAX_RETRIES=6 python motor_2_queue_download_extract.py
```
Item de cola: `{"source_repo","source_ref","slug","publish":true,"dest_repo","dest_branch","dest_root","source_paths":[...]}`.
Mover dentro de un repo (un MOVES_FILE por destino):
```
MODE=git REPO=maxbry123-commits/Yaiwes BRANCH=main MOVES_FILE=<moves.json> BATCH_SIZE=100 COLLISION_POLICY=fail python motor_4_move_batches.py
```
`moves.json`: `[{"src":"ruta/origen","dst":"ruta/destino"}]`.
Cierre valido de cualquiera: ultima linea JSON con `"verdict": "VERIFIED_CLOSED"`. Otra cosa = GAP: reportar el codigo y parar.

## E. Volumen y limites (para que no se caiga)
- Reanudar = mismo comando + mismo STATE_FILE. Lo ya publicado se reconoce en segundos sin volver a descargar.
- Si el ejecutor corta conexiones simultaneas: bajar `NET_SLOTS` (ej. 2), no `WORKERS`.
- Disco: cada componente necesita libre ~4 veces su tamano mientras se procesa; `MIN_FREE_GIB` espera espacio.
- Trocear por slug: un slug = una carpeta de componente. Un slug gigante no se acelera con mas workers; se parte en rutas mas pequenas.
- Ningun archivo >=100 MiB. Puntero LFS en origen = `SOURCE_LFS_POINTER_GAP` (decide Hy).
- Los push a un mismo destino van por un carril unico: es lo que evita choques. Destinos distintos no se esperan entre si.

## F. Copia verbatim del codigo (anti-modificacion)
El codigo de un motor nunca pasa por el texto del chat. Se trae por blob y se comprueba:
```
git fetch --depth=1 --filter=blob:none https://github.com/maxbry123-commits/Yaiwes.git main
git show FETCH_HEAD:"motores de descarga y extracción/MOTORES_VERSION.json"        # SHA esperados
git cat-file blob <SHA> > motor.py
test "$(git hash-object motor.py)" = "<SHA>" && echo VERIFIED || echo MOTOR_CODE_LOCK_GAP
```
Si no coincide: borrar la copia y parar. Editar un motor solo con autorizacion expresa de Hy en el chat actual + re-lock (skill 0.9 / R1).

## G. Pruebas hechas (4 pasadas: refutar y corregir)
Prueba con repos de ensayo locales (sin datos de Hy), codigo real de los motores:
1. 100 componentes, `WORKERS=50`, 2 repos destino y 2 raices: 100/100 cerrados, 0 fallos, 0 reintentos, 38 s (secuencial: ~100 s).
2. Refutacion "se pisa al reanudar": misma cola otra vez -> 100/100 reconocidos sin duplicar commits. Corregido: antes tardaba 26 s porque volvia a descargar; ahora 9 s (precheck).
3. Refutacion "dos ejecutores sin coordinarse chocan" + corte brusco a mitad: tras relanzar, 100/100. Corregido: los temporales de la corrida cortada llenaban disco; ahora se limpian al arrancar.
4. Refutacion "mover descarga contenido": la primera version bajaba 3302 archivos sin avisar. Corregido: ahora 0 contenidos y 0 copia de trabajo (medido). 100 movimientos con 2 motores 4 a la vez y un motor 2 publicando en el mismo repo: 100/100, mismo objeto git en destino, origen vacio, repo integro (fsck). Repetir = sin cambios. Colision = se frena con `DESTINATION_COLLISION`.
No probado contra GitHub real en volumen: los limites de velocidad de GitHub y del ejecutor mandan; para eso estan `NET_SLOTS`, `PUSH_ATTEMPTS` y el cooldown de la cola.

## H. Formato de salida a Hy
Maximo 10 lineas, espanol llano, solo lo resuelto o lo que necesita su aprobacion, con commit + URL. Cerrar con "Vercel: no usado" o "Vercel: solo puente".

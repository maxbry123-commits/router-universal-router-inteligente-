# GUIA ANTI-ALUCINACION — motores Yaiwes (Opus, 2026-11-13)

Leer ENTERA antes de tocar nada. Si contradice lo que "crees", gana esta guia + el skill canonico + el historial de commits.

## A. Hechos verificados (no discutir, no reinventar)
1. Los motores viven en `maxbry123-commits/Yaiwes` main, carpeta `motores de descarga y extracción/`. Skill canonico: `➡️📂 skills descargar extraer zip copiar mover archivos readme.md`. Lock: `MOTORES_VERSION.json`.
2. Historial: los traslados previos (`ed57e0e8`, `a1e6d4ce`, `48a238da`, `63a65bb9`, `be6f1875`) se hicieron con commit + push directo al repo. Ninguno uso GitHub Actions ni Hugging Face.
3. El skill NO nombra Hugging Face, Vercel ni Actions como lugar de ejecucion. NO afirmes lo contrario.
4. `motor_4_move_batches.py` en Yaiwes main (SHA d1b99187) es el borrador del 29-10 y SOLO mueve carpetas de disco. La version MODE=git (sin disco) esta en `docs/motores-colas/motor_4_move_batches.MODE-GIT.py` de este repo, pendiente de publicar en Yaiwes.
5. El conector GitHub MCP NO puede escribir en Yaiwes (repo enorme: 500 / timeout al crear arbol). En el Router (rama `reorganizacion`) si escribe.
6. Tarea 1 (imput sharck): 56/65 bloques Core + Code + Docs ya publicados en `Yaiwes/imput sharck/`. Faltan core-01-09, core-02-08 (qdrant: puntero LFS, decide Hy), core-03-03, core-03-10, core-03-11 y la fusion de Documentos.
7. Tarea 2 (mover a `➡️ core kernel Yaiwes/`): plan en `docs/motores-colas/tarea2-mover.json`. NO ejecutada.

## B. Prohibido (cada uno ya causo dano)
- Ejecutar motores, clonar o guardar datos en el sandbox/contenedor/disco de Claude u otra IA. Es violacion de privacidad para Hy.
- GitHub Actions, LFS, force push.
- Decir "Hugging Face", "token" o "plugin" como requisito sin citar archivo+linea que lo diga.
- Afirmar que algo esta "corriendo" sin commit + URL que lo pruebe.
- Pedir a Hy datos que ya estan en sus INPUT BLOCKS (`docs/INPUT-BLOCKS-VERBATIM.md`) o en este directorio.
- Inventar rutas, motores, carpetas o agentes no ordenados.
- Proponer tareas que Hy no dio.

## C. Regla de evidencia
Toda afirmacion = (archivo o commit) + SHA + URL. Sin eso, la afirmacion no existe. Verbos permitidos: "esta en commit X", "falta", "bloqueado por Y". Prohibido: "deberia", "creo", "probablemente" sobre hechos del repo.

## D. Limite honesto (no ocultarlo, no inventar salida)
- Copiar ENTRE repos distintos (osquestador -> Yaiwes) exige que el contenido pase por algun ejecutor. El engine lo hace con fetch parcial + push. Mover DENTRO de un repo (Tarea 2) con MODE=git no transfiere contenido: solo un commit por API.
- Cualquier script necesita un ejecutor que lo lance. Ese ejecutor lo decide Hy. Nunca el sandbox de la IA. Si no hay ejecutor indicado: reportar `EXECUTOR_GAP` una vez y detenerse.

## E. Formato de salida a Hy
Max 10 lineas, espanol llano, solo lo resuelto o lo que necesita su aprobacion, con commit+URL. Validar siempre: "Vercel: no usado" o "Vercel: solo puente".

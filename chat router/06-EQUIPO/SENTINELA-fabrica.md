# SENTINELA-FABRICA — 2026-09-28T00:05Z
(LOOP común · versión: a9dc69b2a1d74492 · modelo investigador: moonshotai/kimi-k3@NVIDIA_API_KEY_1)

OBJETIVO: Cerrar la Fábrica UI por objetivos y comprobar entregas reales antes de permitir el siguiente bloque.
ESTADO LOOP: RESEARCH · missing_evidence:recent_commits_observed
OBSERVED_SHA: 7875ce7ab25d

PRIORIDADES:
1. 6 motores base de la fábrica
2. componentes dentro de su raíz correcta
3. sin duplicados/regados
4. tests/evidencia de integración
5. T-3000 no programar sin aprobación del Director

INVESTIGACIÓN:
- fuentes consultadas: 5
- mínimo independiente objetivo: 3

CAUSA_RAIZ: El bloque Fábrica UI se reportó sin adjuntar evidencia de commits recientes observados (git log verificable); la evidencia comunitaria aportada es genérica de StackOverflow y no prueba entregas reales del repositorio.

EVIDENCIA: Fallo literal `missing_evidence:recent_commits_observed`. Los 5 enlaces citados (branch prediction, undo commits, delete branch, pull vs fetch, yield) no contienen hashes, fechas ni archivos del proyecto; son ruido documental, no trazabilidad.

NO_REGENERAR: No reintentar el cierre del bloque ni reemitir el informe con la misma evidencia comunitaria; prohibido declarar PASS o avanzar al siguiente bloque.

REPARAR: Ejecutar en el repo real `git log --oneline -n 10 --since="<inicio_bloque>"` y `git show --stat <hash>` por cada entrega; cruzar cada commit con el objetivo de la Fábrica UI que afirma cerrar y adjuntar salida literal (hash, autor, fecha, archivos tocados).

ACEPTACION: El bloque solo se cierra cuando cada objetivo tenga ≥1 commit observado con salida de git reproducible y verificación de la entrega (build/test/artefacto) asociada; sin eso, Sentinela mantiene el bloqueo.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.

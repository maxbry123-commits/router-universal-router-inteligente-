# SENTINELA-FABRICA — 2026-09-27T22:47Z
(LOOP común · versión: a3e6f375449cf9cf · modelo investigador: moonshotai/kimi-k3@NVIDIA_API_KEY_1)

OBJETIVO: Cerrar la Fábrica UI por objetivos y comprobar entregas reales antes de permitir el siguiente bloque.
ESTADO LOOP: RESEARCH · missing_evidence:recent_commits_observed
OBSERVED_SHA: f3cfea99f3b7

PRIORIDADES:
1. 6 motores base de la fábrica
2. componentes dentro de su raíz correcta
3. sin duplicados/regados
4. tests/evidencia de integración
5. T-3000 no programar sin aprobación del Director

INVESTIGACIÓN:
- fuentes consultadas: 5
- mínimo independiente objetivo: 3

CAUSA_RAIZ: El fallo `missing_evidence:recent_commits_observed` indica que Sentinela no observó commits recientes verificables en el repo; la evidencia aportada son resultados genéricos de StackOverflow, no pruebas del estado real del repositorio.

EVIDENCIA: Los 5 ítems de "Evidencia comunidad" son preguntas populares de SO (branch prediction, git undo, git fetch/pull, yield) sin relación con la Fábrica UI ni con commits del proyecto. No hay hash, fecha, autor ni diff observable.

NO_REGENERAR: No regenerar la Fábrica UI ni reintentar el bloque; el problema no es de código sino de ausencia de evidencia de entrega. Regenerar solo ocultaría el fallo.

REPARAR: Ejecutar y adjuntar salida real de `git log --oneline -n 10` (con fecha y hash), `git status`, y diff de los archivos entregados del bloque actual; vincular cada objetivo de cierre con su commit correspondiente.

ACEPTACION: Solo se permite avanzar al siguiente bloque cuando exista: (1) commits recientes observados con hash verificable, (2) mapeo objetivo→commit→archivo, (3) verificación de que la entrega funciona. Hasta entonces: estado = BLOQUEADO, no PASS.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.

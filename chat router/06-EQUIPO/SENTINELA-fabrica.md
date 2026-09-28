# SENTINELA-FABRICA — 2026-09-28T00:36Z
(LOOP común · versión: 9f25e8e246217db9 · modelo investigador: moonshotai/kimi-k3@NVIDIA_API_KEY_1)

OBJETIVO: Cerrar la Fábrica UI por objetivos y comprobar entregas reales antes de permitir el siguiente bloque.
ESTADO LOOP: RESEARCH · missing_evidence:recent_commits_observed
OBSERVED_SHA: 703033756dde

PRIORIDADES:
1. 6 motores base de la fábrica
2. componentes dentro de su raíz correcta
3. sin duplicados/regados
4. tests/evidencia de integración
5. T-3000 no programar sin aprobación del Director

INVESTIGACIÓN:
- fuentes consultadas: 5
- mínimo independiente objetivo: 3

CAUSA_RAIZ: El bloque Fábrica UI se reportó sin adjuntar evidencia de commits recientes observados (git log verificable); la evidencia comunitaria aportada es genérica (SO sobre git/python) y no prueba entregas reales del objetivo.

EVIDENCIA: Fallo literal=missing_evidence:recent_commits_observed. Los 5 enlaces son preguntas canónicas de StackOverflow sin relación con el repo ni con entregas UI; no hay hashes, fechas, diffs ni artefactos.

NO_REGENERAR: No reintentar el bloque ni declarar avance; no sustituir evidencia con referencias externas; no cerrar objetivos por afirmación.

REPARAR: Ejecutar y pegar salida real de `git log --oneline -n 10` y `git status` en sentinela-fabrica; listar archivos entregados por objetivo con diff o ruta verificable; vincular cada objetivo de la Fábrica UI a su commit/artefacto.

ACEPTACION: Solo se abre el siguiente bloque cuando cada objetivo tenga commit reciente observado + artefacto comprobable; veredicto actual: FAIL (sin PASS).

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.

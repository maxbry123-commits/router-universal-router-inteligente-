# SENTINELA-FABRICA — 2026-09-27T23:16Z
(LOOP común · versión: 1a36c3b6f8bb2dd9 · modelo investigador: moonshotai/kimi-k3@NVIDIA_API_KEY_1)

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

CAUSA_RAIZ: El bloque Fábrica UI se reportó sin adjuntar evidencia de commits recientes observados (git log verificable); la evidencia comunitaria aportada es genérica (SO sobre git/python) y no prueba entregas reales del objetivo.

EVIDENCIA: Fallo literal=missing_evidence:recent_commits_observed. Los 5 enlaces son preguntas canónicas de StackOverflow sin relación con el repo ni con la Fábrica UI; no hay hashes, fechas, diffs ni artefactos de build.

NO_REGENERAR: No reintentar el cierre del bloque ni reemitir el informe con la misma evidencia comunitaria; prohibido declarar PASS o avanzar al siguiente bloque.

REPARAR: Ejecutar en el repo sentinela-fabrica: `git log --oneline -n 10 --since="<inicio_bloque>"` y `git show --stat <hash>` por commit relevante; adjuntar salida cruda + diff de archivos UI tocados + resultado de build/tests (artefacto o log) vinculado a cada objetivo del bloque.

ACEPTACION: Solo se cierra cuando cada objetivo tenga: (1) hash de commit existente en origin, (2) diff que toca código UI, (3) build/test verde reproducible, (4) checklist objetivo→entrega 1:1 firmado por INVESTIGADOR.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.

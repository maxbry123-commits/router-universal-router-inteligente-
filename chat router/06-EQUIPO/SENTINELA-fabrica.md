# SENTINELA-FABRICA — 2026-09-27T23:09Z
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

EVIDENCIA: Fallo literal `missing_evidence:recent_commits_observed`. Los 5 enlaces son preguntas canónicas de StackOverflow sin relación con el repo, sin hashes, sin timestamps, sin diff ni artefactos UI. Nada vincula commits → objetivos → entregas.

NO_REGENERAR: No reintentar el bloque ni declarar avance; no sustituir evidencia con referencias externas; no cerrar objetivos por afirmación.

REPARAR: Ejecutar y pegar salida real de `git log --oneline -n 10` con fecha, `git status`, `git show --stat <hash>` por commit relevante, y mapear cada hash al objetivo de Fábrica UI que cierra, incluyendo artefacto entregado (archivo/build/test) verificable.

ACEPTACION: PASS solo cuando cada objetivo tenga: hash de commit observado + diff/stat + artefacto comprobado + criterio de cierre cumplido. Hasta entonces: BLOQUEADO, siguiente bloque prohibido.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.

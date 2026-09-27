# SENTINELA-FABRICA — 2026-09-27T23:02Z
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

EVIDENCIA: Fallo literal=missing_evidence:recent_commits_observed. Los 5 enlaces SO no contienen hashes, fechas ni diff del repo sentinela-fabrica; no hay salida de `git log --oneline -n`, ni artefactos UI, ni CI run.

NO_REGENERAR: No reintentar el bloque ni declarar avance; no sustituir evidencia con referencias externas; no cerrar objetivos por afirmación.

REPARAR: Ejecutar en sentinela-fabrica: `git log --oneline -10 --date=iso`, `git status`, `git show --stat <hash>` por cada entrega UI, y adjuntar salida cruda + enlace a CI/artefacto desplegado. Mapear cada objetivo de la Fábrica UI a su commit/artefacto concreto.

ACEPTACION: Solo se permite el siguiente bloque cuando cada objetivo tenga: (1) hash de commit observado, (2) diff/stat verificable, (3) artefacto o test ejecutado con resultado. Hasta entonces: BLOQUEADO, sin PASS.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.

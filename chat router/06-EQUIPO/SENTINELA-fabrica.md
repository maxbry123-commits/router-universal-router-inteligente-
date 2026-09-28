# SENTINELA-FABRICA — 2026-09-28T01:48Z
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

CAUSA_RAIZ: El bloque Fábrica UI se reportó sin evidencia verificable de commits recientes; la evidencia aportada son URLs genéricas de StackOverflow (Git, Python, branch prediction) sin relación con el objetivo ni con el repositorio sentinela-fabrica.

EVIDENCIA: Ninguna. No hay hashes de commit, salida de `git log`, diff, ni artefactos de entrega. Los 5 enlaces son contenido comunitario reciclado, no prueba de trabajo real.

NO_REGENERAR: No aceptar listas de URLs externas como evidencia. No declarar PASS. No avanzar al siguiente bloque. No reinterpretar "evidencia comunidad" como entrega.

REPARAR: Exigir al ejecutor: (1) `git log --oneline -n 10` con hashes y fechas del repo sentinela-fabrica; (2) diff o lista de archivos modificados por objetivo; (3) resultado de verificación funcional (tests/build/demo) por cada objetivo de la Fábrica UI; (4) mapeo objetivo→commit→verificación.

ACEPTACION: Bloque cerrado solo cuando cada objetivo tenga commit real observado en el repo + verificación ejecutada con salida adjunta. Estado actual: FAIL — missing_evidence:recent_commits_observed. Siguiente bloque: BLOQUEADO.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.

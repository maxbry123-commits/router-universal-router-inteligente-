# SENTINELA-FABRICA — 2026-09-27T23:19Z
(LOOP común · versión: 2b406ed4fafbae72 · modelo investigador: moonshotai/kimi-k3@NVIDIA_API_KEY_1)

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

CAUSA_RAIZ: El bloque Fábrica UI se reportó sin evidencia verificable de commits recientes; la evidencia aportada son URLs genéricas de StackOverflow (Git, Python, branch prediction) sin relación con el objetivo ni con el repositorio sentinela-fabrica.

EVIDENCIA: Ninguna. No hay hashes de commit, timestamps, diffs, ni salida de `git log` observable. Los 5 enlaces son contenido comunitario reciclado, no entregas reales del bloque.

NO_REGENERAR: No aceptar listas de URLs externas como prueba de trabajo. No reintentar el bloque con la misma fuente de evidencia. No avanzar al siguiente bloque bajo ninguna condición.

REPARAR: Exigir a sentinela-fabrica: (1) `git log --oneline -n 10` con fecha/hora del repo real, (2) hash de commit vinculado al objetivo "Cerrar la Fábrica UI", (3) diff o artefacto verificable de la entrega, (4) checklist de objetivos marcado contra commits concretos.

ACEPTACION: Solo PASS cuando exista correlación 1:1 entre objetivo declarado, commit reciente verificable y artefacto entregado. Estado actual: FAIL — missing_evidence:recent_commits_observed confirmado.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.

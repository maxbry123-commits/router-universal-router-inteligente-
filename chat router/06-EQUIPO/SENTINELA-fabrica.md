# SENTINELA-FABRICA — 2026-09-27T22:57Z
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

CAUSA_RAIZ: El bloque "Cerrar la Fábrica UI" no aporta evidencia de commits recientes observados en el repo (git log verificable); la evidencia comunitaria adjunta son preguntas genéricas de StackOverflow sin relación con el objetivo.

EVIDENCIA: Fallo literal=missing_evidence:recent_commits_observed. Ninguna de las 5 URLs citadas documenta commits del proyecto sentinela-fabrica; son tutoriales de Git/Python ajenos a la entrega.

NO_REGENERAR: No regenerar el bloque ni reintentar el cierre; no declarar PASS bajo ninguna circunstancia.

REPARAR: Ejecutar y adjuntar salida real de `git log --oneline -n 10` con hashes, fechas y autores del repo sentinela-fabrica, más diff/artefactos que prueben la entrega de la Fábrica UI por objetivos.

ACEPTACION: Solo se permite avanzar al siguiente bloque cuando exista log de commits reciente verificado y cada objetivo de la Fábrica UI tenga entrega comprobada (artefacto + commit asociado).

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.

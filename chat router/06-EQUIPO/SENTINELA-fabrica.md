# SENTINELA-FABRICA — 2026-09-29T02:17Z
(LOOP común · versión: 9f25e8e246217db9 · modelo investigador: z-ai/glm-5.3@NVIDIA_API_KEY_1)

OBJETIVO: Cerrar la Fábrica UI por objetivos y comprobar entregas reales antes de permitir el siguiente bloque.
ESTADO LOOP: RESEARCH · missing_evidence:recent_commits_observed
OBSERVED_SHA: cf144986b775

PRIORIDADES:
1. 6 motores base de la fábrica
2. componentes dentro de su raíz correcta
3. sin duplicados/regados
4. tests/evidencia de integración
5. T-3000 no programar sin aprobación del Director

INVESTIGACIÓN:
- fuentes consultadas: 5
- mínimo independiente objetivo: 3

**CAUSA_RAIZ:** El bloqueo es legítimo: no existe evidencia de commits recientes en el repositorio del proyecto; lo aportado son enlaces Q&A genéricos de StackOverflow sobre conceptos de Git, no registros verificables del repo objetivo.

**EVIDENCIA:** Las 5 URLs tratan temas generales (deshacer commits, borrar ramas, pull vs fetch, yield, arrays ordenados); ninguna contiene hash de commit, fecha, autor, diff ni rama del proyecto → 0 commits observados → `missing_evidence:recent_commits_observed` se confirma.

**NO_REGENERAR:** No regenerar la UI ni las specs para forzar el avance; no fabricar hashes ni reintentar el sentinela con los mismos enlaces; no declarar PASS sin salida cruda

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.

# SENTINELA-FABRICA — 2026-09-28T16:56Z
(LOOP común · versión: 9f25e8e246217db9 · modelo investigador: z-ai/glm-5.3@NVIDIA_API_KEY_2)

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

CAUSA_RAIZ: El colector de evidencia sustituyó el historial real del repositorio por enlaces genéricos de StackOverflow; no se observó ningún commit del proyecto, solo referencias externas sobre conceptos de Git/Python.

EVIDENCIA: Los 5 enlaces son preguntas populares (undo commits, borrar branch, pull vs fetch, yield, branch prediction) — ninguno contiene SHA, timestamp, autor ni diff de commits reales; el fallo missing_evidence:recent_commits_observed es correcto y procede mantenerlo.

NO_REGENERAR: No regenerar la Fábrica UI ni sustituir la evidencia faltante con más enlaces comunitarios; regenerar artifacts enmascararía la ausencia de entregas sin probarlas.

REPARAR: Ejecutar en el repositorio real `git log --since=<ventana_del_bloque> --pretty=format:"%h %ad %an %s"`, mapear cada SHA al objetivo del bloque y adjuntar diff resumido + estado de CI como evidencia verificable

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.

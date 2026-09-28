# SENTINELA-FABRICA — 2026-09-28T22:34Z
(LOOP común · versión: 9f25e8e246217db9 · modelo investigador: z-ai/glm-5.3-flash@NVIDIA_API_KEY_2)

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

**CAUSA_RAIZ:** El fallo `missing_evidence:recent_commits_observed` indica que el sentinela no observó commits recientes en el repositorio del bloque Fábrica UI; además el campo "Error literal" llegó vacío, señal de cadena de evidencia rota, no de código defectuoso.

**EVIDENCIA:** Las 5 referencias de comunidad (array ordenado, git undo, branches, pull/fetch, yield) son genéricas y no guardan relación con objetivos UI ni con verificación de entregas: son ruido, no prueba. No hay hashes de commit, diff, ni run de CI adjuntos.

**NO_REGENERAR:** No regenerar el bloque ni reintentar generación: el problema es ausencia de entrega observable (commits), no calidad del código. Regenerar produciría más salida sin verificación.

**REPARAR:** (1) Confirmar que los cambios de Fábrica UI existen y hacer `git commit` real con mensaje referenciando el objetivo; (2) `git push` a la rama/remoto correcto que lee el sentinela; (3) verificar ventana temporal del observador (commits dentro del periodo de chequeo); (4) adjuntar hash(es), diff y evidencia de CI al informe de cierre.

**ACEPTACION:** El sentinela observa ≥1 commit reciente con hash visible en `git log`, el mensaje vincula el objetivo de Fábrica UI, y existe artefacto/CI correspondiente. Solo entonces se cierra el bloque y se habilita el siguiente. PASS no declarado.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.

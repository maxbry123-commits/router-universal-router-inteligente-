# SENTINELA-FABRICA — 2026-09-27T23:26Z
(LOOP común · versión: 0fb8da292b84d201 · modelo investigador: moonshotai/kimi-k3@NVIDIA_API_KEY_1)

OBJETIVO: Cerrar la Fábrica UI por objetivos y comprobar entregas reales antes de permitir el siguiente bloque.
ESTADO LOOP: RESEARCH · missing_observed_sha
OBSERVED_SHA: 

PRIORIDADES:
1. 6 motores base de la fábrica
2. componentes dentro de su raíz correcta
3. sin duplicados/regados
4. tests/evidencia de integración
5. T-3000 no programar sin aprobación del Director

INVESTIGACIÓN:
- fuentes consultadas: 0
- mínimo independiente objetivo: 3

CAUSA_RAIZ: El cierre de la Fábrica UI exige un SHA observado (commit real verificado en el repo) como prueba de entrega, y ninguno fue registrado ni verificado; la evidencia de comunidad está vacía ([]), por lo que no existe trazabilidad de que los objetivos del bloque se entregaron.

EVIDENCIA: Fallo literal `missing_observed_sha`; `Evidencia comunidad=[]` — sin SHA observado ni artefactos verificables, no hay base para declarar PASS ni abrir el siguiente bloque.

NO_REGENERAR: No regenerar código UI ni re-ejecutar la fábrica; el problema no es de contenido sino de verificación/registro de entrega. No declarar PASS bajo ninguna circunstancia.

REPARAR: 1) Ejecutar `git log`/`git rev-parse HEAD` en el repo de la Fábrica UI y capturar el SHA real del commit de entrega. 2) Registrarlo como `observed_sha` en el manifiesto de cierre. 3) Adjuntar evidencia de comunidad (artefactos, builds, tests con hash) al array vacío. 4) Re-ejecutar el chequeo de cierre por objetivos.

ACEPTACION: El bloque se cierra solo cuando exista `observed_sha` verificado contra el repo, `Evidencia comunidad` no vacía con artefactos comprobables, y el verificador confirme cada objetivo entregado; entonces y solo entonces se permite el siguiente bloque.

CONTROL:
- PASS no lo decide la LLM.
- Cada ciclo relee HEAD; un informe con SHA viejo queda inválido.
- Si el mismo fallo se repite, escala a investigación antes de reintentar.
- El sentinela solo puede escribir informes/órdenes, no código del objetivo.

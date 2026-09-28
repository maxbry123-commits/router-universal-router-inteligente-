# T08 — SENTINEL CONTEXT

## Fuente de verdad
`chat router/INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL-PARTE-4.md`

Documento 18 define como primera implementación exactamente 6 motores base:
Capability → Canvas → Layout → Action/Flow → Sandbox → QA.

Contrato común:
`Engine.id` + `capabilities` + `can_handle(task)` + `execute(task, context)` + `verify(result)`.

Registro base esperado:
- ui.capability
- ui.canvas
- ui.layout
- ui.actions
- code.sandbox
- qa.visual

Ejecución paralela: `asyncio.gather(...)`.

## Evidencia actual
- commit T08: `3657b7d03b0a304bb2e26fff6cbe9b27d23028e8`
- run: `36350637066`
- pytest reportado: `14 passed in 1.10s`

## GAPS demostrados
1. `README.md` contiene texto de `.pytest_cache`; falso verde documental.
2. T08.md apuntaba a una ruta inexistente para Documento 18; ya corregida.
3. Hay `__pycache__/*.pyc` versionados en el scope; el workflow debe eliminarlos antes de stage.
4. El contrato anterior cerraba T08 solo por pytest + presencia de archivos; faltaban checks objetivos.

## Orden al ejecutor
NO regenerar motores/tests que ya funcionan.
Primero:
1. Reemplaza SOLO `README.md` por micro resumen y micro flujo transversal de los 6 motores.
2. Ejecuta aceptación completa.
3. Solo toca otro archivo si un objective_check concreto falla.
4. Informa salida real de tests y cualquier GAP residual.

Microflujo requerido en README:
INPUT → Capability → Canvas → Layout → Action/Flow → Sandbox → QA → PASS|FAIL


## REEMPLAZO DE EJECUTOR
Orden del Director: sustituir la instancia anterior de T08 por una instancia nueva del espejo T08.

Alcance estricto del reemplazo:
1. NO regenerar engine.py, capability_engine.py, canvas_engine.py, layout_engine.py, action_flow_engine.py, sandbox_engine.py, qa_engine.py, registry.py ni tests/test_motores.py mientras los gates objetivos pasen.
2. Corregir únicamente `README.md`, que hoy contiene texto de `.pytest_cache`.
3. El README debe incluir micro resumen de Capability, Canvas, Layout, Action/Flow, Sandbox y QA y el flujo:
   INPUT → Capability → Canvas → Layout → Action/Flow → Sandbox → QA → PASS|FAIL
4. Ejecutar la aceptación T08 completa y registrar evidencia real.
5. Si los checks pasan, cerrar; si falla un check concreto, corregir solo ese check.

La instancia anterior queda reemplazada para esta vuelta. No duplicar ejecutores T08.


## SUPERVISIÓN FINAL T08
Estado observado por el operador:
- gates estáticos de Engine: PASS
- ENGINE_REGISTRY + asyncio.gather: PASS
- QA touch mínimo 44 px: PASS
- detección de botón muerto: PASS
- README de los 6 motores: PASS
- GAP restante demostrado: artefactos versionados __pycache__/*.pyc
- estado persistido del sentinela: STALE; debe recalcularse, no copiarse manualmente

El sentinela T08 debe supervisar únicamente:
1. required_files completos;
2. acceptance exit 0;
3. objective_checks completos;
4. cero __pycache__, .pytest_cache o *.pyc en el scope publicado;
5. informe T08 fresco respecto al último cambio del scope;
6. tested/current SHA coherentes antes de PASS.

El ejecutor nuevo debe preservar los motores válidos. Si acceptance ya pasa, no necesita regenerar código: la vuelta puede limitarse a limpiar artefactos, producir evidencia fresca y cerrar.

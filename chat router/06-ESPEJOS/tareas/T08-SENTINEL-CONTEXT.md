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

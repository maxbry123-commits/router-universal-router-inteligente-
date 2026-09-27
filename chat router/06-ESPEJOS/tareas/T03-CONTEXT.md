# T03 — CONTEXTO DIVIDIDO PARA EL AGENTE

TRABAJO ACTIVO:
T03-A-RUNTIME.md -> investigar/corregir runtime e instalación.
T03-C-CIERRE.md -> completar auditoría externa y cierre.

TRABAJO PROTEGIDO:
T03-B-SUPERVISOR-DB.md -> 9 tests verdes; NO regenerar.

ORDEN:
A -> ejecutar tests/bas h-n -> C -> gate final.
Si A descubre contradicción, documentarla antes de editar.
Si B sigue verde, dejarlo intacto.

REGLA DE MIRROR:
mirror/T03 conserva el estado de partida. Si el cierre queda REVISE, guardar
trabajo útil allí; no perderlo ni mezclar otras tareas.

FUENTE DE VERDAD:
T03.md + T03-A/B/C + código upstream v3.8.50.

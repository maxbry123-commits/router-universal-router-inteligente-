# T04 — SENTINELA SIMPLE

Objetivo: cerrar T04 sin regenerar trabajo válido.
Scope: `chat router/09-CLAUDE-CODE`.

Supervisar solo:
1. los 7 archivos requeridos existen;
2. `python -m pytest "chat router/09-CLAUDE-CODE" -q` sale 0;
3. los 7 objective_checks del contrato pasan;
4. no hay scope escape ni `__pycache__/.pytest_cache/*.pyc` publicados.

Estado comprobado por GPT:
- evidencia funcional previa: 13/13 tests PASS;
- objective_checks actuales: 7/7 PASS;
- GAP de INVESTIGACION.md corregido: fuentes con URL completa verificable;
- caches/pyc: eliminados;
- no se modificó pasarela.py, normalizar.py, iniciar_claude_code.sh ni tests.

Regla:
- si esos cuatro gates pasan → PASS;
- si uno falla → corregir solo ese fallo;
- no investigar ni relanzar agente cuando no exista un GAP concreto.

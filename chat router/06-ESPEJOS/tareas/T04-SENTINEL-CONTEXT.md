# T04 — CONTEXTO DEL SENTINELA

OBJETIVO: Pasarela Anthropic↔NVIDIA para que Claude Code trabaje con nuestros modelos
ALCANCE: chat router/09-CLAUDE-CODE
ARCHIVOS OBLIGATORIOS:
- pasarela.py
- normalizar.py
- iniciar_claude_code.sh
- tests/test_normalizar.py
- INVESTIGACION.md
- README.md

ACEPTACIÓN: python -m pytest 'chat router/09-CLAUDE-CODE' -q

EVIDENCIA ACTUAL:
- causa: OBJECTIVE_DRIFT
- faltan: []
- pytest/acceptance exit: 0
- scope_escape: False
- objective_drift: True

REGLAS:
- No regenerar archivos que ya pasen.
- No escribir fuera del ALCANCE.
- Si falta conocimiento, investigar antes de inventar.
- Corregir solo la causa demostrada y volver a ejecutar aceptación.

CHEQUEOS INDEPENDIENTES DEL OBJETIVO:
- grep -q '/v1/messages' 'chat router/09-CLAUDE-CODE/pasarela.py'
- grep -q 'count_tokens' 'chat router/09-CLAUDE-CODE/pasarela.py'
- grep -q '/v1/models' 'chat router/09-CLAUDE-CODE/pasarela.py'
- grep -q 'tool_use' 'chat router/09-CLAUDE-CODE/normalizar.py'
- grep -q 'tool_calls' 'chat router/09-CLAUDE-CODE/normalizar.py'
- grep -q 'ANTHROPIC_BASE_URL' 'chat router/09-CLAUDE-CODE/iniciar_claude_code.sh'
- grep -Eq 'https://github.com|https://docs[.]' 'chat router/09-CLAUDE-CODE/INVESTIGACION.md'

FUENTES ENCONTRADAS:
- GitHub:anthropics/claude-code: Detect if underlying file has change between when diff was computed and apply https://github.com/anthropics/claude-code/issues/13
- GitHub:BerriAI/litellm: Show me details about my llm calls - breakdown models called, total costs, by user ID https://github.com/BerriAI/litellm/issues/13

ANÁLISIS DEL INVESTIGADOR:
sin respuesta del modelo; usar evidencia determinista

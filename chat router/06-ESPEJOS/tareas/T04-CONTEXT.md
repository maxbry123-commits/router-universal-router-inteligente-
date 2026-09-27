# T04 — CONTEXTO COMPACTO DE EJECUCIÓN

Objetivo único: construir una pasarela local Anthropic-compatible para Claude Code
que traduzca /v1/messages hacia NVIDIA OpenAI-compatible /v1/chat/completions.

## Archivos obligatorios
- pasarela.py
- normalizar.py
- iniciar_claude_code.sh
- tests/__init__.py
- tests/test_normalizar.py
- INVESTIGACION.md
- README.md

## Orden de trabajo
1. Crear primero tests/test_normalizar.py con pruebas sin red.
2. Implementar normalizar.py hasta que esas pruebas pasen.
3. Implementar pasarela.py usando FastAPI.
4. Implementar iniciar_claude_code.sh.
5. Completar INVESTIGACION.md y README.md.
6. Ejecutar una sola suite completa.
7. Corregir solo el traceback observado.

## Traducciones mínimas
Anthropic -> NVIDIA/OpenAI:
- system + messages
- tool_use -> assistant.tool_calls
- tool_result -> role=tool
- quitar/normalizar reasoning y output_config
- thinking adaptive: eliminar o convertir a formato soportado
- alias claude-opus/sonnet/haiku-* -> MODELO NVIDIA configurado

NVIDIA/OpenAI -> Anthropic:
- content texto -> content block text
- tool_calls -> content blocks tool_use
- finish_reason=tool_calls -> stop_reason=tool_use
- finish_reason=stop -> stop_reason=end_turn
- usage -> input_tokens/output_tokens cuando existan

## Endpoints
- POST /v1/messages
- POST /v1/messages/count_tokens
- GET /v1/models
- stream=false y stream=true (SSE Anthropic-compatible)

## Runtime
- upstream: https://integrate.api.nvidia.com/v1/chat/completions
- env MODELO (Kimi K3 por defecto)
- env NVIDIA_API_KEY
- puente local :8082
- ANTHROPIC_BASE_URL=http://127.0.0.1:8082

## Reglas
- tests: CERO red
- no tocar fuera de chat router/09-CLAUDE-CODE
- no copiar README ni archivos de otra tarea
- máximo 500 líneas por archivo
- PASS solo con pytest real exit 0 e informe real

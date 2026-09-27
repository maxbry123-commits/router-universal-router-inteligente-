# INVESTIGACION — T04 Pasarela Claude Code ↔ NVIDIA

## Problema verificado (27-sep)
Claude Code habla Anthropic Messages API (`/v1/messages`, SSE, bloques
`tool_use`/`tool_result`, `thinking`, `output_config`, subagentes que piden
`claude-opus/sonnet/haiku-*`). NVIDIA API Catalog habla OpenAI
`/v1/chat/completions`. Sin traducción real, las tool calls se cortan tras
leer 1 archivo. Fallos concretos observados:
- `reasoning` no soportado → HTTP 400.
- `thinking: {type: adaptive}` no traducido → 400.
- Subagentes/plugins piden `claude-opus-*` → modelo inexistente en NVIDIA.

## Fuentes consultadas
1. **Free Claude Code** (github.com/codeaashu/free-claude-code, Python/FastAPI):
   proxy en :8082 que implementa `/v1/messages`, `/v1/messages/count_tokens`,
   `/v1/models`; mapea MODEL_OPUS/SONNET/HAIKU; convierte `reasoning_content`
   y `<think>` a bloques thinking; usa `ANTHROPIC_BASE_URL=http://localhost:8082`
   (raíz, no `/v1`) y `ANTHROPIC_AUTH_TOKEN`. Es la base de diseño elegida.
2. **Claude-NIM Proxy** (github.com/claude-server/claude-nim, TypeScript/Bun):
   traducción completa text/tool_use/tool_result, `tool_choice` auto/any/tool,
   system string|array → mensaje system, límite 10 MB, binding localhost.
   Confirma el contrato de traducción; descartado por requerir Bun/Node.
3. **Anthropic Messages API** (docs oficiales): contrato de bloques
   text/tool_use/tool_result, stop_reason end_turn/tool_use/max_tokens.
4. **NVIDIA NIM OpenAI-compatible** (integrate.api.nvidia.com/v1): contrato
   chat/completions con tool_calls y finish_reason tool_calls/stop/length.

## Decisión
Implementación propia mínima en Python (FastAPI + httpx), inspirada en
free-claude-code, con la lógica de traducción aislada en `normalizar.py`
(funciones puras, testeables sin red). Se eliminan `reasoning`,
`output_config` y `thinking` del request upstream; los alias
`claude-opus/sonnet/haiku-*` se reescriben al modelo de env `MODELO`
(Kimi K3/K2.5 por defecto). El streaming SSE Anthropic se sintetiza local
a partir de la respuesta completa (suficiente para Claude Code; el streaming
token-a-token upstream queda como mejora futura).

## Vía oficial DeepSeek (alternativa documentada)
- DeepSeek Harness → Claude Code como subagente:
  `dsh plugin add @deepseek-ai/dsh-subagent-claude-code` y
  `@deepseek-ai/dsh-hooks-claude-code`
  (repo github.com/deepseek-ai/deepseek-harness — hoy devuelve 404, no
  verificable).
- DeepSeek directo con endpoint Anthropic-compatible:
  `https://api.deepseek.com/anthropic` (requiere `DEEPSEEK_API_KEY`).
  Hoy NO disponible (sin clave; la URL responde "Authentication Fails") →
  queda como GAP documentado, no bloquea la pasarela NVIDIA.

## Prueba real opcional
Si existe `NVIDIA_API_KEY_1`: arrancar `pasarela.py` y hacer
`POST /v1/messages` con una tool `Read`; verificar que la respuesta contiene
un bloque `tool_use` con `stop_reason=tool_use`. Resultado: pendiente de
ejecutar en entorno con clave (ver GAP en informe).

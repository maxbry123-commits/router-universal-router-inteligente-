# WATCHDOG — estado de los agentes (2026-09-24 00:10:08Z)

**Acción:** hay pendientes; 3 reintentos sin avance: ESCALAR A CLAUDE (mejorar el DSL DAG, la ruta o crear agentes)

| agente | marco | estado | pasos cerrados | bloqueado en | GAPs |
|---|---|---|---|---|---|
| agent-1-chat-hf | pocketflow | CLOSED | 3/3 | - | - |
| agent-10-model-install | pocketflow | CLOSED | 3/1 | - | - |
| agent-11-download-extraction | smolagents | CLOSED | 3/1 | - | cerebras/gpt-oss-120b:AgentGenerationError:Error while generating output:
Error code: 402 - {'message': 'Payment require | cerebras/gpt-oss-120b:AgentGenerationError:Error while generating output:
Error code: 402 - {'message': 'Payment require |
| agent-12-yaiwes-router | smolagents | CLOSED | 2/1 | - | - |
| agent-13-repo-inventory | pocketflow | BLOCKED | 0/1 | inventory_module | la prueba falló (exit=1): AssertionError |
| agent-14-orchestrator-msaf | pocketflow | BLOCKED | 5/4 | director_close_audit | falta 'PRUEBAS' | falta 'SIGUIENTE ACCIÓN' |
| agent-15-orchestrator-grok | smolagents | CLOSED | 4/3 | - | hf/deepseek-ai/DeepSeek-V4-Flash:AgentGenerationError:Error while generating output:
Request timed out. |
| agent-15-orchestrator-grokbuild | pocketflow | BLOCKED | 0/1 | fetch_and_connect | la prueba falló (exit=1): RuntimeError: No hay release no-draft ni no-prerelease en xai-org/grok-build |
| agent-16-chat-space-oauth | pocketflow | CLOSED | 2/1 | - | Python inválido: unexpected character after line continuation character (línea 17) | falta 'private=False' |
| agent-17-chat-backend-32gb | pocketflow | CLOSED | 1/1 | - | falta 'Volume' | la prueba falló (exit=1): ImportError: cannot import name 'run' from 'chat_backend_32gb' (/home/runner/work/router-unive |
| agent-18-chat-final-auditor | pocketflow | CLOSED | 1/1 | - | falta 'Archivos' | falta 'Memoria' |
| agent-19-chat-components-motors | pocketflow | BLOCKED | 0/1 | acquire_open_webui | motor falló (exit=1): RuntimeError: DESTINATION_EXISTS:router inteligente universal/Componente open soure router intelig |
| agent-2-chat-hf-smol | smolagents | CLOSED | 3/3 | - | - |
| agent-20-openclaw-rowboat | smolagents | CLOSED | 1/1 | - | - |
| agent-3-router | pocketflow | CLOSED | 4/4 | - | - |
| agent-4-router-smol | smolagents | CLOSED | 4/1 | - | - |
| agent-5-auditor | smolagents | BLOCKED | 2/4 | lens_models | hf/deepseek-ai/DeepSeek-V4-Flash:el Sheriff no dio PASS | hf/deepseek-ai/DeepSeek-V4-Flash:el Sheriff no dio PASS |
| agent-6-hf-nodes | pocketflow | CLOSED | 3/1 | - | - |
| agent-7-llama-hf | smolagents | CLOSED | 4/4 | - | - |
| agent-8-router-local | pocketflow | CLOSED | 2/2 | - | - |
| agent-9-models-catalog | smolagents | CLOSED | 2/2 | - | - |

Claude lee este archivo al abrir sesión o cuando el Director lo pida, y decide (nada de esto lo decide el watchdog): corregir `ROUTE.json`, editar un `chain.yaml`, o crear agentes.

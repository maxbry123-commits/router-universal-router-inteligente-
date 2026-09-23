# WATCHDOG — estado de los agentes (2026-09-23 02:41:05Z)

**Acción:** hay pendientes; una ronda ya está en curso: no se lanza otra

| agente | marco | estado | pasos cerrados | bloqueado en | GAPs |
|---|---|---|---|---|---|
| agent-1-chat-hf | pocketflow | CLOSED | 3/3 | - | - |
| agent-10-model-install | pocketflow | CLOSED | 3/1 | - | - |
| agent-11-download-extraction | smolagents | CLOSED | 2/2 | - | cerebras/gpt-oss-120b:AgentGenerationError:Error while generating output:
Error code: 402 - {'message': 'Payment require | cerebras/gpt-oss-120b:AgentGenerationError:Error while generating output:
Error code: 402 - {'message': 'Payment require |
| agent-12-yaiwes-router | smolagents | CLOSED | 1/1 | - | - |
| agent-13-repo-inventory | pocketflow | BLOCKED | 0/1 | inventory_module | la prueba falló (exit=1): AssertionError |
| agent-14-orchestrator-msaf | pocketflow | CLOSED | 1/1 | - | - |
| agent-15-orchestrator-grok | smolagents | BLOCKED | 0/1 | verify_and_connect (tiempo agotado) | - |
| agent-15-orchestrator-grokbuild | pocketflow | BLOCKED | 0/1 | fetch_and_connect | la prueba falló (exit=1): requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://api.github.com/rep |
| agent-16-chat-space-oauth | pocketflow | BLOCKED | 0/1 | publish_static_live | Python inválido: unexpected character after line continuation character (línea 17) | falta 'private=False' |
| agent-17-chat-backend-32gb | pocketflow | BLOCKED | 0/1 | backend_live | falta 'Volume' | la prueba falló (exit=1): ImportError: cannot import name 'run' from 'chat_backend_32gb' (/home/runner/work/router-unive |
| agent-18-chat-final-auditor | pocketflow | BLOCKED | 0/2 | wait_live | Python inválido: invalid syntax (línea 1) | la prueba falló (exit=1): SyntaxError: invalid syntax |
| agent-19-chat-components-motors | ? | SIN_ESTADO | 0/0 | - | - |
| agent-2-chat-hf-smol | smolagents | CLOSED | 3/3 | - | - |
| agent-3-router | pocketflow | CLOSED | 4/4 | - | - |
| agent-4-router-smol | smolagents | CLOSED | 3/3 | - | - |
| agent-5-auditor | smolagents | BLOCKED | 2/4 | lens_models (tiempo agotado) | - |
| agent-6-hf-nodes | pocketflow | CLOSED | 2/2 | - | - |
| agent-7-llama-hf | smolagents | CLOSED | 4/4 | - | - |
| agent-8-router-local | pocketflow | CLOSED | 2/2 | - | - |
| agent-9-models-catalog | smolagents | CLOSED | 2/2 | - | - |

Claude lee este archivo al abrir sesión o cuando el Director lo pida, y decide (nada de esto lo decide el watchdog): corregir `ROUTE.json`, editar un `chain.yaml`, o crear agentes.

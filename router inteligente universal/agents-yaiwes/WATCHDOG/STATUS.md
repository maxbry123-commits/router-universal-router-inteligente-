# WATCHDOG — estado de los agentes (2026-09-23 07:19:49Z)

**Acción:** hay pendientes; una ronda ya está en curso: no se lanza otra

| agente | marco | estado | pasos cerrados | bloqueado en | GAPs |
|---|---|---|---|---|---|
| agent-1-chat-hf | pocketflow | CLOSED | 3/3 | - | - |
| agent-10-model-install | pocketflow | CLOSED | 3/1 | - | - |
| agent-11-download-extraction | smolagents | CLOSED | 3/1 | - | cerebras/gpt-oss-120b:AgentGenerationError:Error while generating output:
Error code: 402 - {'message': 'Payment require | cerebras/gpt-oss-120b:AgentGenerationError:Error while generating output:
Error code: 402 - {'message': 'Payment require |
| agent-12-yaiwes-router | smolagents | CLOSED | 2/1 | - | - |
| agent-13-repo-inventory | pocketflow | BLOCKED | 0/1 | inventory_module | la prueba falló (exit=1): AssertionError |
| agent-14-orchestrator-msaf | pocketflow | BLOCKED | 2/2 | director_question_1 | falta 'duda' | falta 'tiempo' |
| agent-15-orchestrator-grok | smolagents | CLOSED | 2/1 | - | - |
| agent-15-orchestrator-grokbuild | pocketflow | BLOCKED | 0/1 | fetch_and_connect | la prueba falló (exit=1): requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://api.github.com/rep |
| agent-16-chat-space-oauth | pocketflow | BLOCKED | 1/1 | adapt_openwebui_real | falta 'Open WebUI' | falta 'Router' |
| agent-17-chat-backend-32gb | pocketflow | BLOCKED | 0/1 | backend_router_live | falta 'Volume' | la prueba falló (exit=1): ImportError: cannot import name 'run' from 'chat_backend_32gb' (/home/runner/work/router-unive |
| agent-18-chat-final-auditor | pocketflow | CLOSED | 1/1 | - | falta 'Archivos' | falta 'Memoria' |
| agent-19-chat-components-motors | pocketflow | BLOCKED | 0/1 | acquire_open_webui | motor canónico no existe: ➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-intelige |
| agent-2-chat-hf-smol | smolagents | CLOSED | 3/3 | - | - |
| agent-3-router | pocketflow | CLOSED | 4/4 | - | - |
| agent-4-router-smol | smolagents | CLOSED | 4/1 | - | - |
| agent-5-auditor | smolagents | BLOCKED | 2/4 | lens_models | hf/deepseek-ai/DeepSeek-V4-Flash:el Sheriff no dio PASS | hf/deepseek-ai/DeepSeek-V4-Flash:el Sheriff no dio PASS |
| agent-6-hf-nodes | pocketflow | CLOSED | 3/1 | - | - |
| agent-7-llama-hf | smolagents | CLOSED | 4/4 | - | - |
| agent-8-router-local | pocketflow | CLOSED | 2/2 | - | - |
| agent-9-models-catalog | smolagents | CLOSED | 2/2 | - | - |

Claude lee este archivo al abrir sesión o cuando el Director lo pida, y decide (nada de esto lo decide el watchdog): corregir `ROUTE.json`, editar un `chain.yaml`, o crear agentes.

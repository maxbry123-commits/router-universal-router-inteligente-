# WATCHDOG — estado de los agentes (2026-09-23 00:09:50Z)

**Acción:** hay pendientes; una ronda ya está en curso: no se lanza otra

| agente | marco | estado | pasos cerrados | bloqueado en | GAPs |
|---|---|---|---|---|---|
| agent-1-chat-hf | pocketflow | CLOSED | 3/3 | - | - |
| agent-10-model-install | pocketflow | BLOCKED | 2/1 | install_launch_test | Python inválido: unterminated string literal (detected at line 5) (línea 5) | la prueba falló (exit=1): SyntaxError: unterminated string literal (detected at line 5) |
| agent-11-download-extraction | smolagents | CLOSED | 2/2 | - | cerebras/gpt-oss-120b:AgentGenerationError:Error while generating output:
Error code: 402 - {'message': 'Payment require | cerebras/gpt-oss-120b:AgentGenerationError:Error while generating output:
Error code: 402 - {'message': 'Payment require |
| agent-12-yaiwes-router | smolagents | CLOSED | 1/1 | - | - |
| agent-13-repo-inventory | pocketflow | BLOCKED | 0/1 | inventory_module | la prueba falló (exit=1): AssertionError |
| agent-14-orchestrator-msaf | ? | SIN_ESTADO | 0/0 | - | - |
| agent-15-orchestrator-grok | ? | SIN_ESTADO | 0/0 | - | - |
| agent-15-orchestrator-grokbuild | ? | SIN_ESTADO | 0/0 | - | - |
| agent-2-chat-hf-smol | smolagents | CLOSED | 3/3 | - | - |
| agent-3-router | pocketflow | CLOSED | 4/4 | - | - |
| agent-4-router-smol | smolagents | CLOSED | 3/3 | - | - |
| agent-5-auditor | smolagents | BLOCKED | 2/4 | lens_models (tiempo agotado) | - |
| agent-6-hf-nodes | pocketflow | CLOSED | 2/2 | - | - |
| agent-7-llama-hf | smolagents | CLOSED | 3/3 | - | - |
| agent-8-router-local | pocketflow | CLOSED | 2/2 | - | - |
| agent-9-models-catalog | smolagents | CLOSED | 2/2 | - | - |

Claude lee este archivo al abrir sesión o cuando el Director lo pida, y decide (nada de esto lo decide el watchdog): corregir `ROUTE.json`, editar un `chain.yaml`, o crear agentes.

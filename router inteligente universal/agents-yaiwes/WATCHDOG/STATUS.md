# WATCHDOG — estado de los agentes (2026-09-23 01:43:19Z)

**Acción:** hay pendientes; se lanzó `RIU Agents Run` (reintento 1/3)

| agente | marco | estado | pasos cerrados | bloqueado en | GAPs |
|---|---|---|---|---|---|
| agent-1-chat-hf | pocketflow | CLOSED | 3/3 | - | - |
| agent-10-model-install | pocketflow | CLOSED | 3/1 | - | - |
| agent-11-download-extraction | smolagents | CLOSED | 2/2 | - | cerebras/gpt-oss-120b:AgentGenerationError:Error while generating output:
Error code: 402 - {'message': 'Payment require | cerebras/gpt-oss-120b:AgentGenerationError:Error while generating output:
Error code: 402 - {'message': 'Payment require |
| agent-12-yaiwes-router | smolagents | CLOSED | 1/1 | - | - |
| agent-13-repo-inventory | pocketflow | BLOCKED | 0/1 | inventory_module | la prueba falló (exit=1): AssertionError |
| agent-14-orchestrator-msaf | ? | SIN_ESTADO | 0/0 | - | - |
| agent-15-orchestrator-grok | ? | SIN_ESTADO | 0/0 | - | - |
| agent-15-orchestrator-grokbuild | ? | SIN_ESTADO | 0/0 | - | - |
| agent-16-chat-space-oauth | ? | SIN_ESTADO | 0/0 | - | - |
| agent-17-chat-backend-32gb | ? | SIN_ESTADO | 0/0 | - | - |
| agent-18-chat-final-auditor | ? | SIN_ESTADO | 0/0 | - | - |
| agent-2-chat-hf-smol | smolagents | CLOSED | 3/3 | - | - |
| agent-3-router | pocketflow | PENDING_VERIFY | 3/4 | - | Space inexistente o inaccesible sin auth real (smoke FAIL) |
| agent-4-router-smol | smolagents | BLOCKED | 3/3 | paper_closed_sin_health_live | - |
| agent-5-auditor | smolagents | BLOCKED | 2/4 | lens_models (tiempo agotado) | - |
| agent-6-hf-nodes | pocketflow | CLOSED | 2/2 | - | - |
| agent-7-llama-hf | smolagents | CLOSED | 4/4 | - | - |
| agent-8-router-local | pocketflow | BLOCKED | 2/2 | paper_closed_sin_health_live | - |
| agent-9-models-catalog | smolagents | BLOCKED | 2/2 | paper_closed_sin_health_live | - |

Claude lee este archivo al abrir sesión o cuando el Director lo pida, y decide (nada de esto lo decide el watchdog): corregir `ROUTE.json`, editar un `chain.yaml`, o crear agentes.

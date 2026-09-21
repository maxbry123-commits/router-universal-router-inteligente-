# WATCHDOG — estado de los agentes (2026-09-21 18:46:42Z)

**Acción:** hay pendientes; se lanzó `RIU Agents Run` (reintento 1/3)

| agente | marco | estado | pasos cerrados | bloqueado en | GAPs |
|---|---|---|---|---|---|
| agent-1-chat-hf | pocketflow | CLOSED | 3/3 | - | - |
| agent-2-chat-hf-smol | smolagents | CLOSED | 3/3 | - | - |
| agent-3-router | pocketflow | CLOSED | 3/3 | - | - |
| agent-4-router-smol | smolagents | CLOSED | 3/3 | - | - |
| agent-5-auditor | smolagents | BLOCKED | 0/4 | lens_chat (tiempo agotado) | - |
| agent-6-hf-nodes | pocketflow | CLOSED | 2/2 | - | - |
| agent-7-llama-hf | smolagents | BLOCKED | 2/3 | bench_report (tiempo agotado) | - |
| agent-8-router-local | pocketflow | CLOSED | 2/2 | - | - |
| agent-9-models-catalog | smolagents | CLOSED | 2/2 | - | - |

Claude lee este archivo al abrir sesión o cuando el Director lo pida, y decide (nada de esto lo decide el watchdog): corregir `ROUTE.json`, editar un `chain.yaml`, o crear agentes.

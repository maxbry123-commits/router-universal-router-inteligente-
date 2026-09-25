# WATCHDOG — estado de los agentes (2026-09-25 07:53:53Z)

**Acción:** hay pendientes; se lanzó `RIU Agents Run` (reintento 2/3)

| agente | marco | estado | pasos cerrados | bloqueado en | GAPs |
|---|---|---|---|---|---|
| agent-1-chat-hf | pocketflow | CLOSED | 3/3 | - | - |
| agent-10-model-install | pocketflow | CLOSED | 3/1 | - | - |
| agent-11-download-extraction | smolagents | CLOSED | 3/1 | - | cerebras/gpt-oss-120b:AgentGenerationError:Error while generating output:
Error code: 402 - {'message': 'Payment require | cerebras/gpt-oss-120b:AgentGenerationError:Error while generating output:
Error code: 402 - {'message': 'Payment require |
| agent-12-yaiwes-router | smolagents | CLOSED | 2/1 | - | - |
| agent-13-repo-inventory | pocketflow | BLOCKED | 0/1 | inventory_module | la prueba falló (exit=1): AssertionError |
| agent-14-orchestrator-msaf | pocketflow | CLOSED | 6/4 | - | - |
| agent-15-orchestrator-grok | smolagents | CLOSED | 4/3 | - | hf/deepseek-ai/DeepSeek-V4-Flash:AgentGenerationError:Error while generating output:
Request timed out. |
| agent-15-orchestrator-grokbuild | pocketflow | BLOCKED | 0/1 | fetch_and_connect | la prueba falló (exit=1): Exception: No releases found |
| agent-16-chat-space-oauth | pocketflow | CLOSED | 4/1 | - | JavaScript inválido: Node.js v22.23.2 | menos de 1500 caracteres |
| agent-17-chat-backend-32gb | pocketflow | CLOSED | 4/3 | - | falta 'Volume' | la prueba falló (exit=1): ImportError: cannot import name 'run' from 'chat_backend_32gb' (/home/runner/work/router-unive |
| agent-18-chat-final-auditor | pocketflow | CLOSED | 1/1 | - | falta 'Archivos' | falta 'Memoria' |
| agent-19-chat-components-motors | pocketflow | CLOSED | 2/2 | - | motor falló (exit=1): RuntimeError: DESTINATION_EXISTS:router inteligente universal/Componente open soure router intelig |
| agent-2-chat-hf-smol | smolagents | CLOSED | 3/3 | - | - |
| agent-20-openclaw-rowboat | smolagents | CLOSED | 1/1 | - | - |
| agent-21-router-connect | pocketflow | CLOSED | 1/1 | - | - |
| agent-22-grok-connect | pocketflow | CLOSED | 1/1 | - | - |
| agent-24-almacenamiento | pocketflow | CLOSED | 2/2 | - | - |
| agent-25-cableo-agentes | pocketflow | CLOSED | 2/2 | - | - |
| agent-26-plan-4-objetivos | pocketflow | CLOSED | 2/2 | - | - |
| agent-27-centinela | pocketflow | CLOSED | 3/3 | - | - |
| agent-28-memoria-descarga | pocketflow | BLOCKED | 1/7 | falkordb | motor falló (exit=1): RuntimeError: DESTINATION_EXISTS:router inteligente universal/Componente open soure router intelig | motor falló (exit=1): RuntimeError: SOURCE_SPECIAL_FILE_GAP:CLAUDE.md |
| agent-29-github-gateway | pocketflow | CLOSED | 2/2 | - | - |
| agent-3-router | pocketflow | CLOSED | 4/4 | - | - |
| agent-30-sandbox-dsl | pocketflow | CLOSED | 2/2 | - | - |
| agent-31-micro-sistema | pocketflow | BLOCKED | 1/2 | generador | Python inválido: unterminated string literal (detected at line 31) (línea 31) |
| agent-32-organizador | pocketflow | CLOSED | 4/2 | - | - |
| agent-33-enchufe-mcp | pocketflow | CLOSED | 2/2 | - | - |
| agent-35-skills-obligatorias | pocketflow | CLOSED | 2/2 | - | - |
| agent-36-panel-control | pocketflow | CLOSED | 3/3 | - | - |
| agent-37-router-gratuito | pocketflow | CLOSED | 2/2 | - | - |
| agent-38-deepseek-harness | pocketflow | BLOCKED | 0/2 | acquire_harness | motor falló (exit=1): RuntimeError: COMMAND_FAILED:git:128:fatal: couldn't find remote ref main |
| agent-39-descargas-verificadas | pocketflow | BLOCKED | 0/5 | memanto | motor falló (exit=1): RuntimeError: DESTINATION_EXISTS:router inteligente universal/Componente open soure router intelig |
| agent-4-router-smol | smolagents | CLOSED | 4/1 | - | - |
| agent-5-auditor | smolagents | BLOCKED | 2/4 | lens_models | hf/deepseek-ai/DeepSeek-V4-Flash:el Sheriff no dio PASS | hf/deepseek-ai/DeepSeek-V4-Flash:el Sheriff no dio PASS |
| agent-6-hf-nodes | pocketflow | CLOSED | 3/1 | - | - |
| agent-7-llama-hf | smolagents | CLOSED | 4/4 | - | - |
| agent-8-router-local | pocketflow | CLOSED | 2/2 | - | - |
| agent-9-models-catalog | smolagents | CLOSED | 2/2 | - | - |

Claude lee este archivo al abrir sesión o cuando el Director lo pida, y decide (nada de esto lo decide el watchdog): corregir `ROUTE.json`, editar un `chain.yaml`, o crear agentes.

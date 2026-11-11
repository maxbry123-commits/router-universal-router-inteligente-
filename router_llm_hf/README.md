# router_llm_hf — Control Plane

Regla de oro: nunca computa, solo controla. El Data Plane (Router MVP v1) ejecuta.

## Componentes
| Archivo | Funcion |
|---|---|
| queue_manager.py | Cola con prioridad, 1 tarea por modelo, salto al 85% RAM |
| watchdog.py | Heartbeat 30s, timeout 96s por llamada |
| recall_engine.py | Re-invocacion con feedback, maximo 8 intentos |
| output_contract.py | Contrato Pydantic estricto de salida |
| escalation_guard.py | AND-gate anti-escalada |
| mode_router.py | 12 modos a (dataset, LoRA) |

## Integracion
control_bridge.py en Router MVP v1 importa este paquete al arrancar:
si existe usa Watchdog y RecallEngine; si no, passthrough sin caida.

## Dependencias
pydantic 2 o superior. psutil opcional (RAM en QueueManager).

## Pruebas
pytest router_llm_hf/tests/ -v

## Cierre (Salida 2/3, 2026-11-11)
Code cerrado: los 6 modulos + paquete + tests.
Operacional (owner): /health y chat en vivo, GITHUB_BRANCH y MODEL_* en HF Secrets.

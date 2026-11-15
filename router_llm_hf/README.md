# router_llm_hf — Control Plane

Servidor de control de LLMs. Delega cómputo al Router MVP v1 (Data Plane).

## Componentes

| Archivo | Función |
|---|---|
| `queue_manager.py` | Cola con prioridad |
| `watchdog.py` | Heartbeat + cancelación por timeout |
| `recall_engine.py` | Re-invocación con feedback |
| `output_contract.py` | Pydantic strict (8 campos) |
| `escalation_guard.py` | AND-gate anti-escalada |
| `mode_router.py` | Selección modo/LoRA (12 modos) |

## Separación Control/Data

- **router_llm_hf** = control + decisión
- **Router MVP v1** = cómputo + almacenamiento
- **HF Spaces** = modelos GGUF + LoRAs

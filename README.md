# Router Universal — Inteligente

Indice de planos y cableado. Rama de trabajo: ccr-f01c3de9-bmry0s.

## Indice de planos
| Plano | Ruta | Rol |
|---|---|---|
| Data Plane | ROUTER MVP v1/system_prompt_py/ | Ejecuta y almacena. Nunca decide. |
| Control Plane | router_llm_hf/ | Decide y controla. Nunca computa. |
| HF Plane | llm system HF/ + Spaces | Pesos, datasets, LoRAs, cascaron. |
| Control HF | control huggueface/ | Pausa, reinicio, mirror, wake, registry. |
| Satelite | SYSTEM_WIRING_REGISTRY.yaml + connections/ | Registro de cableado. |

## Diagrama transversal
[Cliente]
   |
   v
[Data Plane] --delega control--> [Control Plane]
   |                                  |
   | (git clone via entrypoint)       | (HfApi restart/pause)
   v                                  v
[HF Spaces: s1/s2/s3] <-------- [Control HF]
   |
   v
[Buckets/Datasets: estado persistente]

Regla de oro: Data Plane nunca decide. Control Plane nunca computa.
HF nunca aloja logica de control. Control HF solo gestiona ciclo de vida.

## Handoffs
- docs/handoff/ROUTER_MVP_V1_HANDOFF.md (Salida 1/3)
- docs/handoff/LLM_SYSTEM_HF_HANDOFF.md (Salida 3/3)
- docs/handoff/CONTROL_HUGGUEFACE_HANDOFF.md (Salida 3/3)
- docs/handoff/ROUTER2_AUDITORIA.md (main)

## Cierre (2026-11-11)
Salidas 1/3, 2/3, 3/3 publicadas en rama ccr-f01c3de9-bmry0s.
Pendiente operacional: prueba Groq, secrets HF, decision main.

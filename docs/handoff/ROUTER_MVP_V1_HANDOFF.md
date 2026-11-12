# Handoff — Router MVP v1 (Data Plane)

Actualizado: 2026-11-11 · Rama: ccr-f01c3de9-bmry0s · Salida 1/3 CERRADA.

## Estado
Data Plane funcional. Delega control al Control Plane via control_bridge.py.
Si router_llm_hf no existe, passthrough total (nunca cae).

## Componentes clave
| Archivo | Funcion |
|---|---|
| openai_compatible_proxy.py | Proxy OpenAI-compatible (7860), delega via BRIDGE.run |
| control_bridge.py | Puente a router_llm_hf; watchdog 96s + recall si disponible |
| key_pool.py | Pool de claves Groq/NVIDIA |
| fallback_middleware.py | Fallback ante sin saldo |
| provider_window.py | Ventana 114s |
| queue_manager.py | Cola local del Data Plane |

## Endpoints
POST /v1/chat/completions · GET /health · GET /control-plane/status

## Cerrado en Salida 1/3
- G9 delegacion de control (proxy + bridge)
- Prueba de cierre (tests/test_control_bridge.py)
- docs data plane (README.md)

## Cerrado previamente
- R1 dev_key (control_api movido a control huggueface, falla cerrado)
- sim35 en tests/
- R4 buscar_web registrado en tools y usado por gap loop

## Pendiente operacional (owner)
- Prueba real contra Groq con llaves de prueba
- Decision de integracion main vs rama de trabajo
- Aprobacion del motor de descarga (R5)

## Riesgos abiertos
- R2 NVIDIA 410 en watchdogs historicos (revisar endpoint/llave)
- R3 ramas divergidas main vs trabajo (no mezclar sin revision)

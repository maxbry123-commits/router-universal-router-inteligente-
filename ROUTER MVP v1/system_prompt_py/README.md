# Router MVP v1 — Data Plane

## Rol
Data Plane del sistema. Recibe peticiones HTTP OpenAI-compatible, gestiona pool de
claves (Groq y NVIDIA), ejecuta llamadas a proveedores y aplica fallback y rate limiting.

Regla de oro: nunca decide, solo ejecuta y almacena.
Toda logica de decision vive en router_llm_hf (Control Plane, Salida 2/3).

## Componentes
| Archivo | Funcion |
|---|---|
| openai_compatible_proxy.py | Proxy HTTP OpenAI-compatible (puerto 7860) |
| control_bridge.py | Puente al Control Plane; passthrough si no existe |
| key_pool.py | Pool de claves por proveedor con rotacion |
| fallback_middleware.py | Fallback entre proveedores ante sin saldo |
| provider_window.py | Ventana de rate limiting (114 s) |
| provider_timeouts.py | Timeouts por proveedor |
| queue_manager.py | Cola concurrente local del Data Plane |

## Endpoints
| Ruta | Funcion |
|---|---|
| POST /v1/chat/completions | Chat con fallback y control de concurrencia |
| GET /health | Health check |
| GET /control-plane/status | Estado del puente al Control Plane |

## Integracion con Control Plane
control_bridge intenta importar router_llm_hf al arrancar:
- Disponible: watchdog con timeout 96 s y heartbeat por tarea.
- No disponible: passthrough total. El Data Plane nunca cae por ausencia de control.

## Variables de entorno
ROUTER_API_KEY obligatoria, falla cerrado si falta.
GROQ_KEYS lista separada por comas.
NVIDIA_KEYS lista separada por comas.

## Ejecucion
cd "ROUTER MVP v1/system_prompt_py"
pip install -r requirements.txt
uvicorn openai_compatible_proxy:app --host 0.0.0.0 --port 7860

## Pruebas de cierre
pytest tests/test_control_bridge.py -v

## Estado de cierre (Salida 1/3, 2026-11-11)
Cerrado en code: delegacion de control (G9), puente con fallback, prueba de cierre.
Cerrado previamente: dev_key fuera (control_api en control huggueface), sim35 en tests,
buscar_web registrado en tools y usado por gap loop.
Cierre operacional (owner, no code): prueba real Groq, decision main vs rama,
aprobacion del motor de descarga.

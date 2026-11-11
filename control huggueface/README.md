# control huggueface — Centro de control de Spaces

## Rol
Control externo del plano Hugging Face. Pausa, reinicio, sleep-time, mirror,
wake y registry de modelos. No ejecuta logica de negocio de los routers.

## Componentes
| Archivo | Funcion |
|---|---|
| control_api.py | Endpoints pause/restart/sleep-time (falla cerrado sin ROUTER_API_KEY) |
| bootstrap_spaces.py | Arranque inicial de Spaces |
| sync_to_hf.py | Sincronizacion repo -> Space |
| hf_upload.sh | Upload de artefactos |
| mirror_spaces.py | Duplicar Space a region de respaldo (Objetivo 3.2) |
| trigger_wake.py | Despertar SLEEPING/PAUSED (Objetivo 3.3) |
| registry_models.py | SHA-256 de GGUF/LoRA, fill-on-first-run (Objetivo 3.6) |

## Seguridad
- ROUTER_API_KEY obligatoria, falla cerrado si falta.
- HF_TOKEN por entorno, nunca en el repo.
- Ningun archivo contiene valores de clave (escaneo de patrones).

## Variables de entorno
HF_TOKEN (obligatoria para HfApi)
ROUTER_API_KEY (obligatoria para control_api)

## Pruebas
python3 -m py_compile control_api.py mirror_spaces.py trigger_wake.py registry_models.py
bash -n hf_upload.sh

## Cierre (Salida 3/3, 2026-11-11)
Code cerrado: mirror, wake, registry. Pendiente operacional: fijar secrets en Spaces.

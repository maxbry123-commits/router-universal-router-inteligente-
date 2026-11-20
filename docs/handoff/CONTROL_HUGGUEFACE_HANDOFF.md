# Handoff — Centro de control Hugging Face (control huggueface/)

Actualizado: 2026-11-11 · Rama: ccr-f01c3de9-bmry0s · Salida 1/3 HF CERRADA.

## Estado
Control externo del plano HF. Pausa, reinicio, sleep-time, mirror, wake,
registry de modelos. No ejecuta logica de negocio de los routers.

## Componentes
| Archivo | Funcion |
|---|---|
| control_api.py | Endpoints pause/restart/sleep-time (falla cerrado sin ROUTER_API_KEY) |
| bootstrap_spaces.py | Arranque inicial |
| sync_to_hf.py | Sincronizacion repo -> Space |
| hf_upload.sh | Upload artefactos |
| mirror_spaces.py | Duplicar Space a respaldo (3.2) |
| trigger_wake.py | Despertar SLEEPING/PAUSED (3.3) |
| registry_models.py | SHA-256 GGUF/LoRA fill-on-first-run (3.6) |

## Seguridad
- ROUTER_API_KEY obligatoria, falla cerrado.
- HF_TOKEN por entorno, nunca en repo.
- Escaneo de patrones de clave: 0 coincidencias.

## Cerrado en Salida 1/3 HF
- mirror, wake, registry (Objetivos 3.2, 3.3, 3.6, 3.8)
- docs del centro de control

## Pendiente operacional (owner)
- Fijar secrets en Spaces s1/s2/s3
- Ejecutar mirror_all y wake_all tras configurar

## Hallazgos de auditoria Router 2 (fuera de este repo)
- H-2 JWT dev-change-me en hf-bucket-mcp/auth.py (parche propuesto, aplicar en Space origen)
- H-3 write_file sin allowlist en hf-bucket-mcp/server.py (parche propuesto, aplicar en Space origen)
- H-1 stub cuentas.js: decision owner (mantener marcado o quitar import de browser.js)

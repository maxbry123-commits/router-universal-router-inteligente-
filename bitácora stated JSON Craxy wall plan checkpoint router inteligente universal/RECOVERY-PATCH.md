# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Arquitectura y Handoff de componentes leídos.
- Plan limitado a 3 pasos aprobado por el Director.
- Paso 1 activo.
- Componentes movidos y verificados en `router inteligente universal/Componente open soure router inteligente universal/`.
- Reuse HF confirmado: `huggueface/manifest.yml` y `huggueface/bridge/router_hf_bridge.py`.
- Auditoría persistida en `router inteligente universal/integration/huggingface/HF-LLM-AUDIT.md`.
- StrategyDelta ejecutado con Hugging Face Job + `huggingface_hub.HfApi`: inventario público del owner `COMAND-CENTER-1` = 0 modelos.
- Job de control confirmó que no hay `HF_TOKEN` inyectado en el contenedor; privados/endpoints siguen sin demostrar.
- Paso 2 y Paso 3 permanecen pendientes; no añadir tareas externas al plan.

## Boot de recuperación
1. Leer `STATE.json`, `CHECKPOINT.json`, `PLAN-TAREAS.md`, `BITACORA-CRAZY-WALL.md`, README arquitectura y `HF-LLM-AUDIT.md`.
2. Consultar HEAD real y verificar destino/SHAs antes de escribir.
3. Continuar cola 1×1 desde `P01_COMPONENTS_AND_HF_LLM_AUDIT`.

## GAP-HF-CATALOG-001 — PARTIAL
La herramienta `model_search` sigue fallando, pero la ruta alternativa autorizada por Hugging Face Jobs resolvió el inventario público: `COUNT 0`. No inferir que esto incluye modelos privados ni endpoints configurados.

Evidencia:
- `https://huggingface.co/jobs/COMAND-CENTER-1/6aa0f30c32d5d0c22c5af586` → `COUNT 0`.
- `https://huggingface.co/jobs/COMAND-CENTER-1/6aa0f328900620b5c77e5534` → no token en entorno.

StrategyDelta siguiente: cruzar `HF_INFERENCE_ENDPOINT`/referencias persistidas y registry de endpoints; verificar IDs/revision/task por una ruta real antes de generar adapters FastAPI.

## Refutaciones persistentes
1. autenticación HF != modelos enumerados;
2. COUNT 0 público != ausencia de privados/endpoints;
3. bridge presente != LLM integrado.

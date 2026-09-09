# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Arquitectura y Handoff de componentes leídos.
- Plan limitado a 3 pasos aprobado por el Director.
- Paso 1 activo.
- Componentes movidos y verificados en `router inteligente universal/Componente open soure router inteligente universal/`.
- Reuse HF confirmado: `huggueface/manifest.yml` y `huggueface/bridge/router_hf_bridge.py`.
- Auditoría persistida en `router inteligente universal/integration/huggingface/HF-LLM-AUDIT.md`.
- Paso 2 y Paso 3 permanecen pendientes; no añadir tareas externas al plan.

## Boot de recuperación
1. Leer `STATE.json`, `CHECKPOINT.json`, `PLAN-TAREAS.md`, `BITACORA-CRAZY-WALL.md`, README arquitectura y `HF-LLM-AUDIT.md`.
2. Consultar HEAD real y verificar destino/SHAs antes de escribir.
3. Continuar cola 1×1 desde `P01_COMPONENTS_AND_HF_LLM_AUDIT`.

## GAP-HF-CATALOG-001
HF autenticado como `COMAND-CENTER-1`, pero `model_search` devolvió `Tool model_search not found`. No inferir ni inventar `model_id`.

StrategyDelta: usar otra ruta autorizada de lectura del Hub o evidencia persistida para enumerar modelos reales; reconciliar IDs/revision/task; solo entonces materializar registry/adapters FastAPI.

## Refutaciones persistentes
1. autenticación HF != modelos enumerados;
2. bridge presente != LLM integrado;
3. model_id sin evidencia != modelo disponible.

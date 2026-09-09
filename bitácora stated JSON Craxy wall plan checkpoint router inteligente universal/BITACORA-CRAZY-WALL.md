# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001 — BASELINE
Se replica el método de trabajo de `frontend/UI YAIWES/` sin copiar la arquitectura funcional de UI YAIWES.

## RIU-0002 — COMPONENTES OPEN SOURCE
Los componentes descargados fueron centralizados inicialmente y luego movidos a `router inteligente universal/Componente open soure router inteligente universal/`.

## RIU-0003 — ÍNDICE
Se crea índice de componentes y regla `presencia != integración`.

## RIU-0004 — ARQUITECTURA / LOOP
README arquitectura, guía LOOP, Crazy Wall, STATE, CHECKPOINT, PLAN y RECOVERY publicados.

## RIU-0005 — HANDOFF ARQUITECTURA
`readme Handoff indice componentes.md` identifica C01-C23, REUSE/PATCH/ADAPT/GENERATE y GAP de integración.

## RIU-0006 — PLAN 3 PASOS AUTORIZADO
1. Componentes + auditoría LLM/Hugging Face/FastAPI.
2. Cableado + poda + código faltante + filtro de comportamiento LLM.
3. Test integración HF + GitHub + API + agentes.
No se añaden pasos fuera de este contrato.

## RIU-0007 — P01 COMPONENTES
Movimiento físico completado bajo la raíz de código del Router; el tree de componentes queda preservado y se exige read-back antes de integración.

## RIU-0008 — HF REUSE AUDIT
Se audita código local antes de programar: `huggueface/manifest.yml` (`HF-ROUTER-BRIDGE-V1`, REMOTE_ONLY, FastAPI/OpenAI-compatible, secretos por env, failover HF1→HF2→HF3→WAITING) y `huggueface/bridge/router_hf_bridge.py` (provider_models/chat para proveedores remotos). Resultado: REUSE/PATCH primero; no crear segundo gateway sin justificar.

## RIU-0009 — GAP-HF-CATALOG-001
Autenticación HF confirmada para `COMAND-CENTER-1`; la enumeración por `model_search` falló con `Tool model_search not found`. Se persiste `router inteligente universal/integration/huggingface/HF-LLM-AUDIT.md`; prohibido inventar `model_id`.

## RIU-0010 — STRATEGYDELTA HF JOBS
Se cambia materialmente la estrategia: Hugging Face Jobs ejecuta `huggingface_hub.HfApi.list_models(author='COMAND-CENTER-1', full=True)`.
- Job `6aa0f30c32d5d0c22c5af586`: instalación reproducible de `huggingface_hub`; resultado `COUNT 0` para modelos públicos del owner.
- Job `6aa0f328900620b5c77e5534`: confirma `HF_TOKEN=False`, `HUGGING_FACE_HUB_TOKEN=False`, `HUGGINGFACE_TOKEN=False` dentro del contenedor.
Conclusión: el inventario público del owner queda verificado en cero; privados/endpoints siguen pendientes y no se infieren. GAP reclasificado a `PARTIAL_REMOTE_ENUMERATION`.

## 3 REFUTACIONES
1. HF autenticado ≠ modelos enumerados.
2. COUNT 0 público ≠ ausencia de privados/endpoints.
3. Bridge FastAPI presente ≠ LLM integrado.

## REGLAS
- INPUT literal.
- 1 nodo activo a la vez.
- No monolito.
- REUSE > PATCH > ADAPT > GENERATE.
- GAP → StrategyDelta distinto.
- Sin evidencia no hay PASS.
- Archivo presente ≠ integrado.

## NEXT
Cruzar referencias `HF_INFERENCE_ENDPOINT`/registry/configuración persistida, verificar modelos reales consumibles y solo entonces preparar adapters/FastAPI por `model_id` confirmado.

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
StrategyDelta: enumerar por otra ruta autorizada, reconciliar IDs/revision/task y solo entonces crear registry/adapters FastAPI.

## 3 REFUTACIONES
1. HF autenticado ≠ modelos enumerados.
2. Bridge FastAPI presente ≠ LLM integrado.
3. Modelo sugerido sin evidencia remota ≠ modelo disponible.

## REGLAS
- INPUT literal.
- 1 nodo activo a la vez.
- No monolito.
- REUSE > PATCH > ADAPT > GENERATE.
- GAP → StrategyDelta distinto.
- Sin evidencia no hay PASS.
- Archivo presente ≠ integrado.

## NEXT
Resolver `GAP-HF-CATALOG-001` con lectura alternativa autorizada y completar inventario real HF; después preparar adapters/FastAPI únicamente para modelos confirmados.

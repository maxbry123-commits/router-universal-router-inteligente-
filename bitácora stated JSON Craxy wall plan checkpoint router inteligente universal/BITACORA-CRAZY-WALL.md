# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001 — BASELINE
Se replica el método de trabajo de `frontend/UI YAIWES/` sin copiar la arquitectura funcional de UI YAIWES.

## RIU-0002 — COMPONENTES OPEN SOURCE
Los componentes descargados fueron centralizados inicialmente en `Componente open soure router inteligente universal/`.

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

## RIU-0007 — P01 ACTIVE
Se inicia `P01_COMPONENTS_AND_HF_LLM_AUDIT`.
Delta físico: mover la biblioteca open source completa bajo `router inteligente universal/Componente open soure router inteligente universal/` conservando el mismo tree SHA de componentes y eliminando la raíz top-level anterior mediante commit fast-forward.

## REGLAS
- INPUT literal.
- 1 nodo activo a la vez.
- No monolito.
- REUSE > PATCH > ADAPT > GENERATE.
- GAP → StrategyDelta distinto.
- Sin evidencia no hay PASS.
- Archivo presente ≠ integrado.

## NEXT
Read-back del destino movido + auditoría real de LLM disponibles en Hugging Face; después preparar adapters/FastAPI únicamente para modelos confirmados.

# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Arquitectura y Handoff de componentes leídos.
- Plan limitado a 3 pasos aprobado por el Director.
- Paso 1 activo.
- Destino de componentes: `router inteligente universal/Componente open soure router inteligente universal/`.
- Paso 2 y Paso 3 permanecen pendientes; no añadir tareas externas al plan.

## Boot de recuperación
1. Leer `STATE.json`, `CHECKPOINT.json`, `PLAN-TAREAS.md`, `BITACORA-CRAZY-WALL.md` y README arquitectura.
2. Consultar HEAD real y verificar destino/SHAs antes de escribir.
3. Continuar cola 1×1 desde `P01_COMPONENTS_AND_HF_LLM_AUDIT`.

## GAP/FLAG
GAP → investigar alternativas y ejecutar StrategyDelta materialmente distinto. FLAG → registrar evidencia y continuar solo con tarea independiente segura.

## Siguiente delta
Finalizar read-back del movimiento de componentes y continuar auditoría real de LLM/Hugging Face para definir adapters/FastAPI sin segundo orquestador.

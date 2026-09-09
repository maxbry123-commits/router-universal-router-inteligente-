# RECOVERY PATCH — ROUTER INTELIGENTE UNIVERSAL

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Estado válido
- Plan limitado a 3 pasos.
- Paso 1: componentes centralizados; owner público HF 0; privados/endpoints FLAG no bloqueante.
- Paso 2 ACTIVE: Gate/conectores reutilizados desde fuente canónica.
- `ConectorHuggingFace`, `ConectorDB`, `ConectorGitLab`, `ConectorMCPApp`, `ConectorVPS`, `ConectorMemoria`, `ConectorInterno` y `ConectorWebhook` permanecen contractualmente verificados.
- `connector_registry.py` actual registra HTTP/MCP/MCP App/GitHub/HuggingFace/DB/GitLab/VPS/Memoria/Interno/Webhook.
- Auditoría del filtro LLM cerrada como recuperación contractual: `Readme arquitectura router inteligente universal/README.md` exige filtro únicamente cuando exista contrato definido/recuperado.
- Handoff referencia `enchufe/validator_v2.py`, pero fetch de esa ruta en `main` devuelve 404; búsqueda de código no recuperó contrato explícito del filtro.
- No se generó semántica/policy inventada.
- Paso 3 pendiente.

## Boot de recuperación
1. Leer STATE/CHECKPOINT/PLAN/BITACORA/README arquitectura.
2. Verificar HEAD y SHAs.
3. Continuar P02 cola 1×1 con StrategyDelta de recuperación contractual: documentos fuente de verdad + donor local `guardrails`.
4. Solo si aparece contrato explícito, materializarlo detrás de guard/plugin y fijar test; si no aparece, continuar únicamente tarea P02 independiente segura.

## GAP-HF-CATALOG-001
No inventar modelos. Reintentar privados/endpoints solo con nueva evidencia consumible; continuar tareas P02 independientes.

## GAP-BEHAVIOR-CONTRACT-001
No inventar reglas de comportamiento. Evidencia: README arquitectura blob `85365fb67397ebb38c6660afaea04b079ce17fe5`; Handoff blob `1182154d2a96497867f29529cf97871a18a9434b`; `enchufe/validator_v2.py` ausente en `main` (404).

## Refutaciones
1. Donor `guardrails` disponible físicamente != contrato de comportamiento autorizado.
2. Handoff que menciona `validator_v2.py` != archivo materializado.
3. Auditoría contractual cerrada != filtro LLM implementado ni Paso 2 cerrado.

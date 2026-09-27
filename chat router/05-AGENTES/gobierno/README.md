# Gobierno del equipo YAIWES (T01)

T01 gobierna al **agente ejecutor** con controles deterministas. El agente no
puede declararse PASS por texto libre: el cierre depende de evidencia real.

## Control del agente

| Módulo | Función |
|---|---|
| `agent_control.py / AgentDSL` | DSL declarativo del objetivo |
| `AgentDAG` | orden fijo de estados y ramas de recuperación |
| `AgentTaskSpec + SchemaValidator` | schema/contrato y validación previa |
| `sheriff.py` | bloquea dependencias/rutas prohibidas |
| `EvidenceVerifier` | exige archivos completos + pytest exit 0 + tests > 0 |
| `sentinel.py` | watchdog de runtime |
| `Guardian` | bloquea path escape, falso verde y sync con árbol sucio |
| `Investigator` | prepara ResearchPacket, máximo 20 fuentes |
| `AgentOrchestrator` | decide PASS / REVISE / RESEARCH / BLOCK |
| `judge.py` | gate final |
| `mirror_manager.py` | worktree aislado + merge selectivo |

## Micro flujo

`DSL → DAG → Schema → Sheriff → Ejecutar → Verificar → Guardián → Judge`
`                                      ↘ REVISE → Investigar → Ejecutar`

## Regla de cierre

PASS solo si:
1. todos los archivos requeridos existen;
2. pytest fue ejecutado y devuelve código 0;
3. se recolectó al menos un test;
4. no hay cambios fuera del scope;
5. el trabajo se integra desde el mirror limpio.

## Reparación T01

Se corrigieron dos causas del fallo original de MirrorManager:
- el merge `--no-ff` del repo principal ahora recibe identidad Git;
- los archivos no rastreados se obtienen con `git status --porcelain`, por lo
  que un archivo nuevo prohibido ya no puede escapar del Sheriff/Guardian.

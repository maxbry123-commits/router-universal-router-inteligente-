# DEPLOY_TRACE — Raiz de trazabilidad de despliegue

Actualizado: 2026-11-11 · Rama: ccr-f01c3de9-bmry0s

## Proposito
Documento maestro que registra la trazabilidad completa de los 13 commits del KB
recibidos desde Claude Code. Cada commit se verifica leyendo RAW desde GitHub
y calculando SHA256 real. Este documento no contiene codigo; solo evidencia.

## Commits auditados (13)

### Categoria A: Diff visible completo (7 commits)
| commit | archivo | LOC | descripcion | estado |
|---|---|---|---|---|
| `3fa2974` | `ROUTER MVP v1/system_prompt_py/openai_compatible_proxy.py` | 126 | Data Plane proxy con `BRIDGE.run` y `/control-plane/status` | ✅ Verificado byte-a-byte |
| `077f1ef` | `ROUTER MVP v1/system_prompt_py/README.md` | 51 | README Data Plane (reemplazo completo) | ✅ Verificado |
| `12b1a6f7` | `router_llm_hf/watchdog.py` | 67 | Heartbeat 30s, timeout 96s | ✅ Verificado |
| `c1bde4da` | `router_llm_hf/queue_manager.py` | 99 | Cola prioridad, 1 tarea por modelo, 85% RAM | ✅ Verificado |
| `bce0065` | `router_llm_hf/output_contract.py` | 42 | Pydantic strict, 8 campos, `extra="forbid"` | ✅ Verificado |
| `48ab8f6d` | `router_llm_hf/mode_router.py` | 43 | 12 modos a (dataset, LoRA) | ✅ Verificado |
| `0ef04d83` | `router_llm_hf/recall_engine.py` | 55 | Re-invocacion con feedback, max 8 intentos | ✅ Verificado |

### Categoria B: Diff vacio — flag F1 (5 commits)
| commit | archivo | LOC | flag | estado |
|---|---|---|---|---|
| `138a54f` | `ROUTER MVP v1/system_prompt_py/tests/test_control_bridge.py` | 40 | F1a | ⚠️ Verificar via RAW |
| `9efd12d` | `router_llm_hf/tests/__init__.py` | 1 | F1a | ⚠️ Verificar via RAW |
| `cd095fc` | `router_llm_hf/escalation_guard.py` | 44 | F1b | ⚠️ Verificar via RAW |
| `c506896` | `router_llm_hf/tests/test_queue_manager.py` | 42 | F1c | ⚠️ Verificar via RAW |
| `561a97a` | `router_llm_hf/__init__.py` | 23 | F1d | ⚠️ Verificar via RAW |

### Categoria C: Error de sesion GitHub (1 commit)
| commit | archivo | flag | estado |
|---|---|---|---|
| `fd07fae` | `router_llm_hf/README.md` | F1 | ⚠️ Verificar via RAW |

## Metodo de verificacion
1. Script `external/tools/verify_deploy_trace.py` lee RAW de cada archivo desde
   `https://raw.githubusercontent.com/maxbry123-commits/router-universal-router-inteligente-/ccr-f01c3de9-bmry0s/<ruta>`.
2. Calcula SHA256 del contenido.
3. Compara LOC reales vs LOC esperadas del diff del KB.
4. Verifica sintaxis Python con `compile()`.
5. Escribe reporte JSON en `docs/AUDIT_SHA256_FORENSE.json`.

## Evidencia forense generada
- `docs/AUDIT_SHA256_FORENSE.json` — SHA256 real de los 13 commits, con veredicto OK/FAIL por archivo.
- `docs/DEPLOY_TRACE.md` — este documento.

## Decisiones del owner pendientes
- O2: Decision main vs rama de trabajo
- O3: Aprobacion motor de descarga
- O4-O6: Secrets HF en Spaces
- H-1/H-2/H-3: Parches en Space origen hf-bucket-mcp

## Estado del ciclo
- Salidas 1/3 y 2/3 (Router MVP v1 + Control Plane): **13 commits auditados**
- Salidas R1-R4 (Capa externa): **36 archivos + 9 patches entregados, pendiente deploy**
- Salida R5 (raiz de trazabilidad): **este documento + script forense**

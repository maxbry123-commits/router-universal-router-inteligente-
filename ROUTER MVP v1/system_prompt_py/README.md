---
title: Router MVP v1
emoji: 🚦
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---
# Router MVP v1

Orquestador de dos agentes (Chat A arquitecto, Chat B implementador) sobre proveedores externos (Groq, NVIDIA) con checkpoint persistente, bloques de código ≤200 LOC verificados con pytest y herramientas HTTP.

Actualizado: 2026-11-08 · rama `ccr-f01c3de9-bmry0s` · último código `c38821dd87` (Lote 35).

## Arquitectura

```
Cliente OpenAI-compatible
        │
openai_compatible_proxy.py  (FastAPI, 7860)
        │  ProviderHTTPError (≥400)
        ▼
ChatABOrchestrator (chat_ab_orchestrator.py)
 ├─ ChatAArchitect ........ consejo y descomposición en bloques
 ├─ ChatBImplementer ...... genera código o pide herramienta
 │    └─ GenericModelAdapter ─ fallback_middleware ─ provider_window
 │         (Groq, NVIDIA; 114 s de ventana; sin saldo → no_balance)
 ├─ code_splitter ......... AST, partes ≤200 LOC + agregador
 ├─ SemanticCheckpoint .... completed_blocks, partials, parts, locked_objective
 ├─ EvidencePacket ........ evidencia por parte (code, tests)
 ├─ ToolExecutor .......... HTTP a AGENT_HARNESS_URL
 ├─ research_engine ....... búsqueda sin LLM (no cableada como herramienta)
 └─ gap_resolution_loop ... fail-closed ante gaps repetidos
```

Flujo por bloque: deduplicación → contexto de reanudación → llamada a Chat B (continuación si `finish=length`, parcial guardado si se agota) → pytest sobre el bloque → checkpoint → evidencia.

## Archivos clave

| Archivo | Responsabilidad |
|---|---|
| `chat_ab_orchestrator.py` | Bucle principal, rondas, goal lock, pytest. |
| `chat_b_implementer.py` | Continuación y `IncompleteResponse`. |
| `generic_model_adapter.py` | Llamadas a proveedores con pool de llaves. |
| `provider_window.py` | Ventana deslizante de 114 s (Groq 8, NVIDIA 12). |
| `fallback_middleware.py` | Reintento en el mismo proveedor; cambio solo si no hay saldo. |
| `code_splitter.py` | División determinista de código. |
| `semantic_checkpoint.py` | Estado persistente. |
| `evidence_packet.py` | Evidencia de código y pruebas. |
| `control_api.py` | Pausar, reiniciar y fijar sleep-time de Spaces en Hugging Face. |
| `scaler_ram.py`, `inject_scaler.py` | Autoescalado. **No se ejecuta** desde 2026-11-08. |

## Variables de entorno

| Variable | Uso |
|---|---|
| `ROUTER_API_KEY` | Clave del router. Pendiente: fallar cerrado si falta (no usar `dev_key`). |
| `GROQ_KEYS`, `NVIDIA_KEYS` | Llaves separadas por coma. |
| `AGENT_HARNESS_URL` | URL del harness de herramientas. Obligatoria. |
| `HF_TOKEN` | Token para `control_api.py`. |
| `ORCHESTRATOR_WORKSPACE` | Carpeta de bloques generados. |

No guardar valores en el repositorio.

## Verificar

```bash
pip install -r requirements.txt pytest
python -m py_compile provider_window.py fallback_middleware.py generic_model_adapter.py \
  openai_compatible_proxy.py code_splitter.py semantic_checkpoint.py chat_b_implementer.py chat_ab_orchestrator.py
```

La simulación del lote 35 vive fuera del repo (scratchpad). Pendiente copiarla a `tests/`.

## Documentación relacionada

- `docs/handoff/ROUTER_MVP_V1_HANDOFF.md` — estado, riesgos y pendientes.
- `docs/bitacora/BITACORA_CRAZY_WALL.html` — mapa de una pantalla.
- `docs/handoff/LLM_SYSTEM_HF_HANDOFF.md` — Space de modelo local.

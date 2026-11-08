# Handoff — Router MVP v1 (`ROUTER MVP v1/system_prompt_py/`)

Actualizado: 2026-11-08. Rama: `ccr-f01c3de9-bmry0s`. Último commit de código: `c38821dd87` (Lote 35). Último commit de docs: ver `git log`.

## 0. Registro de actividad (más reciente primero)

- 2026-11-08 — Lote 35 en `c38821dd87`: ventana de proveedor, aviso de saldo, división ≤200 LOC, parcial persistente. Simulación TODO OK (fuera del repo).
- 2026-11-08 — Dockerfile: CMD sin `scaler_ram.py` (encendido automático retirado).
- 2026-11-08 — README y handoffs actualizados con arquitectura. SALIDA 3 retirada del repo.
- 2026-11-08 — `test_audit.py`: no existe en el repo ni en las ramas. Pendiente de localizar.

## 0.1 Arquitectura resumida

Proxy OpenAI-compatible (`openai_compatible_proxy.py`) → `ChatABOrchestrator` → Chat A (descomposición) y Chat B (implementación) → `GenericModelAdapter` con `fallback_middleware` y `provider_window` → Groq/NVIDIA. Bloques pasan por `code_splitter`, pytest, `SemanticCheckpoint` y `EvidencePacket`. Detalle en `ROUTER MVP v1/system_prompt_py/README.md`.

## 1. Qué es
Router con orquestación Chat A (arquitecto) / Chat B (implementador) sobre proveedores Groq y NVIDIA, con checkpoint, parcial persistente, bloques ≤200 LOC verificados con pytest, herramientas HTTP y bucle agéntico acotado.

## 2. Estado por componente

| Componente | Archivo | Estado |
|---|---|---|
| Orquestador A/B | `chat_ab_orchestrator.py` | Funciona con fakes (sim35 PASS). Sin prueba contra proveedor real. |
| Implementador B | `chat_b_implementer.py` | Continuación por `finish=length`, `IncompleteResponse` guarda parcial. |
| Adaptador de modelo | `generic_model_adapter.py` | Groq y NVIDIA. Pool de llaves por `GROQ_KEYS` / `NVIDIA_KEYS`. |
| Ventana de proveedor | `provider_window.py` | 114 s, Groq 8 / NVIDIA 12 peticiones. Espera en el mismo proveedor. |
| Fallback | `fallback_middleware.py` | Sin saldo → evento `no_balance` y siguiente proveedor. Todos sin saldo → `NoBalanceError`. |
| Proxy OpenAI-compatible | `openai_compatible_proxy.py` | Devuelve `ProviderHTTPError` en ≥400. CMD: uvicorn en 7860. |
| División de código | `code_splitter.py` | AST, partes ≤200 LOC, agregador. Nodo >200 → `NodeTooLargeError`. |
| Checkpoint | `semantic_checkpoint.py` | `partials`, `parts`, `completed_blocks`, `locked_objective`. |
| Evidencia | `evidence_packet.py` | Registra por parte. Rechaza bloque >200. |
| Investigación web | `research_engine.py`, `web_search_tool.py` | Motor sin LLM. **No cableado** como herramienta `buscar_web`. |
| Bucle de gaps | `gap_resolution_loop.py` | Fail-closed. |
| Herramientas | `tool_executor.py` | Requiere `AGENT_HARNESS_URL` (falla al construir si falta). |
| Control HF | `control_api.py` | Pausa, reinicio, sleep-time. Ver riesgo R1. |
| Autoescalado | `scaler_ram.py`, `inject_scaler.py` | **Desactivado en CMD** desde este handoff (ver §5). Archivos conservados. |

## 3. Variables de entorno

| Variable | Obligatoria | Uso |
|---|---|---|
| `ROUTER_API_KEY` | Sí | Clave maestra del router. Ver R1. |
| `GROQ_KEYS` | Sí para Groq | Llaves separadas por coma. |
| `NVIDIA_KEYS` | Sí para NVIDIA | Llaves separadas por coma. |
| `AGENT_HARNESS_URL` | Sí para herramientas | URL HTTP del harness. |
| `HF_TOKEN` | Para `control_api` | Token de Hugging Face. |
| `ORCHESTRATOR_WORKSPACE` | No | Carpeta de bloques generados. Por defecto `./workspace`. |
| `NEXT_SPACE_URL` | No | Solo lo usa `scaler_ram.py`, que ya no arranca. |

No guardar valores en el repositorio.

## 4. Cómo verificar

```bash
cd "ROUTER MVP v1/system_prompt_py"
pip install -r requirements.txt pytest
python -m py_compile provider_window.py fallback_middleware.py generic_model_adapter.py \
  openai_compatible_proxy.py code_splitter.py semantic_checkpoint.py chat_b_implementer.py chat_ab_orchestrator.py
```

Resultado en el último lote: compilación OK; simulación de lote 35 (`sim35.py`) TODO OK.

**Gap de trazabilidad:** la simulación `sim35.py` está en la carpeta de scratchpad de la sesión y **no está en el repositorio**. Hay que copiarla a `tests/` antes de depender de ella.

## 5. Cambios en este handoff

- **Dockerfile:** el CMD ya no lanza `scaler_ram.py` en segundo plano. Antes, cuando la RAM superaba el 85 %, `scaler_ram.py` despertaba el Space indicado en `NEXT_SPACE_URL`. Eso es encendido automático, y la instrucción previa era eliminarlo. Ahora el CMD es solo `uvicorn openai_compatible_proxy:app`.

## 6. Riesgos abiertos

- **R1 — Clave por defecto en `control_api.py`:** `ROUTER_API_KEY` cae a `"dev_key"` si la variable no existe. Con esa clave se puede pausar o reiniciar Spaces. Debe fallar cerrado si falta la variable.
- **R2 — NVIDIA devuelve 410** en los watchdogs del historial (ciclos 2026-11-06 a 2026-11-07). Groq sí responde. Revisar si el endpoint o la llave cambiaron.
- **R3 — Historias divergidas:** `main` (`7ff5e111ba`) y la rama de trabajo no se contienen mutuamente. No mezclar sin revisar.
- **R4 — Herramienta web sin cablear:** el motor de búsqueda existe, pero el modelo no puede llamarlo todavía.
- **R5 — Descarga y extracción de componentes:** requiere aprobación explícita (ejecuta código descargado). No implementada.

## 7. Pendientes (orden sugerido)

1. Copiar `sim35.py` a `tests/` y ejecutarlo en CI o local.
2. Quitar el valor por defecto `dev_key` (R1).
3. Cablear `buscar_web` en el orquestador y en Chat B (R4).
4. Búsqueda de componentes en GitHub y Hugging Face, solo lectura por API (metadatos).
5. Decidir cómo integrar `main` y la rama de trabajo (R3).
6. Prueba real contra Groq con llaves de prueba (la ventana de 114 s no se ha medido en vivo).
7. Aprobación para el motor de descarga y extracción (R5).

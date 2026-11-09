# HANDOFF — Sistema Chat A / Chat B y recuperación de modelos

Actualizado: 2026-11-09 · Rama: `ccr-f01c3de9-bmry0s` (Router 1) · Carpeta: `ROUTER MVP v1/system_prompt_py/`
Estado: Chat A es un esqueleto. Chat B y la recuperación funcionan con simulación. Las tools nuevas NO están conectadas al orquestador.

## 1. Archivos del sistema

| Archivo | Función | Estado |
|---|---|---|
| [chat_ab_orchestrator.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/chat_ab_orchestrator.py) | Bucle principal: une Chat A, Chat B, checkpoint, dedup, pytest y evidencia. | Activo. Usa el plan fijo de Chat A. |
| [chat_a_architect.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/chat_a_architect.py) | Consejo (`ask_council`) y descomposición (`decompose`). | ESQUELETO: siempre 3 bloques genéricos y `AUTHORIZE`. Sin llamada al modelo. |
| [chat_b_implementer.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/chat_b_implementer.py) | Genera código y tests. Si la respuesta se corta tras 3 continuaciones, levanta `IncompleteResponse` con el parcial. | Activo. Probado con simulación. |
| [semantic_checkpoint.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/semantic_checkpoint.py) | Estado persistente en `.checkpoints/`: bloques completados, parciales, partes, objetivo bloqueado (goal lock). | Activo. Es el checkpoint que usa el orquestador. |
| [code_splitter.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/code_splitter.py) | Divide código en partes ≤200 LOC por AST, con agregador. Nodo >200 LOC lanza `NodeTooLargeError`. | Activo. |
| [context_rehydrator.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/context_rehydrator.py) | Arma el resumen de reanudación: bloques hechos, último error, bloque actual. | Activo. |
| [workflow_tools.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/workflow_tools.py) | Tools nativas: `dividir_tarea`, `entregar_parte`, `checkpoint_guardar`, `recuperar_checkpoint`, `continuar_cola`. | Probado. NO conectado al orquestador (0 referencias). |
| [tool_executor.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/tool_executor.py) | Enruta las 5 tools de workflow a `WorkflowTools` si `ToolExecutor.workflow` está asignado. | Enrutamiento listo. Nadie asigna `workflow` todavía. |
| [evidence_packet.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/evidence_packet.py) | Evidencia por parte y resultados de pytest. Rechaza bloques >200 LOC. | Activo. En memoria, no persiste tras un fallo del proceso. |
| [deduplication_layer.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/deduplication_layer.py) | Evita regenerar el mismo bloque. TTL de 60 s por defecto. | Activo. El TTL es corto. |
| [loc_limits.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/loc_limits.py) | Límites: `MAX_BLOCK_LOC=200`, `MAX_CONTINUATIONS=3`, `MAX_PACK_CHARS=3000`. | Activo. |
| [agentic_loop_controller.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/agentic_loop_controller.py) | Cuenta rondas (máximo 3) y detecta llamadas repetidas. | Activo. |
| [checkpoint_manager.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/checkpoint_manager.py) | Segundo sistema de checkpoint (SHA-256 y `core_recovery`). | NO usado por el orquestador. Duplicado a decidir. |
| [workflow_state.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/workflow_state.py) | Estado de workflow. | NO revisado a fondo. Decidir si sirve o va a cuarentena. |
| [resume_validator.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/resume_validator.py) | Valida los campos obligatorios del checkpoint al cargarlo. | Activo (lo llama `semantic_checkpoint`). |
| [forensic_dlq.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/forensic_dlq.py) | Cola de errores forense; el rehidratador reproduce el último fallo. | Activo. |
| [gap_resolution_loop.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/gap_resolution_loop.py) | Bucle de gaps fail-closed con `buscar_web`. | Activo. |
| [research_engine.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/research_engine.py) | Motor de investigación sin LLM (variantes, fuentes, score). | Activo. |
| [tool_executor.py](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/ccr-f01c3de9-bmry0s/ROUTER%20MVP%20v1/system_prompt_py/tool_executor.py) | Ejecutor de tools (ver arriba). | Activo. |
| `tests/sim35.py` y `tests/test_workflow_tools.py` | Simulación del flujo completo y pruebas de tools. | Pasan con proveedores falsos. |

## 2. Flujo actual (cómo funciona hoy)

1. Chat A (`ask_council`) devuelve `AUTHORIZE`. Siempre.
2. `decompose` devuelve 3 bloques fijos. Se calcula `plan_sha256` sobre ese plan.
3. El objetivo se bloquea (`lock_objective`). Si cambia, se aborta.
4. Por cada bloque no completado:
   a. Dedup: si ya existe el mismo bloque, se restaura del caché.
   b. El rehidratador arma el resumen de reanudación.
   c. Chat B genera código o pide una tool, hasta 3 rondas.
   d. Si la respuesta se corta tras 3 continuaciones: `save_partial`. Al reintentar, el prompt incluye el parcial.
   e. Si hay código: se divide en partes, se escribe el agregador, se corre pytest.
   f. Si pasa: `save_block`, `clear_partial`, `store_response`, registro de evidencia.
5. Si el proceso se cae: al reiniciar, `get_next` salta los bloques completados y se reanuda el bloque en curso.

## 3. Qué se recupera y qué no

| Caso | ¿Se recupera? | Cómo |
|---|---|---|
| Bloque completado, proceso reiniciado | Sí | `completed_blocks` en el checkpoint. |
| Respuesta de Chat B cortada | Sí | `partials` + `IncompleteResponse`. |
| Partes ya generadas de un bloque | Parcial | `parts` se guarda, pero el orquestador no las reutiliza al reanudar. |
| Resultados de tools dentro de un bloque | NO | El resultado vive en `enhanced_prompt` (memoria). Si el proceso cae, se pierde. |
| Evidencia (pytest, partes) | NO tras un fallo | `EvidencePacket` vive en memoria. |
| Plan del modelo | NO existe | El plan es fijo. |
| Cambio de objetivo | Se bloquea | Goal lock. |

## 4. Gaps (para el plan de Claude Code 4 y Router 1)

- **G-CAB-1 Chat A no planifica.** Hay que llamar al modelo para que genere el plan vía `dividir_tarea`.
- **G-CAB-2 `workflow_tools` no está conectado.** `chat_ab_orchestrator.py` no lo usa. Hay que asignar `ToolExecutor.workflow` y que el bucle use `continuar_cola`.
- **G-CAB-3 Dos checkpoints.** `checkpoint_manager.py` y `semantic_checkpoint.py` hacen cosas parecidas. Hay que elegir uno y mover el otro a cuarentena.
- **G-CAB-4 Tool results no persistidos.** Hay que guardar cada resultado de tool en el checkpoint antes de continuar.
- **G-CAB-5 Evidencia no persistida.** Hay que escribirla en `runtime/evidence/` tras cada parte.
- **G-CAB-6 Dedup de 60 s.** Para recuperación entre reinicios conviene más TTL o clave por plan.
- **G-CAB-7 Sin prueba en vivo.** Chat B y la recuperación solo se probaron con proveedores falsos. Falta una prueba con Groq o NVIDIA cuando haya llave.
- **G-CAB-8 Reutilizar partes al reanudar.** Si el bloque tenía partes guardadas, el orquestador debería continuar desde la parte pendiente, no regenerar el bloque.

## 5. Propuesta de conexión (pendiente de aprobación)

1. Chat A: el modelo recibe la tarea y llama `dividir_tarea` con sus bloques.
2. El orquestador asigna `ToolExecutor.workflow = WorkflowTools(checkpoint)`.
3. Por cada bloque, el bucle llama `continuar_cola` para elegir la parte siguiente.
4. Cada resultado de tool se guarda con `checkpoint_guardar` antes de la siguiente ronda.
5. Al reiniciar, `recuperar_checkpoint` devuelve hechas, pendientes y parciales, y el bucle sigue desde ahí.

## 6. Pruebas que deben pasar antes de cerrar

- [ ] `tests/test_workflow_tools.py` (4 pruebas) y `tests/sim35.py`.
- [ ] Prueba de reinicio: matar el proceso a mitad de un bloque y reanudar sin regenerar bloques completados.
- [ ] Prueba de tool result persistido: el resultado sobrevive a un reinicio.
- [ ] Prueba del plan del modelo: un plan distinto del fijo se guarda y se respeta.
- [ ] Prueba en vivo con Groq o NVIDIA (🚩 hasta que haya llave en el entorno).

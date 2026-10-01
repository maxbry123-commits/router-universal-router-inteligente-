# Plan de acción tras cotejo X-Ray

Estado: EN CURSO. Fuente: commit `aa8fed0631913783c77d3b9ad3fcca62e1978c11`, los skills trasladados y las capturas adjuntas al chat. Este plan conserva los contratos literales: no los convierte en ejecución por aparecer en el repositorio.

## Cuatro pasadas y verificación cruzada

1. **Procedencia.** Los 30 documentos del enlace (27 contenidos distintos) y 82 skills se preservaron bajo `01-PLAN/`; 65 referencias, 5 diagramas y 12 capturas suman 82 PNG. Los hashes de las 12 capturas coinciden con los 12 adjuntos descargados de la conversación; las dos copias de la captura `052636` tienen el mismo SHA-256. La captura `093043` se añadió como `UI-EXTRA-017`. `AUDITORIA-4-PASADAS.json` conserva fuente, destino, SHA-256 y duplicados por archivo.
2. **Estructura.** La auditoría registra sintaxis comprobable de Python/JSON/YAML/JS/shell, integridad ZIP y encabezados del plan; 6 TSX siguen `🚩 PENDIENTE: TSX_NOT_PARSED`. Los 82 PNG pasan firma, dimensiones declaradas y hash. Un PNG legible no prueba que el texto de la captura sea verdadero.
3. **Integración.** `AUDITORIA-4-PASADAS-POST-CODE.json` registra 19 archivos de código y la prueba local del endpoint autenticado `/chat/org/visual-references`: verifica los 82 hashes y expone solo metadatos. `/chat/send` guarda el turno en SQLite vía fachada de memoria, lo vuelve a leer y aísla el scope por propietario. Los documentos y skills sin prueba de ejecución permanecen `🚩 PENDIENTE`; las imágenes son `REFERENCE_ONLY`. La captura de GPT-6 Sol prueba lo que muestra la pantalla, no el modelo interno de Devin.
4. **Evidencia.** 68 pruebas focalizadas pasan (30 del gate T07 simulado); las suites gate/DAG se solapan con esta selección. El verificador rechaza claims no tipados, hashes falsos y carpetas presentadas como archivos; el recibo de un reviewer debe identificar al actor correspondiente. El compilador produce IDs reproducibles y consultas tipadas; fanout conserva evidencia local si falla GitHub y registra el error como observación tipada para que el gate quede `INCOMPLETE`. La búsqueda local comprueba un plazo entre archivos, pero una operación de E/S bloqueada no tiene cancelación dura. La Puerta recalcula el checksum sobre hechos, fuentes, parser, consultas y observaciones, y exige que cada hecho cite una fuente presente; rechaza alteraciones posteriores como `INCOMPLETE`. Ese hash es una suma de control local, no una firma ni identidad autenticada de Sentinel, Hermes u OpenClaw. Los nuevos eventos de Bitácora incluyen ID y hash de contenido; replay recupera el snapshot en una prueba local, y corrupción posterior o pérdida de los campos de versión después de un evento v2 falla. Los eventos anteriores sin hash siguen siendo legibles; no existe autenticación criptográfica ni garantía de append-only remota. Un test de proveedores espera ocho entradas mientras `openai` figura tanto en el código como en la prueba de `origin/main`. Ruff del backend y los módulos T-11 modificados pasa. No hay respuesta OpenAI real, receipts de revisores externos, conexión runtime Graphiti/Graphify, restauración HF ni prueba visual completa; ninguna recibe `PASS`. La ruta organizativa exige Bitácora en GitHub y devuelve 503 sin esa escritura: la prueba aislada sustituye ese transporte, no lo certifica remotamente.

## Orden ejecutable

| ID | Entrada contractual | Acción y criterio de salida | Estado |
|---|---|---|---|
| X-01 | `T-11-02-PROGRAMACION-NUEVO-01-A-19.md` | Reusar parser, compilador y Puerta existentes: 12 instrucciones conocidas se clasifican de forma determinista, una orden ambigua/negada produce `UNKNOWN`, ninguna query y ningún PASS. Mapear los demás contratos, fanout y EvidencePacket antes de cerrarlo | PARCIAL; 🚩 PENDIENTE: RESTO T-11 |
| X-02 | `T-11-05-HANDOFF-TESTS-PASS-FAIL.md` | Claims falsos, hash incorrecto y reviewer actor suplantado se rechazan localmente; faltan recibos firmados o autenticados de actores externos, lease, replay, recovery y autoridad Judge | PARCIAL; 🚩 PENDIENTE: RESTO T-11 |
| X-03 | `T-11-I-01-SKILL-RUNTIME-SCHEMA-CODE.md` y catálogo de 82 skills | Separar `DOCUMENTATION_ONLY` de código ejecutable; registrar entrada, salida, hash, licencias y adapter Fables antes de activar un skill | 🚩 PENDIENTE |
| X-04 | `T-11-04-HUELLA-DIGITAL-ARCHITECTURE-XRAY.md` | Crear huella de componentes, rutas, tests y conectividad real; marcar `CONFIGURED` distinto de `ACTIVE` | 🚩 PENDIENTE |
| X-05 | Contrato T-12 de investigación sin LLM | Inspeccionar entrypoint del motor de búsqueda existente y ejecutar normalización/deduplicación con `LLM_CALLS=0`; no lanzar 20 búsquedas sin contrato verificado | 🚩 PENDIENTE |
| X-06 | Catálogos de 82 imágenes y Maxbry UI | Mantener metadata backend y roles individuales; revisar contenido visual, secretos y componentes frontend solo al cerrar backend | 🚩 PENDIENTE: VISUAL/FRONTEND |
| X-07 | Memoria Manus y `/chat/send` | Validar aislamiento, persistencia y read-back de SQLite; comprobar con evidencia independiente servicios externos y HF antes de `CONNECTED` | LOCAL VERIFICADO; 🚩 PENDIENTE: EXTERNOS |
| X-08 | T-11 cierre y T-06 | Ejecutar suite backend, comparar revisión publicada y probada, luego prueba desktop/tablet/móvil con segunda pasada; no desplegar todavía | 🚩 PENDIENTE |

El endpoint de referencias comprueba schema, conteo, IDs únicos, ruta y SHA-256; devuelve 503 ante JSON corrupto o entradas inválidas. Solo entrega metadatos; la validación visual independiente sigue 🚩 PENDIENTE.

Siguiente acción exacta: cerrar T-11-C con cancelación dura y segura de la búsqueda local y procedencia de cada hecho; después completar T-11-D con integridad/autenticación de eventos heredados y convergencia remota antes de lease/recovery. 🚩 PENDIENTE: demostrar identidad y ejecución independiente de los reviewers. GitHub Actions no se usa para esta validación.

Comprobación ampliada del backend (separada del gate focalizado): 371 passed, 5 failed, 1 deselected tras instalar `cryptography==48.0.0` y `pytest-asyncio==0.25.3`; 23 pruebas de conectores asíncronos y banco de claves pasan. `requirements.txt` ahora declara la dependencia que el vault necesita. 🚩 PENDIENTE: un E2E con destino público GitHub devolvió 502; la lista de modelos certificados no contiene `Qwen/Qwen3-0.6B` que exige el test; el archivo de política configura `sdk` y el test todavía exige cadena vacía; el mapa JSON incluye `openai` mientras el mapa incorporado y su test no. No se añadieron modelos sin evidencia ni se eliminaron rutas configuradas para ocultar fallos. Las pruebas simuladas de T-11 se ejecutan en proceso independiente porque su bandera de simulación se fija durante el import; en un proceso conjunto depende del orden de importación. 🚩 PENDIENTE: corregir esa independencia de la suite y resolver las discrepancias con la autoridad de configuración.

## Copia wordflow loop code Yaiwes (motor_3, commit `b214f9fe96`)

- Raíz real confirmada por HANDOFF adjunto: `➡️📂 wordflow loop code Yaiwes/` del repo `agentes` (la variante sin emoji está vacía: solo `.gitkeep`; la variante `➡️📂 Wordflow LOOP Yaiwes` solo contiene `wordflow_loop/agent_sources`).
- Copia física verificada por `motor_3_copy_batches.py` (`yaiwes.frontend.copy-batches.v1`): 397 archivos, 16 lotes, SHA-256 por archivo, `VERIFIED_CLOSED`, sin mirror ni move.
- Excluidos por instrucción: `wordflow_loop/agent_sources/` (~20 agentes, 112k archivos) y `frontend/Orca` (27k, vendored) — frontend sigue bloqueado hasta cerrar backend.
- Motores canónicos copiados a `chat router/➡️📂motores de descarga extracción copiado movimiento archivos agentes/` y `chat router/➡️📂 Wordflow LOOP Yaiwes/➡️📂motores...` porque los tests propios del loop verifican blob SHA-1 contra esas rutas exactas.
- Cobertura T-11 aportada por la copia: `dag_engine`, `kernel` (MicroMission/scheduler), `state_machine`, `crazywall_claim_gate` (claims con version/ownership), `continuity_supervisor`, `recovery/{checkpoint,classifier,engine,reconciliation,circuit_breaker_sla}`, `event_bus`, `parallel_scheduler`, `uek/{boot_engine,ficha_contract_v2,sandbox_manager,universal_plugin_bus_v2_integrated}`, `tribunal/{tribunal,hmac_manager,constitutional,budget_gate,cross_validator}`, `mission/sharder`, `observability/engine`, `wordflow_loop/wordflow_loop/{contracts,ledger,llm_gate,model_api_router_mvp,agent_fleet,governance/{judge,sheriff,sentinel,guardian,supervisor,validator,verifier}}`.
- El plugin bus copiado es la variante G-018 (AST-only, sin ejecución dinámica) del enchufe Fables ya presente; queda como referencia canónica, no se borra el enchufe existente cableado.
- Evidencia: 239/242 tests propios del loop pasan con `conftest.py` de wiring (sys.path); suites repo propias siguen verdes (480) salvo fragilidad de orden SIMULADO ya registrada.
- 🚩 PENDIENTE (stale upstream, no se tocan tests ni código vendored para forzar verde):
  - `test_ficha_v2_accepts_testing_contract`: el loader del test no registra `sys.modules` antes de `exec_module`; py3.12 exige registro para dataclasses con anotaciones string. Bug del test, fallaría igual en `agentes`.
  - `test_g009_*`: `decide_value` devuelve `REVIEW_REQUIRED` donde el test espera `NO_VALUE_GAP`; firma de `ValueAssessment` difiere del contrato que asume el test (deriva de versión).
  - `test_g021_*`: el test exige prioridad descendente `('B','A')`; `parallel_scheduler` documenta y aplica `lower = more urgent` (convención Kernel/Mavis). El resto de la suite concuerda con ascendente; el test es el caso aislado.
  - `test_router_cliente_live` hace `os.environ.pop("SIMULADO")` global: ordena suites de forma que `11-EVIDENCIA` corra antes o aislar procesos; fragilidad preexistente, no de la copia.
- Dedup pendiente 🚩: `task_runtime.py`/`mirror_factory.py`/`skill_runtime.py` propios solapan `crazywall_claim_gate`/`recovery`/`agent_fleet`/`uek` de wordflow; los módulos propios quedan cableados a contratos del repo (ui_bridge chain, tool_contracts, autoridad central) hasta consolidar.


## INPUT-BLOCK VERBATIM (instrucciones 1 a 1 del Director)

- "No los 18 agente no se conservan por eso no entiendes. Se conserva el plan que ya tu tenías que venías haciendo no el de el wordflow. Lo que vas hacer es que de los 4 objetivo que dice el plan de opus que falta lo vas añadir lo vas a crear pero adaptar a tus agente que yo te define con el plan que tú estabas haciendo solo réplicas el wordflow no el staff de agentes. Que haces ejemolo al osquestador rotboaw le añades complementos que exigen los 4 objetivos. Creas un agente nuevo llamado seal team YAIWES. Añades los componentes del objetivo 1. Pero mantienes el staff de agente de tu diseño de la arquitectura que yo te di."
- "Integra mirothinker con un sistema thinking. Ya tenemos nuestro osquestador definido creo que no me estás entendiendo."
- Respuesta registrada: opencode = capacidad "writer" y openhands = capacidad "fixer" como complementos invocables via adapter (fail-closed, claim+sheriff), no staff nuevo; mirothinker = capacidad de razonamiento. Staff del Director conservado.

## FASE WORDFLOW-LOOP (delta tras copia de raíz)

- N-2.4: `recovery/checkpoint.py` ya era durable SQLite (patch upstream 2026-09-20) — verificado.
- N-2.5: `runtime/src/agent/agent_router.py` DEPRECATED → delega en AgentFleetAdapter + registry; FAIL_CLOSED sin match real (tested).
- N-2.6: `recovery/engine.py` emite kind tipado (FAILURE_POLICY de task_runtime) por fallo; ESCALATE genérico solo cuando requires_human.
- N-2.7: StuckDetector en RecoveryEngine (fingerprint x3 → BLOCKED_STUCK); tested.
- N-2.8: los 7 archivos governance = gates reales deterministas (veredicto REAL, no stubs).
- N-2.9: `wordflow_loop/contracts/` + `wordflow_loop/evidence/` ya contienen fichas y ~55 evidencias G0xx — verificado físicamente.
- Gap upstream resuelto: `wordflow_loop/wordflow_loop/runner.py` (LayerRunner) no existía → creado cableando la cadena validator→sheriff→sentinel→supervisor→guardian→verifier→judge→ledger.
- ThinkingSystem: `wordflow_loop/wordflow_loop/thinking_system.py` → mirothinker via AgentFleetAdapter, razonamiento sin autoridad de ejecución.
- Dedup: `task_runtime.py` canónico único en `runtime/src/core/`; shim re-export en integration/chat_mvp; mirror_factory apunta al canónico.
- Tests nuevos: test_n26_typed_recovery_and_router.py (7), test_layer_runner.py (5), test_thinking_system.py (3). Suite loop: 254 passed / 3 stale (g009, g021, ficha loader) 🚩.
- 🚩 N-2.10: truth_reconciler.py (43 LOC, sin importadores) vs source_truth_reconciler.py (105 LOC, testeado) — canónico=source_truth_reconciler; truth_reconciler queda deprecated (no borrado).
- 🚩 N-2.13: los 4 archivos (execution_pipeline_dsl.py, -Copiar.md, PIPELINE_MASTER.md, INPUT_BLOCK.md) nunca fueron commiteados ni adjuntados en esta sesión — pendiente material.

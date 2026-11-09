# Claude.md — Checklist maestra de tareas (Router 1 y Router 2)

Fuente verbatim: `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md` (no se resume; se cita por sección).
Pizarra de trabajo, progreso y bloqueos: `Claude notas.md` (esta misma raíz).
Plan de Hugging Face para Router 2: `handoff/HF_PLAN_ROUTER2.md`.

## Reglas de trabajo (instrucción del owner)

- Modo Loop: avanzar tarea por tarea hasta terminar la lista. No parar por dudas menores.
- Cada tarea: un DSL DAG + el archivo que crea + un `state.json` de handoff + entrada en el Crazy Wall (`Claude notas.md`).
- Bloqueante real: detener esa tarea y marcar 🚩 en `Claude notas.md`. Las dudas van al final, en un bloque de preguntas.
- Nada se borra sin análisis de dependencias. Lo que no tiene función demostrable va a `_quarantine/` con su README (nombre, función, workflow A→B→C→D).
- Prohibido: GitHub Actions, LFS en GitHub, despliegue nuevo en Vercel o Hugging Face sin autorización expresa (INPUT_BLOCK §5 y §6).
- Claves y secretos: solo por entorno. Nunca en ficheros, logs, datasets ni URLs.
- Motor `research_prepass.py` (línea 89): intocable hasta autorización expresa (INPUT_BLOCK §6).
- Un archivo = una responsabilidad. Máximo 200 líneas.

## 1. Objetivos principales (INPUT_BLOCK §2)

- [ ] 1. Auditoría histórica y Job Test: recuperar cableados antiguos, compararlos con los actuales, identificar conexiones funcionales, rotas, duplicadas y desaparecidas.
- [ ] 2. Centro único de distribución del cableado: registro central con servicio, archivo, consumidor, proveedor y endpoint. Sin duplicados.
- [ ] 3. Archivos guardianes: identificar, conectar los útiles y eliminar los que no tienen consumidor ni función demostrable.
- [ ] 4. Chat YAIWES y OpenClaw: conservar el cableado funcional de la UI y el mirror de OpenClaw.
- [ ] 5. OpenClaw independiente: llamar a proveedores directamente, MVP de cómputo independiente, respaldo si el Router cae.
- [ ] 6. System Prompt y motores: archivo raíz, recorrido completo, motores que lo reciben, persistencia en Loop y reanudaciones.
- [ ] 7. Componentes y Skills: revisar, mapear dependencias y organizar. Raíces independientes: Chatbot, Loop, Cola, Watchdog, ECC, Skills.
- [ ] 8. Cableado del frontend: UI → backend → Harness → Router → modelos. Selectores, botones y estados.
- [ ] 9. Cableado de agentes: conexión con Harness DeepSeek, ON/OFF, ejecución agéntica y herramientas, almacenamiento y memoria.
- [ ] 10. Modelos, API y servicios centrales: NVIDIA, modelos locales, respuesta real desde selectores, System Prompt, motores, memoria, comunicación vía plugins del Harness.

## 2. Criterio final de aceptación (INPUT_BLOCK §3)

- [ ] Cada conexión muestra: ubicación del código responsable, consumidor y proveedor, cableado real, prueba funcional y evidencia de ejecución.
- [ ] Una conexión no se declara activa por estar configurada. Debe responder realmente.

## 3. Plan técnico, 12 fases (INPUT_BLOCK §5)

- [ ] F1 Recuperación forense del cableado histórico → `audit/historical_connections.json`
- [ ] F2 Auditoría del cableado actual → `audit/current_connections.json`, `dependency_graph.json`, `missing_connections.json`, `duplicate_connections.json`, `orphan_files.json`
- [ ] F3 Registro central → `connections/wiring_registry.yaml` (+ `registry.yaml`, `topology.yaml`, `endpoints.yaml`, `healthchecks.yaml`)
- [ ] F4 Contratos del Harness DeepSeek → `handoff/contracts/`
- [ ] F5 System Prompt y motores → `docs/architecture/`
- [ ] F6 Chat YAIWES + OpenClaw autónomo → `integrations/`
- [ ] F7 Guardianes y código huérfano → `audit/` y `_quarantine/`
- [ ] F8 Frontend y agentes → `tests/`
- [ ] F9 NVIDIA, modelos locales, memoria y storage → `tests/`, `connections/healthchecks.yaml`
- [ ] F10 Job Test integral J01..J13 → `audit/runtime_results.json`, `audit/final_report.json`
- [ ] F11 Automatización de pruebas (sin Actions) → `ops/launch.sh`, `ops/launch_hf.py`
- [ ] F12 Cierre: README, bitácora, handoff, arquitectura, repo limpio

Orden: F1 → F2 → grafo AST → F3 → F4 → F5 → motores → F6 (Chat YAIWES) → OpenClaw → Loop/ECC/Skills → agentes → F9 → F7 → F10.

## 4. Criterio de cierre (INPUT_BLOCK §5)

- [ ] 100 % de conexiones críticas inventariadas, cada una con consumidor y proveedor.
- [ ] Ningún servicio `ACTIVE` sin sonda real.
- [ ] System Prompt trazable hasta el modelo.
- [ ] Chat YAIWES funcional. OpenClaw independiente. Agentes conectados.
- [ ] NVIDIA y modelos locales respondiendo. Memoria y storage comprobados.
- [ ] Ningún archivo eliminado sin análisis de dependencias. Jobs con evidencia y SHA.

## 5. Excluido o pendiente por decisión del owner (INPUT_BLOCK §6)

- [ ] `research_prepass.py` (línea 89): no autorizado. Permanece intacto.
- [ ] Vercel y Hugging Face: sin despliegue nuevo sin autorización expresa.
- [ ] GitHub Actions y LFS: prohibidos.

## 6. Tareas heredadas de la conversación

- [x] Simulación del lote 35 en `tests/` (`ROUTER MVP v1/system_prompt_py/tests/sim35.py`), 296900b211
- [x] `control_api.py` fail-closed sin `ROUTER_API_KEY`, 2612953567
- [x] Rama por defecto del entrypoint, 2612953567
- [x] Nombres exactos de GGUF en Hugging Face (verificados en solo lectura), 296900b211
- [x] `buscar_web` como herramienta del ToolExecutor, 296900b211 (sin prueba en vivo)
- [ ] Diagnóstico del 410 de NVIDIA (requiere llave NVIDIA)
- [ ] Chat A/B como tools nativas: dividir_tarea, entregar_parte, checkpoint_guardar, recuperar_checkpoint, continuar_cola
- [ ] Conectar `buscar_web` al motor de gaps
- [ ] Motor de descarga y extracción: NO AUTORIZADO (Fase 2)
- [ ] Auditoría forense de 4 pasadas de los Spaces de Hugging Face (ver `handoff/HF_PLAN_ROUTER2.md`)

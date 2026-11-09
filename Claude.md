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
- [ ] Diagnóstico del 410 de NVIDIA — 🚩 bloqueado: requiere llave NVIDIA en entorno
- [x] Chat A/B como tools nativas: dividir_tarea, entregar_parte, checkpoint_guardar, recuperar_checkpoint, continuar_cola — `workflow_tools.py`, commit 6a76a9b8b8
- [x] Conectar `buscar_web` al motor de gaps — `gap_resolution_loop.default_engine()`, commit d6fbfd63fb
- [ ] Motor de descarga y extracción: NO AUTORIZADO (Fase 2)
- [ ] Auditoría forense de 4 pasadas de los Spaces de Hugging Face (ver `handoff/HF_PLAN_ROUTER2.md`)

## 7. Router 1: proxy LLM unificado

- [x] Copia del router LLM en `llm system HF/llm_router/` (proxy OpenAI-compatible y dependencias), commit c214932c54
- [ ] Retiro del original en `ROUTER MVP v1/` — 🚩 requiere aprobación del owner (no se borra sin aprobación)
- [ ] Decidir si `llm_router` tiene su propio Space (hoy solo es código; el CMD del Dockerfile de MVP v1 aún apunta al original)

## 8. Tareas nuevas del owner (Router 1, 2026-11-09). Cada una: DSL DAG en `Claude notas.md`

Regla de ejecución: ninguna tarea se detiene por dudas. Si la decisión está en el input block o aquí, se decide y se sigue. Solo se marca 🚩 al final si es bloqueante real (sin llave, sin acceso, o acción destructiva).

- [x] T-A Agentes: Rufo y Rowbot. RESULTADO: no existen en el repo propio, en GitHub público (búsqueda) ni en la cuenta owner (ls-remote). 🚩 final. Búsqueda en `chat-router/`, `chat-router/agentes/` y `chat-router/workflow-loop-code-yaiwes/` de main. Resultado previo: no existen archivos con esos nombres. Acción: buscar en el repo y en GitHub público (`gh api search`, solo lectura). Si no existen, 🚩 final.
- [x] T-B Agentes: Hermes y OpenClaw integrados en un único archivo espejo `llm system HF/llm_router/agentes.py` (commit 39fa94257a, 4 pruebas). Cline descargado con el motor como componente (manifiesto `componentes_manifest.json`, commit b836d6c1d2). Cline: no hay carpeta propia; hay soporte en `Main_Skills/Code/get-shit-done` (tests cline-install). Hermes: hay plugin en `Main_Skills/Code/headroom/code/plugins/hermes`. Acción: integrar como adaptadores en `chat-router/agentes/adaptadores/` y dejar el archivo espejo único.
- [ ] T-C Adaptadores de agentes existentes en `chat-router/agentes/adaptadores/` (claude_code, codex, openclaw, opencode, openhands, swe_agent, dispatcher, workflows): mapear contrato, consumidor y cableado hacia Harness DeepSeek.
- [x] T-D Motor de descarga (mejorado): NO es un tool de código descargado. Es un motor determinista que: busca con motores existentes (sin LLM) skills, componentes, adaptadores, plugins, guías, RAG y bibliotecas; el modelo elige 1 a 10 candidatos por valoración; el motor descarga; el motor fusiona. Destinos: un solo directorio de skills y un solo directorio de componentes. Requiere aprobación para ejecutar código descargado: el motor descarga y extrae, no ejecuta. → Esta tarea SÍ tiene un punto de aprobación; se marca 🚩 solo al llegar a la ejecución.
- [~] T-E Búsqueda dual (parcial: GitHub y Hugging Face en `motor_descarga.py`; falta la lista de 10 métodos por fuente y la búsqueda por URL): GitHub (top 10 por valoración, revisar código fuente para la finalidad) y Hugging Face. Búsqueda por nombre o por URL. 10 métodos por Hugging Face y 10 por GitHub para skills.
- [ ] T-F Conversión de skill (pendiente: no iniciado) a mini sistema Python: análisis de README, código y prompt; resultado: archivo Python ejecutable determinista, 95% determinista y 5% LLM solo para razonamiento. Destino: raíz única de tools.
- [x] T-G Raíz única de tools: `ROUTER MVP v1/system_prompt_py/tools/__init__.py` (commit 02fb25bcc5, 1 prueba). Registra 9 tools. (skills, adaptadores, acopladores, plugins) con workflow schema. Todo expuesto como tool nativa al modelo y a los agentes.
- [ ] T-H Enchufe Fables (pendiente: no iniciado) como conector de todos los tools y workflows. Plugin de cómputo que registra cientos de mini workflows de forma automática. Botón de activación manual y activación por el modelo.
- [ ] T-I Frontend (pendiente: no iniciado): botón que inicia el ciclo búsqueda → descarga → fusión → conversión. Cableado frontend → backend → Harness DeepSeek → plugins → agentes/memoria/cómputo, según la arquitectura del owner.
- [ ] T-J Crazy wall de Router 2 y plan de Hugging Face: revisión y cierre (ver `Claude notas.md`).

## 9. Reglas del owner (vuelta 3, 2026-11-09). Anotadas 1 a 1

- [ ] R-1 Búsqueda antes de escalar: buscar cómo se hace y cómo se resuelve (research system: fuentes S01–S20, ruta de gaps en 10 pasos). Solo después de agotar la búsqueda se escala.
- [ ] R-2 Frontend: criterio obligatorio. Cualquier resultado fuera de criterio es un Gap: se resuelve o queda en tareas pendientes.
- [ ] R-3 Integración automática obligatoria: el sistema prueba en sandbox, integra el tool en la carpeta de tools y conecta sin LLM. El LLM solo razona o escribe la conversión a Python. El motor es plantilla: el modelo anota qué quiere y el sistema corre solo.
- [ ] R-4 Organización de la raíz: dentro de `chat-router/`, por grupo: Agentes, Componentes, Skills, Chatbot, Backend chat, Frontend chat, Motores de descarga y extracción y otros, Tool plugins. En `main` solo puede existir un puente que apunte a esa ubicación.
- [ ] R-5 Enchufe Fables: un solo archivo Python, fusionado a partir de las 3 fuentes. Reemplazar código del router solo si el actual no cumple las mismas características de conexión. Solo Python.
- [ ] R-6 Enrutadores: archivos de plugins (100 MCP, 100 HTTP, 100 URL/web, 100 SDK de los modelos) que se conectan a ambos routers sin tocar su código. Viven en el banco ahora y en una APK local en el futuro. Primero dejar el plugin listo; el contenido después.
- [ ] R-7 Selector de dos vías: una sola ventana con el modelo que razona y el agente que ejecuta. El modelo lo ve como tool interno. Cero fricción.
- [ ] R-8 Método de trabajo: Claude notas, README de cada raíz, y un handoff por archivo, uno por cada punto del input block verbatim.
- [ ] R-9 Atribución: todo commit lleva Co-Authored-By y Claude-Session.
- [ ] R-10 Auto pull: toda la raíz de `chat-router/` puede hacer auto pull; la integración pasa por rama de trabajo y PR, nunca push directo a `main`.

Pendientes de búsqueda que siguen abiertos: Rufo y Rotboat en todas las ramas remotas, y la auditoría X-Ray de 3 pasadas.

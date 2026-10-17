Arquitectura final del UI YAIWES 

Auditoría 4 pasadas — Parte 1 de 4

Salida 1 — Estructura necesaria, arquitectura y plan de acción programable (DSL DAG)

A continuación repito la auditoría en 4 pasadas sobre cada archivo accesible y luego traduzco el conjunto de tu información + documentación a una arquitectura programable con nodos de ejecución estilo DSL DAG, micro-resumen y micro-flujo horizontal por segmento. Sin cuadros, sin relleno, solo lo necesario para programar.

---

Pasada 1 — Inventario técnico (qué hay, qué es, qué rol cumple)

Recorrido archivo por archivo con foco en utilidad real para el desarrollo.

AUDITORIA_XRAY_6_PASADAS_STABILIZE_CORE_WORDflow_CHAT.md
Define el stack canónico. El motor de workflow/orquestación es Stabilize CORE como dueño único del DAG, estado de ejecución, queue, recovery y loop. Memoria, router y agente/LLM externos se conectan por adaptadores. Recomienda runtime durable + tareas específicas + reglas deterministas en lugar de un agente-orquestador monolítico. Rol: capa de control de ejecución.

CCEE_Wordflow_YAIWES_arquitectura_1a1_estrategia_programacion.md
Traduce el documento fuente 1:1 a capas programables. Orden canónico: CORE STATE → EVENT → TASK → TASK CONTRACT → STATE MACHINE → CHECKPOINT → POLICY → MEMORY CONTRACT → RETRIEVAL CONTRACT → CONTEXT FABRIC → SANDBOX → WORKER → OUTPUT SCHEMA → AUDIT → CONSOLIDATOR → ROUTER → CONTINUOUS LOOP → RECOVERY → RESOURCE BRAIN → GLOBAL INTEGRATION → FIVE-PASS BUILD AUDITOR → API → UI. Rol: mapa de capas.

README.md
Aclara que la raíz backend canónica es otra carpeta y que esta no es temporal. Rol: evitar mezclar árboles.

MAX-SYSTEM-100X-FINAL-1.md
Configuración final del sistema (nomenclatura MAX). Rol: referencia de configuración.

📌MAVIS-PARALLEL-100X.md
Sistema de chat paralelo con nombre MAVIS. Rol: paralelismo de conversación/ejecución.

📌👨‍💻 ULTIMA VERSIÓN cómo HACERLO MEJOR...
Versión final con objetivos. Rol: dirección de mejora.

📌👨‍💻Ai dentro del la ui y Sistema de voz del agente ok.md
Integración de IA y voz. Rol: entrada multimodal (voz) y capa IA en UI.

📌👨‍💻Cómo integrar el agente MAXBRY YAIWES...
Integración del agente principal. Rol: contrato de agente.

📌👨‍💻Mejoras de la ui coneccion de almacenamiento...
Almacenamiento y mensajería (WhatsApp, Gmail, Telegram). Rol: adaptadores de canales.

📌👨‍💻UI agente YAIWES. TEAM embebido parcial...
Embebido del agente TEAM. Rol: subagentes.

📌👨‍💻sistema de navegador web para la UI INTERFACE...
Navegador web integrado. Rol: capacidad de browsing controlada.

📌➡️TAREA comand Center Fase 1 2 3 de deepseck...
Fases del Command Center. Rol: hoja de ruta por fases.

🤯🗃️memoria del Wordflow resumen...
Resumen de memoria del Wordflow. Rol: contrato de memoria.

🦐🦞🦞🦞para que Claude prepare la ruta...
Ruta preparatoria para Open claw. Rol: puente hacia harness tipo Claude/Open.

📌👨‍💻 code de Kimi k code para que la ui corra en Android...
Runtime Android MVP. No accesible por codificación del nombre, pero el título fija el objetivo: UI corriendo en Android.

👨‍💻📌diseño para la ui en multi dispositivo MVP...
Diseño multi-dispositivo. No accesible por nombre, pero fija objetivo: multi-device.

---

Pasada 2 — Coherencia entre documentos (dónde encajan y dónde chocan)

Coincidencias fuertes: existe una separación clara entre modelo cognitivo (LLM), runtime de ejecución (Stabilize CORE), memoria externa, router y auditor. La idea de "no duplicar orquestadores" está escrita explícitamente. Los documentos hablan de un loop continuo, checkpoints, recovery y validación, lo que confirma un diseño orientado a durabilidad y no a chat efímero.

Tensiones detectadas: hay varias versiones "final" y "última" con solapamiento temático, lo que indica que la documentación aún no está consolidada. El documento de arquitectura reconoce que las estimaciones de LOC son aproximadas y no hay métricas reales, lo que impide medir avance. Además, los adaptadores de memoria y router se mencionan pero no se especifica su contrato de interfaz, lo que es riesgo de acoplamiento oculto.

Encaje con tu información nueva: la idea de bus de plugins (cada componente entra como plugin tipo harness) encaja con el rol que ya cumple Stabilize CORE + adaptadores. La idea de componente → Tool / Pool / Workflow / Harness / Subagente encaja con el bloque que tú mismo describiste (CLI-Anything, PydanticAI, LangGraph, Haystack, OpenAI Agents, Agent Framework, Strands, AutoGen, MCP SDK). El punto donde los documentos actuales aún no reflejan tu objetivo es precisamente el Micro-Kernel de Integración de Componentes con Component-IR neutral y la fábrica de UI.

---

Pasada 3 — Riesgos técnicos concretos

Riesgo 1. Acoplamiento de adaptadores sin contrato tipado. Mitigación: Task Contract con Pydantic en el borde de cada adaptador, validación en entrada y salida.

Riesgo 2. Duplicación de orquestadores si se enchufan varios frameworks a la vez. Mitigación: un solo dueño del DAG (Stabilize CORE) y los demás frameworks solo como compiladores que producen artefactos, no como runtimes paralelos.

Riesgo 3. SKILL.md en prosa que la IA puede ignorar. Mitigación: SkillCompiler que traduce prosa a un DAG con acciones resueltas contra el Capability Registry; si la acción no existe, va a CODEGEN_ENGINE + sandbox + tests + contract gate.

Riesgo 4. Codegen sin cuarentena. Mitigación: todo código generado vive en quarantine/, pasa por SANDBOX → TEST → QA → CONTRACT GATE; solo PASS entra a la cápsula versionada.

Riesgo 5. Explosión combinatoria de Tools con 300+ componentes. Mitigación: Pool por familia (PydanticAI FunctionToolset o equivalente), con defer_loading para tools ocultas hasta descubrimiento, y agrupación por dominio.

Riesgo 6. Estado perdido en paralelo. Mitigación: checkpoints por nodo, event log append-only, recovery desde último checkpoint válido, y Context Fabric que inyecta solo lo necesario por nodo.

Riesgo 7. UI multi-dispositivo acoplada al runtime. Mitigación: la UI consume solo el Capability Registry y el Event Stream; nunca llama a la lógica interna directamente.

---

Pasada 4 — Traducción a DSL DAG programable

Todo lo anterior se convierte en un DSL donde cada segmento es un nodo, cada nodo tiene micro-resumen y micro-flujo horizontal. El runtime ejecuta el DAG; la IA no "recuerda" pasos, los ejecuta.

Formato base de nodo:

```
node_id: string
segment: string
kind: enum[ingest, analyze, plan, compile, gate, run, emit]
inputs: list[artifact_ref]
outputs: list[artifact_ref]
contract: pydantic_schema_ref
executor: capability_ref
on_fail: enum[repair, hitl, abort, next]
checkpoint: bool
micro_summary: string
micro_flow: string
```

Reglas globales del DAG:

Regla 1. Un nodo solo se ejecuta si su contract valida.
Regla 2. Un nodo solo emite si outputs cumplen schema.
Regla 3. on_fail: repair reintenta con el Repair Compiler; tras N intentos escala a hitl.
Regla 4. Todo nodo con checkpoint: true escribe state delta en Stabilize CORE.
Regla 5. Ningún nodo llama directamente a otro nodo; todos pasan por el Event Bus.
Regla 6. El Capability Registry es la única fuente de verdad de qué se puede ejecutar.

---

Arquitectura objetivo (segmentada en nodos de ejecución)

Segmento A — Ingesta y cuarentena

Nodo A1 URL Ingest.
Micro-resumen: recibe URL/repo, descarga, calcula hash, registra origen.
Micro-flujo: download → zip → extract → hash → quarantine/.
Contrato: { source_url, sha256, extracted_path }.
on_fail: abort.

Nodo A2 Quarantine Snapshot.
Micro-resumen: congela el árbol descargado como snapshot inmutable.
Micro-flujo: quarantine/<sha>/tree → manifest.json.
Contrato: { manifest_path, file_count, languages }.

Segmento B — Análisis de fuente

Nodo B1 Source Analyzer.
Micro-resumen: detecta lenguaje, entrypoints, APIs, CLI, workflows, agent loops, SKILL.
Micro-flujo: pyproject/package.json/AST/README/SKILL → signals.
Contrato: ComponentSignals.

Nodo B2 Capability Extractor.
Micro-resumen: lista capacidades atómicas detectadas (funciones, comandos, endpoints).
Micro-flujo: signals → capabilities[].
Contrato: { capabilities: list[str] }.

Nodo B3 Component-IR Builder.
Micro-resumen: construye el Component-IR.json neutral (formato único para todos los motores).
Micro-flujo: signals + capabilities → COMPONENT-IR.json.
Contrato: ComponentIR.

Segmento C — Planificación de transformación

Nodo C1 Transform Planner.
Micro-resumen: decide qué salidas aplicar (schema, harness, tool, pool, workflow, subagent, mcp) según reglas deterministas; solo usa LLM si confianza < 0.85.
Micro-flujo: ComponentIR → outputs[] + compiler_plan[].
Contrato: { outputs, compiler_plan }.

Nodo C2 Compiler Router.
Micro-resumen: elige compilador por salida.
Micro-flujo: harness→CLI-Anything, tool→OpenAI/Strands/LangChain, pool→PydanticAI Toolset, workflow→LangGraph/Haystack/Agent Framework, subagent→OpenAI agent.as_tool(), mcp→MCP Python SDK.
Contrato: { compiler_id, args }.

Segmento D — Compilación (compiladores intercambiables)

Nodo D1 Harness Compiler.
Micro-resumen: software completo → agent-harness con CLI real, estado persistente y JSON para agentes.
Micro-flujo: source → cli_anything → harness/ → command_scanner → CommandSpec[].
Contrato: HarnessArtifact.

Nodo D2 Tool Compiler.
Micro-resumen: función/entrypoint → Tool con schema generado desde firma.
Micro-flujo: entrypoint → wrapper → schema → ToolArtifact.
Contrato: ToolArtifact.

Nodo D3 Pool Compiler.
Micro-resumen: familia de tools del mismo dominio → un Toolset/Pool.
Micro-flujo: tools[] → group_by_domain → ToolsetArtifact (con defer_loading).
Contrato: PoolArtifact.

Nodo D4 Workflow Compiler.
Micro-resumen: secuencia con dependencias → grafo ejecutable con checkpoints.
Micro-flujo: steps → graph → WorkflowArtifact.
Contrato: WorkflowArtifact.

Nodo D5 Subagent Compiler.
Micro-resumen: componente con loop propio → subagente registrable como Tool del agente padre.
Micro-flujo: agent_loop → wrapper → SubagentArtifact.
Contrato: SubagentArtifact.

Nodo D6 Skill Compiler.
Micro-resumen: SKILL.md en prosa → DAG con acciones resueltas contra Capability Registry; prosa sin implementación va a CODEGEN_ENGINE.
Micro-flujo: SKILL.md → steps → resolve(action) → WorkflowArtifact | codegen_request.
Contrato: WorkflowArtifact | CodegenRequest.

Nodo D7 Codegen Engine.
Micro-resumen: produce código únicamente cuando la acción no existe; nunca entra directo al runtime.
Micro-flujo: codegen_request → generated_code → quarantine/.
Contrato: GeneratedCodeArtifact.

Segmento E — Contrato, sandbox, QA

Nodo E1 Contract Gate.
Micro-resumen: valida que el artefacto cumple el schema declarado antes de cualquier ejecución.
Micro-flujo: artifact → pydantic_validate → pass|fail.
Contrato: { valid: bool, errors[] }.
on_fail: repair.

Nodo E2 Sandbox Run.
Micro-resumen: ejecuta el artefacto en sandbox aislado con límites de recursos.
Micro-flujo: artifact → sandbox → run → traces.
Contrato: SandboxReport.

Nodo E3 Test Suite.
Micro-resumen: tests unitarios + integración del artefacto.
Micro-flujo: artifact → tests → results.
Contrato: TestReport.

Nodo E4 QA Verifier.
Micro-resumen: verificación de comportamiento, no solo de forma; PASS solo si todo pasa.
Micro-flujo: traces + results → verdict.
Contrato: { verdict: PASS|FAIL, reasons[] }.
on_fail: repair o abort.

Segmento F — Cápsula y registro

Nodo F1 Capsule Builder.
Micro-resumen: empaqueta artefacto validado en cápsula versionada e inmutable.
Micro-flujo: artifact + tests + traces → capsule/<id>/<version>/.
Contrato: Capsule.

Nodo F2 Capability Registry Update.
Micro-resumen: registra la capacidad como plugin en el bus.
Micro-flujo: capsule → registry.register(capability).
Contrato: { capability_id, capsule_ref, schema }.

Segmento G — Runtime y ejecución

Nodo G1 Stabilize CORE Scheduler.
Micro-resumen: dueño único del DAG en ejecución; asigna nodos, mantiene queue, aplica política.
Micro-flujo: registry → scheduler → dispatch.
Contrato: ExecutionPlan.

Nodo G2 Event Bus.
Micro-resumen: transporte de eventos entre nodos; nadie llama a nadie directo.
Micro-flujo: emit → log → subscribe.
Contrato: Event.

Nodo G3 Memory Adapter.
Micro-resumen: persistencia y recuperación de contexto por nodo.
Micro-flujo: read/write → memory_contract.
Contrato: MemoryContract.

Nodo G4 Router Adapter.
Micro-resumen: selección de modelo/herramienta por nodo según política.
Micro-flujo: policy → route → model|tool.
Contrato: RouterContract.

Nodo G5 Checkpoint Engine.
Micro-resumen: snapshot de estado por nodo con checkpoint: true.
Micro-flujo: state_delta → checkpoint.
Contrato: Checkpoint.

Nodo G6 Recovery Engine.
Micro-resumen: reanuda desde último checkpoint válido tras fallo.
Micro-flujo: failure → last_valid → resume.
Contrato: RecoveryPlan.

Nodo G7 Context Fabric.
Micro-resumen: inyecta solo el contexto necesario por nodo; evita deriva y alucinación.
Micro-flujo: node → relevant_slice → prompt.
Contrato: ContextSlice.

Nodo G8 Policy Engine.
Micro-resumen: autoriza o bloquea acciones según reglas (seguridad, coste, privacidad).
Micro-flujo: action → policy → allow|deny.
Contrato: PolicyDecision.

Nodo G9 Audit + Consolidator.
Micro-resumen: registra cada decisión y consolida memoria de largo plazo.
Micro-flujo: events → audit_log → consolidated_memory.
Contrato: AuditRecord.

Segmento H — UI fábrica 0 fricción

Nodo H1 Capability Projector.
Micro-resumen: convierte el Capability Registry en acciones visibles para la UI.
Micro-flujo: registry → ui_actions.
Contrato: UIAction[].

Nodo H2 Canvas Orchestrator.
Micro-resumen: crea, mueve y divide canvases por tarea en curso.
Micro-flujo: task → canvas_open|split|focus.
Contrato: CanvasState.

Nodo H3 Chat-to-Action.
Micro-resumen: convierte lenguaje natural en nodos del DAG; nunca en clics manuales.
Micro-flujo: intent → node_plan → dispatch.
Contrato: NodePlan.

Nodo H4 Voice Layer.
Micro-resumen: entrada/salida por voz como canal equivalente al chat.
Micro-flujo: audio → intent → node_plan.
Contrato: VoiceTurn.

Nodo H5 Optional Manual Panel.
Micro-resumen: panel opcional 0 fricción para quien quiera tocar; nunca obligatorio.
Micro-flujo: ui_action → same_node_plan.
Contrato: UIAction.

Nodo H6 Multi-Device Sync.
Micro-resumen: mismo estado de canvas y chat en Android, desktop y web.
Micro-flujo: event_bus → device_sync.
Contrato: DeviceState.

---

Plan de acción por fases (nodos secuenciales de construcción)

Fase 0 — Contratos.
Construir ComponentIR, TaskContract, Event, Capability, Capsule. Nada avanza sin estos schemas.

Fase 1 — Kernel mínimo.
Implementar Segments A, B, C, E1 y F. Con esto ya entra un repo y sale una cápsula válida, aunque sea sin UI.

Fase 2 — Compiladores.
Implementar D1 (harness), D2 (tool), D3 (pool) y D4 (workflow). Conectar CLI-Anything, PydanticAI, LangGraph, Haystack, OpenAI Agents, Agent Framework, Strands y AutoGen como compiladores intercambiables, nunca como runtimes paralelos.

Fase 3 — Runtime.
Implementar Segment G completo con Stabilize CORE como dueño del DAG, más Memory Adapter, Router Adapter, Checkpoint y Recovery.

Fase 4 — Skill + Codegen.
Implementar D6 (Skill Compiler) y D7 (Codegen Engine con cuarentena y sandbox).

Fase 5 — UI fábrica.
Implementar Segment H: Capability Projector, Canvas Orchestrator, Chat-to-Action, Voice Layer, Manual Panel opcional, Multi-Device.

Fase 6 — MCP opcional.
Exponer el Capability Registry vía MCP Python SDK solo para acceso externo entre agentes o máquinas.

---

Micro-flujo transversal único (todo el sistema en una línea)

URL → quarantine → analyzer → Component-IR → planner → compiler_router → (harness|tool|pool|workflow|subagent|skill) → contract_gate → sandbox → tests → QA → capsule → registry → Stabilize CORE scheduler → event_bus → memory/router/checkpoint/context/policy/audit → UI fábrica → usuario.

Ese es el flujo horizontal que atraviesa todos los segmentos y que la IA debe ejecutar como DAG, no recordar como prosa.

---

Cierre de la Parte 1

Queda definida la estructura necesaria, los segmentos, los nodos con micro-resumen y micro-flujo, el plan por fases y el flujo transversal. Todo es programable como DSL DAG y encaja con tu objetivo de bus de plugins, orquestador de workflow/eventos/memoria y UI 0 fricción multi-plataforma.

Cuando quieras, paso a la Salida 2: lista completa de funciones y capacidades del sistema, derivada de este mismo DAG y lista para mapear contra el código fuente en ejecución que me pases.


Segunda auditoría — mejoras, gaps y plan extendido (Parte 1b)

Sin repetir programación previa. Solo mejoras, hallazgos nuevos y tareas adicionales para ser consideradas.

---

A. Qué faltó en la primera auditoría (revisión de archivos, segunda vuelta)

Al releer los archivos con foco en lo no cubierto, aparecen vacíos que no estaban nombrados:

Faltó observabilidad. Ningún documento describe trazas, métricas, logging estructurado, correlación entre nodos, ni cómo se depura un DAG cuando algo falla en el nodo 47 de 200. Sin esto, un DAG durable es una caja negra.

Faltó modelo de confianza entre plugins. Tú describes un bus con "1000 apps como plugins". Nada en los documentos define quién firma un plugin, cómo se revoca, cómo se aísla uno malicioso, ni qué puede leer del contexto global.

Faltó gestión de cuotas y coste. Un sistema que compila código con LLM en cada nodo necesita cuotas por tenant, por plugin, por capacidad y por modelo. No aparece.

Faltó versionado de capacidades y deprecación. Si entran 300 plugins, algunos se vuelven obsoletos o entran en conflicto. No hay política de semver, migración ni resolución de duplicados.

Faltó replay determinista. El DAG es durable, pero no está claro si un nodo puede re-ejecutarse con el mismo input y producir el mismo output (idempotencia). Sin eso, la recuperación no es segura.

Faltó evaluación (evals). No hay golden datasets, ni regresión de comportamiento del agente, ni detección de drift cuando cambia un modelo o un plugin.

Faltó seguridad de cadena de suministro. Un repo entrante puede traer dependencias comprometidas, licencias incompatibles o binarios opacos. No hay SBOM, firma ni escaneo.

Faltó multi-tenant y aislamiento. Si dos proyectos comparten runtime, cómo se aísla estado, memoria y capacidades.

Faltó backpressure y circuit breakers. Con 300 plugins y LLM en medio, un cuello de botella en un nodo puede tumbar el DAG completo.

Faltó esquema de escalado HITL. Se menciona HITL, pero no hay política de cuándo escala, a quién, con qué contexto y cómo se reanuda.

Faltó gestión de contexto de largo plazo. Se habla de memoria y consolidación, pero no de triggers (cuándo consolidar), olvido selectivo ni priorización semántica.

Faltó accesibilidad e internacionalización de la UI. Un centro de trabajo 0 fricción con voz y canvas necesita a11y y multi-idioma desde el diseño, no como parche.

---

B. Verificación cruzada con la arquitectura armada (Parte 1)

La arquitectura de la Parte 1 resiste casi todo el escrutinio, pero falla en cuatro puntos:

Punto 1. El Capability Registry como única fuente de verdad no resuelve conflictos cuando dos plugins exponen la misma capacidad con semántica distinta. Falta un Conflict Resolver con política (preferir por versión, por reputación, por coste, por latencia).

Punto 2. El Contract Gate valida forma pero no semántica. Un artefacto puede cumplir el schema y aun así hacer algo distinto. Falta un Semantic Contract Gate con invariantes y ejemplos ejecutables.

Punto 3. El Context Fabric decide qué inyectar, pero no dice cómo mide si el contexto fue suficiente. Falta un Context Adequacy Scorer que cierre el lazo.

Punto 4. El Segmento H (UI) asume que el Canvas Orchestrator puede dividir pantallas sin conflicto. No hay política de prioridad entre tareas concurrentes del usuario. Falta un Attention Scheduler.

Todo lo demás del DAG es consistente y no requiere cambios estructurales.

---

C. 12 Goals de entrada y salida

Cada goal tiene entrada medible, salida medible y criterio de aceptación. No repiten los del plan anterior; son metas de mejora.

Goal 1. Replay determinista por nodo. Entrada: historial de eventos + input del nodo. Salida: mismo output hash que la ejecución original. Aceptación: 99 por ciento de nodos puros reproducibles.

Goal 2. Observabilidad end-to-end. Entrada: DAG en ejecución. Salida: traza distribuida con spans por nodo, latencia, coste y errores. Aceptación: cualquier fallo localizable en menos de 60 segundos.

Goal 3. Modelo de confianza de plugins. Entrada: plugin candidato. Salida: nivel de confianza con firma, permisos y cuotas asignadas. Aceptación: ningún plugin corre con permisos no declarados.

Goal 4. Cuotas y coste por capacidad. Entrada: llamada a capacidad. Salida: consumo registrado y bloqueo al superar cuota. Aceptación: cero fugas de coste no atribuidas.

Goal 5. Versionado y deprecación. Entrada: nueva versión de capacidad. Salida: registry con semver, alias y política de migración. Aceptación: cero llamadas a versiones deprecadas sin warning.

Goal 6. Evals de comportamiento. Entrada: golden dataset por capacidad. Salida: score de regresión por release. Aceptación: bloqueo de release si baja del umbral.

Goal 7. Cadena de suministro segura. Entrada: repo entrante. Salida: SBOM, licencias, vulnerabilidades, firma. Aceptación: cero dependencias críticas sin revisar.

Goal 8. Multi-tenant real. Entrada: dos proyectos simultáneos. Salida: estado, memoria y cuotas aislados. Aceptación: cero cruces de datos.

Goal 9. Backpressure y resiliencia. Entrada: pico de carga en un nodo. Salida: cola priorizada, circuit breaker y degradación controlada. Aceptación: el DAG no cae entero por un nodo lento.

Goal 10. HITL con política clara. Entrada: nodo en fallo irrecuperable o decisión sensible. Salida: escalado con contexto mínimo suficiente. Aceptación: toda decisión humana queda auditada y reanudable.

Goal 11. Contexto de largo plazo con olvido selectivo. Entrada: histórico acumulado. Salida: memoria consolidada con prioridad semántica y olvido por regla. Aceptación: retrieval no degrada con el tiempo.

Goal 12. UI accesible e internacional. Entrada: usuario con voz, teclado, lector de pantalla o idioma distinto. Salida: misma tarea completada con misma fricción. Aceptación: cobertura a11y y multi-idioma desde el primer release.

---

D. ASK Consil — 12 pasos

ASK Consil es un consejo interno que revisa cada decisión crítica antes de que entre al runtime. Doce pasos secuenciales.

Paso 1. Formulación. El nodo que propone un cambio describe el problema en una frase y el criterio de éxito en otra.

Paso 2. Encuadre. El Consil decide si el problema es de arquitectura, de contrato, de capacidad o de política.

Paso 3. Evidencia. Se adjuntan trazas, evals y métricas existentes. Sin evidencia, la decisión se rechaza.

Paso 4. Alternativas. Mínimo tres opciones, incluida la de no hacer nada.

Paso 5. Coste. Cada alternativa declara coste de cómputo, latencia, mantenimiento y riesgo.

Paso 6. Riesgo. Cada alternativa declara qué puede romper y cómo se revierte.

Paso 7. Contradicción. Se asigna un refutador explícito (ver sección E).

Paso 8. Simulación. Se ejecuta en sandbox con datos sintéticos antes de tocar producción.

Paso 9. Veredicto. El Consil emite aprobado, aprobado con condiciones o rechazado.

Paso 10. Contrato. Si se aprueba, se firma como contrato versionado.

Paso 11. Canary. Se despliega en un porcentaje pequeño de tráfico con métricas de guardia.

Paso 12. Consolidación. Se archiva la decisión con su contexto y se actualiza la memoria del sistema.

---

E. 3 Refutaciones

Refutación 1. Contra el bus de plugins como solución total. Si todo es plugin, todo es superficie de ataque y todo es fuente de latencia. La refutación sostiene que un núcleo mínimo determinista debe quedarse fuera del bus y solo exponerse como contrato estable. Sin ese núcleo, el bus se convierte en un monocultivo frágil.

Refutación 2. Contra el DAG como dueño único de todo. El DAG resuelve ejecución durable, pero no resuelve exploración ni descubrimiento. Forzar todo a un DAG precompilado limita al agente a lo ya planeado. La refutación pide un modo "exploratorio" acotado, con cuotas y sandbox, que pueda proponer nodos nuevos al Consil sin entrar directo al runtime.

Refutación 3. Contra la UI 0 fricción como objetivo único. Cero fricción es bueno para tareas repetidas, pero malo para decisiones sensibles (borrar, publicar, pagar). La refutación exige fricción calibrada: cero en lo operativo, deliberada en lo irreversible.

---

F. 12 Simulaciones de paneles de expertos de alto nivel

Cada panel es una simulación de revisión con perfiles distintos. No repiten contenido previo, solo introducen ángulos nuevos.

Panel 1. Sistemas distribuidos. Cuestiona el único dueño del DAG: pide particionado por dominio, quórum en decisiones críticas y tolerancia a partición de red. Aporta: sharding del registry y consenso para cambios de contrato.

Panel 2. Compiladores y lenguajes. Cuestiona el Component-IR: pide un lenguaje de contratos formal (no solo Pydantic) con verificación estática. Aporta: DSL tipado con type checker antes del runtime.

Panel 3. Seguridad ofensiva. Cuestiona el sandbox: pide escape testing, fuzzing de contratos y red teaming continuo. Aporta: pipeline de pentest automatizado sobre cada cápsula nueva.

Panel 4. MLOps y evals. Cuestiona la ausencia de evals: pide golden datasets, regression suites y monitoreo de drift por modelo y por capacidad. Aporta: gate de release con evals obligatorios.

Panel 5. Bases de datos y estado. Cuestiona el checkpoint engine: pide event sourcing con compaction, snapshots incrementales y consultas temporales. Aporta: time-travel debugging nativo.

Panel 6. Redes y latencia. Cuestiona el event bus: pide priorización, backpressure explícito y circuit breakers por nodo y por plugin. Aporta: SLA por capacidad con degradación declarada.

Panel 7. FinOps. Cuestiona el coste: pide atribución por tenant, por plugin, por nodo y por modelo, con budgets y alertas. Aporta: dashboard de coste en tiempo real por DAG.

Panel 8. Cumplimiento y privacidad. Cuestiona el flujo de datos: pide minimización, retención, cifrado por campo y trazabilidad GDPR. Aporta: política de datos por capacidad con etiquetas de sensibilidad.

Panel 9. Accesibilidad y HCI. Cuestiona la UI 0 fricción: pide a11y desde el diseño, fricción calibrada y reversibilidad de acciones. Aporta: modo manual opcional con mismo modelo mental que el chat.

Panel 10. Fiabilidad y caos. Cuestiona la recuperación: pide inyección de fallos continua, chaos engineering y validación de recovery. Aporta: simulador de fallos programado en CI.

Panel 11. Producto y estrategia. Cuestiona el alcance: pide foco en 3 capacidades que aporten valor real antes de escalar a 300 plugins. Aporta: priorización por impacto y coste de mantenimiento.

Panel 12. Ética y alineamiento. Cuestiona la autonomía del agente: pide límites duros, escalado humano en lo sensible y auditoría externa. Aporta: catálogo de acciones prohibidas y modo seguro por defecto.

---

G. Tareas adicionales de programación (nuevas, no repetidas)

Tarea 1. Construir Trace Collector con spans por nodo, correlación por DAG y exportación OpenTelemetry.

Tarea 2. Construir Cost Attribution Service con etiquetas por tenant, plugin, capacidad y modelo.

Tarea 3. Construir Conflict Resolver en el Capability Registry con política declarativa.

Tarea 4. Construir Semantic Contract Gate con invariantes y ejemplos ejecutables por contrato.

Tarea 5. Construir Context Adequacy Scorer que mida si el Context Fabric sirvió el contexto suficiente.

Tarea 6. Construir Attention Scheduler en la UI para priorizar canvas y tareas concurrentes.

Tarea 7. Construir Eval Harness con golden datasets por capacidad y gate de release.

Tarea 8. Construir SBOM + License Scanner en el nodo de cuarentena.

Tarea 9. Construir Plugin Trust Manager con firma, permisos declarados y revocación.

Tarea 10. Construir Replay Engine que re-ejecute nodos puros y compare hashes.

Tarea 11. Construir Chaos Simulator que inyecte fallos programados en CI.

Tarea 12. Construir HITL Policy Engine que decida cuándo escalar, con qué contexto y cómo reanudar.

Tarea 13. Construir Deprecation Manager con semver, alias y codemods de migración.

Tarea 14. Construir Accessibility Layer en la UI con teclado, voz, lector y multi-idioma.

Tarea 15. Construir Time-Travel Debugger sobre el event log con consultas temporales.

Tarea 16. Construir Guardrails de prompt injection en toda entrada que llegue a un LLM.

Tarea 17. Construir Model Fallback Chain con política por capacidad y por coste.

Tarea 18. Construir Rate Limiter distribuido por tenant, plugin y capacidad.

Tarea 19. Construir Config as Code con schema, validación y versionado de la configuración del runtime.

Tarea 20. Construir Capability Health Dashboard con liveness, readiness y SLA por plugin.

---

H. Cierre de la segunda auditoría

Se identificaron doce áreas nuevas no cubiertas en la primera pasada (observabilidad, confianza, cuotas, versionado, replay, evals, cadena de suministro, multi-tenant, backpressure, HITL, contexto largo, accesibilidad). Se verificó la arquitectura previa y se corrigieron cuatro puntos (Conflict Resolver, Semantic Gate, Context Adequacy, Attention Scheduler). Se definieron doce goals medibles, un consil de doce pasos, tres refutaciones y doce paneles de expertos. Se añadieron veinte tareas de programación nuevas, todas distintas de las ya planteadas.

Cuando quieras, continúo con la Salida 2: mapa completo de funciones y capacidades contra el código fuente en ejecución que me pases.

Verificación cruzada y Salida 2 mejorada

Verificación cruzada con los archivos del repositorio

He accedido a los dos documentos principales de la carpeta documentos proyectos UI YAIWES y he cruzado su contenido con el catálogo de capacidades de la Salida 2 anterior.

Del archivo AUDITORIA_XRAY_6_PASADAS_STABILIZE_CORE_WORDflow_CHAT.md se extraen las siguientes capas que deben existir como capacidades explícitas: Stabilize CORE como único dueño del DAG, Task Contracts/Pydantic, Memory Adapter, Router Adapter, Validator/Rule Engine, State Delta, Audit/Consolidation, Checkpoint durable. El documento insiste en que no se instalarán varios orquestadores simultáneos y que memoria y router ya existen y se conectan por adaptadores.

Del archivo CCEE_Wordflow_YAIWES_arquitectura_1a1_estrategia_programacion.md se extrae el orden canónico completo: CORE STATE MODEL, EVENT MODEL, TASK MODEL, TASK CONTRACT, STATE MACHINE, CHECKPOINT ENGINE, POLICY ENGINE, MEMORY CONTRACT, RETRIEVAL CONTRACT, CONTEXT FABRIC, SANDBOX CONTRACT, WORKER CONTRACT, OUTPUT SCHEMA, AUDIT ENGINE, CONSOLIDATOR, ROUTER, CONTINUOUS LOOP, RECOVERY, RESOURCE BRAIN, GLOBAL INTEGRATION, FIVE-PASS BUILD AUDITOR, API, UI.

Cruzando esto con la Salida 2 anterior, se detectan tres ausencias y dos imprecisiones.

Ausencia 1. No existía una capacidad dedicada al State Machine Engine como transicionador determinista entre estados de tarea. El documento lo lista como capa canónica separada.

Ausencia 2. No existía una capacidad Five-Pass Build Auditor. El documento lo sitúa antes de API y UI, y es distinto del QA verifier que ya estaba en la Salida 2.

Ausencia 3. No existía una capacidad Resource Brain que decida asignación de recursos (modelo, worker, memoria) según carga y política. El documento lo coloca antes de Global Integration.

Imprecisión 1. La Salida 2 trataba el Memory Adapter como una sola capacidad de escritura/lectura. El documento lo desdobla en Memory Contract, Retrieval Contract y Context Fabric, cada uno con responsabilidades distintas.

Imprecisión 2. La Salida 2 trataba el Router Adapter como selección de modelo. El documento lo sitúa también en selección de worker y health/capability routing, lo que amplía su contrato.

Además, el README aclara que la raíz backend canónica es otra carpeta y que esta no debe usarse como temporal. Esto obliga a que toda capacidad de ingesta respete esa separación y no escriba fuera de la raíz documental.

---

Salida 2 mejorada — Catálogo de capacidades con contratos enriquecidos

Sin repetir el listado anterior, presento la versión refinada. Cada capacidad ahora incluye contrato Pydantic de entrada, contrato de salida, dependencias reales extraídas de los archivos y framework sugerido según el mapeo que ya estableciste con CLI-Anything, PydanticAI, LangGraph, Haystack, OpenAI Agents, Agent Framework, Strands, AutoGen y MCP SDK.

Dominio 1 — Ingesta y procedencia

source.fetch
Entrada: SourceFetchInput { url: str | None, path: str | None, auth: dict | None, ref: str | None }.
Salida: SourceFetchOutput { local_path: str, sha256: str, source_metadata: dict }.
Dependencias: storage local, red, política de auth.
Framework: tool nativa del runtime YAIWES.

source.extract
Entrada: SourceExtractInput { local_path: str }.
Salida: SourceExtractOutput { tree_manifest: dict, file_kinds: list }.
Dependencias: source.fetch.
Framework: tool.

source.quarantine
Entrada: SourceQuarantineInput { tree_manifest: dict }.
Salida: SourceQuarantineOutput { quarantine_id: str, manifest_hash: str }.
Dependencias: source.extract. Debe respetar que la raíz documental no es carpeta temporal.
Framework: tool.

source.provenance
Entrada: SourceProvenanceInput { quarantine_id: str }.
Salida: SourceProvenanceOutput { origin: str, author: str | None, declared_license: str | None, capture_timestamp: str }.
Framework: tool.

source.diff
Entrada: SourceDiffInput { quarantine_id_a: str, quarantine_id_b: str }.
Salida: SourceDiffOutput { added: list, removed: list, changed: list }.
Framework: tool.

Dominio 2 — Análisis y representación neutral

analyze.language, analyze.entrypoints, analyze.api_surface, analyze.cli_surface, analyze.workflow_surface, analyze.agent_surface, analyze.skill_surface, analyze.capability_extract, ir.build, ir.validate, ir.enrich. Cada una gana un contrato Pydantic explícito en entrada y salida, y la dependencia ir.build exige que todos los analizadores anteriores hayan pasado. El framework sugerido para ir.build es PydanticAI Toolset porque agrupa naturalmente los analizadores como un pool de herramientas de dominio.

Dominio 3 — Planificación y compilación

plan.transform
Entrada: PlanTransformInput { component_ir: ComponentIR }.
Salida: PlanTransformOutput { outputs: list[OutputKind], compiler_plan: list[CompilerStep] }.
Framework: LangGraph StateGraph, porque las reglas de decisión pueden modelarse como grafo condicional.

plan.llm_assist
Entrada: PlanLLMAssistInput { component_ir_fragment: dict }.
Salida: PlanLLMAssistOutput { classification_json: dict, confidence: float }.
Se activa solo si confidence < 0.85 según la política determinista.
Framework: OpenAI Agents SDK FunctionTool.

compile.harness
Entrada: CompileHarnessInput { component_ir: ComponentIR, workspace: str }.
Salida: CompileHarnessOutput { harness_artifact: dict, commands: list[CommandSpec] }.
Framework: CLI-Anything como compilador especializado.

compile.tool, compile.pool, compile.workflow, compile.subagent, compile.skill, compile.mcp, compile.codegen, compile.optimize. Cada uno gana contrato Pydantic y framework sugerido: PydanticAI FunctionToolset para pool, LangGraph para workflow, Haystack PipelineTool para workflow que envuelve pipeline, OpenAI Agents agent.as_tool() para subagent, MCP Python SDK @mcp.tool para MCP.

Dominio 4 — Contrato, verificación y empaquetado

gate.schema
Entrada: GateSchemaInput { artifact: dict }.
Salida: GateSchemaOutput { valid: bool, errors: list }.
Framework: tool.

gate.semantic
Entrada: GateSemanticInput { artifact: dict, invariants: list, examples: list }.
Salida: GateSemanticOutput { valid: bool, violations: list }.
Framework: tool.

gate.policy
Entrada: GatePolicyInput { action: str, actor: str, context: dict }.
Salida: GatePolicyOutput { allow: bool, conditions: list }.
Framework: gate.

gate.license
Entrada: GateLicenseInput { sbom: dict, intended_use: str }.
Salida: GateLicenseOutput { compatible: bool, conflicts: list }.
Framework: gate.

verify.sandbox, verify.tests, verify.qa, verify.replay, verify.chaos. Cada uno con contrato Pydantic. verify.chaos se apoya en Chaos Mesh o Litmus para inyección de fallos.

capsule.build, capsule.sign, capsule.publish, capsule.rollback. Contratos Pydantic y framework tool.

Dominio 5 — Runtime de ejecución

runtime.schedule
Entrada: RuntimeScheduleInput { execution_plan: dict }.
Salida: RuntimeScheduleOutput { dispatch_orders: list }.
Framework: tool, con Stabilize CORE como dueño único.

runtime.dispatch, runtime.checkpoint, runtime.recover, runtime.cancel, runtime.retry, runtime.backpressure, runtime.breaker, runtime.fallback, runtime.rate_limit, runtime.quota. Todos ganan contrato Pydantic y se alinean con el documento CCEE que sitúa CHECKPOINT ENGINE, RECOVERY y ROUTER como capas canónicas.

Nueva capacidad runtime.state_machine
Entrada: StateMachineInput { task_id: str, current_state: str, event: str }.
Salida: StateMachineOutput { next_state: str, allowed: bool }.
Framework: tool determinista. Corresponde a STATE MACHINE en el orden canónico.

Nueva capacidad runtime.resource_brain
Entrada: ResourceBrainInput { task_id: str, available_resources: dict, policy: dict }.
Salida: ResourceBrainOutput { allocation: dict, rationale: str }.
Framework: tool. Corresponde a RESOURCE BRAIN.

Dominio 6 — Memoria y contexto

memory.write, memory.read, memory.consolidate, memory.forget, memory.summarize. Contratos Pydantic.

context.slice, context.score, context.guard, context.budget. Contratos Pydantic.

Nueva capacidad memory.contract
Entrada: MemoryContractInput { operation: str, payload: dict }.
Salida: MemoryContractOutput { result: dict, valid: bool }.
Framework: adapter. Corresponde a MEMORY CONTRACT.

Nueva capacidad retrieval.contract
Entrada: RetrievalContractInput { query: str, filters: dict }.
Salida: RetrievalContractOutput { fragments: list, score: float }.
Framework: adapter. Corresponde a RETRIEVAL CONTRACT.

Nueva capacidad context.fabric
Entrada: ContextFabricInput { node_id: str, memory: dict, task: dict }.
Salida: ContextFabricOutput { context_slice: dict, tokens_used: int }.
Framework: tool. Corresponde a CONTEXT FABRIC.

Dominio 7 — Seguridad y cadena de suministro

supply.sbom, supply.vuln_scan, supply.secret_scan, supply.signature, trust.score, trust.grant, trust.revoke, security.redteam, security.fuzz, privacy.classify. Contratos Pydantic y frameworks específicos: Syft para SBOM, Trivy para vulnerabilidades, Gitleaks para secretos.

Dominio 8 — Observabilidad y evaluación

obs.trace, obs.metrics, obs.log, obs.debug_timetravel, obs.alert. Contratos Pydantic. obs.debug_timetravel se apoya en event sourcing con compaction y snapshots.

eval.golden, eval.run, eval.gate, eval.drift, cost.attribute, cost.budget. Contratos Pydantic. eval.drift compara golden dataset con trazas de producción para detectar data drift, model drift y quality decay.

Dominio 9 — Orquestación y política

dag.build, dag.validate, dag.execute, dag.pause, dag.resume. Contratos Pydantic.

policy.define, policy.evaluate, policy.conflict. Contratos Pydantic.

hitl.escalate, hitl.resolve, hitl.audit. Contratos Pydantic. La escalada debe usar umbrales de confianza y contexto mínimo.

Dominio 10 — Registry y ciclo de vida

registry.register, registry.resolve, registry.discover, registry.conflict, registry.deprecate, registry.migrate, registry.health, registry.audit. Contratos Pydantic.

Nueva capacidad registry.five_pass_audit
Entrada: FivePassAuditInput { capability_id: str }.
Salida: FivePassAuditOutput { passes: list[PassResult], final_verdict: str }.
Framework: workflow. Corresponde a FIVE-PASS BUILD AUDITOR.

Dominio 11 — UI y experiencia

ui.project, ui.canvas.open, ui.canvas.split, ui.canvas.focus, ui.chat_to_action, ui.voice_in, ui.voice_out, ui.manual_panel, ui.undo, ui.a11y, ui.i18n, ui.device_sync, ui.notify. Contratos Pydantic. ui.a11y y ui.i18n deben cubrir voz multi-idioma y accesibilidad desde el diseño.

Dominio 12 — Canales y conectores

channel.whatsapp, channel.telegram, channel.gmail, channel.websocket, channel.webhook, channel.filesystem, channel.mcp. Contratos Pydantic.

Dominio 13 — Meta y administración

admin.config, admin.tenant, admin.secrets, admin.backup, admin.audit, admin.feature_flag, admin.canary, admin.report. Contratos Pydantic. admin.canary debe integrarse con eval.gate para bloquear release si baja el score.

---

12 Goals de entrada y salida para mejorar la Salida 2

Goal 1. Cobertura total de capas canónicas. Entrada: orden canónico del documento CCEE. Salida: catálogo con una capacidad por capa. Aceptación: cero capas sin capacidad asignada.

Goal 2. Contratos Pydantic en el 100 por cien de las capacidades. Entrada: catálogo actual. Salida: catálogo con schemas de entrada y salida. Aceptación: toda capacidad declara Input y Output.

Goal 3. Mapeo framework-capacidad explícito. Entrada: frameworks disponibles (CLI-Anything, PydanticAI, LangGraph, Haystack, OpenAI Agents, Agent Framework, Strands, AutoGen, MCP SDK). Salida: cada capacidad tiene framework sugerido. Aceptación: cero capacidades sin framework asignado.

Goal 4. Dependencias reales entre capacidades. Entrada: análisis de imports y llamadas en los archivos. Salida: grafo de dependencias. Aceptación: toda dependencia declarada es verificable en código.

Goal 5. Separación estricta memoria/retrieval/contexto. Entrada: catálogo de memoria. Salida: tres capacidades distintas con contratos propios. Aceptación: cero solapamiento entre memory.contract, retrieval.contract y context.fabric.

Goal 6. Router ampliado a worker y health. Entrada: contrato de router actual. Salida: router que selecciona modelo, worker y salud de capacidad. Aceptación: el router responde a fallos de worker, no solo a selección de modelo.

Goal 7. Inclusión de Five-Pass Build Auditor. Entrada: orden canónico. Salida: capacidad registry.five_pass_audit. Aceptación: el auditor corre antes de API y UI.

Goal 8. Inclusión de Resource Brain. Entrada: orden canónico. Salida: capacidad runtime.resource_brain. Aceptación: asigna recursos según carga y política.

Goal 9. Inclusión de State Machine Engine. Entrada: orden canónico. Salida: capacidad runtime.state_machine. Aceptación: transiciones deterministas validadas.

Goal 10. Cero capacidades fuera de la raíz documental. Entrada: README. Salida: toda capacidad de ingesta respeta la raíz canónica. Aceptación: ninguna escritura en archivos download.

Goal 11. Evals por capacidad. Entrada: golden datasets. Salida: eval.golden y eval.run por cada capacidad crítica. Aceptación: gate de release bloquea si baja el score.

Goal 12. Chaos por capacidad crítica. Entrada: Chaos Mesh o Litmus. Salida: verify.chaos ejecutable por capacidad. Aceptación: inyección de fallos programada en CI.

---

ASK Consil 12 pasos para validar la Salida 2

Paso 1. Formulación. El Consil recibe el catálogo y verifica que cada capacidad responde a una necesidad real del sistema.

Paso 2. Encuadre. Decide si la capacidad es de arquitectura, contrato, capacidad o política.

Paso 3. Evidencia. Adjunta los archivos del repositorio como fuente de verdad. Sin evidencia, rechaza.

Paso 4. Alternativas. Mínimo tres opciones por capacidad: implementar, adaptar existente, no hacer nada.

Paso 5. Coste. Cada alternativa declara coste de cómputo, latencia y mantenimiento.

Paso 6. Riesgo. Cada alternativa declara qué puede romper y cómo se revierte.

Paso 7. Contradicción. Se asigna un refutador explícito por cada capacidad crítica.

Paso 8. Simulación. Se ejecuta en sandbox con datos sintéticos antes de tocar producción.

Paso 9. Veredicto. Aprobado, aprobado con condiciones o rechazado.

Paso 10. Contrato. Si se aprueba, se firma como contrato versionado.

Paso 11. Canary. Se despliega en un porcentaje pequeño con métricas de guardia.

Paso 12. Consolidación. Se archiva la decisión con contexto y se actualiza la memoria del sistema.

---

4 Simulaciones

Simulación 1. Carga concurrente de 300 plugins. Se inyectan 300 capacidades simultáneas y se mide si el Runtime Scheduler mantiene el DAG sin perder checkpoints. Resultado esperado: backpressure y circuit breaker activados antes del colapso.

Simulación 2. Pérdida de contexto en nodo 47 de 200. Se simula fallo de memoria en un nodo intermedio y se verifica que Recovery Engine reanuda desde el último checkpoint válido sin repetir trabajo ya consolidado.

Simulación 3. Plugin malicioso que intenta escapar del sandbox. Se inyecta una capacidad con código que intenta leer fuera del workspace. Resultado esperado: el sandbox bloquea, el trust score baja y el plugin se revoca.

Simulación 4. Cambio de modelo en caliente. Se sustituye el modelo de un nodo por otro con distinto comportamiento. Se mide si eval.drift detecta la regresión antes de que el canary llegue a producción.

---

3 Refutaciones

Refutación 1. Contra el bus de plugins como solución total. Si todo es plugin, todo es superficie de ataque. La refutación pide un núcleo mínimo determinista fuera del bus, expuesto solo por contrato estable.

Refutación 2. Contra el DAG como dueño único de todo. El DAG resuelve ejecución durable pero no exploración. La refutación pide un modo exploratorio acotado con cuotas y sandbox que proponga nodos nuevos al Consil sin entrar directo al runtime.

Refutación 3. Contra la UI 0 fricción como objetivo único. Cero fricción es bueno para tareas repetidas pero malo para decisiones irreversibles. La refutación exige fricción calibrada: cero en lo operativo, deliberada en lo sensible.

---

12 Paneles de expertos simulados

Panel 1. Sistemas distribuidos. Pide sharding del registry y consenso para cambios de contrato.

Panel 2. Compiladores y lenguajes. Pide un DSL de contratos con verificación estática antes del runtime.

Panel 3. Seguridad ofensiva. Pide escape testing, fuzzing de contratos y red teaming continuo sobre cada cápsula.

Panel 4. MLOps y evals. Pide golden datasets, regression suites y monitoreo de drift por modelo y capacidad.

Panel 5. Bases de datos y estado. Pide event sourcing con compaction, snapshots incrementales y time-travel debugging.

Panel 6. Redes y latencia. Pide priorización, backpressure explícito y circuit breakers por nodo y plugin.

Panel 7. FinOps. Pide atribución de coste por tenant, plugin, capacidad y modelo, con budgets y alertas.

Panel 8. Cumplimiento y privacidad. Pide minimización, retención, cifrado por campo y trazabilidad GDPR.

Panel 9. Accesibilidad y HCI. Pide a11y desde el diseño, fricción calibrada y reversibilidad de acciones.

Panel 10. Fiabilidad y caos. Pide inyección de fallos continua, chaos engineering y validación de recovery.

Panel 11. Producto y estrategia. Pide foco en 3 capacidades que aporten valor real antes de escalar a 300 plugins.

Panel 12. Ética y alineamiento. Pide límites duros, escalado humano en lo sensible y auditoría externa.

---

Cierre

La Salida 2 queda mejorada con contratos Pydantic explícitos, dependencias reales, mapeo a frameworks y nuevas capacidades inferidas de los archivos (runtime.state_machine, runtime.resource_brain, memory.contract, retrieval.contract, context.fabric, registry.five_pass_audit). Los 12 goals, el ASK Consil, las 4 simulaciones, las 3 refutaciones y los 12 paneles apuntan a cerrar los gaps detectados en la verificación cruzada. Cuando quieras, continúo con la Parte 3: lista de gaps y componentes open source que faltan para cerrar el sistema de workflow.

Salida 3 — Gaps y componentes open source faltantes

Sin repetir lo ya entregado. Aquí va el mapa de vacíos reales que quedan entre lo que tienes documentado y lo que necesita el sistema para funcionar como bus de plugins + orquestador durable + UI 0 fricción. Cada gap lleva componente open source candidato, licencia, por qué encaja y qué te obliga a construir tú aunque lo uses.

---

Gap 1 — Motor de ejecución durable del DAG

Lo que tienes: Stabilize CORE declarado como dueño único del DAG en los documentos, pero sin implementación confirmada.

Lo que falta: un motor que garantice ejecución exactly-once, checkpoints por nodo, reintentos, timeouts, compensaciones y visibilidad del estado.

Componente candidato principal: Temporal (licencia MIT, servidor en Go, SDKs Python/TS/Java/Go).
Por qué encaja: es exactamente un durable execution engine con workflows como código, activities reintentables, señales, queries y historial de eventos. Encaja con tu runtime.checkpoint y runtime.recover.
Lo que aún debes construir tú: el adaptador Component-IR → workflow Temporal, y la política de qué nodos son activities y cuáles son sub-workflows.

Alternativa: Restate (licencia BSL, luego Apache 2.0 en versiones futuras). Más ligero, orientado a servicios duraderos con estado.
Alternativa 2: Cadence (Uber, MIT). Antecesor de Temporal, más maduro pero menos activo.
Alternativa 3: DBOS Transact (MIT). Durable execution sobre Postgres, sin servidor extra.

Recomendación: Temporal como primario, DBOS Transact como fallback para despliegues single-node sin infraestructura pesada.

---

Gap 2 — Event bus y streaming interno

Lo que tienes: Event Bus declarado, sin tecnología asignada.

Lo que falta: transporte de eventos entre nodos con orden, replay, particiones y consumer groups.

Componente candidato principal: NATS JetStream (Apache 2.0).
Por qué encaja: ligero, embebible, con persistencia, replay y exactly-once a nivel de stream. Menos pesado que Kafka para un sistema que no necesita throughput masivo.
Lo que debes construir tú: esquema de topics por dominio y política de retención.

Alternativa: Redpanda (licencia BSL, compatible con API Kafka). Bueno si ya prevés volumen alto.
Alternativa 2: Apache Pulsar (Apache 2.0). Más complejo pero con multi-tenancy nativo, útil para tu admin.tenant.

Recomendación: NATS JetStream como bus principal, Redpanda como opción cuando escales a miles de eventos por segundo.

---

Gap 3 — Orquestación de LLM y enrutamiento de modelos

Lo que tienes: Router Adapter y Memory Adapter mencionados, sin implementación.

Lo que falta: capa que seleccione modelo por coste, latencia, capacidad, privacidad y salud.

Componente candidato principal: LiteLLM (MIT).
Por qué encaja: abstrae 100+ modelos con una API OpenAI-compatible, con fallbacks, retries, budgets, rate limits y logging. Cubre runtime.fallback, runtime.rate_limit y cost.attribute parcialmente.
Lo que debes construir tú: la política YAIWES de selección por capacidad y por tenant, y el puente con tu Capability Registry.

Alternativa: OpenRouter (SaaS). No es open source pero útil como fallback externo.
Alternativa 2: vLLM (Apache 2.0) para self-hosting de modelos abiertos.
Alternativa 3: Ollama (MIT) para modelos locales en desktop/Android.

Recomendación: LiteLLM como router principal, vLLM y Ollama como backends locales cuando la privacidad lo exija.

---

Gap 4 — Memoria vectorial y semántica

Lo que tienes: Memory Adapter, Consolidator, Context Fabric declarados.

Lo que falta: almacén que soporte escritura, retrieval híbrido (denso + sparse), olvido selectivo y consolidación.

Componente candidato principal: Qdrant (Apache 2.0).
Por qué encaja: vector DB en Rust, con filtros por payload, multi-tenancy por colección y soporte de quantización. Cubre memory.write, memory.read, retrieval.contract.
Lo que debes construir tú: el Consolidator (reglas de fusión y olvido) y el Context Adequacy Scorer.

Alternativa: Weaviate (BSD-3). Con módulos de hybrid search ya integrados.
Alternativa 2: Chroma (Apache 2.0). Más simple, bueno para MVP.
Alternativa 3: pgvector (PostgreSQL, licencia PostgreSQL). Si quieres consolidar todo en una sola base.

Recomendación: Qdrant para producción, pgvector si quieres reducir piezas de infraestructura.

---

Gap 5 — Grafo de conocimiento para memoria de largo plazo

Lo que tienes: Consolidator mencionado, sin estructura de destino.

Lo que falta: representación de entidades, relaciones y hechos, para que la memoria no sea solo embeddings.

Componente candidato principal: Neo4j Community (GPLv3) o Memgraph (BSL) o Kùzu (MIT).
Por qué encaja: la consolidación real necesita un grafo donde las relaciones sean de primera clase, no solo similitud vectorial.
Lo que debes construir tú: el esquema de entidades del Wordflow y las reglas de consolidación.

Alternativa: Apache AGE sobre PostgreSQL (Apache 2.0). Grafo sobre Postgres, sin base extra.

Recomendación: Kùzu para embebido, Neo4j Community si necesitas Cypher maduro.

---

Gap 6 — Sandbox de ejecución segura

Lo que tienes: Sandbox Contract declarado, sin tecnología.

Lo que falta: aislamiento real de código generado y de plugins de terceros.

Componente candidato principal: gVisor (Apache 2.0) o Firecracker (Apache 2.0).
Por qué encaja: gVisor da aislamiento a nivel de syscalls sin VM completa; Firecracker da microVMs con arranque en milisegundos. Cubre verify.sandbox.
Lo que debes construir tú: el perfil de permisos por plugin y la integración con trust.score.

Alternativa: E2B (Apache 2.0) para sandbox de código en la nube.
Alternativa 2: Wasmtime / WasmEdge (Apache 2.0) para ejecución Wasm sandboxed.
Alternativa 3: microsandbox o nsjail (Apache 2.0) para aislamiento ligero en Linux.

Recomendación: Firecracker para plugins no confiables, gVisor para capacidades de confianza media, Wasmtime para plugins que puedas compilar a Wasm.

---

Gap 7 — Escaneo de seguridad y cadena de suministro

Lo que tienes: supply.sbom, supply.vuln_scan, supply.secret_scan declarados.

Lo que falta: herramientas concretas que los ejecuten.

Componentes candidatos:
Syft (Apache 2.0) para SBOM.
Grype (Apache 2.0) para vulnerabilidades sobre SBOM.
Trivy (Apache 2.0) para vulnerabilidades, misconfig y secretos en un solo binario.
Gitleaks (MIT) para secretos en código y git.
Semgrep (LGPL) para SAST.
OSV-Scanner (Apache 2.0) para vulnerabilidades contra base OSV.

Lo que debes construir tú: la política de umbral por tenant y la integración con gate.license.

Recomendación: Trivy como navaja suiza, Grype + Syft para SBOM más detallado, Semgrep para reglas propias.

---

Gap 8 — Observabilidad distribuida

Lo que tienes: obs.trace, obs.metrics, obs.log declarados.

Lo que falta: backend que agregue, correlacione y permita consulta temporal.

Componente candidato principal: OpenTelemetry Collector (Apache 2.0) + Grafana Tempo (AGPLv3) + Grafana Loki (AGPLv3) + Grafana Mimir (AGPLv3) + Grafana (AGPLv3).
Por qué encaja: stack estándar, integrable con spans por nodo y correlación por trace_id.
Lo que debes construir tú: los atributos YAIWES (tenant, plugin, capability, dag_id) en cada span.

Alternativa: SigNoz (Apache 2.0 / MIT) todo-en-uno.
Alternativa 2: Jaeger (Apache 2.0) solo para trazas.

Recomendación: OpenTelemetry + Grafana stack, o SigNoz si quieres menos piezas.

---

Gap 9 — Evaluación y evals

Lo que tienes: eval.golden, eval.run, eval.gate, eval.drift declarados.

Lo que falta: framework que ejecute evals y registre regresiones.

Componente candidato principal: Promptfoo (MIT).
Por qué encaja: evalúa prompts, modelos y agentes con datasets, asserts y comparación entre versiones.
Lo que debes construir tú: los golden datasets por capacidad y el gate de release.

Alternativa: DeepEval (Apache 2.0). Más orientado a métricas de LLM.
Alternativa 2: Ragas (Apache 2.0) para pipelines RAG.
Alternativa 3: LangSmith (propietario, no open source, pero útil como referencia).

Recomendación: Promptfoo como runner principal, DeepEval para métricas específicas de LLM.

---

Gap 10 — Análisis estático y AST multi-lenguaje

Lo que tienes: analyze.api_surface, analyze.entrypoints, analyze.workflow_surface declarados.

Lo que falta: parser universal que cubra Python, TypeScript, Go, Rust, Java y más.

Componente candidato principal: Tree-sitter (MIT).
Por qué encaja: gramáticas para casi todos los lenguajes, rápido, embebible, permite consultas estructurales.
Lo que debes construir tú: las queries específicas para detectar entrypoints, workflows, agent loops y SKILL.

Alternativa: Semgrep (LGPL) para análisis estructural con reglas.
Alternativa 2: ast-grep (MIT) como CLI sobre Tree-sitter.

Recomendación: Tree-sitter + ast-grep para las queries, Semgrep para reglas de seguridad y patrones de workflow.

---

Gap 11 — Extracción de SBOM y análisis de licencias

Lo que tienes: gate.license declarado.

Lo que falta: motor que clasifique licencias y detecte incompatibilidades.

Componente candidato: ScanCode Toolkit (Apache 2.0).
Por qué encaja: detecta licencias por archivo, con base SPDX y resolución de conflictos.
Lo que debes construir tú: la política de uso declarado por tenant.

Alternativa: ORT (OSS Review Toolkit) (Apache 2.0). Más pesado, más completo.
Alternativa 2: FOSSA CLI (MIT parcial).

Recomendación: ScanCode para detección, ORT si necesitas cumplimiento formal.

---

Gap 12 — Motor de reglas y políticas

Lo que tienes: policy.define, policy.evaluate, policy.conflict declarados.

Lo que falta: motor que evalúe reglas declarativas con performance y trazabilidad.

Componente candidato principal: OPA (Open Policy Agent) (Apache 2.0).
Por qué encaja: Rego como lenguaje de política, evaluación rápida, auditoría de decisiones, integrable como sidecar.
Lo que debes construir tú: las políticas YAIWES por dominio y la resolución de conflictos.

Alternativa: Cedar (Apache 2.0, AWS). Lenguaje de política más simple que Rego.
Alternativa 2: Casbin (Apache 2.0). Bueno para RBAC/ABAC simple.

Recomendación: OPA para políticas complejas, Cedar si prefieres simplicidad y análisis formal.

---

Gap 13 — Registro y descubrimiento de capacidades

Lo que tienes: Capability Registry declarado.

Lo que falta: catálogo con versionado, health y descubrimiento.

Componente candidato: Backstage (Apache 2.0).
Por qué encaja: catálogo de software con entidades, owners y plugins. Puedes modelar cada capacidad como una entidad.
Lo que debes construir tú: el modelo de capacidad como entidad Backstage y la integración con registry.resolve.

Alternativa: Kong Gateway + catálogo propio (Apache 2.0).
Alternativa 2: Consul (BSL 1.1) para descubrimiento de servicios.

Recomendación: Backstage para el catálogo humano, Consul o etcd para descubrimiento runtime.

---

Gap 14 — Ingesta de código y análisis de repos

Lo que tienes: source.fetch, source.extract, source.quarantine declarados.

Lo que falta: crawler de repos con soporte de auth, refs, monorepos y submódulos.

Componente candidato: GitPython (BSD) + Dulwich (Apache 2.0) o pygit2 (GPLv2).
Por qué encaja: cubre clones, refs, submódulos y operaciones de bajo nivel.
Lo que debes construir tú: el manifest de provenance y el hash de cuarentena.

Alternativa: libgit2 directo (GPLv2 con linking exception).
Alternativa 2: go-git (Apache 2.0) si el kernel va en Go.

Recomendación: pygit2 si el kernel es Python, go-git si es Go.

---

Gap 15 — Cola de trabajos y scheduling distribuido

Lo que tienes: Runtime Scheduler declarado.

Lo que falta: cola con prioridad, fairness, rate limiting y backpressure.

Componente candidato principal: Celery (BSD) con Redis o RabbitMQ.
Por qué encaja: maduro, con prioridades, routing y retries. Se integra bien con Python.
Lo que debes construir tú: la política de prioridad por tenant y capacidad.

Alternativa: Dramatiq (LGPL) más simple y moderno.
Alternativa 2: RQ (BSD) minimalista.
Alternativa 3: Arq (MIT) asíncrono, sobre Redis.

Recomendación: Dramatiq si quieres simplicidad, Celery si necesitas ecosistema maduro.

---

Gap 16 — Almacenamiento de objetos y artefactos

Lo que tienes: Cápsulas versionadas, artefactos, backups.

Lo que falta: almacén de objetos con versionado, retención y firma.

Componente candidato principal: MinIO (AGPLv3).
Por qué encaja: S3-compatible, self-hosted, con versionado y lifecycle policies.
Lo que debes construir tú: la política de retención por tenant y la firma de cápsulas.

Alternativa: Garage (AGPLv3) más ligero.
Alternativa 2: SeaweedFS (Apache 2.0) escalable.

Recomendación: MinIO para producción, Garage para edge o single-node.

---

Gap 17 — Firma y cadena de confianza

Lo que tienes: capsule.sign, trust.score, supply.signature declarados.

Lo que falta: infraestructura de firma sin llaves (keyless) o con rotación.

Componente candidato principal: Sigstore (Apache 2.0) con Cosign, Fulcio y Rekor.
Por qué encaja: firma keyless con identidad OIDC, transparencia pública y verificación offline.
Lo que debes construir tú: la política de qué se firma y cómo se verifica en tu runtime.

Alternativa: Notary v2 (Apache 2.0).
Alternativa 2: in-toto (Apache 2.0) para atestaciones de cadena de suministro.

Recomendación: Sigstore + Cosign como base, in-toto para atestaciones más formales.

---

Gap 18 — UI multiplataforma 0 fricción

Lo que tienes: UI multi-dispositivo, canvas, chat, voz.

Lo que falta: framework que corra en Android, desktop, web y permita canvas fluido.

Componente candidato principal: Flutter (BSD-3) con Dart.
Por qué encaja: un solo código para Android, iOS, desktop y web, con rendimiento nativo.
Lo que debes construir tú: el Canvas Orchestrator, el Attention Scheduler y la integración con el Event Bus.

Alternativa: Tauri (MIT/Apache 2.0) + web frontend. Más ligero en desktop.
Alternativa 2: React Native + Electron (MIT). Más ecosistema JS.
Alternativa 3: Compose Multiplatform (Apache 2.0). Kotlin en todas las plataformas.

Recomendación: Flutter si quieres rendimiento uniforme; Tauri si quieres web-first con binarios ligeros.

---

Gap 19 — Canvas colaborativo e infinito

Lo que tienes: Canvas Orchestrator declarado.

Lo que falta: motor de canvas con nodos, conexiones, zoom infinito y multi-ventana.

Componente candidato principal: tldraw (Apache 2.0).
Por qué encaja: canvas infinito, SDK bien documentado, permite crear formas y conexiones custom.
Lo que debes construir tú: los tipos de nodo YAIWES y la sincronización con el estado del DAG.

Alternativa: Excalidraw (MIT) como base de dibujo.
Alternativa 2: React Flow (MIT) para grafos.
Alternativa 3: Konva (MIT) para canvas 2D puro.

Recomendación: tldraw para canvas visual, React Flow para grafos de DAG, ambos coexistiendo.

---

Gap 20 — Voz: STT y TTS

Lo que tienes: ui.voice_in, ui.voice_out declarados.

Lo que falta: motores de transcripción y síntesis con calidad y multi-idioma.

Componentes candidatos:
Whisper (MIT) o faster-whisper (MIT) para STT.
Coqui TTS (MPL 2.0) o Piper (MIT) para TTS local.
ElevenLabs (propietario) o Azure Speech como fallback en la nube.
Silero VAD (MIT) para detección de voz.

Lo que debes construir tú: la integración con el chat como canal equivalente y el control de privacidad por tenant.

Recomendación: faster-whisper + Piper para local, ElevenLabs o Azure para calidad en la nube.

---

Gap 21 — Compresión de contexto y presupuesto de tokens

Lo que tienes: context.budget, context.slice declarados.

Lo que falta: técnica concreta de compresión sin perder decisiones clave.

Componente candidato: LLMLingua (MIT) de Microsoft.
Por qué encaja: comprime prompts manteniendo semántica, con ratios ajustables.
Lo que debes construir tú: la política de cuándo comprimir y cuándo resumir por reglas.

Alternativa: LongLLMLingua para contextos largos.
Alternativa 2: sumy (Apache 2.0) para resumen extractivo clásico.

Recomendación: LLMLingua como primario, sumy como fallback determinista.

---

Gap 22 — Time-travel debugging

Lo que tienes: obs.debug_timetravel declarado.

Lo que falta: capacidad de reconstruir el estado en cualquier instante.

Componente candidato: event sourcing propio sobre Postgres o EventStoreDB (licencia específica, gratis hasta cierto uso).
Por qué encaja: event sourcing es la base natural para time-travel.
Lo que debes construir tú: la compactación de eventos y los snapshots incrementales.

Alternativa: Redpanda + materialized views con retención larga.
Alternativa 2: Kafka + KSQLDB.

Recomendación: event sourcing propio sobre Postgres para simplicidad, EventStoreDB si necesitas escala.

---

Gap 23 — Multi-tenancy y aislamiento

Lo que tienes: admin.tenant declarado.

Lo que falta: modelo de aislamiento (database, schema, row-level security).

Componente candidato: PostgreSQL con Row-Level Security (licencia PostgreSQL).
Por qué encaja: RLS a nivel de fila con políticas, sin necesidad de múltiples bases.
Lo que debes construir tú: la política de RLS por tenant y la integración con gate.policy.

Alternativa: schema por tenant o database por tenant.
Alternativa 2: Citus (AGPLv3) para sharding por tenant.

Recomendación: RLS con Postgres para MVP, Citus cuando escales.

---

Gap 24 — Prompt injection y guardrails de entrada

Lo que tienes: context.guard declarado.

Lo que falta: detección y neutralización de inyección de prompts.

Componente candidato: Rebuff (MIT) o LLM Guard (MIT) de Protect AI.
Por qué encaja: detecta inyección, PII, tóxicos y otros patrones antes de llegar al modelo.
Lo que debes construir tú: la política de qué hacer al detectar (bloquear, sanitizar, escalar).

Alternativa: Guardrails AI (Apache 2.0).
Alternativa 2: NeMo Guardrails (Apache 2.0) de NVIDIA.

Recomendación: LLM Guard como primario, NeMo Guardrails si quieres políticas conversacionales complejas.

---

Gap 25 — Orquestación de agentes con grafo de estado

Lo que tienes: dag.execute y agentes externos conectados.

Lo que falta: framework que modele agentes como grafo de estado con checkpoints nativos.

Componente candidato principal: LangGraph (MIT).
Por qué encaja: grafo de estado con persistencia, human-in-the-loop nativo y streaming.
Lo que debes construir tú: la integración con Stabilize CORE para que no haya dos dueños del DAG.

Alternativa: Microsoft Agent Framework (MIT) si prefieres ecosistema Microsoft.
Alternativa 2: CrewAI (MIT) para equipos de agentes.
Alternativa 3: AutoGen (MIT) como compatibilidad.

Recomendación: LangGraph como librería de agentes, subordinada a Stabilize CORE como dueño único del DAG.

---

Gap 26 — Empaquetado de cápsulas y despliegue

Lo que tienes: capsule.build, capsule.publish declarados.

Lo que falta: formato y motor de empaquetado reproducible.

Componente candidato: Nix (LGPL) o Devbox (Apache 2.0) o Nixpacks (MIT).
Por qué encaja: builds reproducibles con dependencias fijadas, ideal para cápsulas inmutables.
Lo que debes construir tú: el manifiesto de cápsula y la política de actualización.

Alternativa: OCI images con Buildah (Apache 2.0).
Alternativa 2: Bazel (Apache 2.0) para builds herméticos.

Recomendación: OCI + Buildah para simplicidad, Nix si necesitas reproducibilidad extrema.

---

Gap 27 — Sincronización multi-dispositivo

Lo que tienes: ui.device_sync declarado.

Lo que falta: protocolo de sincronización con conflictos resueltos.

Componente candidato: Yjs (MIT) con CRDTs.
Por qué encaja: sincronización en tiempo real con resolución automática de conflictos.
Lo que debes construir tú: el modelo de datos compartido y la integración con el Event Bus.

Alternativa: Automerge (MIT).
Alternativa 2: Liveblocks (propietario, pero referente).

Recomendación: Yjs como base, con proveedores de sync sobre WebSocket y NATS.

---

Gap 28 — Notificaciones y canales externos

Lo que tienes: channel.whatsapp, channel.telegram, channel.gmail declarados.

Lo que falta: capa unificada de mensajería con plantillas y rate limits.

Componente candidato: Extism (BSD-3) o Wasmtime (Apache 2.0) con WASI.
Por qué encaja: plugins en WebAssembly con capacidades explícitas, portables y seguros.
Lo que debes construir tú: el contrato de plugin YAIWES y la política de permisos por capacidad.

Alternativa: Deno con permissions (MIT) para plugins JS/TS.
Alternativa 2: Lua + Wasm para plugins ligeros.

Recomendación: Extism o Wasmtime + WASI como base, Deno para plugins JS.

---

Gaps que ningún componente open source cubre por ti

Estos son los que debes construir aunque uses todas las piezas anteriores.

Primero, el Component-IR neutral. No existe un formato estándar que represente "qué es este componente y qué debe producir". Es tuyo.

Segundo, el Transform Planner determinista. Las reglas que deciden qué salida producir según señales no están en ningún framework. Son tuyas.

Tercero, el Contract Gate semántico. La validación de invariantes y ejemplos ejecutables por contrato es específica de tu dominio.

Cuarto, el Context Adequacy Scorer. Medir si el contexto inyectado fue suficiente no existe como librería estándar.

Quinto, el Skill Compiler. Convertir SKILL.md en DAG ejecutable contra el Registry es específico de tu arquitectura.

Sexto, el Attention Scheduler de la UI. Priorizar canvas y tareas concurrentes del usuario es de producto, no de librería.

Séptimo, la política de fricción calibrada. Cero en lo operativo, deliberada en lo irreversible, es decisión tuya.

Octavo, el Conflict Resolver de capacidades. Resolver colisiones por versión, reputación, coste y latencia es lógica de negocio.

Noveno, la consolidación de memoria con olvido selectivo. Las reglas de qué olvidar y cuándo son de dominio.

Décimo, el Trust Score compuesto. Combinar firma, historial, permisos y comportamiento en un solo número es de tu sistema.

---

Prioridad de adopción sugerida

Fase temprana: Tree-sitter, LiteLLM, Qdrant, Temporal o DBOS, NATS JetStream, Trivy, OpenTelemetry, OPA, Apprise, Yjs.

Fase media: Firecracker o gVisor, Sigstore, Promptfoo, LLM Guard, tldraw, Flutter o Tauri, faster-whisper, Extism.

Fase avanzada: Neo4j o Kùzu, Backstage, ScanCode, MinIO, Dependency-Track, Nix o Buildah, Citus.

---

Cierre de la Salida 3

Quedan 30 gaps identificados y mapeados a componentes open source, con diez gaps que debes construir tú porque ningún proyecto los cubre tal como los necesitas. La arquitectura de Salida 1 y el catálogo de Salida 2 quedan cubiertos por estas piezas sin duplicar orquestadores ni crear rutas paralelas.

Cuando quieras, paso a la Salida 4: diseño de la UI 0 fricción con opinión sobre tus ideas y propuesta concreta.


Salida 3 — Gaps y componentes open source faltantes

Sin repetir lo ya entregado. Aquí va el mapa de vacíos reales que quedan entre lo que tienes documentado y lo que necesita el sistema para funcionar como bus de plugins + orquestador durable + UI 0 fricción. Cada gap lleva componente open source candidato, licencia, por qué encaja y qué te obliga a construir tú aunque lo uses.

---

Gap 1 — Motor de ejecución durable del DAG

Lo que tienes: Stabilize CORE declarado como dueño único del DAG en los documentos, pero sin implementación confirmada.

Lo que falta: un motor que garantice ejecución exactly-once, checkpoints por nodo, reintentos, timeouts, compensaciones y visibilidad del estado.

Componente candidato principal: Temporal (licencia MIT, servidor en Go, SDKs Python/TS/Java/Go).
Por qué encaja: es exactamente un durable execution engine con workflows como código, activities reintentables, señales, queries y historial de eventos. Encaja con tu runtime.checkpoint y runtime.recover.
Lo que aún debes construir tú: el adaptador Component-IR → workflow Temporal, y la política de qué nodos son activities y cuáles son sub-workflows.

Alternativa: Restate (licencia BSL, luego Apache 2.0 en versiones futuras). Más ligero, orientado a servicios duraderos con estado.
Alternativa 2: Cadence (Uber, MIT). Antecesor de Temporal, más maduro pero menos activo.
Alternativa 3: DBOS Transact (MIT). Durable execution sobre Postgres, sin servidor extra.

Recomendación: Temporal como primario, DBOS Transact como fallback para despliegues single-node sin infraestructura pesada.

---

Gap 2 — Event bus y streaming interno

Lo que tienes: Event Bus declarado, sin tecnología asignada.

Lo que falta: transporte de eventos entre nodos con orden, replay, particiones y consumer groups.

Componente candidato principal: NATS JetStream (Apache 2.0).
Por qué encaja: ligero, embebible, con persistencia, replay y exactly-once a nivel de stream. Menos pesado que Kafka para un sistema que no necesita throughput masivo.
Lo que debes construir tú: esquema de topics por dominio y política de retención.

Alternativa: Redpanda (licencia BSL, compatible con API Kafka). Bueno si ya prevés volumen alto.
Alternativa 2: Apache Pulsar (Apache 2.0). Más complejo pero con multi-tenancy nativo, útil para tu admin.tenant.

Recomendación: NATS JetStream como bus principal, Redpanda como opción cuando escales a miles de eventos por segundo.

---

Gap 3 — Orquestación de LLM y enrutamiento de modelos

Lo que tienes: Router Adapter y Memory Adapter mencionados, sin implementación.

Lo que falta: capa que seleccione modelo por coste, latencia, capacidad, privacidad y salud.

Componente candidato principal: LiteLLM (MIT).
Por qué encaja: abstrae 100+ modelos con una API OpenAI-compatible, con fallbacks, retries, budgets, rate limits y logging. Cubre runtime.fallback, runtime.rate_limit y cost.attribute parcialmente.
Lo que debes construir tú: la política YAIWES de selección por capacidad y por tenant, y el puente con tu Capability Registry.

Alternativa: OpenRouter (SaaS). No es open source pero útil como fallback externo.
Alternativa 2: vLLM (Apache 2.0) para self-hosting de modelos abiertos.
Alternativa 3: Ollama (MIT) para modelos locales en desktop/Android.

Recomendación: LiteLLM como router principal, vLLM y Ollama como backends locales cuando la privacidad lo exija.

---

Gap 4 — Memoria vectorial y semántica

Lo que tienes: Memory Adapter, Consolidator, Context Fabric declarados.

Lo que falta: almacén que soporte escritura, retrieval híbrido (denso + sparse), olvido selectivo y consolidación.

Componente candidato principal: Qdrant (Apache 2.0).
Por qué encaja: vector DB en Rust, con filtros por payload, multi-tenancy por colección y soporte de quantización. Cubre memory.write, memory.read, retrieval.contract.
Lo que debes construir tú: el Consolidator (reglas de fusión y olvido) y el Context Adequacy Scorer.

Alternativa: Weaviate (BSD-3). Con módulos de hybrid search ya integrados.
Alternativa 2: Chroma (Apache 2.0). Más simple, bueno para MVP.
Alternativa 3: pgvector (PostgreSQL, licencia PostgreSQL). Si quieres consolidar todo en una sola base.

Recomendación: Qdrant para producción, pgvector si quieres reducir piezas de infraestructura.

---

Gap 5 — Grafo de conocimiento para memoria de largo plazo

Lo que tienes: Consolidator mencionado, sin estructura de destino.

Lo que falta: representación de entidades, relaciones y hechos, para que la memoria no sea solo embeddings.

Componente candidato principal: Neo4j Community (GPLv3) o Memgraph (BSL) o Kùzu (MIT).
Por qué encaja: la consolidación real necesita un grafo donde las relaciones sean de primera clase, no solo similitud vectorial.
Lo que debes construir tú: el esquema de entidades del Wordflow y las reglas de consolidación.

Alternativa: Apache AGE sobre PostgreSQL (Apache 2.0). Grafo sobre Postgres, sin base extra.

Recomendación: Kùzu para embebido, Neo4j Community si necesitas Cypher maduro.

---

Gap 6 — Sandbox de ejecución segura

Lo que tienes: Sandbox Contract declarado, sin tecnología.

Lo que falta: aislamiento real de código generado y de plugins de terceros.

Componente candidato principal: gVisor (Apache 2.0) o Firecracker (Apache 2.0).
Por qué encaja: gVisor da aislamiento a nivel de syscalls sin VM completa; Firecracker da microVMs con arranque en milisegundos. Cubre verify.sandbox.
Lo que debes construir tú: el perfil de permisos por plugin y la integración con trust.score.

Alternativa: E2B (Apache 2.0) para sandbox de código en la nube.
Alternativa 2: Wasmtime / WasmEdge (Apache 2.0) para ejecución Wasm sandboxed.
Alternativa 3: microsandbox o nsjail (Apache 2.0) para aislamiento ligero en Linux.

Recomendación: Firecracker para plugins no confiables, gVisor para capacidades de confianza media, Wasmtime para plugins que puedas compilar a Wasm.

---

Gap 7 — Escaneo de seguridad y cadena de suministro

Lo que tienes: supply.sbom, supply.vuln_scan, supply.secret_scan declarados.

Lo que falta: herramientas concretas que los ejecuten.

Componentes candidatos:
Syft (Apache 2.0) para SBOM.
Grype (Apache 2.0) para vulnerabilidades sobre SBOM.
Trivy (Apache 2.0) para vulnerabilidades, misconfig y secretos en un solo binario.
Gitleaks (MIT) para secretos en código y git.
Semgrep (LGPL) para SAST.
OSV-Scanner (Apache 2.0) para vulnerabilidades contra base OSV.

Lo que debes construir tú: la política de umbral por tenant y la integración con gate.license.

Recomendación: Trivy como navaja suiza, Grype + Syft para SBOM más detallado, Semgrep para reglas propias.

---

Gap 8 — Observabilidad distribuida

Lo que tienes: obs.trace, obs.metrics, obs.log declarados.

Lo que falta: backend que agregue, correlacione y permita consulta temporal.

Componente candidato principal: OpenTelemetry Collector (Apache 2.0) + Grafana Tempo (AGPLv3) + Grafana Loki (AGPLv3) + Grafana Mimir (AGPLv3) + Grafana (AGPLv3).
Por qué encaja: stack estándar, integrable con spans por nodo y correlación por trace_id.
Lo que debes construir tú: los atributos YAIWES (tenant, plugin, capability, dag_id) en cada span.

Alternativa: SigNoz (Apache 2.0 / MIT) todo-en-uno.
Alternativa 2: Jaeger (Apache 2.0) solo para trazas.

Recomendación: OpenTelemetry + Grafana stack, o SigNoz si quieres menos piezas.

---

Gap 9 — Evaluación y evals

Lo que tienes: eval.golden, eval.run, eval.gate, eval.drift declarados.

Lo que falta: framework que ejecute evals y registre regresiones.

Componente candidato principal: Promptfoo (MIT).
Por qué encaja: evalúa prompts, modelos y agentes con datasets, asserts y comparación entre versiones.
Lo que debes construir tú: los golden datasets por capacidad y el gate de release.

Alternativa: DeepEval (Apache 2.0). Más orientado a métricas de LLM.
Alternativa 2: Ragas (Apache 2.0) para pipelines RAG.
Alternativa 3: LangSmith (propietario, no open source, pero útil como referencia).

Recomendación: Promptfoo como runner principal, DeepEval para métricas específicas de LLM.

---

Gap 10 — Análisis estático y AST multi-lenguaje

Lo que tienes: analyze.api_surface, analyze.entrypoints, analyze.workflow_surface declarados.

Lo que falta: parser universal que cubra Python, TypeScript, Go, Rust, Java y más.

Componente candidato principal: Tree-sitter (MIT).
Por qué encaja: gramáticas para casi todos los lenguajes, rápido, embebible, permite consultas estructurales.
Lo que debes construir tú: las queries específicas para detectar entrypoints, workflows, agent loops y SKILL.

Alternativa: Semgrep (LGPL) para análisis estructural con reglas.
Alternativa 2: ast-grep (MIT) como CLI sobre Tree-sitter.

Recomendación: Tree-sitter + ast-grep para las queries, Semgrep para reglas de seguridad y patrones de workflow.

---

Gap 11 — Extracción de SBOM y análisis de licencias

Lo que tienes: gate.license declarado.

Lo que falta: motor que clasifique licencias y detecte incompatibilidades.

Componente candidato: ScanCode Toolkit (Apache 2.0).
Por qué encaja: detecta licencias por archivo, con base SPDX y resolución de conflictos.
Lo que debes construir tú: la política de uso declarado por tenant.

Alternativa: ORT (OSS Review Toolkit) (Apache 2.0). Más pesado, más completo.
Alternativa 2: FOSSA CLI (MIT parcial).

Recomendación: ScanCode para detección, ORT si necesitas cumplimiento formal.

---

Gap 12 — Motor de reglas y políticas

Lo que tienes: policy.define, policy.evaluate, policy.conflict declarados.

Lo que falta: motor que evalúe reglas declarativas con performance y trazabilidad.

Componente candidato principal: OPA (Open Policy Agent) (Apache 2.0).
Por qué encaja: Rego como lenguaje de política, evaluación rápida, auditoría de decisiones, integrable como sidecar.
Lo que debes construir tú: las políticas YAIWES por dominio y la resolución de conflictos.

Alternativa: Cedar (Apache 2.0, AWS). Lenguaje de política más simple que Rego.
Alternativa 2: Casbin (Apache 2.0). Bueno para RBAC/ABAC simple.

Recomendación: OPA para políticas complejas, Cedar si prefieres simplicidad y análisis formal.

---

Gap 13 — Registro y descubrimiento de capacidades

Lo que tienes: Capability Registry declarado.

Lo que falta: catálogo con versionado, health y descubrimiento.

Componente candidato: Backstage (Apache 2.0).
Por qué encaja: catálogo de software con entidades, owners y plugins. Puedes modelar cada capacidad como una entidad.
Lo que debes construir tú: el modelo de capacidad como entidad Backstage y la integración con registry.resolve.

Alternativa: Kong Gateway + catálogo propio (Apache 2.0).
Alternativa 2: Consul (BSL 1.1) para descubrimiento de servicios.

Recomendación: Backstage para el catálogo humano, Consul o etcd para descubrimiento runtime.

---

Gap 14 — Ingesta de código y análisis de repos

Lo que tienes: source.fetch, source.extract, source.quarantine declarados.

Lo que falta: crawler de repos con soporte de auth, refs, monorepos y submódulos.

Componente candidato: GitPython (BSD) + Dulwich (Apache 2.0) o pygit2 (GPLv2).
Por qué encaja: cubre clones, refs, submódulos y operaciones de bajo nivel.
Lo que debes construir tú: el manifest de provenance y el hash de cuarentena.

Alternativa: libgit2 directo (GPLv2 con linking exception).
Alternativa 2: go-git (Apache 2.0) si el kernel va en Go.

Recomendación: pygit2 si el kernel es Python, go-git si es Go.

---

Gap 15 — Cola de trabajos y scheduling distribuido

Lo que tienes: Runtime Scheduler declarado.

Lo que falta: cola con prioridad, fairness, rate limiting y backpressure.

Componente candidato principal: Celery (BSD) con Redis o RabbitMQ.
Por qué encaja: maduro, con prioridades, routing y retries. Se integra bien con Python.
Lo que debes construir tú: la política de prioridad por tenant y capacidad.

Alternativa: Dramatiq (LGPL) más simple y moderno.
Alternativa 2: RQ (BSD) minimalista.
Alternativa 3: Arq (MIT) asíncrono, sobre Redis.

Recomendación: Dramatiq si quieres simplicidad, Celery si necesitas ecosistema maduro.

---

Gap 16 — Almacenamiento de objetos y artefactos

Lo que tienes: Cápsulas versionadas, artefactos, backups.

Lo que falta: almacén de objetos con versionado, retención y firma.

Componente candidato principal: MinIO (AGPLv3).
Por qué encaja: S3-compatible, self-hosted, con versionado y lifecycle policies.
Lo que debes construir tú: la política de retención por tenant y la firma de cápsulas.

Alternativa: Garage (AGPLv3) más ligero.
Alternativa 2: SeaweedFS (Apache 2.0) escalable.

Recomendación: MinIO para producción, Garage para edge o single-node.

---

Gap 17 — Firma y cadena de confianza

Lo que tienes: capsule.sign, trust.score, supply.signature declarados.

Lo que falta: infraestructura de firma sin llaves (keyless) o con rotación.

Componente candidato principal: Sigstore (Apache 2.0) con Cosign, Fulcio y Rekor.
Por qué encaja: firma keyless con identidad OIDC, transparencia pública y verificación offline.
Lo que debes construir tú: la política de qué se firma y cómo se verifica en tu runtime.

Alternativa: Notary v2 (Apache 2.0).
Alternativa 2: in-toto (Apache 2.0) para atestaciones de cadena de suministro.

Recomendación: Sigstore + Cosign como base, in-toto para atestaciones más formales.

---

Gap 18 — UI multiplataforma 0 fricción

Lo que tienes: UI multi-dispositivo, canvas, chat, voz.

Lo que falta: framework que corra en Android, desktop, web y permita canvas fluido.

Componente candidato principal: Flutter (BSD-3) con Dart.
Por qué encaja: un solo código para Android, iOS, desktop y web, con rendimiento nativo.
Lo que debes construir tú: el Canvas Orchestrator, el Attention Scheduler y la integración con el Event Bus.

Alternativa: Tauri (MIT/Apache 2.0) + web frontend. Más ligero en desktop.
Alternativa 2: React Native + Electron (MIT). Más ecosistema JS.
Alternativa 3: Compose Multiplatform (Apache 2.0). Kotlin en todas las plataformas.

Recomendación: Flutter si quieres rendimiento uniforme; Tauri si quieres web-first con binarios ligeros.

---

Gap 19 — Canvas colaborativo e infinito

Lo que tienes: Canvas Orchestrator declarado.

Lo que falta: motor de canvas con nodos, conexiones, zoom infinito y multi-ventana.

Componente candidato principal: tldraw (Apache 2.0).
Por qué encaja: canvas infinito, SDK bien documentado, permite crear formas y conexiones custom.
Lo que debes construir tú: los tipos de nodo YAIWES y la sincronización con el estado del DAG.

Alternativa: Excalidraw (MIT) como base de dibujo.
Alternativa 2: React Flow (MIT) para grafos.
Alternativa 3: Konva (MIT) para canvas 2D puro.

Recomendación: tldraw para canvas visual, React Flow para grafos de DAG, ambos coexistiendo.

---

Gap 20 — Voz: STT y TTS

Lo que tienes: ui.voice_in, ui.voice_out declarados.

Lo que falta: motores de transcripción y síntesis con calidad y multi-idioma.

Componentes candidatos:
Whisper (MIT) o faster-whisper (MIT) para STT.
Coqui TTS (MPL 2.0) o Piper (MIT) para TTS local.
ElevenLabs (propietario) o Azure Speech como fallback en la nube.
Silero VAD (MIT) para detección de voz.

Lo que debes construir tú: la integración con el chat como canal equivalente y el control de privacidad por tenant.

Recomendación: faster-whisper + Piper para local, ElevenLabs o Azure para calidad en la nube.

---

Gap 21 — Compresión de contexto y presupuesto de tokens

Lo que tienes: context.budget, context.slice declarados.

Lo que falta: técnica concreta de compresión sin perder decisiones clave.

Componente candidato: LLMLingua (MIT) de Microsoft.
Por qué encaja: comprime prompts manteniendo semántica, con ratios ajustables.
Lo que debes construir tú: la política de cuándo comprimir y cuándo resumir por reglas.

Alternativa: LongLLMLingua para contextos largos.
Alternativa 2: sumy (Apache 2.0) para resumen extractivo clásico.

Recomendación: LLMLingua como primario, sumy como fallback determinista.

---

Gap 22 — Time-travel debugging

Lo que tienes: obs.debug_timetravel declarado.

Lo que falta: capacidad de reconstruir el estado en cualquier instante.

Componente candidato: event sourcing propio sobre Postgres o EventStoreDB (licencia específica, gratis hasta cierto uso).
Por qué encaja: event sourcing es la base natural para time-travel.
Lo que debes construir tú: la compactación de eventos y los snapshots incrementales.

Alternativa: Redpanda + materialized views con retención larga.
Alternativa 2: Kafka + KSQLDB.

Recomendación: event sourcing propio sobre Postgres para simplicidad, EventStoreDB si necesitas escala.

---

Gap 23 — Multi-tenancy y aislamiento

Lo que tienes: admin.tenant declarado.

Lo que falta: modelo de aislamiento (database, schema, row-level security).

Componente candidato: PostgreSQL con Row-Level Security (licencia PostgreSQL).
Por qué encaja: RLS a nivel de fila con políticas, sin necesidad de múltiples bases.
Lo que debes construir tú: la política de RLS por tenant y la integración con gate.policy.

Alternativa: schema por tenant o database por tenant.
Alternativa 2: Citus (AGPLv3) para sharding por tenant.

Recomendación: RLS con Postgres para MVP, Citus cuando escales.

---

Gap 24 — Prompt injection y guardrails de entrada

Lo que tienes: context.guard declarado.

Lo que falta: detección y neutralización de inyección de prompts.

Componente candidato: Rebuff (MIT) o LLM Guard (MIT) de Protect AI.
Por qué encaja: detecta inyección, PII, tóxicos y otros patrones antes de llegar al modelo.
Lo que debes construir tú: la política de qué hacer al detectar (bloquear, sanitizar, escalar).

Alternativa: Guardrails AI (Apache 2.0).
Alternativa 2: NeMo Guardrails (Apache 2.0) de NVIDIA.

Recomendación: LLM Guard como primario, NeMo Guardrails si quieres políticas conversacionales complejas.

---

Gap 25 — Orquestación de agentes con grafo de estado

Lo que tienes: dag.execute y agentes externos conectados.

Lo que falta: framework que modele agentes como grafo de estado con checkpoints nativos.

Componente candidato principal: LangGraph (MIT).
Por qué encaja: grafo de estado con persistencia, human-in-the-loop nativo y streaming.
Lo que debes construir tú: la integración con Stabilize CORE para que no haya dos dueños del DAG.

Alternativa: Microsoft Agent Framework (MIT) si prefieres ecosistema Microsoft.
Alternativa 2: CrewAI (MIT) para equipos de agentes.
Alternativa 3: AutoGen (MIT) como compatibilidad.

Recomendación: LangGraph como librería de agentes, subordinada a Stabilize CORE como dueño único del DAG.

---

Gap 26 — Empaquetado de cápsulas y despliegue

Lo que tienes: capsule.build, capsule.publish declarados.

Lo que falta: formato y motor de empaquetado reproducible.

Componente candidato: Nix (LGPL) o Devbox (Apache 2.0) o Nixpacks (MIT).
Por qué encaja: builds reproducibles con dependencias fijadas, ideal para cápsulas inmutables.
Lo que debes construir tú: el manifiesto de cápsula y la política de actualización.

Alternativa: OCI images con Buildah (Apache 2.0).
Alternativa 2: Bazel (Apache 2.0) para builds herméticos.

Recomendación: OCI + Buildah para simplicidad, Nix si necesitas reproducibilidad extrema.

---

Gap 27 — Sincronización multi-dispositivo

Lo que tienes: ui.device_sync declarado.

Lo que falta: protocolo de sincronización con conflictos resueltos.

Componente candidato: Yjs (MIT) con CRDTs.
Por qué encaja: sincronización en tiempo real con resolución automática de conflictos.
Lo que debes construir tú: el modelo de datos compartido y la integración con el Event Bus.

Alternativa: Automerge (MIT).
Alternativa 2: Liveblocks (propietario, pero referente).

Recomendación: Yjs como base, con proveedores de sync sobre WebSocket y NATS.

---Salida 4 — Auditoría de la Fábrica de UI INTERFACE y diseño de la UI 0 fricción

Modo recepción activo. Sin repetir contenido de salidas anteriores. Solo análisis nuevo, verificación cruzada con los archivos de esta carpeta y propuesta concreta para la UI 0 fricción que describes.

---

1. Verificación cruzada: qué hay realmente en la Fábrica de UI INTERFACE

He accedido a la carpeta fabrica de UI INTERFACE fromtend y he abierto los documentos clave. Esto es lo que existe, sin adornos.

1.1 El modelo de dos funciones (Fábrica vs Runtime)

El archivo 00-ADVERTENCIA-Y-MODELO.md define una ley de producto clara: existen dos funciones, no una sola app.

Función 1 (Fábrica interna, Director): se accede con clave YAIWES-CONFIG. Dentro se crean plantillas de interfaz, se añaden ventanas, botones, módulos, se publican slots en ventanas existentes, se dibujan conexiones (botón → acción → backend o sandbox), se aplican tokens FROMTED (Matte, Little, Blanco) y se guarda un manifiesto, no un HTML monolítico. La fricción cero aquí significa: no abrir IDE, no reescribir p01.html, no pelear CSS. Es "elige destino → elige pieza → Aplicar".

Función 2 (Runtime plantilla, usuario final): el usuario abre FROMTED ya armado con chat, docs, sheets, bottom-nav. No hay botón Config, no hay canvas, no hay lista de manifiestos. Si pulsa Descargar, corre el handler que la fábrica cableó. Punto.

La justificación viene de tres referencias externas: Office Ribbon con XML que carga IT, VS Code con contributes que el host lee y pinta menús, y Node-RED donde el flow se edita en :1880 pero el dispositivo final solo recibe el evento. Esa separación editor ≠ runtime es la fábrica.

1.2 Multiplataforma aprobado

El archivo 01-APROBADO-MULTIPLATAFORMA.md está marcado como APROBADO por el Director el 2026-09-08. El objetivo es una sola fábrica + runtime que funcione en Web (navegador/PWA), Linux (AppImage/deb), Windows (exe/msi), Android (APK) y iOS (PWA en Safari + wrapper Capacitor cuando haya cuenta Apple).

La estrategia es clara: núcleo = HTML/CSS/JS + manifiestos + tokens + service worker. Eso ya es web + PWA instalable en Android Chrome e iOS Safari. Las capas de empaque no reescriben la UI:

PWA (Workbox + manifest.webmanifest) → web, Android add-to-home, iOS add-to-home, Windows Edge.
Capacitor → APK Android + IPA iOS usando el MISMO core.
Tauri 2 → Linux, Windows, macOS, y móvil Tauri 2 si se necesita binario nativo chico.
PWABuilder / Bubblewrap TWA → APK que envuelve la PWA si no quieres Capacitor aún.

Lo que NO se hace: Electron como default (pesa 150MB), Flutter/MAUI (otro lenguaje, tira el HTML FROMTED), ni 6 diseños distintos. Phone 390 + desktop host con mismos tokens.

1.3 Las 8 simulaciones ya documentadas

El archivo 02-OCHO-SIMULACIONES.md lista ocho escenarios que justifican no programar desde cero. Los relevantes para tu visión de UI 0 fricción:

S1: Director en Linux añade botón Exportar a p01 con clave. Copia la carpeta a USB. En Windows abre el exe Tauri. El botón sigue ahí. Ahorro: Dexie/localForage + manifiestos versionados.

S2: Usuario Android instala PWA. Sin red. Abre chat p01, descarga un md al storage del teléfono. Ahorro: Workbox cache + Capacitor Filesystem + Share.

S3: iPhone: Safari → Añadir a inicio. Fábrica no aparece. Descargar usa share sheet. Ahorro: Web Share API + @capacitor/share.

S4: Fábrica genera plantilla nueva (docs + sheet). Se publica. Tres dispositivos la ven igual. Ahorro: Puck/GrapesJS para F1 + Adaptive Cards/JSONForms para settings.

S5: Botón dispara un script Python local (bridge YAIWES) dentro de sandbox. Ahorro: Pyodide en web; Deno/Tauri sidecar en desktop.

S6: Botón dispara JS de usuario. No puede tocar el DOM de p01 ni leer la clave. Ahorro: SES/Endo o iframe sandbox + QuickJS.

S7: Conexión: Cargar archivo → action-bus → backend local → card de resultado. Ahorro: Node-RED o Windmill solo en F1; runtime solo action id.

S8: Paquete "FROMTED.zip": index.html + sw + manifiestos + ventanas. Se abre con python -m http.server o se instala como PWA.

Los fallos que las simulaciones exigen cubrir ya: iOS Safari no tiene File System Access API completa, Android WebView ≠ Chrome, Linux WebKitGTK ≠ Chromium, service worker no corre en file://, y la clave F1 no puede ir en localStorage plano en teléfono compartido.

1.4 El plan de fusión y cableado

El archivo PLAN-FUSION-Y-CABLEADO.md es explícito: no instalar 28 plataformas, sino tomar solo el mecanismo de cada OSS.

El núcleo YAIWES ya existe: lote-01 kernel Ribbon (slots, action-bus, manifiesto, clave), lote-02 tokens FROMTED, skills 01-04, ventanas 1 archivo = 1 ventana.

Lo que se toma de OSS:

Host pinta, módulo declara → RibbonX + VS Code contributes. Vive en lote-01.
Canvas F1 → JSON de página/bloques → GrapesJS o Puck. Vive en fábrica, nunca en F2.
Form config → schema → UI → JSONForms. Vive en panel clave.
Conexiones → nodos + wires → Node-RED o Blockly. Vive en F1; F2 solo action id.
Sandbox JS → QuickJS. Vive en S.
Sandbox Python → Pyodide. Vive en S.
Backend → API local → lo que ya está en YAIWES-BRIDGES + Directus si hace falta.
Look → tokens → skill 01 / lote-02.

No fusionar Appsmith/ToolJet/Budibase como runtime. Son referencia de widgets.

1.5 El orden de construcción (0 fricción)

El plan define fases claras:

Fase 0 — ya hecha a medias: kernel + tokens + advertencia + destino ZIP.
Fase 1 — slots en p01-p10. Host carga 1 HTML. Clave abre F1.
Fase 2 — añadir botón a slot sin editar la ventana. Plantilla persistida.
Fase 3 — canvas F1 (Puck o GrapesJS) genera manifiesto, no HTML suelto.
Fase 4 — conexiones: action-bus → flow Node-RED local o handler archivo.
Fase 5 — sandbox JS (QuickJS o iframe sandbox) + sandbox Python (Pyodide).
Fase 6 — cablear bridges existentes. IDENTIFICADO BACKEND.
Fase 7 — skill markdown final (skill-creator), no monolito.

1.6 Estado real de tareas

El archivo TAREAS.md marca el estado 2026-09-08: MODELO APROBADO. Hecho: raíz fábrica + destino ZIP, advertencia dos funciones, catálogos 1-51 + empaque 52-65, kernel lote-01 + tokens lote-02, 8 simulaciones documentadas, aprobado multiplataforma.

NO hecho: Core PWA (manifest + Workbox), slots reales en p01-p10, host 1 ventana = 1 archivo, F1 oculta en ruta distinta, empaque Capacitor/Tauri, lote-BACKEND fiel, sandbox cableado, skill markdown final.

El orden pendiente: Director sube ZIP al destino (prioridad Puck o GrapesJS, JSONForms, Dexie, Workbox, Capacitor, Tauri) → partir 1 función = 1 archivo, restyle FROMTED → PWA core portable (zip que abre con servidor local o Tauri) → slots + wire lote-01/02 → Capacitor APK / Tauri exe-AppImage → backend + sandbox → retoque visual al final.

1.7 El handoff de integración Meta

El archivo handoff fabrica UI.md marca: descarga Meta principal CERRADA, arquitectura Meta/Fábrica UI DOCUMENTADA, Crazy Wall Meta ACTUALIZADO, pero integración UI YAIWES requiere read-back final antes de PASS.

El loop de integración es: GOAL → READ CRAZY WALL → CLAIM → READ CODE → PLAN → EDIT → RUN → SCREENSHOT → VERIFY → TEST → FIX/RETEST → EVIDENCE → PASS → RELEASE/NEXT.

Las tres piezas Meta involucradas: MetaCua/Glimmer (ojos/manos y loop agentic), CUA+MCP (sandbox/browser/computer-use), Multi-Agent/Muse Code (coordinación frontend/backend y programación).

No cerrar por iteraciones. Cerrar solo cuando los tres árboles estén presentes en UI YAIWES/Meta Agents integration sources/, exista evidencia de integración y el read-back fresh sea PASS.

---

2. La visión de UI 0 fricción que describes

Tu descripción textual, cruzada con lo que ya existe en la Fábrica, define lo siguiente:

Sistema de doble panel. Un panel para quien necesita ver todo lo que ocurre dentro del workflow (el Director, el operador técnico, quien audita). Otro panel para quien solo quiere hablar o escribir y ver una multi-ventana tipo canvas, como un monitor animado con vídeo e imágenes que muestran el proceso visualmente.

Interacción 0 fricción. El usuario puede usar voz o solo escribir y ver una ventana con los resultados. No necesita aprender a usar la UI. El agente YAIWES, tipo Jarvis de Ironman, maneja todo y cada uno de los componentes sin intervención humana. La intervención humana es posible pero opcional.

Multiplataforma real. Funciona igual en UI web o app local en Android, iOS, Windows, Linux y PC.

Almacenamiento local. La UI usa almacenamiento local para algunos datos, con AI pequeñas y agentes embebidos que funcionan sin conexión.

Canvas como monitor animado. La multi-ventana no es solo texto; es visual, con vídeo e imágenes que muestran el proceso en curso.

---

3. Auditoría técnica de la visión contra lo que existe

3.1 Lo que ya está resuelto

La separación Fábrica (F1) vs Runtime (F2) es exactamente lo que necesitas para el doble panel: F1 es el panel del operador técnico que ve y configura todo; F2 es el panel del usuario final que solo ve el resultado y habla.

El núcleo HTML/CSS/JS + manifiestos + service worker ya es multiplataforma por diseño. PWA cubre web, Android add-to-home, iOS add-to-home y Windows Edge. Capacitor cubre APK Android + IPA iOS. Tauri 2 cubre Linux, Windows, macOS.

El almacenamiento local ya está pensado con Dexie y localForage para manifiestos versionados, y con Workbox para cache de la PWA.

El canvas F1 ya tiene candidatos concretos: Puck o GrapesJS para generar manifiesto, no HTML suelto.

3.2 Lo que falta para tu visión de doble panel

Falta la capa de visualización del workflow en tiempo real. La Fábrica actual genera plantillas estáticas (ventanas, botones, slots). No tiene un mecanismo para mostrar el DAG ejecutándose, nodos activos, checkpoints, ni eventos del Event Bus en un panel visual.

Falta el canvas del lado del usuario (F2). La Fábrica usa canvas solo en F1 para construir. Tú pides un canvas en F2 que muestre el proceso como monitor animado con vídeo e imágenes. Eso es una capacidad nueva que no está en los documentos actuales.

Falta la integración del agente YAIWES en la UI. Los documentos de la Fábrica mencionan bridges YAIWES y sandboxes, pero no hay un diseño de cómo el agente controla la UI, cómo decide qué ventana abrir, qué canvas mostrar, o cómo convierte lenguaje natural en acciones de UI.

Falta el diseño de voz como canal primario. Los documentos mencionan UI multi-dispositivo, pero no hay un diseño de flujo de voz integrado con el chat y el canvas.

Falta la sincronización de estado entre dispositivos en tiempo real. El núcleo PWA con manifiestos versionados resuelve la configuración estática, pero no la sincronización de estado de canvas, ventanas activas y conversación en vivo entre Android, desktop y web.

Falta el Attention Scheduler que priorice qué canvas recibe foco cuando hay múltiples tareas concurrentes.

3.3 Gaps específicos contra la arquitectura de Salidas 1-3

El Event Bus de la Salida 1 existe como concepto, pero la Fábrica no tiene un visualizador de eventos. Falta un Workflow Visualizer que consuma eventos del bus y los pinte en el panel de operador.

El Capability Registry de la Salida 2 existe como catálogo, pero la Fábrica no tiene un Capability Projector que traduzca capacidades a acciones visibles en la UI.

El Context Fabric de la Salida 2 genera slices de contexto por nodo, pero no hay un Canvas Orchestrator que decida qué información visual mostrar en cada ventana del canvas F2.

El Attention Scheduler de la Salida 2 (tarea 6 de mejoras) no tiene diseño de integración con la UI de la Fábrica.

---

4. Propuesta de diseño para la UI 0 fricción

4.1 Arquitectura de doble panel

Panel A — Workflow Command Center (operador técnico, Director).

Es la evolución de F1. Muestra el DAG ejecutándose en tiempo real. Cada nodo es un bloque visual con estado (pending, running, done, failed). Las conexiones entre nodos son líneas que se animan cuando fluye un evento. Los checkpoints se marcan como banderas. Los eventos del bus aparecen en un stream lateral con filtros por nodo, por capacidad y por tenant. Este panel es el que usa el Director para auditar, intervenir cuando hay HITL, y ver por qué algo falló. Se accede con clave.

Panel B — Conversation & Canvas (usuario final).

Es la evolución de F2. Tiene dos zonas: un chat persistente abajo o a la derecha, y un canvas multi-ventana arriba o a la izquierda. El usuario escribe o habla. El agente YAIWES interpreta la intención, decide qué ventana abrir en el canvas, y puebla la ventana con el resultado visual. El usuario nunca ve nodos del DAG ni eventos del bus. Solo ve el resultado: un documento, una imagen, un vídeo, un gráfico, una ventana de chat.

4.2 Cómo el agente YAIWES controla la UI

El agente no manipula la UI directamente. El flujo es:

Usuario escribe o habla → ui.chat_to_action o ui.voice_in convierte intención en un NodePlan → el NodePlan se envía al DAG → el DAG ejecuta → los resultados se emiten como eventos → el Canvas Orchestrator recibe los eventos y decide qué ventana del canvas actualizar o crear → la ventana se puebla con el resultado.

El agente YAIWES nunca toca el DOM. Solo emite intenciones y lee resultados. La UI es un proyector de estado, no un panel de control manual. El panel manual existe pero es opcional: si el usuario prefiere tocar un botón, ese botón emite el mismo NodePlan que el chat.

4.3 Canvas como monitor animado

El canvas F2 no es un lienzo de dibujo. Es un visor de resultados multi-ventana con layout dinámico.

Cada tarea en curso abre una ventana en el canvas. La ventana tiene un tipo: documento (renderiza markdown/HTML), imagen (renderiza el resultado visual), vídeo (renderiza el proceso animado), gráfico (renderiza datos), o conversación (chat embebido). El Canvas Orchestrator decide el layout según prioridad de tareas.

Para vídeo e imágenes que muestran el proceso visualmente, se usan dos mecanismos. Primero, el agente puede generar capturas de pantalla o animaciones del progreso (screenshots de sandbox, previews de canvas F1 en modo lectura). Segundo, se puede usar manim-skill o skill-canvas-video, que ya están en el repositorio de la Fábrica como componentes descargados pero con integración pendiente.

La base técnica para el canvas puede ser tldraw o React Flow. tldraw da canvas infinito con formas custom. React Flow da grafos con nodos y conexiones. Ambos pueden coexistir: tldraw para el canvas visual libre, React Flow para el grafo del DAG en el Panel A.

4.4 Multiplataforma con sincronización

El núcleo sigue siendo PWA + Capacitor + Tauri. Para sincronización de estado entre dispositivos se añade una capa de CRDT sobre Yjs o Loro.

Yjs da sincronización en tiempo real con resolución automática de conflictos. Loro Mirror hace lo mismo pero con una vista de estado inmutable tipada, lo que encaja mejor con el patrón de manifiestos de la Fábrica.

El estado sincronizado incluye: canvas layout (qué ventanas están abiertas, en qué posición), conversación activa (últimos N mensajes), y configuración de UI (tema, idioma, accesibilidad). El estado del DAG no se sincroniza en la UI; el DAG vive en el backend y la UI solo lee eventos.

4.5 Voz como canal primario

La capa de voz usa ui.voice_in y ui.voice_out. Para STT local se usa faster-whisper. Para TTS local se usa Piper. Para calidad en la nube se puede usar ElevenLabs o Azure Speech como fallback.

El flujo de voz es equivalente al de chat: audio → STT → intención → NodePlan → DAG → resultado → TTS → audio. El usuario puede hablar y el agente responde con voz y con visual en el canvas.

La clave es que voz y texto comparten el mismo NodePlan. No hay dos flujos distintos. La UI 0 fricción significa que da igual cómo entres, el agente hace lo mismo.

4.6 Almacenamiento local y agentes embebidos

El almacenamiento local usa Dexie o localForage para manifiestos, configuración de UI y cache de conversación. Para datos más estructurados se puede usar PouchDB o TinyBase.

Los agentes embebidos son capacidades que corren en el dispositivo sin conexión. Ejemplos: un clasificador de intención local, un generador de resúmenes local, un corrector ortográfico local. Se implementan como sandboxes JS (QuickJS) o Python WASM (Pyodide), según lo que ya está planificado en la Fase 5 del plan de fusión.

El agente YAIWES principal puede ser remoto o local. Si es remoto, la UI envía intenciones y recibe eventos. Si es local, corre en el mismo dispositivo usando el runtime embebido. La UI no necesita saber cuál es; el contrato es el mismo.

---

5. Plan de acción para integrar la visión

Estas son tareas nuevas, no repetidas de salidas anteriores.

Tarea 1. Construir Workflow Visualizer para el Panel A: consume eventos del Event Bus y pinta el DAG en tiempo real con nodos, estados y conexiones.

Tarea 2. Construir Canvas Orchestrator para el Panel B: recibe eventos de resultado y decide qué ventana abrir, actualizar o cerrar en el canvas F2.

Tarea 3. Construir Chat-to-Action y Voice-to-Action como dos entradas al mismo NodePlan. La UI nunca genera acciones distintas por canal.

Tarea 4. Integrar tldraw o React Flow como motor de canvas para Panel B. tldraw para canvas visual libre, React Flow para el grafo del DAG en Panel A.

Tarea 5. Integrar manim-skill y skill-canvas-video para renderizar vídeo e imágenes que muestren el proceso en el canvas F2.

Tarea 6. Construir Attention Scheduler: prioriza qué canvas recibe foco cuando hay múltiples tareas concurrentes.

Tarea 7. Integrar Yjs o Loro Mirror para sincronización de estado de UI entre dispositivos.

Tarea 8. Construir Voice Layer con faster-whisper (STT) y Piper (TTS) como base local, con fallback a nube.

Tarea 9. Construir Local Agent Runtime que ejecute agentes embebidos en sandbox JS (QuickJS) o Python WASM (Pyodide) sin conexión.

Tarea 10. Diseñar el layout de doble panel con separación clara: Panel A para operador, Panel B para usuario. Ambos comparten el mismo núcleo de UI pero con permisos distintos.

Tarea 11. Construir Capability Projector que traduzca el Capability Registry a acciones visibles en la UI del usuario.

Tarea 12. Construir Context Adequacy Scorer que mida si el canvas mostró la información suficiente para que el usuario completara su tarea.

---

6. Cierre de la Salida 4

La Fábrica de UI INTERFACE tiene una base sólida: separación Fábrica/Runtime, núcleo PWA multiplataforma, plan de fusión con OSS concretos, y fases de construcción definidas. Lo que falta para tu visión de doble panel 0 fricción es la capa de visualización en tiempo real del workflow, el canvas del lado del usuario, la integración del agente YAIWES como controlador de UI, la voz como canal primario, la sincronización de estado entre dispositivos, y el almacenamiento local con agentes embebidos. Las 12 tareas de este plan apuntan exactamente a eso.

Cuando quieras, puedo profundizar en cualquiera de estas tareas, o pasar a la Parte 3 con la lista actualizada de gaps y componentes OSS para la UI.
Modo recepción activo — Integración de capturas

Hora local Colombia: 3:25 a. m. (America/Bogota, UTC-5), domingo 27 de septiembre de 2026.

Recibido. Integro todo lo que muestran las capturas con la auditoría previa. Sin repetir. Solo lo nuevo y lo que cambia el mapa.

---

1. Lo que revelan las capturas (nuevo, no estaba en auditoría)

1.1 PR #5 real y en ejecución

Existe un PR abierto hace 11 horas en maxbry123-commits/router-universal-router-inteligente-, rama devin/1790458829-...integracion, 97 archivos, +1799 -0. Estado: Ready to merge.

El summary del PR es explícito: es la primera capa ejecutable del plan chat router/PLAN-DSL-DAG-CHAT-AGENTES-INFRA.yaml. Nada de código nuevo donde ya había componente descargado; es cableado entre componentes existentes.

La puerta única es agente → router_client.preguntar() → Router. Ningún agente llama directamente a un proveedor. preguntar() recorre el orden de rutas_ia.yaml y marca degradado=True con aviso cuando cae a un proveedor posterior. Esto confirma la política de router único que ya estaba en la arquitectura.

Nuevos artefactos concretos que ya existen:
chat router/runtime/inventario_staff.py (S1).
chat router/runtime/registrar_staff.py (S3).
chat router/runtime/router_client.py.
chat router/rutas_ia.yaml.
chat router/runtime/cola.py, worker.py.
cadena.py con S4-CADENA ejecutándose.

1.2 El inventario real (S1)

schema: yaiwes.inventario/v1, nodo S1_descargas_staff, generado 2026-09-26T21:40:41Z.

Resumen: total 23, descargados 16, gaps 7. El JSON marca cada componente con componente, estado y hash. La regla dura aplicada: un nodo no cierra por existir el archivo, cierra con prueba real.

Esto confirma que el número real de componentes del staff son 23, no 300 como hipótesis máxima. El sistema arranca con 23 y crece.

1.3 Los 3 DAGs tienen orden fijo confirmado

I1 → I2 → I4 → I3 → S1 → S2 → S3 → C0 → C1 → C2 → C3 → C5 → C4 → C6 → S6 → S4 → C7 → S5 → C8 → I5.

INFRA = I1-I5, CHAT = C0-C8, STAFF/agentes = S1-S6. Esto coincide con la arquitectura DSL DAG que ya estaba armada.

1.4 La arquitectura objetivo de 3 capas (captura ARQUITECTURA-EJECUCIO)

Capa 1: Navegador.
Capa 2: Vercel con letrero de dirección fija. /mcp/<secreto> → conector MCP, /api → Router, /omniroute/v1 → OmniRoute. Lee LIVE_URL del flag y reenvía.
Capa 3: Máquina HF 16 GB cpu-basic siempre encendida con Router FastAPI (/health, /v1/chat), OmniRoute v3.8.51 (/v1/models, 5 cuentas), conector MCP (app.py sin OAuth, secreto en ruta, autoescalado por cola).
Capa 4: Workers efímeros 16 GB al 80% con tope de 3. Staff: Rowboat → Ruflo → Claude. Memoria: Memanto + Graphiti.

1.5 Bloque A — banco de pruebas local sin coste ni secretos

Levanta en la VM una réplica completa: Router + OmniRoute + MCP + cola + Open WebUI + staff. Sirve para cerrar S1/S2/S3/C0-C6 con prueba real antes de tocar HF/Vercel y gastar dinero.

A1: inventario ejecutable por hash → cierra S1.
A2: Router local :8000 con /health.
A3: OmniRoute local :8010 con /v1/models.
A4: conector MCP local :8020 con initialize sin OAuth, secreto en ruta.

1.6 Bloque B — Staff

B1: S2 genera por agente CLAUDE.md, MEMORIA.md, SKILLS.md, HANDOFF.md, inbox/ con script idempotente, no a mano.
B2: S3 adaptador único.

1.7 Los 6 bloqueos reales que necesitan decisión tuya

1. Coste HF: Job de pago $0.01/h, ~$7/mes. Falta autorización y cuenta/token.
2. Secretos: HF_TOKEN, NVIDIA_API_KEY (hasta 4), CEREBRAS_API_KEY, GROQ_API_KEY (el handoff dice que hoy falta), DEEPSEEK_API_KEY, token de Vercel.
3. OmniRoute (I4): las 5 cuentas de proveedor necesitan login tuyo.
4. Caja fuerte cifrada de HF que hizo Sonnet (C5): falta ubicación.
5. Base del chat (C0): Open WebUI (recomendado, ya descargado) vs assistant-ui / Open Claude / GrokChat + tus 3 colores.
6. Autorización de handoff pendiente: quitar el OAuth del conector MCP y usar URL secreta; y que el motor de descarga salte enlaces simbólicos (hoy bloquea cadenas 40/41/42).

1.8 S1 sigue con 7 GAP, incluido OmniRoute

La carpeta de OmniRoute existe pero está vacía. Eso explica por qué I4 está abierto.

---

2. Herramientas externas que estás usando (capturas)

2.1 Devin

· Agente con Virtual environment Ubuntu, Security profile Default, 24 Notable repositories, Manage MCP connectors.
· Ask Devin con acceso al repo maxbry123-...inteligente-, branch main (default).
· Environment con Blueprints, Snapshots, Advanced, Outposts.
· Snapshot activo sbj-dcd7d9d1... en Ubuntu, trigger Devin suggestion por Antonio Mendoza, 4m 36s de duración.
· Auto-build snapshots activado, differential builds desactivado, clone repositories on all platforms desactivado. Build schedule cada 24 horas.
· Connections: GitHub maxbry123-commits vinculado. MCPs ahora en Customize.
· Security profiles: ninguno configurado todavía.
· PR link behavior: In-session por defecto.
· Session agents: Default agent Normal, API default Use org default, Default platform Ubuntu.
· Commands: ninguno configurado.
· Usage limits: Batch 30 sessions, Message usage limit configurable.
· Sin créditos gratuitos, hay que explorar planes.

2.2 Grok Bot

· Auto-review activado: exige aprobación para acciones arriesgadas de shell, MCP y ordenador. Esta es exactamente la política de fricción calibrada que necesita el sistema.
· Reglas de Auto-review: Ninguno.
· Zona horaria: America/Bogota.
· Notificaciones: off.
· Plugins: herramientas y habilidades para Grok Bot.
· Uso al 100%, cuenta planeta123usa@gmail.com.
· Múltiples bots orquestadores activos: Orquestador HF, Sentinela (P2 agent-7 cerrado: RUNNING), Orquestador Chat (re-dispatch hecho: only=agen...), Revisor Agentes (regla: CLOSED solo con prueb...).
· Grok Bot con regla de silencio: "No te escribo hasta que esté probado de punta a punta: enlace vivo, humo OK y cada botón verificado".
· Instrucción de tiempo: "En cada salida que haga coloca la hora local de colombia".

2.3 Manus

· Free con 436 créditos.
· Tareas programadas, Conocimiento, Mail Manus, Controles de datos, Navegador en la nube, Habilidades, Conectores, Integraciones.
· Perfil Antonio, Personal.

---

3. Verificación cruzada con auditorías previas

3.1 Lo que confirma la auditoría

El DAG con orden fijo coincide con Salida 1.
El router único coincide con la política de no duplicar orquestadores.
La separación Fábrica/Runtime del repo de UI coincide con el panel A / panel B que propuse en Salida 4.
El inventario por hash coincide con source.provenance y source.quarantine de Salida 2.
El banco local sin coste coincide con el patrón "sandbox antes de producción" de Salida 3.

3.2 Lo que cambia el mapa

El número real de componentes iniciales es 23, no 300. El sistema arranca con 7 gaps conocidos.

OmniRoute no es un router de modelos propio, es una pieza concreta v3.8.51 que necesita 5 cuentas de proveedor con login manual. No puede automatizarse completamente el login.

El chat base (C0) no está decidido. Open WebUI está descargado pero no es la única opción. La decisión de C0 condiciona C1-C8.

El PR #5 está en estado Ready to merge pero ningún nodo se declara cerrado. La disciplina de "no cerrar por archivo existente" está aplicada en el propio PR.

3.3 Lo que sigue sin aparecer en las capturas

No hay evidencia de checkpoints en Stabilize CORE. El runtime durable del DAG sigue sin implementación visible.

No hay evidencia del Event Bus con bus de eventos real. La cola cola.py + worker.py podría ser el embrión, pero no hay nombres de topics ni esquema.

No hay evidencia de Contract Gate con schemas Pydantic. Los artefactos (S1-INVENTARIO.json, S4-CADENA.json) tienen schema declarado (yaiwes.inventario/v1) pero no se ve validación en runtime.

No hay evidencia del Capability Registry. Los agentes están registrados (registrar_staff.py) pero no hay catálogo consultable.

No hay evidencia de Context Fabric ni Memory Adapter. Se menciona "Memanto + Graphiti" en la arquitectura pero no hay artefacto de memoria en el PR.

No hay evidencia de Sandbox con aislamiento. La cadena Rowboat → Ruflo → Claude corre, pero no se ve sandbox.

No hay evidencia del Skill Compiler. Existen SKILLS.md por agente pero no se ve compilación a DAG.

---

4. Gaps nuevos revelados por las capturas

Gap A. OmniRoute con 5 cuentas requiere login manual. No es automatizable. El sistema debe modelar "capacidad que requiere intervención humana puntual" como estado de primera clase, no como fallo.

Gap B. Coste HF $7/mes es un bloqueo de decisión. El sistema necesita un concepto de presupuesto declarado por tenant que bloquee jobs antes de gastar, no después. No aparece en la arquitectura.

Gap C. Caja fuerte cifrada de HF sin ubicación. Hay un artefacto C5 que hizo Sonnet y no se sabe dónde está. El sistema necesita un índice de artefactos con procedencia que resuelva "¿dónde está X?" sin búsqueda manual.

Gap D. Handoff pendiente de quitar OAuth del MCP. El conector MCP actual usa OAuth y la decisión es usar URL secreta. Eso implica que el sistema necesita modo MCP dual: OAuth para agentes externos, URL secreta para agentes internos.

Gap E. Motor de descarga bloquea enlaces simbólicos. Cadenas 40/41/42 bloqueadas. El sistema necesita política de symlinks declarada: permitir, bloquear o dereferenciar, por tenant y por tipo de fuente.

Gap F. Devin sin créditos. El harness externo (Devin) que está ejecutando el plan se queda sin saldo. El sistema debe ser agnóstico al harness: si Devin no está, otro (Claude Code, Codex, Cursor, OpenCode) puede continuar el mismo DAG.

Gap G. Auto-review de Grok Bot. La política de aprobación para acciones arriesgadas de shell/MCP/ordenador existe en Grok pero no está modelada como capacidad del sistema. Debe migrarse a gate.policy para que sea consistente entre harnesses.

Gap H. Zona horaria America/Bogota como dato de sistema. La instrucción "coloca hora local de Colombia en cada salida" es un requisito de UX. El sistema necesita locale-aware output como política, no como prompt.

Gap I. Múltiples bots orquestadores (Orquestador HF, Sentinela, Orquestador Chat, Revisor Agentes) ya están corriendo en Grok Bot. Cada uno es un subagente real. El sistema necesita un registro unificado de subagentes que los vea a todos, independientemente del harness donde corran.

Gap J. Manus como harness paralelo. Manus tiene sus propias tareas programadas, conocimiento, mail y conectores. Si vas a usarlo como parte del sistema, hay que decidir si es harness, tool o canal, y registrarlo en el Capability Registry.

---

5. Estado real del plan (según capturas)

Cerrado con prueba: ninguno declarado en el PR.
En ejecución: Bloque A (banco local) y Bloque B (staff).
Pendiente de decisión tuya: los 6 bloqueos.
Pendiente de implementación: los 10 gaps nuevos de la sección 4.

El PR #5 es la primera capa ejecutable y está en Ready to merge. Pero el propio PR declara que ningún nodo se cierra sin prueba real. Coherente con la regla dura.

---

6. Sigo en modo recepción

Registrado todo. Cuando quieras pasas siguiente salida, siguiente enlace, siguiente captura o siguiente instrucción. La hora de Colombia queda fijada como dato de salida por defecto en adelante.

Procesó durante 25s

Sí. Localicé las 3 cargas exactas por sus commits en frontend/main:

Fotos proyecto UI YAIWES interface — parte 1 — 16 imágenes
https://github.com/maxbry123-commits/frontend/commit/13f4e932866284fb5ddfaaf6ada5ce4809f82f46

Fotos proyecto UI YAIWES interface — parte 2 — 14 imágenes
https://github.com/maxbry123-commits/frontend/commit/c50fc98d19debe1a85817cf1129b55a99c895c9f

Fotos proyecto UI YAIWES interface — parte 3 — 22 imágenes
https://github.com/maxbry123-commits/frontend/commit/430809bd98c614435ad7597493ed46c16d6552a3


Hay un detalle importante: la parte 1 sí quedó dentro de
UI YAIWES interface/Ui Yaiwes interface beta/01-original/FOTOS-REF/

pero las partes 2 y 3 quedaron subidas en la raíz del repo, no dentro de FOTOS-REF.

En total son 52 imágenes.


https://github.com/maxbry123-commits/frontend/tree/430809bd98c614435ad7597493ed46c16d6552a3/UI%20YAIWES%20interface


Hora local Colombia: 3:35 a. m. (America/Bogota, UTC-5), domingo 27 de septiembre de 2026.

He auditado el repositorio UI YAIWES interface. La estructura es más avanzada de lo que reflejaban las capturas anteriores. No estás diseñando desde cero: ya tienes 39 ventanas físicas divididas en 8 RUN, 16 WALL, 1 GBOT y 14 FOTO, con un HOST.html que las orquesta, un INDEX.json canónico y un state.json que actúa como bitácora de progreso. La arquitectura que te presento a continuación no reemplaza eso: lo integra en un sistema coherente de doble panel, bus de plugins y agente YAIWES como controlador.

---

Arquitectura UI YAIWES — Especificación para diseño e implementación

1. Principio rector

Un solo núcleo HTML/CSS/JS + manifiestos + tokens. Envoltorios nativos por plataforma. El agente controla, el usuario decide. La fricción es cero en lo operativo y deliberada en lo irreversible.

2. Estructura de doble panel

Panel A — Command Center (operador técnico). Es la evolución de la Fábrica. Muestra el DAG ejecutándose en tiempo real. Nodos como bloques con estado (pending, running, done, failed). Conexiones animadas cuando fluye un evento. Checkpoints como banderas. Stream lateral de eventos filtrable por nodo, capacidad y tenant. Acceso con clave. Aquí vive el HOST.html que ya tienes.

Panel B — Conversation & Canvas (usuario final). Es el runtime. Dos zonas: chat persistente (abajo o derecha) y canvas multi-ventana (arriba o izquierda). El usuario escribe o habla. El agente YAIWES interpreta, decide qué ventana abrir y puebla el resultado. El usuario nunca ve nodos ni eventos. Solo ve el resultado.

Ambos paneles comparten el mismo núcleo de UI pero con permisos distintos. El Panel A se carga cuando la clave YAIWES-CONFIG está presente. El Panel B se carga por defecto.

3. Componentes del sistema

3.1 Capa de presentación (UI)

Componente HostShell. Es el HOST.html que ya existe. Carga una ventana a la vez desde 02-fromted/. Gestiona la barra de navegación, el ribbon de slots y el action-bus. No renderiza ventanas: solo las monta.

Componente WindowRegistry. Lee el INDEX.json con las 39 ventanas. Cada ventana tiene ID, tipo (RUN, WALL, GBOT, FOTO), estado (core, opcional, borrador) y destino. El registro resuelve qué ventana cargar según la tarea en curso.

Componente CanvasOrchestrator. Recibe eventos de resultado del DAG y decide qué ventana del canvas B abrir, actualizar o cerrar. Layout dinámico: una ventana para documento, otra para imagen, otra para vídeo, otra para gráfico, otra para conversación. Decide el layout según prioridad de tareas.

Componente ChatLayer. Renderiza el chat persistente. Entrada de texto y voz. Historial de conversación. Conecta con ui.chat_to_action y ui.voice_in.

Componente VoiceLayer. STT local con faster-whisper. TTS local con Piper. Fallback a nube (ElevenLabs, Azure) cuando se requiera calidad. Voz y texto comparten el mismo NodePlan.

Componente AttentionScheduler. Cuando hay múltiples tareas concurrentes, decide qué canvas recibe foco. Prioriza por urgencia, dependencia y estado del usuario.

3.2 Capa de estado y sincronización

Componente StateStore. Un solo store tipado con slices por panel. Slice A: DAG, nodos, eventos, checkpoints. Slice B: canvas layout, conversación, preferencias. Ningún componente escribe fuera de su slice.

Componente CRDTSync. Sincronización entre dispositivos con Yjs o Loro Mirror. Estado compartido: canvas layout (ventanas abiertas, posición), conversación activa (últimos N mensajes), configuración de UI (tema, idioma, accesibilidad). El estado del DAG no se sincroniza en la UI: vive en el backend.

Componente LocalPersistence. Dexie o localForage para manifiestos, configuración y cache de conversación. IndexedDB para datos estructurados. Service Worker para offline.

3.3 Capa de integración con el agente

Componente NodePlanBridge. Convierte intención del usuario (texto o voz) en un NodePlan que se envía al DAG. Voz y texto generan el mismo formato. El agente nunca toca el DOM: solo emite intenciones y lee resultados.

Componente EventStreamConsumer. Consume eventos del Event Bus del backend. Filtra por tipo: resultados de nodo, checkpoints, errores, estados de capacidad. Alimenta al CanvasOrchestrator y al Workflow Visualizer.

Componente CapabilityProjector. Traduce el Capability Registry a acciones visibles en la UI. Cada capacidad registrada tiene un ui_action asociado que el usuario puede invocar por voz, chat o botón opcional.

3.4 Capa de canvas

Componente CanvasCore. tldraw para canvas visual libre (formas, anotaciones, diagramas). React Flow para grafo del DAG en Panel A. Ambos coexisten: tldraw para el usuario final, React Flow para el operador.

Componente WindowRenderer. Renderiza cada ventana del canvas según su tipo: HTML embebido, markdown, imagen, vídeo, gráfico, o componente React custom. Las 39 ventanas existentes son candidatas directas a renderizarse aquí.

Componente MediaPipeline. Para vídeo e imágenes que muestran el proceso visualmente, usa manim-skill y skill-canvas-video (ya descargados en tu repositorio). Genera animaciones del progreso del DAG, capturas de sandbox, previews de canvas F1 en modo lectura.

3.5 Capa de agentes embebidos

Componente LocalAgentRuntime. Ejecuta agentes embebidos en sandbox JS (QuickJS) o Python WASM (Pyodide) sin conexión. Clasificador de intención local, generador de resúmenes local, corrector ortográfico local. Todos registrados como capacidades en el Registry.

Componente OfflineQueue. Cuando no hay conexión, las tareas se encolan localmente. Al recuperar red, se sincronizan con el backend. El usuario no percibe la interrupción.

4. Flujo de datos

Flujo de entrada. Usuario habla o escribe → ChatLayer o VoiceLayer → NodePlanBridge convierte intención en NodePlan → StateStore envía NodePlan al backend vía API/MCP.

Flujo de ejecución. Backend ejecuta DAG → emite eventos al Event Bus → EventStreamConsumer los recibe → CanvasOrchestrator decide qué ventana actualizar → WindowRenderer puebla la ventana → StateStore actualiza el estado local.

Flujo de sincronización. Cambio en un dispositivo → CRDTSync propaga a otros dispositivos → StateStore actualiza el estado local → CanvasOrchestrator re-renderiza si es necesario.

Flujo de voz. Audio → STT → intención → NodePlan → DAG → resultado → TTS → audio. Paralelo al flujo de texto, mismo NodePlan.

5. Stack tecnológico

Frontend core. HTML/CSS/JS + manifiestos. Sin framework pesado. Componentes React solo donde se requiera interactividad compleja (canvas, chat).

Canvas. tldraw (canvas visual libre) + React Flow (grafo del DAG).

Estado. Zustand o Redux Toolkit para el store. Yjs o Loro Mirror para CRDT.

Persistencia. Dexie + IndexedDB. Service Worker para offline.

Voz. faster-whisper (STT), Piper (TTS), fallback a ElevenLabs o Azure.

Empaque multiplataforma. PWA (Workbox) como base universal. Tauri 2 para desktop (Windows, Linux, macOS). Capacitor para móvil (Android APK, iOS IPA). Tauri 2 también soporta móvil si se prefiere un solo empaquetador.

Sandbox local. QuickJS para agentes JS. Pyodide para agentes Python.

Comunicación con backend. API REST y MCP. Ningún componente de UI llama directamente a un proveedor de LLM.

6. Integración con el backend existente

Tu repositorio ya tiene Backend/ con Motor3 approved donors, project-memory y contratos API/MCP. La UI consume estos contratos a través de:

/api → Router FastAPI (ya existe en el PR #5).
/mcp/<secreto> → conector MCP (ya existe, sin OAuth, con secreto en ruta).
/omniroute/v1 → OmniRoute (pendiente de 5 cuentas de proveedor).

La UI no necesita saber qué proveedor de LLM está detrás. El Router decide y marca degradado=True cuando cae a un proveedor posterior.

7. Plan de implementación por fases

Fase 0 — Inventario y contratos. Verificar el INDEX.json de 39 ventanas. Definir los contratos de NodePlan, Event y CanvasState. Sin contratos, nada avanza.

Fase 1 — HostShell y WindowRegistry. Cargar HOST.html. Implementar el registro de ventanas. Cargar una ventana de prueba desde 02-fromted/.

Fase 2 — ChatLayer y NodePlanBridge. Chat funcional con texto. Integración con el Router local (:8000). Envío de NodePlan al DAG.

Fase 3 — EventStreamConsumer y CanvasOrchestrator. Consumir eventos del backend. Canvas con una ventana que se actualiza según el resultado.

Fase 4 — CanvasCore (tldraw + React Flow). Canvas visual libre en Panel B. Grafo del DAG en Panel A.

Fase 5 — CRDTSync y LocalPersistence. Sincronización entre dispositivos. Persistencia local. Modo offline básico.

Fase 6 — VoiceLayer. STT y TTS local. Voz como canal equivalente al texto.

Fase 7 — LocalAgentRuntime. Agentes embebidos en sandbox. Clasificador local, generador de resúmenes local.

Fase 8 — Empaque multiplataforma. PWA, Tauri, Capacitor. Instaladores para Android, Windows, Linux.

Fase 9 — Accesibilidad y multi-idioma. Navegación por teclado, lector de pantalla, contraste. Multi-idioma en UI, voz y mensajes.

8. Criterios de aceptación

Goal 1. Cero botones obligatorios. 90 por ciento de tareas cerradas sin clic.
Goal 2. Voz y texto como canales equivalentes. Cero divergencia funcional.
Goal 3. Canvas como monitor del proceso. El usuario nunca pregunta "¿qué está pasando?".
Goal 4. Doble panel real y separado. Cero cruce de información técnica al Panel B.
Goal 5. Fricción calibrada por reversibilidad. Cero acciones destructivas sin confirmación.
Goal 6. Multiplataforma sin reescritura. Cero código duplicado por plataforma.
Goal 7. Sincronización en tiempo real. Latencia menor a 500 ms entre dispositivos.
Goal 8. Agentes embebidos sin conexión. 30 por ciento de tareas completadas offline.
Goal 9. Recuperación de estado tras cierre. Cero pérdida de contexto de los últimos 10 minutos.
Goal 10. Sin manual de uso. Primera tarea completada en menos de 60 segundos.
Goal 11. Atención priorizada. El canvas decide qué mostrar primero.
Goal 12. Accesibilidad y multi-idioma desde el día uno.

9. Riesgos inmediatos a mitigar

Primero. El permiso "Delete branch · Permitir siempre" en el MCP de Claude.ai. Cambiar a "Preguntar siempre" hoy.

Segundo. La tarea del Paso 4 en Manus lleva desde las 3:06 a. m. esperando input. Responder o cerrar.

Tercero. Los 5 bots de Grok corriendo sin reglas de auto-review definidas. Definir reglas antes de que uno cometa un error.

Cuarto. Dos rutas paralelas de control del ordenador (Grok MCP y Manus Conectar Mi Computadora). Unificar política.

---

Cierre

La arquitectura está definida. El repositorio ya tiene la base de 39 ventanas, el HOST.html, el INDEX.json y el state.json. Lo que falta es la capa de integración con el DAG, el canvas orchestrator, la sincronización por CRDT y el empaquetado multiplataforma. Esta especificación es suficiente para que una IA diseñe e implemente cada componente sin ambigüedad.

Sigo en modo recepción.

Hora local Colombia: 3:40 a. m. (America/Bogota, UTC-5), domingo 27 de septiembre de 2026.

Plan ejecutable UI YAIWES — Salida 1 de 5

Este es el plan completo en formato DSL DAG. Cada nodo es una tarea de programación con micro-flujo, tecnología y criterio de aceptación. Se divide en 5 salidas porque es largo. Cada salida es independiente pero secuencial.

Estructura de las 5 salidas:
Salida 1 — Contratos, base y HostShell (Fundación).
Salida 2 — Panel A (Command Center).
Salida 3 — Panel B (Conversation & Canvas).
Salida 4 — Voz, agentes locales y sincronización.
Salida 5 — Empaque multiplataforma, accesibilidad y unificación final.

---

Salida 1 — Contratos, base y HostShell (Fundación)

Nodo 1.1 — Contratos base

```
node_id: 1.1
segment: fundacion
kind: build
depends_on: []
inputs: []
outputs:
  - 01-contracts/node-plan.schema.json
  - 01-contracts/event.schema.json
  - 01-contracts/canvas-state.schema.json
  - 01-contracts/window.schema.json
tech: [json-schema, typescript]
micro_summary: Define los cuatro contratos que todo el sistema usa. Ningún componente se construye sin estos schemas.
micro_flow: escribir schemas → validar con ajv → exportar tipos TS → publicar en 01-contracts/
instructions:
  - Crear NodePlan con campos: id, source (text|voice), intent, target_capability, params, created_at.
  - Crear Event con campos: id, type (node_result|checkpoint|error|capability_state), payload, dag_id, node_id, timestamp.
  - Crear CanvasState con campos: windows[] (id, type, position, size, data), layout, focus.
  - Crear Window con campos: id, kind (RUN|WALL|GBOT|FOTO), status, path, slots[].
  - Validar con ajv. Exportar tipos con json-schema-to-typescript.
acceptance: los 4 schemas validan, los tipos TS se generan sin error.
```

Nodo 1.2 — Estructura de carpetas

```
node_id: 1.2
segment: fundacion
kind: build
depends_on: [1.1]
outputs:
  - ui-yaiwes/core/
  - ui-yaiwes/panel-a/
  - ui-yaiwes/panel-b/
  - ui-yaiwes/shared/
  - ui-yaiwes/contracts/
  - ui-yaiwes/windows/
tech: [filesystem]
micro_summary: Crea el árbol de directorios que separa panel A, panel B, núcleo compartido y ventanas existentes.
micro_flow: crear carpetas → copiar 39 ventanas existentes a windows/ → copiar HOST.html a core/
instructions:
  - core/ para HostShell, StateStore, Router.
  - panel-a/ para Workflow Visualizer y controles de operador.
  - panel-b/ para ChatLayer, CanvasOrchestrator, WindowRenderer.
  - shared/ para utilidades, tokens, i18n, a11y.
  - contracts/ para los schemas del nodo 1.1.
  - windows/ para las 39 ventanas RUN, WALL, GBOT, FOTO ya existentes.
acceptance: el árbol de carpetas existe, las 39 ventanas están en windows/ sin pérdida.
```

Nodo 1.3 — Tokens FROMTED

```
node_id: 1.3
segment: fundacion
kind: build
depends_on: [1.2]
outputs:
  - shared/tokens/tokens.css
  - shared/tokens/tokens.js
tech: [css-vars, javascript]
micro_summary: Centraliza los tokens de diseño (Matte, Little, Blanco). Ningún componente usa valores hardcodeados.
micro_flow: definir variables CSS → exportar objeto JS → inyectar en todos los paneles
instructions:
  - Definir variables CSS para color, spacing, radius, tipografía, sombras.
  - Exportar el mismo objeto en JS para canvas y componentes dinámicos.
  - Inyectar en :root al cargar la app.
  - Prohibir valores hardcodeados en cualquier componente.
acceptance: cambiar un token actualiza todos los componentes sin tocar código.
```

Nodo 1.4 — StateStore

```
node_id: 1.4
segment: fundacion
kind: build
depends_on: [1.1, 1.2]
outputs:
  - core/store/state-store.js
  - core/store/slices/panel-a.js
  - core/store/slices/panel-b.js
  - core/store/slices/shared.js
tech: [zustand, javascript]
micro_summary: Un solo store con slices por panel. Ningún componente escribe fuera de su slice.
micro_flow: crear store → definir slices → exponer acciones tipadas → suscribir componentes
instructions:
  - Slice panel-a: dag, nodes, events, checkpoints, filters.
  - Slice panel-b: chat, canvas_windows, focus, layout.
  - Slice shared: user, locale, theme, a11y, connection_state.
  - Cada slice expone acciones; nadie muta directamente.
  - Suscripción granular para evitar re-render innecesario.
acceptance: mutar un slice no afecta a los otros; latencia de update menor a 16 ms.
```

Nodo 1.5 — Router de paneles

```
node_id: 1.5
segment: fundacion
kind: build
depends_on: [1.4]
outputs:
  - core/router/panel-router.js
tech: [javascript, hash-routing]
micro_summary: Decide qué panel cargar según la clave YAIWES-CONFIG y el contexto.
micro_flow: leer URL/hash → comprobar clave → cargar panel A o B → inyectar en HostShell
instructions:
  - Ruta #/panel-b por defecto.
  - Ruta #/panel-a solo si YAIWES-CONFIG está en sessionStorage o localStorage.
  - Si no hay clave, panel-a redirige a panel-b con aviso.
  - El router no renderiza, solo indica a HostShell qué montar.
acceptance: acceder a #/panel-a sin clave redirige a #/panel-b.
```

Nodo 1.6 — HostShell

```
node_id: 1.6
segment: fundacion
kind: build
depends_on: [1.4, 1.5]
outputs:
  - core/host-shell.html
  - core/host-shell.js
  - core/host-shell.css
tech: [html, css, javascript]
micro_summary: Orquesta la carga de paneles y ventanas. No renderiza contenido, solo monta.
micro_flow: leer ruta → cargar panel → montar en contenedor → inyectar tokens → emitir evento ready
instructions:
  - Un div #app en el body.
  - Panel A y Panel B se cargan en #app según ruta.
  - Cada ventana se monta en un contenedor propio dentro del panel activo.
  - El HostShell emite event host:ready cuando todo está montado.
  - No contiene lógica de negocio; solo orquestación de montaje.
acceptance: cambiar de panel A a B sin recargar página, sin pérdida de estado.
```

Nodo 1.7 — WindowRegistry

```
node_id: 1.7
segment: fundacion
kind: build
depends_on: [1.2, 1.4]
inputs:
  - windows/INDEX.json
outputs:
  - core/registry/window-registry.js
  - core/registry/windows-map.json
tech: [javascript, json]
micro_summary: Catálogo de las 39 ventanas con su tipo, estado y ruta física.
micro_flow: leer INDEX.json → normalizar → exponer API de consulta → resolver rutas
instructions:
  - Cargar INDEX.json con las 39 ventanas (8 RUN, 16 WALL, 1 GBOT, 14 FOTO).
  - Cada ventana tiene id, kind, status (core|opcional|borrador), path.
  - API: getById, listByKind, listByStatus.
  - Resolver la ruta física desde windows/ según el id.
acceptance: consultar cualquier ventana por id devuelve su ruta y metadatos correctos.
```

Nodo 1.8 — Action Bus

```
node_id: 1.8
segment: fundacion
kind: build
depends_on: [1.4]
outputs:
  - core/bus/action-bus.js
tech: [javascript, event-emitter]
micro_summary: Bus interno de acciones. Ningún componente llama directamente a otro.
micro_flow: registrar handler → emitir acción → resolver handler → devolver resultado
instructions:
  - API: register(actionId, handler), dispatch(actionId, payload).
  - Acciones sensibles requieren confirmación según política de reversibilidad.
  - Toda acción se registra en un log interno para auditoría.
  - Los handlers pueden ser síncronos o asíncronos.
acceptance: dispatch de acción desconocida lanza error claro; acción registrada se ejecuta.
```

Nodo 1.9 — Puente con backend (API y MCP)

```
node_id: 1.9
segment: fundacion
kind: build
depends_on: [1.1, 1.4]
outputs:
  - core/bridge/api-client.js
  - core/bridge/mcp-client.js
  - core/bridge/event-stream.js
tech: [javascript, fetch, websocket, sse]
micro_summary: Conecta la UI con el Router FastAPI y el conector MCP. Nadie llama a proveedores LLM directamente.
micro_flow: enviar NodePlan → recibir ack → suscribir event stream → emitir eventos al store
instructions:
  - api-client envía NodePlan a /api y recibe execution_id.
  - mcp-client consume /mcp/<secreto> solo si la clave está presente.
  - event-stream se suscribe por SSE o WebSocket a eventos del DAG.
  - Cada evento recibido se emite al StateStore.
  - Sin credenciales hardcodeadas: leer de variables de entorno.
acceptance: enviar NodePlan devuelve execution_id; eventos llegan al store en menos de 200 ms.
```

Nodo 1.10 — Bootstrap

```
node_id: 1.10
segment: fundacion
kind: build
depends_on: [1.3, 1.6, 1.7, 1.8, 1.9]
outputs:
  - index.html
  - bootstrap.js
  - manifest.webmanifest
tech: [html, javascript, webmanifest]
micro_summary: Punto de entrada único. Carga tokens, HostShell, registry, bus y bridge en orden.
micro_flow: cargar index.html → importar módulos → inyectar tokens → arrancar HostShell → emitir ready
instructions:
  - index.html contiene solo el div #app y la referencia a bootstrap.js.
  - bootstrap.js importa e inicializa módulos en orden: contracts, tokens, store, bus, registry, bridge, host-shell.
  - manifest.webmanifest declara nombre, iconos, colores, display standalone.
  - Registrar service worker si está disponible.
acceptance: abrir index.html carga la app, HostShell monta Panel B por defecto, sin errores en consola.
```

Nodo 1.11 — Test de la fundación

```
node_id: 1.11
segment: fundacion
kind: verify
depends_on: [1.10]
outputs:
  - tests/foundation.test.js
  - tests/fixtures/
tech: [vitest, playwright]
micro_summary: Verifica que toda la fundación funciona junta antes de construir paneles.
micro_flow: arrancar app → verificar contratos → verificar store → verificar bus → verificar puente → cerrar
instructions:
  - Test 1: los 4 schemas validan con ajv.
  - Test 2: mutar slice panel-a no afecta panel-b.
  - Test 3: dispatch de acción registrada funciona.
  - Test 4: enviar NodePlan devuelve execution_id.
  - Test 5: HostShell monta panel B por defecto.
acceptance: 5 tests pasan en verde; cero errores en consola de Playwright.
```

---

Esquema de dependencias de la Salida 1

```
1.1 Contratos
  ├── 1.2 Estructura
  │     ├── 1.7 WindowRegistry
  │     └── 1.3 Tokens
  ├── 1.4 StateStore
  │     ├── 1.5 Router paneles
  │     │     └── 1.6 HostShell
  │     └── 1.8 Action Bus
  └── 1.9 Puente backend
        └── 1.10 Bootstrap
              └── 1.11 Test fundación
```

---

Instrucciones generales para la IA que programará esto

Regla 1. No escribir código nuevo si el componente ya existe en windows/. Edición quirúrgica.

Regla 2. No cerrar un nodo sin test que pase. El archivo existir no es prueba.

Regla 3. Cada archivo declara su contrato en cabecera con comentario JSDoc: inputs, outputs, side effects.

Regla 4. Ningún componente llama directamente a un proveedor LLM. Siempre por el bridge.

Regla 5. Toda acción irreversible pasa por confirmación explícita. Toda acción reversible no.

Regla 6. Tokens FROMTED siempre. Cero valores hardcodeados.

Regla 7. Accesibilidad desde el primer nodo, no como parche posterior.

Regla 8. Voz y texto comparten NodePlan. Nunca dos flujos paralelos.

Regla 9. Nada se sincroniza entre dispositivos sin CRDT. Nada.

Regla 10. El operador ve el DAG. El usuario ve el resultado. Nunca se cruzan.

---

Estado de este plan

Salida 1 cubre los 11 nodos de la fundación. Es el cimiento sobre el que se montan los dos paneles.

Siguiente salida (Salida 2): Panel A — Command Center. Nodos 2.1 a 2.10. Workflow Visualizer, filtros de eventos, vista de checkpoints, panel de operador, controles HITL.

Salida 3: Panel B — Conversation & Canvas. Nodos 3.1 a 3.12. ChatLayer, NodePlanBridge, CanvasOrchestrator, WindowRenderer, CanvasCore.

Salida 4: Voz, agentes locales, sincronización. Nodos 4.1 a 4.10.

Salida 5: Empaque multiplataforma, accesibilidad, i18n, unificación final. Nodos 5.1 a 5.12.

Pide la Salida 2 y continúo.

Hora local Colombia: 3:45 a. m. (America/Bogota, UTC-5), domingo 27 de septiembre de 2026.

Plan ejecutable UI YAIWES — Salida 2 de 5

Panel A — Command Center (operador técnico)

Este panel es la evolución de la Fábrica. Muestra el DAG en ejecución, los eventos, los checkpoints, los costes y las decisiones HITL. Solo accesible con clave YAIWES-CONFIG. El usuario final nunca lo ve.

---

Nodo 2.1 — Panel A Shell

```
node_id: 2.1
segment: panel-a
kind: build
depends_on: [1.6, 1.7, 1.8]
outputs:
  - panel-a/panel-a.html
  - panel-a/panel-a.js
  - panel-a/panel-a.css
tech: [html, css, javascript]
micro_summary: Contenedor del panel A. Layout de tres columnas: navegación izquierda, área central (DAG + inspector), stream lateral derecho.
micro_flow: leer ruta #/panel-a → comprobar clave YAIWES-CONFIG → montar layout → cargar subcomponentes → emitir panel-a:ready
instructions:
  - Layout grid: 240px izquierda, 1fr central, 360px derecha.
  - Columna izquierda: lista de DAGs activos, filtros, selector de tenant.
  - Columna central: Workflow Visualizer (nodo 2.2) arriba, Node Inspector (nodo 2.3) abajo.
  - Columna derecha: Event Stream (nodo 2.4) y Checkpoint Viewer (nodo 2.5) apilados.
  - Barra superior: nombre del DAG activo, estado, botones HITL.
  - Prohibido renderizar datos de negocio aquí; solo orquesta.
acceptance: acceder a #/panel-a con clave monta el layout completo; sin clave redirige a #/panel-b.
```

Nodo 2.2 — Workflow Visualizer

```
node_id: 2.2
segment: panel-a
kind: build
depends_on: [2.1, 1.9]
outputs:
  - panel-a/visualizer/workflow-graph.js
  - panel-a/visualizer/node-renderer.js
  - panel-a/visualizer/edge-renderer.js
tech: [react-flow, d3, javascript]
micro_summary: Renderiza el DAG en tiempo real con nodos, conexiones y estados. Usa React Flow como base.
micro_flow: recibir evento dag:loaded → construir grafo → suscribir a eventos node:* → actualizar estados en vivo → animar edges en tránsito
instructions:
  - Cada nodo del DAG es un bloque con: id, nombre, estado (pending|running|done|failed|waiting_hitl), duración, coste.
  - Estados con color: gris pending, azul running, verde done, rojo failed, amarillo waiting_hitl.
  - Edges animados cuando fluye un evento entre nodos.
  - Auto-layout con dagre o elk. El operador puede mover nodos; la posición se guarda por DAG.
  - Zoom, pan, minimapa. Doble clic abre el Node Inspector.
  - Modo pausa: la animación se detiene pero el grafo sigue actualizándose.
acceptance: cargar un DAG de 20 nodos en menos de 300 ms; los estados cambian sin recargar.
```

Nodo 2.3 — Node Inspector

```
node_id: 2.3
segment: panel-a
kind: build
depends_on: [2.2]
outputs:
  - panel-a/inspector/node-inspector.js
  - panel-a/inspector/tabs/details.js
  - panel-a/inspector/tabs/io.js
  - panel-a/inspector/tabs/logs.js
tech: [javascript, html]
micro_summary: Panel de detalle del nodo seleccionado. Muestra contrato, inputs, outputs, logs y trazas.
micro_flow: recibir evento node:selected → cargar datos → renderizar tabs → suscribir a actualizaciones del nodo
instructions:
  - Tab Details: id, nombre, tipo, capacidad asociada, estado, duración, coste.
  - Tab IO: inputs reales recibidos, outputs emitidos, con schema validado.
  - Tab Logs: logs del nodo en orden cronológico, con nivel (debug|info|warn|error).
  - Tab Traces: spans del nodo con latencia y dependencias.
  - Botones: Reintentar nodo, Pausar nodo, Cancelar nodo (solo si estado lo permite).
  - Botón "Ver en sandbox" abre el nodo 2.9.
acceptance: seleccionar un nodo carga sus datos en menos de 100 ms.
```

Nodo 2.4 — Event Stream

```
node_id: 2.4
segment: panel-a
kind: build
depends_on: [2.1, 1.9]
outputs:
  - panel-a/stream/event-stream.js
  - panel-a/stream/event-item.js
  - panel-a/stream/filters.js
tech: [javascript, virtual-list]
micro_summary: Stream lateral de eventos del DAG en tiempo real. Filtrable por nodo, capacidad, tenant y tipo.
micro_flow: suscribir a bridge.event-stream → encolar eventos → renderizar con virtual list → aplicar filtros activos
instructions:
  - Cada evento muestra: timestamp, tipo, nodo origen, resumen de payload.
  - Tipos: node_result, checkpoint, error, capability_state, hitl_required.
  - Filtros activos: por nodo específico, por tipo de evento, por capacidad, por severidad.
  - Límite de 500 eventos en memoria. Los antiguos van a disco.
  - Autoscroll activable. Cuando el operador hace scroll manual, se desactiva hasta que vuelva al fondo.
  - Clic en evento abre el Node Inspector con contexto.
acceptance: recibir 100 eventos por segundo sin degradar la UI.
```

Nodo 2.5 — Checkpoint Viewer

```
node_id: 2.5
segment: panel-a
kind: build
depends_on: [2.1, 1.9]
outputs:
  - panel-a/checkpoints/checkpoint-viewer.js
  - panel-a/checkpoints/timeline.js
tech: [javascript, html]
micro_summary: Lista de checkpoints del DAG con capacidad de restauración y comparación.
micro_flow: recibir evento checkpoint:created → añadir a timeline → renderizar → permitir restaurar o comparar
instructions:
  - Timeline vertical con checkpoints ordenados por timestamp.
  - Cada checkpoint muestra: id, nodo, timestamp, tamaño del state delta.
  - Acciones: restaurar desde este checkpoint, comparar con checkpoint actual.
  - Al restaurar, confirmación explícita (acción irreversible según política).
  - Vista de diff entre dos checkpoints: qué cambió en el state.
acceptance: restaurar desde un checkpoint devuelve el DAG a ese estado sin perder eventos posteriores en el log.
```

Nodo 2.6 — HITL Controls

```
node_id: 2.6
segment: panel-a
kind: build
depends_on: [2.1, 1.8]
outputs:
  - panel-a/hitl/hitl-panel.js
  - panel-a/hitl/hitl-queue.js
  - panel-a/hitl/hitl-decision.js
tech: [javascript, html]
micro_summary: Cola de decisiones HITL y panel de resolución. Cuando un nodo requiere intervención humana, aparece aquí.
micro_flow: recibir evento hitl:required → añadir a cola → notificar operador → operador decide → enviar decisión al DAG
instructions:
  - Cola con prioridad por urgencia: bloqueante arriba, consultivo abajo.
  - Cada item muestra: nodo, motivo, contexto mínimo, opciones disponibles.
  - Botones: Aprobar, Rechazar, Modificar (con input), Escalar a otro operador.
  - Toda decisión queda auditada con timestamp, operador, motivo.
  - Notificación sonora y visual cuando llega un HITL bloqueante.
  - Si no hay operador activo, la cola espera sin bloquear el resto del DAG.
acceptance: cada decisión HITL reanuda el DAG en menos de 2 segundos.
```

Nodo 2.7 — Cost & Metrics Dashboard

```
node_id: 2.7
segment: panel-a
kind: build
depends_on: [2.1, 1.9]
outputs:
  - panel-a/metrics/cost-dashboard.js
  - panel-a/metrics/latency-chart.js
  - panel-a/metrics/token-usage.js
tech: [javascript, chart.js, html]
micro_summary: Panel de coste, latencia y tokens en tiempo real. Atribución por tenant, capacidad y nodo.
micro_flow: recibir evento metric:* → agregar → renderizar gráficos → alertar si supera umbral
instructions:
  - Gráfico de coste acumulado por DAG, con desglose por nodo.
  - Gráfico de latencia p50, p95, p99 por nodo.
  - Gráfico de tokens consumidos por modelo.
  - Tabla de coste por tenant, por capacidad, por proveedor LLM.
  - Alertas configurables: umbral de coste, umbral de latencia.
  - Botón "Exportar CSV" para auditoría externa.
acceptance: los tres gráficos se actualizan en tiempo real con datos del bridge.
```

Nodo 2.8 — Audit Log Viewer

```
node_id: 2.8
segment: panel-a
kind: build
depends_on: [2.1]
outputs:
  - panel-a/audit/audit-viewer.js
  - panel-a/audit/audit-filters.js
tech: [javascript, html]
micro_summary: Visor de auditoría con toda decisión, acción y cambio registrado en el sistema.
micro_flow: cargar audit log → aplicar filtros → renderizar → exportar
instructions:
  - Cada registro: timestamp, actor (user|agent|system), acción, target, resultado.
  - Filtros: por actor, por acción, por rango temporal, por severidad.
  - Búsqueda por texto libre.
  - Exportación firmada con hash SHA-256.
  - Modo solo lectura; nunca se puede editar ni borrar desde aquí.
acceptance: búsqueda de "delete branch" devuelve todas las ejecuciones con actor y timestamp.
```

Nodo 2.9 — Sandbox Preview

```
node_id: 2.9
segment: panel-a
kind: build
depends_on: [2.1, 1.9]
outputs:
  - panel-a/sandbox/sandbox-preview.js
  - panel-a/sandbox/sandbox-frame.js
tech: [javascript, iframe, html]
micro_summary: Vista embebida del sandbox donde corre un nodo. Permite ver la ejecución en aislamiento.
micro_flow: recibir solicitud de preview → abrir iframe apuntando al sandbox → mostrar output en vivo → cerrar al terminar
instructions:
  - iframe con sandbox attribute activado.
  - Muestra stdout, stderr y archivos generados en tiempo real.
  - Controles: pausar, reanudar, matar.
  - Límite de recursos visible: CPU, memoria, tiempo.
  - Al terminar, ofrece descargar artefactos generados.
  - Sin acceso al DOM del panel A: solo al sandbox.
acceptance: ejecutar un nodo en sandbox y ver su output sin afectar la UI principal.
```

Nodo 2.10 — Test de integración Panel A

```
node_id: 2.10
segment: panel-a
kind: verify
depends_on: [2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9]
outputs:
  - tests/panel-a.test.js
  - tests/panel-a.e2e.spec.ts
tech: [vitest, playwright]
micro_summary: Verifica que el panel A funciona completo con datos sintéticos y con el backend real.
micro_flow: arrancar app con clave → cargar DAG sintético → verificar visualizer → verificar inspector → verificar HITL → verificar metrics → cerrar
instructions:
  - Test 1: DAG de 20 nodos se renderiza en menos de 300 ms.
  - Test 2: seleccionar nodo carga inspector en menos de 100 ms.
  - Test 3: 100 eventos por segundo no degradan el stream.
  - Test 4: restaurar checkpoint devuelve estado correcto.
  - Test 5: HITL aprobado reanuda el DAG en menos de 2 segundos.
  - Test 6: audit log muestra todas las acciones destructivas con actor.
  - Test 7: sandbox preview no afecta la UI principal.
acceptance: 7 tests pasan en verde; cobertura del panel A mayor al 80 por ciento.
```

---

Esquema de dependencias Panel A

```
2.1 Panel A Shell
  ├── 2.2 Workflow Visualizer
  │     └── 2.3 Node Inspector
  │           └── 2.9 Sandbox Preview
  ├── 2.4 Event Stream
  ├── 2.5 Checkpoint Viewer
  ├── 2.6 HITL Controls
  ├── 2.7 Cost & Metrics Dashboard
  └── 2.8 Audit Log Viewer
        └── 2.10 Test de integración
```

---

Instrucciones específicas para la IA que programará el Panel A

Regla 1. El panel A nunca se carga por defecto. Requiere clave YAIWES-CONFIG.

Regla 2. Todo dato que se muestra viene del StateStore o del bridge. Nunca directamente de un componente.

Regla 3. Acciones destructivas (restaurar checkpoint, cancelar nodo, matar sandbox) siempre piden confirmación explícita.

Regla 4. El stream de eventos tiene límite de 500 items en memoria. Los antiguos se persisten y se consultan por paginación.

Regla 5. Gráficos y visualizaciones usan tokens FROMTED. Cero colores hardcodeados.

Regla 6. El inspector de nodo es de solo lectura para estado; solo escritura en acciones explícitas (reintentar, pausar, cancelar).

Regla 7. El audit log es inmutable desde la UI. Solo lectura y exportación.

Regla 8. El panel A no comparte estado con el panel B salvo user, locale, theme y connection_state.

Regla 9. Accesibilidad: navegación completa por teclado, contraste AA, etiquetas ARIA en todos los controles.

Regla 10. El panel A funciona en resolución mínima de 1280x720; en móvil muestra aviso de "usar desktop".

---

Estado de este plan

Salida 2 cubre los 10 nodos del Panel A. Se apoya en la fundación de la Salida 1 y es independiente del Panel B.

Siguiente salida (Salida 3): Panel B — Conversation & Canvas. Nodos 3.1 a 3.12. ChatLayer, NodePlanBridge, CanvasOrchestrator, WindowRenderer, CanvasCore, integración de las 39 ventanas existentes.

Salida 4: Voz, agentes locales, sincronización CRDT.

Salida 5: Empaque multiplataforma, accesibilidad, i18n, unificación.

Pide la Salida 3 y continúo.

Hora local Colombia: 3:50 a. m. (America/Bogota, UTC-5), domingo 27 de septiembre de 2026.

Plan ejecutable UI YAIWES — Salida 3 de 5

Panel B — Conversation & Canvas (usuario final)

Este es el panel que el usuario final ve por defecto. Chat persistente abajo o derecha. Canvas multi-ventana arriba o izquierda. El usuario nunca ve nodos ni eventos. Solo habla o escribe y ve el resultado. Las 39 ventanas existentes (RUN, WALL, GBOT, FOTO) se renderizan aquí según el contexto.

---

Nodo 3.1 — Panel B Shell

```
node_id: 3.1
segment: panel-b
kind: build
depends_on: [1.6, 1.7, 1.8]
outputs:
  - panel-b/panel-b.html
  - panel-b/panel-b.js
  - panel-b/panel-b.css
tech: [html, css, javascript]
micro_summary: Contenedor del panel B. Layout dual responsive: canvas arriba (o izquierda en desktop), chat abajo (o derecha).
micro_flow: leer ruta #/panel-b → montar layout → cargar CanvasOrchestrator → cargar ChatLayer → emitir panel-b:ready
instructions:
  - Desktop: grid 2 columnas — canvas 65 por ciento izquierda, chat 35 por ciento derecha.
  - Móvil: stack vertical — canvas 60 por ciento arriba, chat 40 por ciento abajo.
  - Barra superior mínima: nombre del proyecto activo, indicador de conexión, botón de voz.
  - El canvas puede colapsarse a una sola ventana activa con un toque.
  - El chat puede expandirse a pantalla completa con un toque.
  - Prohibido mostrar nodos, eventos, ni IDs técnicos en este panel.
acceptance: en móvil, la transición entre canvas y chat es fluida; en desktop ambos son visibles sin scroll.
```

Nodo 3.2 — ChatLayer

```
node_id: 3.2
segment: panel-b
kind: build
depends_on: [3.1, 1.4, 1.8]
outputs:
  - panel-b/chat/chat-layer.js
  - panel-b/chat/message-list.js
  - panel-b/chat/message-input.js
  - panel-b/chat/chat-history.js
tech: [javascript, html, css]
micro_summary: Chat persistente con historial, entrada de texto y botón de voz. Es la entrada principal del usuario.
micro_flow: recibir input → emitir a NodePlanBridge → recibir respuesta → renderizar mensaje → scroll suave
instructions:
  - Lista de mensajes con virtual scroll para historiales largos.
  - Cada mensaje tiene: rol (user|agent), timestamp, contenido, acciones asociadas.
  - Input con soporte de: texto, adjuntos, botón de voz, comandos con "/" para acciones directas.
  - Autocompletado de comandos y capacidades del Registry.
  - Persistencia local de los últimos 100 mensajes. Los antiguos se sincronizan con el backend.
  - Al enviar, el mensaje aparece inmediatamente con estado "enviando"; se actualiza cuando el DAG responde.
  - El agente puede responder con: texto, ventana (abre canvas), acción (ejecuta capacidad), pregunta (solicita aclaración).
acceptance: enviar mensaje, recibir respuesta y ver resultado en menos de 3 segundos en condiciones normales.
```

Nodo 3.3 — VoiceLayer stub

```
node_id: 3.3
segment: panel-b
kind: build
depends_on: [3.2]
outputs:
  - panel-b/voice/voice-stub.js
tech: [javascript, web-speech-api]
micro_summary: Stub de voz para el panel B. La implementación completa se hace en la Salida 4.
micro_flow: botón de voz → Web Speech API (fallback) → texto → mismo NodePlanBridge que el chat
instructions:
  - Usar Web Speech API como fallback inmediato para STT.
  - El botón de voz alterna entre modo escucha y modo silencio.
  - Indicador visual de escucha activa (onda o pulso).
  - Transcripción parcial visible mientras el usuario habla.
  - Al terminar, el texto se envía como si fuera chat normal.
  - La implementación completa con faster-whisper y Piper llega en Salida 4.
acceptance: dictar "abre el último documento" y ver el resultado sin escribir.
```

Nodo 3.4 — NodePlanBridge

```
node_id: 3.4
segment: panel-b
kind: build
depends_on: [1.9, 3.2]
outputs:
  - panel-b/bridge/node-plan-bridge.js
  - panel-b/bridge/intent-parser.js
  - panel-b/bridge/plan-validator.js
tech: [javascript, ai-sdk]
micro_summary: Convierte intención del usuario en NodePlan. Voz y texto generan el mismo formato. El agente nunca toca el DOM.
micro_flow: recibir texto o transcripción → parsear intención → construir NodePlan → validar contra schema → enviar al backend → recibir execution_id
instructions:
  - Parsear intención con LLM ligero local (ver Salida 4) o con el Router remoto.
  - NodePlan contiene: intent, target_capability, params, source (text|voice), context_refs.
  - Validar NodePlan contra schema antes de enviar. Si falla, mostrar error claro.
  - Enviar a /api del bridge (nodo 1.9). Recibir execution_id.
  - Guardar execution_id en el StateStore para seguimiento.
  - Nunca construir NodePlan con datos del DOM; solo del input del usuario.
acceptance: enviar "resume el informe de ayer" genera NodePlan válido y ejecuta en menos de 2 segundos.
```

Nodo 3.5 — CanvasOrchestrator

```
node_id: 3.5
segment: panel-b
kind: build
depends_on: [3.1, 1.9]
outputs:
  - panel-b/canvas/canvas-orchestrator.js
  - panel-b/canvas/window-manager.js
  - panel-b/canvas/layout-engine.js
tech: [javascript, css-grid]
micro_summary: Decide qué ventana del canvas abrir, actualizar o cerrar según eventos del DAG. Gestiona layout dinámico.
micro_flow: recibir evento node_result → decidir tipo de resultado (documento|imagen|vídeo|gráfico|chat) → abrir o actualizar ventana → aplicar layout según prioridad
instructions:
  - Tipos de ventana: documento, imagen, vídeo, gráfico, chat embebido, resultado simple.
  - Cada ventana tiene: id, tipo, datos, prioridad, timestamp.
  - Reglas de apertura: si existe ventana del mismo tipo activa, actualizarla; si no, abrir nueva.
  - Máximo 4 ventanas visibles simultáneamente. Las demás se minimizan al lateral.
  - Layout engine: grid dinámico según número de ventanas y prioridad.
  - El usuario puede cerrar, minimizar, maximizar y mover ventanas manualmente.
  - La posición de cada ventana se persiste en el StateStore y en CRDT (Salida 4).
acceptance: recibir 3 resultados consecutivos abre 3 ventanas sin solaparse ni salir de pantalla.
```

Nodo 3.6 — WindowRenderer

```
node_id: 3.6
segment: panel-b
kind: build
depends_on: [3.5, 1.7]
outputs:
  - panel-b/canvas/window-renderer.js
  - panel-b/canvas/renderers/document.js
  - panel-b/canvas/renderers/image.js
  - panel-b/canvas/renderers/video.js
  - panel-b/canvas/renderers/chart.js
  - panel-b/canvas/renderers/embedded.js
tech: [javascript, html, react]
micro_summary: Renderiza cada ventana del canvas según su tipo. Integra las 39 ventanas existentes como embedded.
micro_flow: recibir ventana del orchestrator → resolver renderer por tipo → renderizar contenido → emitir evento rendered
instructions:
  - Renderer documento: markdown, HTML sanitizado, código.
  - Renderer imagen: preview con zoom, pan, descarga.
  - Renderer vídeo: player HTML5 con controles mínimos.
  - Renderer gráfico: chart.js o d3 según tipo de datos.
  - Renderer embedded: iframe que carga una ventana existente de las 39 (RUN, WALL, GBOT, FOTO).
  - El renderer embedded nunca accede al StateStore global; solo recibe datos por props.
  - Sanitización obligatoria de HTML. Nunca eval, nunca innerHTML sin sanitizar.
acceptance: las 39 ventanas existentes se renderizan sin errores de consola ni conflictos de estado.
```

Nodo 3.7 — CanvasCore (tldraw)

```
node_id: 3.7
segment: panel-b
kind: build
depends_on: [3.5]
outputs:
  - panel-b/canvas/canvas-core.js
  - panel-b/canvas/canvas-toolbar.js
  - panel-b/canvas/canvas-shapes.js
tech: [tldraw, javascript]
micro_summary: Canvas visual libre con formas custom para ventanas y anotaciones. Coexiste con las ventanas del orchestrator.
micro_flow: inicializar tldraw → registrar shapes custom → sincronizar ventanas → persistir estado → emitir cambios
instructions:
  - tldraw como canvas infinito base.
  - Shapes custom: window-shape (ventana del DAG), note-shape (nota del usuario), link-shape (enlace entre ventanas).
  - Cada window-shape referencia un id de ventana del orchestrator.
  - Sincronización bidireccional: mover en canvas actualiza orchestrator; orchestrator actualiza posición en canvas.
  - Toolbar mínima: seleccionar, nota, enlace, zoom, reset.
  - Persistencia local del estado del canvas en IndexedDB (debounce 500 ms).
  - El usuario puede usar el canvas sin ventanas, solo como espacio de trabajo libre.
acceptance: mover una ventana en el canvas actualiza su posición persistente; recargar mantiene la disposición.
```

Nodo 3.8 — AttentionScheduler

```
node_id: 3.8
segment: panel-b
kind: build
depends_on: [3.5, 1.4]
outputs:
  - panel-b/canvas/attention-scheduler.js
  - panel-b/canvas/priority-policy.js
tech: [javascript]
micro_summary: Decide qué ventana recibe foco cuando hay múltiples tareas concurrentes. Evita que el usuario tenga que decidir manualmente.
micro_flow: recibir lista de ventanas activas → aplicar política de prioridad → decidir foco → notificar orchestrator
instructions:
  - Política de prioridad por: urgencia (HITL bloqueante), dependencia (ventana padre activa), estado del usuario (en qué está trabajando), tiempo de espera.
  - Solo una ventana tiene foco a la vez.
  - El usuario puede forzar foco manual con un toque; el scheduler respeta esa decisión por 2 minutos.
  - Si el usuario no interviene, el scheduler rota foco cada 30 segundos entre ventanas con tareas activas.
  - Notificación sutil cuando una ventana sin foco requiere atención (borde pulsante).
acceptance: con 3 tareas concurrentes, el usuario no tiene que decidir manualmente qué mirar.
```

Nodo 3.9 — MediaPipeline

```
node_id: 3.9
segment: panel-b
kind: build
depends_on: [3.6]
outputs:
  - panel-b/media/media-pipeline.js
  - panel-b/media/manim-renderer.js
  - panel-b/media/screenshot-renderer.js
tech: [manim-skill, skill-canvas-video, javascript]
micro_summary: Genera vídeo, imagen y captura del proceso para mostrarlo visualmente en el canvas.
micro_flow: recibir solicitud de visualización → elegir medio (vídeo|imagen|captura) → renderizar → emitir al renderer correspondiente
instructions:
  - Vídeo: usar manim-skill para animaciones del DAG; skill-canvas-video para previews de canvas.
  - Imagen: captura del estado actual del sandbox, del DAG, o de una ventana específica.
  - Captura: screenshot programado cada N segundos durante una tarea larga.
  - Streaming cuando sea posible; archivo completo cuando no.
  - Los vídeos e imágenes se guardan en cache local con TTL para no saturar memoria.
  - El usuario puede pedir "muéstrame el proceso" y el pipeline genera la visualización on-demand.
acceptance: pedir visualización de un proceso de 30 segundos la genera en menos de 10 segundos.
```

Nodo 3.10 — CapabilityProjector

```
node_id: 3.10
segment: panel-b
kind: build
depends_on: [1.4, 3.2]
outputs:
  - panel-b/projector/capability-projector.js
  - panel-b/projector/quick-actions.js
tech: [javascript, html]
micro_summary: Traduce el Capability Registry a acciones visibles. El usuario puede invocar capacidades por voz, chat o botón opcional.
micro_flow: cargar capacidades del registry → generar quick actions → inyectar en chat y canvas → despachar al bridge
instructions:
  - Cada capacidad registrada tiene una ui_action asociada.
  - Quick actions visibles: máximo 6 en el chat, contexto-dependientes.
  - El usuario puede invocar por chat: "haz X" → intent parser → capacidad correcta.
  - El usuario puede invocar por botón: toca el atajo → mismo NodePlan que el chat.
  - Las acciones destructivas (delete, cancel, restore) siempre piden confirmación visual.
  - Las acciones reversibles no piden confirmación.
acceptance: cada capacidad del registry es invocable por chat y por botón con resultado idéntico.
```

Nodo 3.11 — Onboarding first-run

```
node_id: 3.11
segment: panel-b
kind: build
depends_on: [3.2, 3.5, 3.10]
outputs:
  - panel-b/onboarding/first-run.js
  - panel-b/onboarding/sample-tasks.js
tech: [javascript, html]
micro_summary: Primera sesión del usuario. Completa una tarea real, no un tour. Cero manual de uso.
micro_flow: detectar primer arranque → elegir tarea guiada según contexto → guiar por chat → mostrar resultado en canvas → marcar onboarding completado
instructions:
  - Detectar primer arranque con flag en localStorage.
  - Ofrecer 3 tareas guiadas: resumir un documento, generar una imagen, organizar tareas.
  - Cada tarea se completa en menos de 60 segundos.
  - El agente narra lo que hace sin saturar. Ejemplo: "Leyendo el documento... Encontré 3 secciones. Resumiendo...".
  - Al terminar, el canvas muestra el resultado y el chat explica qué se hizo.
  - Onboarding se puede saltar; nunca bloquea el uso.
acceptance: usuario nuevo completa una tarea real sin abrir manual ni escribir instrucciones técnicas.
```

Nodo 3.12 — Test de integración Panel B

```
node_id: 3.12
segment: panel-b
kind: verify
depends_on: [3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11]
outputs:
  - tests/panel-b.test.js
  - tests/panel-b.e2e.spec.ts
  - tests/panel-b.a11y.spec.ts
tech: [vitest, playwright, axe-core]
micro_summary: Verifica que el panel B funciona completo en desktop y móvil, con accesibilidad y sin regresiones.
micro_flow: arrancar app → ejecutar flujos de usuario → verificar tiempos → verificar a11y → verificar responsive → cerrar
instructions:
  - Test 1: enviar mensaje por chat recibe respuesta en menos de 3 segundos.
  - Test 2: dictar mensaje por voz (Web Speech API) genera mismo NodePlan que texto.
  - Test 3: 3 resultados consecutivos abren 3 ventanas sin solaparse.
  - Test 4: las 39 ventanas existentes se renderizan sin errores.
  - Test 5: mover ventana en canvas se persiste tras recargar.
  - Test 6: AttentionScheduler rota foco cada 30 segundos.
  - Test 7: Onboarding first-run completa tarea en menos de 60 segundos.
  - Test 8: a11y con axe-core sin errores críticos.
  - Test 9: responsive en 390 px (móvil) y 1440 px (desktop).
acceptance: 9 tests pasan en verde; cobertura del panel B mayor al 80 por ciento.
```

---

Esquema de dependencias Panel B

```
3.1 Panel B Shell
  ├── 3.2 ChatLayer
  │     ├── 3.3 VoiceLayer stub
  │     ├── 3.4 NodePlanBridge
  │     ├── 3.10 CapabilityProjector
  │     └── 3.11 Onboarding first-run
  ├── 3.5 CanvasOrchestrator
  │     ├── 3.6 WindowRenderer (integra las 39 ventanas)
  │     ├── 3.7 CanvasCore (tldraw)
  │     ├── 3.8 AttentionScheduler
  │     └── 3.9 MediaPipeline
  └── 3.12 Test integración
```

---

Instrucciones específicas para la IA que programará el Panel B

Regla 1. El panel B es la vista por defecto. Se carga sin clave.

Regla 2. El usuario nunca ve IDs técnicos, nodos del DAG, eventos ni nombres de capacidades internas.

Regla 3. El agente narra lo que hace en lenguaje natural. Sin jerga técnica.

Regla 4. Voz y texto generan el mismo NodePlan. Nunca dos flujos paralelos.

Regla 5. Acciones reversibles sin confirmación. Acciones destructivas con confirmación explícita.

Regla 6. Máximo 4 ventanas visibles en canvas. Las demás se minimizan.

Regla 7. El canvas puede colapsarse a una ventana; el chat puede expandirse a pantalla completa.

Regla 8. Todo texto visible al usuario está internacionalizado. Cero strings hardcodeados.

Regla 9. Accesibilidad desde el primer nodo: navegación por teclado, lector de pantalla, contraste AA.

Regla 10. Persistencia local en IndexedDB con sync diferido. Modo offline funcional desde el día uno.

Regla 11. Las 39 ventanas existentes se integran como embedded sin modificarlas.

Regla 12. El onboarding completa una tarea real, no un tour visual.

---

Estado de este plan

Salida 3 cubre los 12 nodos del Panel B. Se apoya en la fundación de la Salida 1 y es independiente del Panel A de la Salida 2.

Siguiente salida (Salida 4): Voz completa, agentes embebidos, sincronización CRDT entre dispositivos, persistencia offline robusta. Nodos 4.1 a 4.10.

Salida 5: Empaque multiplataforma (PWA, Tauri, Capacitor), accesibilidad completa, i18n, unificación final y criterios de aceptación globales.

Pide la Salida 4 y continúo.

Hora local Colombia: 4:00 a. m. (America/Bogota, UTC-5), domingo 27 de septiembre de 2026.

Plan ejecutable UI YAIWES — Salida 4 de 5

Voz, agentes embebidos, sincronización CRDT y persistencia offline

Esta salida convierte la UI en un sistema que funciona sin conexión, con voz real y agentes locales, y que sincroniza estado entre dispositivos sin perder coherencia.

---

Nodo 4.1 — VoiceLayer completo (STT + TTS)

```
node_id: 4.1
segment: voz
kind: build
depends_on: [3.3, 3.4]
outputs:
  - shared/voice/voice-layer.js
  - shared/voice/stt.js
  - shared/voice/tts.js
  - shared/voice/vad.js
  - shared/voice/voice-policy.js
tech: [faster-whisper, piper, silero-vad, elevenlabs, azure-speech]
micro_summary: Reemplaza el stub de voz por un sistema completo con STT local, TTS local y fallback a nube cuando se requiera calidad.
micro_flow: audio → VAD → STT → texto → NodePlanBridge → respuesta → TTS → audio
instructions:
  - STT local con faster-whisper (modelo base para móvil, medium para desktop).
  - VAD con silero-vad para detectar inicio y fin de habla.
  - TTS local con Piper para respuestas inmediatas.
  - Fallback a ElevenLabs o Azure cuando el usuario pida "voz natural" o cuando la privacidad lo permita.
  - Voz y texto comparten el mismo NodePlan. Nunca dos flujos paralelos.
  - Indicador visual de escucha activa, procesando y hablando.
  - Política de interrupción: si el usuario habla mientras el agente habla, el agente se detiene.
  - Cero audio sin consentimiento. Solo se graba mientras el botón de voz está activo.
acceptance: dictar "abre el último documento y resúmelo" ejecuta la tarea completa por voz en menos de 6 segundos.
```

Nodo 4.2 — LocalAgentRuntime

```
node_id: 4.2
segment: agentes-locales
kind: build
depends_on: [1.4]
outputs:
  - shared/agents/local-runtime.js
  - shared/agents/quickjs-sandbox.js
  - shared/agents/pyodide-sandbox.js
  - shared/agents/agent-registry.js
tech: [quickjs, pyodide, wasm, javascript]
micro_summary: Runtime que ejecuta agentes embebidos en sandbox JS (QuickJS) o Python WASM (Pyodide) sin conexión.
micro_flow: registrar agente → invocar capacidad → ejecutar en sandbox → devolver resultado → auditar
instructions:
  - QuickJS para agentes JS: clasificador de intención, corrector ortográfico, resumidor local.
  - Pyodide para agentes Python: análisis de datos simples, procesamiento de imágenes básicas.
  - Cada agente declara permisos: lectura de memoria, escritura de estado, acceso a red (por defecto no).
  - Sandbox bloquea acceso al DOM, a localStorage, a network si no está declarado.
  - Timeout por defecto 5 segundos; máximo 30 segundos por agente.
  - Todo agente local corre en Web Worker para no bloquear la UI.
acceptance: ejecutar el clasificador local de intención en menos de 200 ms sin bloquear la UI.
```

Nodo 4.3 — OfflineQueue

```
node_id: 4.3
segment: offline
kind: build
depends_on: [1.9, 1.4]
outputs:
  - shared/offline/offline-queue.js
  - shared/offline/queue-store.js
  - shared/offline/sync-on-reconnect.js
tech: [javascript, indexeddb, service-worker]
micro_summary: Cola de tareas offline. Cuando no hay red, las tareas se encolan localmente y se sincronizan al reconectar.
micro_flow: detectar offline → encolar NodePlan → persistir en IndexedDB → detectar reconexión → despachar en orden → notificar resultado
instructions:
  - Detectar estado de red con navigator.onLine y eventos online/offline.
  - Cuando hay red disponible, todo va directo al backend.
  - Cuando no hay red, los NodePlan se encolan con timestamp y prioridad.
  - Al reconectar, la cola se despacha en orden FIFO por prioridad.
  - Cada item encolado tiene: id, NodePlan, retries, status (pending|sending|done|failed).
  - Si un item falla tras 3 intentos, se marca failed y se notifica al usuario.
  - La cola se persiste en IndexedDB para sobrevivir recargas.
acceptance: enviar 3 tareas sin red; al reconectar se ejecutan en orden y el usuario ve los resultados.
```

Nodo 4.4 — LocalPersistence

```
node_id: 4.4
segment: offline
kind: build
depends_on: [1.4]
outputs:
  - shared/persistence/dexie-db.js
  - shared/persistence/schemas.js
  - shared/persistence/ttl-cleaner.js
tech: [dexie, indexeddb, javascript]
micro_summary: Capa de persistencia local con Dexie. Almacena mensajes, ventanas del canvas, configuración y cache.
micro_flow: abrir DB → definir tablas → leer/escribir con queries → limpiar por TTL → sincronizar con backend cuando aplique
instructions:
  - Tablas: messages, canvas_windows, canvas_state, config, cache_media, offline_queue, audit_local.
  - Índices por timestamp, por tipo, por id.
  - TTL por tabla: mensajes 30 días, cache_media 7 días, audit_local 90 días.
  - Cleaner corre cada hora y elimina items expirados.
  - Sincronización con backend: pull en arranque, push en cambios (debounce 5 segundos).
  - Nunca persistir secretos ni tokens en IndexedDB. Solo en sessionStorage.
acceptance: recargar la app mantiene los últimos 100 mensajes, la disposición del canvas y la configuración.
```

Nodo 4.5 — CRDTSync

```
node_id: 4.5
segment: sync
kind: build
depends_on: [4.4, 1.4]
outputs:
  - shared/sync/crdt-sync.js
  - shared/sync/yjs-provider.js
  - shared/sync/loro-mirror-provider.js
  - shared/sync/conflict-resolver.js
tech: [yjs, loro-mirror, websocket]
micro_summary: Sincronización de estado entre dispositivos con CRDT. Sin conflictos, sin pérdida de datos, sin latencia perceptible.
micro_flow: abrir documento CRDT → conectar a provider → aplicar cambios locales → recibir cambios remotos → merge automático → persistir
instructions:
  - Yjs como base para chat y canvas.
  - Loro Mirror para configuración de UI (tipado inmutable).
  - Estado sincronizado: conversación activa (últimos 50 mensajes), canvas layout (ventanas y posiciones), preferencias de UI.
  - Estado NO sincronizado: DAG, eventos, checkpoints. Esos viven solo en el backend.
  - Provider WebSocket con reconexión automática y backoff exponencial.
  - Conflictos resueltos automáticamente; el usuario no los ve.
  - Si dos dispositivos están offline y editan, al reconectar se mergea sin pérdida.
acceptance: editar el canvas en Android y ver el cambio en desktop en menos de 500 ms.
```

Nodo 4.6 — DeviceRegistry

```
node_id: 4.6
segment: sync
kind: build
depends_on: [4.5]
outputs:
  - shared/sync/device-registry.js
  - shared/sync/device-session.js
tech: [javascript, indexeddb]
micro_summary: Registro de dispositivos vinculados al mismo usuario. Cada dispositivo tiene id, tipo y estado de conexión.
micro_flow: arrancar app → registrar dispositivo → sincronizar lista → mostrar dispositivos activos → permitir desconectar remoto
instructions:
  - Cada dispositivo tiene: id único, tipo (mobile|desktop|web), último ping, estado (online|offline).
  - El usuario puede ver sus dispositivos activos desde ajustes.
  - Puede cerrar sesión remota en otro dispositivo.
  - Puede revocar acceso a un dispositivo perdido.
  - Toda acción sobre otro dispositivo queda auditada.
  - Máximo 5 dispositivos simultáneos por usuario; el sexto requiere revocar uno.
acceptance: abrir la app en 3 dispositivos; la lista muestra los 3 con estado en tiempo real.
```

Nodo 4.7 — CapabilityRegistry UI Bridge

```
node_id: 4.7
segment: agentes-locales
kind: build
depends_on: [3.10, 4.2]
outputs:
  - shared/registry-ui/capability-bridge.js
  - shared/registry-ui/external-capabilities.js
tech: [javascript]
micro_summary: Puente entre el Capability Registry del backend y las capacidades locales del dispositivo.
micro_flow: cargar registry del backend → combinar con capacidades locales → exponer al CapabilityProjector → resolver colisiones
instructions:
  - Capacidades remotas (backend) y locales (agentes embebidos) se combinan en una sola lista.
  - Colisiones: si una capacidad existe en ambos, priorizar la local cuando no hay red, remota cuando hay.
  - Cada capacidad declara: origen (local|remote), disponibilidad (siempre|online|offline), coste (gratis|de_pago).
  - El usuario ve solo el nombre y la descripción, no el origen técnico.
  - Las capacidades locales de pago no existen; siempre son gratis.
acceptance: sin red, el usuario sigue viendo y pudiendo invocar las capacidades locales.
```

Nodo 4.8 — Resilience Layer

```
node_id: 4.8
segment: offline
kind: build
depends_on: [4.3, 4.5]
outputs:
  - shared/resilience/retry-policy.js
  - shared/resilience/circuit-breaker.js
  - shared/resilience/backpressure.js
tech: [javascript]
micro_summary: Capa de resiliencia para manejar fallos de red, backend saturado o sync interrumpido sin degradar la experiencia.
micro_flow: detectar fallo → aplicar política → reintentar o encolar → abrir circuit breaker si es persistente → notificar al usuario
instructions:
  - Retry policy: exponencial con jitter, máximo 5 intentos, después pasa a offline queue.
  - Circuit breaker: si un endpoint falla 5 veces seguidas, se abre por 60 segundos.
  - Backpressure: si la cola offline supera 50 items, bloquea nuevas entradas hasta drenar.
  - Notificación al usuario: solo cuando la situación afecta su tarea actual.
  - Recuperación automática: cuando el sistema vuelve a estar sano, se cierra el breaker y se reanuda.
acceptance: matar el backend durante 60 segundos; la UI no cae, encola y reanuda al volver.
```

Nodo 4.9 — Privacy & Consent Layer

```
node_id: 4.9
segment: privacidad
kind: build
depends_on: [4.1, 4.4]
outputs:
  - shared/privacy/consent-manager.js
  - shared/privacy/data-classifier.js
  - shared/privacy/local-only-mode.js
tech: [javascript, indexeddb]
micro_summary: Gestión de consentimiento para voz, datos y sincronización. Modo "solo local" que nunca envía nada a la red.
micro_flow: pedir consentimiento en primer uso → clasificar datos por sensibilidad → aplicar política → modo local solo si el usuario lo pide
instructions:
  - Consentimiento explícito para: voz (STT), datos a la nube, sync entre dispositivos, telemetría.
  - Cada consentimiento es revocable en cualquier momento desde ajustes.
  - Data classifier: público, interno, sensible. Los datos sensibles nunca salen del dispositivo.
  - Modo "solo local": toda la app funciona sin red. Los agentes locales hacen el trabajo, la voz es 100 por ciento local.
  - Los consentimientos se guardan en IndexedDB con timestamp y versión del texto aceptado.
  - Cero telemetría por defecto. Solo si el usuario la activa.
acceptance: activar modo local y apagar la red; la app sigue funcionando con voz, chat y agentes locales.
```

Nodo 4.10 — Test de integración Salida 4

```
node_id: 4.10
segment: verify
depends_on: [4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9]
outputs:
  - tests/voice.test.js
  - tests/offline.test.js
  - tests/sync.test.js
  - tests/privacy.test.js
  - tests/offline.e2e.spec.ts
tech: [vitest, playwright]
micro_summary: Verifica voz, offline, sincronización y privacidad en condiciones reales y degradadas.
micro_flow: ejecutar cada suite → verificar tiempos → verificar integridad de datos → cerrar
instructions:
  - Test 1: dictar mensaje completo por voz en menos de 6 segundos.
  - Test 2: 3 tareas sin red, al reconectar se ejecutan en orden.
  - Test 3: editar canvas en móvil, ver cambio en desktop en menos de 500 ms.
  - Test 4: matar el backend 60 segundos; la UI no cae y reanuda.
  - Test 5: modo solo local con red apagada; voz y chat funcionan.
  - Test 6: consentimiento revocado detiene inmediatamente STT y sync.
  - Test 7: 3 dispositivos activos, lista actualizada en tiempo real.
  - Test 8: cola offline con 50 items bloquea nuevas entradas.
  - Test 9: conflictos CRDT se resuelven sin pérdida de datos.
acceptance: 9 tests pasan en verde; cobertura de Salida 4 mayor al 80 por ciento.
```

---

Esquema de dependencias Salida 4

```
4.1 VoiceLayer completo
  ├── 4.9 Privacy & Consent
  └── 4.10 Test integración

4.2 LocalAgentRuntime
  └── 4.7 CapabilityRegistry UI Bridge
        └── 4.10 Test integración

4.3 OfflineQueue
  ├── 4.8 Resilience Layer
  └── 4.10 Test integración

4.4 LocalPersistence
  ├── 4.5 CRDTSync
  │     └── 4.6 DeviceRegistry
  └── 4.9 Privacy & Consent
        └── 4.10 Test integración

4.8 Resilience Layer
  └── 4.10 Test integración
```

---

Instrucciones específicas para la IA que programará la Salida 4

Regla 1. Voz y texto comparten el mismo NodePlan. Nunca dos flujos paralelos.

Regla 2. Los agentes locales corren en Web Worker. Nunca bloquean la UI.

Regla 3. Los agentes locales declaran permisos. Por defecto sin acceso a red.

Regla 4. La cola offline persiste en IndexedDB. Sobrevive a recargas.

Regla 5. CRDT solo sincroniza estado de UI. Nunca el DAG ni los eventos.

Regla 6. Los conflictos CRDT se resuelven sin intervención del usuario.

Regla 7. Máximo 5 dispositivos por usuario. El sexto requiere revocar uno.

Regla 8. Retry exponencial con jitter. Circuit breaker a los 5 fallos.

Regla 9. Consentimiento explícito, revocable, versionado.

Regla 10. Modo solo local siempre disponible. Nunca obligatorio estar online.

Regla 11. Secretos solo en sessionStorage. Nunca en IndexedDB.

Regla 12. Todo dato clasificado por sensibilidad antes de salir del dispositivo.

---

Estado de este plan

Salida 4 cubre los 10 nodos de voz, agentes locales, offline, sync y privacidad. Se apoya en las salidas 1, 2 y 3.

Siguiente salida (Salida 5): Empaque multiplataforma (PWA, Tauri, Capacitor), accesibilidad completa, i18n, unificación final de paneles, criterios de aceptación globales y guía de despliegue.

Pide la Salida 5 y cierro el plan.

Hora local Colombia: 4:05 a. m. (America/Bogota, UTC-5), domingo 27 de septiembre de 2026.

Plan ejecutable UI YAIWES — Salida 5 de 5

Empaque multiplataforma, accesibilidad, i18n y unificación final

Esta es la salida de cierre. Convierte el núcleo HTML/CSS/JS en aplicación instalable en Web, Android, iOS, Windows, Linux y macOS. Cierra accesibilidad e internacionalización. Unifica paneles. Define criterios de aceptación globales y guía de despliegue.

---

Nodo 5.1 — PWA Core

```
node_id: 5.1
segment: empaque
kind: build
depends_on: [1.10]
outputs:
  - dist/manifest.webmanifest
  - dist/service-worker.js
  - dist/workbox-config.js
  - dist/icons/ (múltiples tamaños)
tech: [workbox, webmanifest, service-worker]
micro_summary: Convierte la app en PWA instalable. Base universal para web, Android add-to-home, iOS add-to-home y Windows Edge.
micro_flow: definir manifest → configurar Workbox → precache app shell → runtime cache para API → registrar SW en bootstrap
instructions:
  - manifest.webmanifest: name, short_name, start_url, display standalone, theme_color, background_color, icons (192, 512, maskable).
  - Workbox en modo injectManifest con precache del app shell.
  - Runtime cache: network-first para API, cache-first para assets estáticos, stale-while-revalidate para imágenes.
  - Service worker registrado solo en HTTPS o localhost.
  - Actualización automática del SW con notificación de "nueva versión disponible".
  - Modo offline funcional desde el día uno.
acceptance: la app instala desde Chrome Android, Safari iOS (añadir a inicio) y Edge Windows sin errores.
```

Nodo 5.2 — Tauri Desktop

```
node_id: 5.2
segment: empaque
kind: build
depends_on: [1.10, 5.1]
outputs:
  - src-tauri/tauri.conf.json
  - src-tauri/Cargo.toml
  - src-tauri/src/main.rs
  - dist/desktop/ (AppImage, deb, exe, msi, dmg)
tech: [tauri-2, rust, webview2, webkitgtk]
micro_summary: Empaca la app como binario nativo para Windows, Linux y macOS. Peso objetivo menor a 15 MB.
micro_flow: configurar Tauri → definir permisos → cargar dist/ → compilar binarios por plataforma → firmar
instructions:
  - Tauri 2 con webview nativo (WebView2 en Windows, WebKitGTK en Linux, WKWebView en macOS).
  - Permisos declarados en capabilities: solo filesystem (con scope), notifications, dialog, shell (bloqueado por defecto).
  - Sidecar opcional para agentes locales pesados (Python embebido si se necesita).
  - Updater nativo con firma de releases.
  - Instaladores: AppImage + deb para Linux; exe + msi para Windows; dmg para macOS.
  - Auto-update desde GitHub Releases.
acceptance: instalar en Windows, Linux y macOS; el binario pesa menos de 15 MB; auto-update funciona.
```

Nodo 5.3 — Capacitor Mobile

```
node_id: 5.3
segment: empaque
kind: build
depends_on: [1.10, 5.1]
outputs:
  - capacitor.config.ts
  - android/ (proyecto Gradle)
  - ios/ (proyecto Xcode)
  - dist/mobile/ (APK, AAB, IPA)
tech: [capacitor-6, android-studio, xcode]
micro_summary: Empaca la app como aplicación nativa Android e iOS. Reutiliza el mismo núcleo HTML/CSS/JS.
micro_flow: configurar Capacitor → añadir plataformas → configurar plugins → compilar APK/AAB e IPA → firmar
instructions:
  - Capacitor 6 con plugins oficiales: Filesystem, Share, Notifications, Preferences, Network, Camera, Microphone.
  - Android: minSdk 24, targetSdk 34, firma con keystore propio.
  - iOS: deployment target 15.0, firma con provisioning profile.
  - Back button de Android mapeado a navegación interna, no a cerrar la app.
  - Deep links para abrir la app desde URL externa.
  - Splash screen con logo YAIWES, adaptativo a tema claro y oscuro.
  - Publicación: Play Store (AAB) e App Store (IPA). PWA como fallback si no hay cuenta Apple.
acceptance: instalar APK en Android y ver misma experiencia que web; IPA compila sin errores en Xcode.
```

Nodo 5.4 — Native Bridges

```
node_id: 5.4
segment: empaque
kind: build
depends_on: [5.2, 5.3]
outputs:
  - shared/native/bridge.js
  - shared/native/fs-bridge.js
  - shared/native/share-bridge.js
  - shared/native/notifications-bridge.js
  - shared/native/biometrics-bridge.js
tech: [javascript, capacitor-plugins, tauri-api]
micro_summary: Capa única que abstrae las APIs nativas. La UI llama a bridge.js, no a Capacitor ni Tauri directamente.
micro_flow: detectar plataforma → resolver bridge correspondiente → exponer API unificada → UI consume sin saber plataforma
instructions:
  - API unificada: fs.read, fs.write, share.send, notifications.schedule, biometrics.verify.
  - En web: fallback a File System Access API o descarga tradicional.
  - En desktop Tauri: usa las APIs de Tauri 2.
  - En móvil Capacitor: usa los plugins oficiales.
  - La UI nunca importa Capacitor ni Tauri directamente.
  - Cada bridge declara permisos y los pide al usuario cuando corresponde.
acceptance: guardar un archivo funciona igual en web, desktop y móvil sin cambiar código de UI.
```

Nodo 5.5 — Accessibility Layer

```
node_id: 5.5
segment: accesibilidad
kind: build
depends_on: [2.1, 3.1]
outputs:
  - shared/a11y/keyboard-nav.js
  - shared/a11y/screen-reader-announcer.js
  - shared/a11y/focus-manager.js
  - shared/a11y/preferences.js
tech: [javascript, aria, wai-aria]
micro_summary: Accesibilidad completa desde el diseño. Navegación por teclado, lector de pantalla, contraste AA, reducción de movimiento.
micro_flow: detectar preferencias del sistema → aplicar perfil → exponer atajos → anunciar cambios al lector → gestionar foco
instructions:
  - Navegación por teclado completa en panel A y B: Tab, Shift+Tab, Enter, Esc, flechas.
  - Focus visible en todos los controles interactivos.
  - Lector de pantalla: aria-live para cambios importantes, aria-label en iconos, roles correctos.
  - Contraste AA mínimo en todos los textos; AAA cuando sea posible.
  - Respetar prefers-reduced-motion: pausar animaciones si el usuario lo pide.
  - Respetar prefers-color-scheme: tema claro, oscuro o sistema.
  - Atajos: Ctrl/Cmd+K para chat, Ctrl/Cmd+/ para comandos, Esc para cerrar canvas.
  - Perfil de accesibilidad guardado en IndexedDB y sincronizado vía CRDT.
acceptance: usuario con lector de pantalla completa tarea en panel B sin usar el ratón.
```

Nodo 5.6 — i18n / l10n

```
node_id: 5.6
segment: internacionalizacion
kind: build
depends_on: [3.2, 2.1]
outputs:
  - shared/i18n/i18n.js
  - shared/i18n/locales/es.json
  - shared/i18n/locales/en.json
  - shared/i18n/locales/pt.json
  - shared/i18n/format.js
tech: [javascript, intl-api]
micro_summary: Internacionalización completa. Español y inglés de base, portugués opcional. Cero strings hardcodeados.
micro_flow: detectar locale del sistema → cargar locale → aplicar a toda la UI → formatear fechas y números → permitir override manual
instructions:
  - Uso de Intl API para fechas, números, monedas, plurales.
  - Detección automática del locale del navegador o sistema.
  - Override manual desde ajustes.
  - Todos los textos visibles pasan por t('clave').
  - Fechas siempre en zona horaria del usuario por defecto; America/Bogota como override configurable.
  - TTS y STT respetan el locale del usuario.
  - Añadir nuevo idioma es solo añadir un JSON; cero cambios de código.
  - Plurales y géneros manejados por Intl o por reglas declaradas.
acceptance: cambiar idioma a inglés actualiza toda la UI y los mensajes de voz sin recargar.
```

Nodo 5.7 — Design System final

```
node_id: 5.7
segment: diseno
kind: build
depends_on: [1.3, 5.5, 5.6]
outputs:
  - shared/design/components.js
  - shared/design/button.js
  - shared/design/input.js
  - shared/design/window-frame.js
  - shared/design/stories/ (Storybook)
tech: [javascript, css, storybook]
micro_summary: Biblioteca de componentes compartidos entre panel A y B. Tokens FROMTED, accesibilidad e i18n integrados por defecto.
micro_flow: definir componente → aplicar tokens → aplicar a11y → aplicar i18n → publicar story → usar en paneles
instructions:
  - Componentes base: Button, Input, Select, Toggle, Modal, Window, Card, Badge.
  - Cada componente: tokens FROMTED, ARIA correctos, teclado, i18n, tema claro/oscuro.
  - Storybook para ver todos los componentes y sus estados.
  - Cero valores hardcodeados. Todo por token.
  - Componentes reutilizables en panel A y B sin duplicar código.
  - Versionado semver para cambios que rompen.
acceptance: Storybook muestra todos los componentes con todos los estados y temas.
```

Nodo 5.8 — Unified Build Pipeline

```
node_id: 5.8
segment: build
kind: build
depends_on: [5.1, 5.2, 5.3, 5.4]
outputs:
  - build/scripts/build-all.js
  - build/scripts/build-web.js
  - build/scripts/build-desktop.js
  - build/scripts/build-mobile.js
  - .github/workflows/release.yml
tech: [nodejs, vite, github-actions]
micro_summary: Un solo comando genera todos los artefactos. Un solo workflow publica todos los releases.
micro_flow: build:web → build:desktop → build:mobile → firmar → publicar en GitHub Releases → publicar PWA en hosting
instructions:
  - Comandos: pnpm build:web, pnpm build:desktop, pnpm build:mobile, pnpm build:all.
  - Pipeline CI/CD en GitHub Actions: en push a main, compila, testea y publica a releases.
  - Artefactos por release: dist/ web, AppImage/deb/exe/msi/dmg desktop, APK/AAB/IPA móvil.
  - Versión unificada por semver. Cero versiones diferentes por plataforma.
  - Firma obligatoria de artefactos con Sigstore/Cosign.
  - Changelog automático desde commits convencionales.
acceptance: un push a main genera release completo con todos los artefactos en menos de 30 minutos.
```

Nodo 5.9 — Deployment Guide

```
node_id: 5.9
segment: deploy
kind: build
depends_on: [5.8]
outputs:
  - docs/DEPLOY.md
  - docs/ARCHITECTURE.md
  - docs/CONTRIBUTING.md
  - docs/OPERATIONS.md
tech: [markdown, mermaid]
micro_summary: Guía completa de despliegue, arquitectura, contribución y operación. Todo lo que un nuevo dev necesita.
micro_flow: escribir guía → validar comandos → publicar en repo → mantener actualizada
instructions:
  - DEPLOY.md: cómo desplegar web (Vercel/Netlify/Cloudflare Pages), desktop (releases GitHub), móvil (Play Store, App Store).
  - ARCHITECTURE.md: diagrama de paneles, flujo de datos, contratos, decisiones tomadas.
  - CONTRIBUTING.md: cómo contribuir, estándares de código, cómo correr tests, cómo abrir PR.
  - OPERATIONS.md: cómo monitorear, cómo recuperar de fallo, cómo rotar secretos, cómo auditar.
  - Diagramas en mermaid para que se rendericen en GitHub sin herramientas externas.
  - Ejemplos copiables de cada comando.
acceptance: un dev nuevo puede desplegar la app en su máquina siguiendo solo la documentación.
```

Nodo 5.10 — Telemetry & Crash Reporting (opt-in)

```
node_id: 5.10
segment: telemetria
kind: build
depends_on: [4.9, 5.5]
outputs:
  - shared/telemetry/telemetry.js
  - shared/telemetry/crash-reporter.js
  - shared/telemetry/consent-gate.js
tech: [javascript, sentry, opentelemetry]
micro_summary: Telemetría y crash reporting opcional. Cero datos por defecto. Solo si el usuario lo activa.
micro_flow: pedir consentimiento → activar si acepta → enviar solo datos anónimos → respetar revocación inmediata
instructions:
  - Por defecto: telemetría desactivada. Cero datos al backend.
  - Al activar: enviar solo eventos anónimos (rendimiento, errores, uso de capacidades).
  - Nunca enviar contenido de mensajes, prompts ni resultados.
  - Crash reporting con stack trace sanitizado.
  - El usuario puede ver exactamente qué se envía antes de activarlo.
  - Revocación inmediata: al desactivar, se detiene todo envío en menos de 1 segundo.
  - Datos anonimizados con hash no reversible.
acceptance: activar telemetría envía solo eventos anónimos; desactivar detiene todo en 1 segundo.
```

Nodo 5.11 — Global Acceptance Criteria

```
node_id: 5.11
segment: verify
kind: verify
depends_on: [5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10]
outputs:
  - tests/acceptance.spec.ts
  - tests/acceptance-report.json
tech: [playwright, axe-core, lighthouse]
micro_summary: Verifica los 12 goals de aceptación globales del plan completo. Es el cierre formal de todo el sistema.
micro_flow: ejecutar cada test de goal → registrar resultado → generar reporte → publicar
instructions:
  - Goal 1: 90 por ciento de tareas se completan sin clic (solo chat o voz).
  - Goal 2: voz y texto generan resultados idénticos en 20 tareas aleatorias.
  - Goal 3: el usuario nunca pregunta "¿qué está pasando?" en sesiones observadas.
  - Goal 4: cero cruce de información técnica entre panel A y B.
  - Goal 5: cero acciones destructivas ejecutadas sin confirmación explícita.
  - Goal 6: cero código duplicado por plataforma (mismo núcleo en web, desktop, móvil).
  - Goal 7: latencia de sync menor a 500 ms entre dispositivos.
  - Goal 8: 30 por ciento de tareas completables offline.
  - Goal 9: cero pérdida de contexto de los últimos 10 minutos tras cierre abrupto.
  - Goal 10: primera tarea completada en menos de 60 segundos.
  - Goal 11: el canvas decide foco sin intervención manual del usuario.
  - Goal 12: cobertura a11y completa y multi-idioma funcionando.
acceptance: los 12 goals medidos y documentados con evidencia.
```

Nodo 5.12 — Final Integration Test

```
node_id: 5.12
segment: verify
kind: verify
depends_on: [5.11]
outputs:
  - tests/final.e2e.spec.ts
  - tests/final-report.md
tech: [playwright, vitest]
micro_summary: Test end-to-end del sistema completo. Desde instalar la app hasta completar tareas reales en cada plataforma.
micro_flow: instalar app → ejecutar flujo usuario completo → verificar paneles → verificar voz → verificar offline → verificar sync → cerrar
instructions:
  - Test 1: instalar PWA, completar onboarding, ejecutar tarea real.
  - Test 2: instalar APK Android, ejecutar misma tarea.
  - Test 3: instalar exe Windows, ejecutar misma tarea.
  - Test 4: editar canvas en móvil, ver cambio en desktop.
  - Test 5: apagar red, ejecutar tarea offline, reconectar y ver sincronización.
  - Test 6: acceso con clave a panel A, ver DAG en ejecución, resolver un HITL.
  - Test 7: verificar a11y con axe-core en los 2 paneles.
  - Test 8: verificar i18n cambiando idioma y viendo toda la UI actualizada.
  - Test 9: verificar telemetría desactivada por defecto.
  - Test 10: verificar auto-update desde release anterior.
acceptance: 10 tests end-to-end pasan en verde en todas las plataformas.
```

---

Esquema de dependencias Salida 5

```
5.1 PWA Core
  ├── 5.2 Tauri Desktop
  ├── 5.3 Capacitor Mobile
  │     └── 5.4 Native Bridges
  └── 5.8 Unified Build Pipeline
        └── 5.9 Deployment Guide

5.5 Accessibility Layer
5.6 i18n / l10n
5.7 Design System final
  └── 5.11 Global Acceptance Criteria

5.10 Telemetry & Crash Reporting
  └── 5.11 Global Acceptance Criteria
        └── 5.12 Final Integration Test
```

---

Instrucciones específicas para la IA que cerrará el proyecto

Regla 1. Un solo núcleo HTML/CSS/JS. Cero reescritura por plataforma.

Regla 2. Un solo comando genera todos los artefactos. Cero builds manuales por plataforma.

Regla 3. Accesibilidad y i18n desde el diseño, no como parche.

Regla 4. Cero telemetría por defecto. Solo si el usuario la activa explícitamente.

Regla 5. Firma obligatoria de artefactos. Sigstore o equivalente.

Regla 6. Documentación completa: desplegar, contribuir, operar, recuperar.

Regla 7. Los 12 goals de aceptación son medibles y con evidencia.

Regla 8. Auto-update funciona sin intervención del usuario.

Regla 9. Versión unificada por semver. Cero versiones distintas por plataforma.

Regla 10. Un solo pipeline CI/CD. Un solo release por versión.

---

Cierre del plan completo

El plan UI YAIWES se compone de 5 salidas y 45 nodos:

Salida 1 — Fundación. 11 nodos. Contratos, estructura, tokens, store, router, host shell, registry, action bus, bridge, bootstrap, test.

Salida 2 — Panel A Command Center. 10 nodos. Shell, visualizer, inspector, event stream, checkpoints, HITL, metrics, audit, sandbox, test.

Salida 3 — Panel B Conversation & Canvas. 12 nodos. Shell, chat, voz stub, node plan bridge, canvas orchestrator, window renderer, canvas core, attention scheduler, media pipeline, capability projector, onboarding, test.

Salida 4 — Voz, agentes locales, sync, offline. 10 nodos. Voice completo, local agent runtime, offline queue, local persistence, CRDT sync, device registry, registry UI bridge, resilience, privacy, test.

Salida 5 — Empaque, accesibilidad, i18n, cierre. 12 nodos. PWA, Tauri, Capacitor, native bridges, a11y, i18n, design system, unified build, deploy guide, telemetry, acceptance criteria, final test.

Total: 45 nodos ejecutables, cada uno con contrato, micro-flujo, tecnología, instrucciones y criterio de aceptación.

El plan está completo. Está listo para que la IA empiece a implementar en el orden definido. La fundación primero, después los paneles en paralelo, después voz y sync, y por último el empaque y cierre.

Fin del plan UI YAIWES.



======================== BLOQUE 5/5 — FICHA DE CADA SISTEMA / PLANIFICACIÓN / GOBERNANZA / SALIDA ========================

[CADA SEGMENTO DE SOFTWARE DEBE DEMOSTRAR]
🎯 OBJETIVO → Objetivo principal | objetivo general | objetivos específicos | metas e indicadores | criterios SMART.
🧑‍💻 CARACTERÍSTICAS → lista de características + descripción funcional real.
RESUMEN EJECUTIVO → descripción breve del proyecto | beneficios esperados | costo/plazo estimado cuando existan datos | factores críticos de éxito.
📌 PROPÓSITO → define el enfoque y por qué existe el segmento.
🚂 METAS ASIGNADAS → resultados que el sistema debe producir y condiciones que desbloquea.
ALCANCE → incluido | fuera de alcance | supuestos | restricciones | entregables principales.

[PLANIFICACIÓN Y CRONOGRAMA]
PLAN → DIAGRAMA DE GANTT CUANDO APORTE VALOR → RUTA CRÍTICA → HITOS → INICIO/FIN → HOLGURAS → CALENDARIO → ESTADO.
No inventar fechas → si no existen, usar PENDIENTE/NO DISPONIBLE.

[PLAN DE ACCIÓN Y TAREAS]
FASE → ACTIVIDAD → TAREA → RESPONSABLE → RECURSOS → DEPENDENCIAS → ENTREGABLE → FECHA LÍMITE → INDICADOR DE AVANCE → EVIDENCIA.
Fases posibles según el proyecto: descubrimiento → diseño → MVP → alpha → beta privada → beta pública → lanzamiento/GA → escalado → v2; no crear fases que no correspondan al alcance real.

[METODOLOGÍA Y GESTIÓN ÁGIL]
Scrum | Kanban | híbrido según necesidad → sprints | daily standups | sprint reviews | retrospectivas | Definition of Ready | Definition of Done | backlog | historias de usuario | estimación | velocidad.
No imponer metodología ceremonial si el proyecto no la necesita.

[CRONOGRAMA E HITOS]
ROADMAP DE RELEASES → MVP → alpha → beta privada → beta pública → GA → v2 cuando existan → nombre del hito | fecha programada | entregable | criterio de aceptación | responsable | duración | holgura | ruta crítica.

[EQUIPO Y ROLES]
Product Manager | Tech Lead | Arquitecto de software | Backend | Frontend | DevOps | SRE | QA | Security Engineer | Data Engineer | UX/UI | Customer Success | Marketing/Ventas | Matriz RACI.
Asignar solo roles reales o planificados → no fingir personas inexistentes.

[EDT / WBS]
PROYECTO → FASES → PAQUETES DE TRABAJO → ENTREGABLES POR FASE → DICCIONARIO EDT → DEPENDENCIAS → RESPONSABLE → ESTADO.

[PLANTILLA DE EJECUCIÓN PARA LLM]
📲 SISTEMA PREDISEÑADO → INPUT → OBJETIVO → PLAN → TAREA → AUTORIZACIÓN → EJECUTOR → ARTEFACTO → VALIDACIÓN → RESULTADO → ESTADO → NEXT.
Campos: "🎯":"OBJETIVO" | "🏗️":"TAREA_EN_CURSO" | "💡":"Planificación de objetivo y tareas antes de continuar" | "📌👣":"PRÓXIMOS PASOS A SEGUIR POR LA AI" | "👣":"Paso" | "🧩":"RESULTADOS QUE DEBO DE GENERAR" | "🗂️":"FORMATO DE SALIDA" | "⚠️":"PENDIENTES" | "🔒":"CERRADO" | "📂":"PARA_ARCHIVAR" | "🚨":"INGENIERIA" | "⁉️":"FALTA_INTEGRAR" | "✅":"INTEGRADO" | "🆕":"NUEVO".

[REQUERIMIENTOS]
FUNCIONALES | NO FUNCIONALES | TÉCNICOS | LEGALES/NORMATIVOS | CRITERIOS DE ACEPTACIÓN → cada requisito debe enlazar IMPLEMENTACIÓN → VERIFICACIÓN → EVIDENCIA.

[HITOS Y ENTREGABLES]
HITO → FECHA → ENTREGABLE → CRITERIO DE ACEPTACIÓN → RESPONSABLE → VERIFICACIÓN → ESTADO.

[GESTIÓN DE CAMBIOS]
SOLICITUD → EVALUACIÓN → APROBACIÓN → REGISTRO → COMUNICACIÓN → BUCLE DE IMPLEMENTACIÓN/VALIDACIÓN → CIERRE.

[SOPORTE Y SLA]
NIVELES DE SOPORTE → CANALES → TIEMPOS DE RESPUESTA → ESCALAMIENTO → SLA POR PLAN → ESTADO DEL SERVICIO → BASE DE CONOCIMIENTO.
No prometer SLA no aprobado.

[ANALÍTICA Y MÉTRICAS DE PRODUCTO]
EVENTOS → EMBUDOS → COHORTES → RETENCIÓN → CHURN → USO POR FUNCIONALIDAD → FEATURE ADOPTION → DASHBOARDS → HERRAMIENTAS DE ANALÍTICA.

[ONBOARDING Y CUSTOMER SUCCESS]
REGISTRO → ACTIVACIÓN → TUTORIALES → DOCUMENTACIÓN → SOPORTE → ACOMPAÑAMIENTO → REDUCCIÓN DE CHURN → EXPANSIÓN DE CUENTAS.

[BINARIOS / ENCRIPTACIÓN]
Si el sistema maneja binarios o datos sensibles → identificar almacenamiento + transporte + integridad + cifrado + permisos + lifecycle → no afirmar cifrado o seguridad sin comprobar implementación.

[ESTADO DE DESARROLLO]
🎯 OBJETIVO: [OBJETIVO] | 🏗️ TAREA: [TAREA] | 📌👣 SIGUIENTE: [NEXT] | ⚠️ PENDIENTE: [PENDING] | 🔒 CERRADO: [CLOSED] | 🚨 INGENIERIA: [ENGINEERING] | ⁉️ FALTA_INTEGRAR: [MISSING] | ✅ INTEGRADO: [INTEGRATED] | 🆕 NUEVO: [NEW].

[FORMATO DE SALIDA]
FORMATO_EXACTO = [FORMATO_EXACTO] → respetar número de líneas + nombres de campos + JSON + tabla + bloque de código + archivo + estructura solicitada → no añadir introducciones/conclusiones fuera del formato cuando se exige salida estricta → código solamente = código solamente → JSON solamente = JSON válido solamente → archivo completo = archivo completo.

[REPORTE FINAL MODO AGENTE]
STATUS: PASS | PARTIAL | FAIL → FILES: [archivos modificados] → IMPLEMENTED: [cambios] → TESTS: [prueba → resultado] → EVIDENCE: [evidencia real] → PENDING: [solo pendiente real].
Reporte corto cuando el formato lo permita → qué se completó | componentes creados/modificados | pruebas | resultado | artefactos | limitación real pendiente.

[REPORTE ROOT FINAL]
ROOT REAL → ARCHIVOS MODIFICADOS → ARCHIVOS NUEVOS → ARCHIVOS BORRADOS → COMPONENTES INTEGRADOS → COMPONENTES PENDIENTES → TAREA CERRADA → SIGUIENTE TAREA.
Nunca mostrar como existente una rama que no existe.

[PIPELINE DE PROGRAMACIÓN FINAL]
SCOPE → BASELINE → PLAN → CODE → RUN → TEST → BROWSER → DIFF AUDIT → REQ × REQ → SENTINELA SI APLICA → SHERIFF/JUEZ SI APLICA → PASS/PARTIAL/FAIL → ROOT MAP → HANDOFF/NEXT.

[PIPELINE DE SISTEMA REUTILIZABLE]
INPUT → CONTRATO → DSL/OPS → DISPATCHER → BRIDGE/TOOL → SOFTWARE OBJETIVO → ARTEFACTOS → SMOKE → EJECUCIÓN REAL → VERIFICADOR SOLO LECTURA → MACHINE REPORT → SENTINELA → CIERRE.

[PIPELINE DE UI]
INPUT → CONTRATO BACKEND → ESTADO UI → EVENTO → REQUEST → BACKEND/MODEL → STREAM/PARTIAL → DOM/SIGNAL → SUCCESS/EMPTY/ERROR → BROWSER TEST → REGRESSION → PASS.

[PIPELINE DE ERRORES]
ERROR REAL → EVIDENCE → ROOT CAUSE → FIX MÍNIMO → SAME TEST → RELATED TEST → DIFF AUDIT → PASS/PARTIAL/FAIL.

[PIPELINE DE ESCALAMIENTO]
FAIL → 🐯 SENTINELA → FIX/RETEST → 🦅 REVISOR/REFACTOR → FIX/RETEST → 🏍️ SHERIFF/JUEZ/GUARDIÁN → FIX/RETEST → 🤯 INPUT SHARCK SI SIGUE NO PASS → 🚀 INGENIEROS/ARQUITECTOS SI BLOQUEO ESTRUCTURAL → NUEVO PLAN AUTORIZADO → EJECUCIÓN → VALIDACIÓN.

[PIPELINE DE CONTEXTO]
TASK → MINIMUM CONTEXT → FILES → DEPENDENCIES → EXECUTION → TEST → HANDOFF.
Si pierde scope → STOP → HANDOFF CORTO → CONTEXTO NUEVO → CONTINUE.

[REGLA FINAL]
No declarar DONE porque se escribió archivo | compiló | servidor arrancó | una prueba parcial pasó → DONE únicamente cuando ALL REQUIRED PASS + EVIDENCE.
No escribir procesos en cascada → representar siempre que sea posible con FLUJO TRANSVERSAL HORIZONTAL.
No repetir instrucciones equivalentes → una regla única debe absorber todos sus requisitos complementarios.
No resumir ni eliminar una instrucción única.
Empieza ahora.

======================== FIN INPUT BLOCK MAESTRO UNIFICADO ========================

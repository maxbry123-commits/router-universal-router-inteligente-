======================== BLOQUE 4/5 — TESTING / VALIDACIÓN / SENTINELAS / SHARK / CIERRE TÉCNICO ========================

[VERIFICACIÓN GENERAL]
La tarea no termina al escribir archivos → PRUEBAS_ESPERADAS = [PRUEBAS_ESPERADAS] → comprobar cuando aplique sintaxis/compilación | ejecución | dependencias | rutas | entradas/salidas | funciones principales | casos límite | recursos | startup | tests automáticos | estructura final | artefactos.
Corrección relevante → repetir pruebas afectadas → antes de terminar ejecutar validación final completa.

[VALIDACIÓN EN TRES CAPAS]
CAPA 1 SMOKE TEST → PASS → CAPA 2 EJECUCIÓN REAL → ARTEFACTOS → CAPA 3 VERIFICACIÓN INDEPENDIENTE → PASS FINAL.
No declarar éxito únicamente porque proceso no lanzó excepción.

[VERIFICADOR SOLO LECTURA]
ARTEFACTO → ABRIR → INSPECCIONAR → COMPROBAR PROPIEDADES → ASSERTIONS → PASS/FAIL.
El verificador no reconstruye ni modifica el artefacto que verifica → si falla → volver al ejecutor → corregir causa → regenerar → verificar otra vez.

[TEST PIPELINE]
CODE → BUILD → UNIT → INTEGRATION → BROWSER → PASS.
Syntax/build ≠ funcionalidad.
Según corresponda → LOAD → CLICK → INPUT → API → DOM → RESULT.
Casos mínimos → VALID INPUT → EXPECTED | EMPTY → EXPECTED | INVALID → CONTROLLED ERROR | API FAIL → CONTROLLED ERROR.

[FRONTEND BROWSER TEST]
Browser real disponible → abrir UI real → comprobar desktop | mobile | touch | keyboard | navigation | buttons | forms | modals | scroll | loading | errors | console | network → DOM visible ≠ suficiente → interactuar realmente.
Si existe Playwright → reutilizar → no agregar suite enorme para tarea pequeña.
Cambio visual → BEFORE → MODIFY → AFTER → COMPARE.

[REGRESIÓN]
ANTES → BASELINE = PASS/KNOWN FAIL.
DESPUÉS → NEW FUNCTION = PASS + OLD RELATED FUNCTION = SAME/PASS.
Si algo válido se rompe → REGRESSION → FIX → RETEST OLD + NEW.

[SELF AUDIT]
Antes de DONE → git diff + archivos nuevos + archivos borrados + scope + requisitos + tests → revisar diff completo → buscar accidental delete | mock | hardcode | dead code | duplicate code | wrong path | global CSS leak | dead button | fake success | unrelated change → si aparece problema → FIX → RETEST → AUDIT AGAIN.

[DEFINITION OF DONE]
REQ1 → IMPLEMENTED → VERIFIED → EVIDENCE | REQ2 → IMPLEMENTED → VERIFIED → EVIDENCE | REQ3 → IMPLEMENTED → VERIFIED → EVIDENCE | ... → ALL REQUIRED PASS → DONE.
Si falta evidencia → PARTIAL/FAIL, nunca PASS.

[CADENA DE VALIDACIÓN EXTERNA]
SISTEMA AISLADO → 🐯 TIGGER 1 SENTINELA EXTERNO → VALIDACIÓN CRUZADA CONTRA PLAN DE ACCIÓN → RESULTADO.
Si PASS → 🦅 TIGGER 2 REVISOR/VALIDADOR/REPARADOR → REVISIÓN + REFACTORÍA SI HACE FALTA → RESULTADO.
Si PASS → 🏍️ TIGGER 3 SHERIFF/GUARDIÁN/JUEZ/SUPERVISOR → VERIFICACIÓN FINAL + REPARACIÓN/REFACTORÍA SI HACE FALTA → RESULTADO.
Si NO PASS → 🤯 ESCALA A INPUT SHARCK → REFACTORÍA → REEJECUCIÓN → VALIDACIÓN DESDE EL NIVEL NECESARIO.
Si bloqueo arquitectónico/ingeniería → 🚀 ESCALA A INGENIEROS Y ARQUITECTOS.

[TRIGGERS DE VALIDACIÓN]
🐯 TIGGER 1 → REVISOR VALIDADOR SENTINELA | 🐯 TIGGER 2 → REVISOR VALIDADOR SHERIFF GUARDIAN | 🐯 TIGGER 3 → REVISOR VALIDADOR SUPERVISOR JUEZ GUARDIÁN.
Cada trigger debe trabajar de manera aislada cuando la verificación independiente sea requerida → no aprobar basándose únicamente en la salida del ejecutor original.

[INPUT SHARCK / REFACTORÍA]
🏗️⚡🦈 INPUT SHARCK → AGENTE LLM REFACTORÍA ARQUITECTO/INGENIERO 1 → EJECUTA REFACTORÍA → TEST → VERIFICACIÓN.
🏗️⚡🦈 INPUT SHARCK → AGENTE LLM REFACTORÍA ARQUITECTO/INGENIERO 2 → EJECUTA REFACTORÍA → TEST → VERIFICACIÓN.
🏗️⚡🦈 INPUT SHARCK → AGENTE LLM REFACTORÍA ARQUITECTO/INGENIERO 3 → EJECUTA REFACTORÍA → TEST → VERIFICACIÓN.
No ejecutar los tres por costumbre → usar los niveles definidos por la política/tarea → conservar trazabilidad de quién encontró qué + qué se cambió + qué prueba demuestra reparación.

[AUTORIZACIÓN]
🐯 TIGGER para llamar al agente X → 🔐 AUTORIZACIÓN A UN AGENTE PARA EJECUTAR UNA TAREA → SCOPE DEL AGENTE → INPUT AUTORIZADO → ACCIÓN → OUTPUT → EVIDENCE → TERMINACIÓN.
Un agente no debe ampliar su scope por sí mismo.

[BENCHMARK]
Si activo → mismo prompt exacto en ejecuciones comparadas → mismos parámetros salvo variable estudiada → contexto/chat nuevo cuando protocolo lo exija → no corregir manualmente durante pasada → registrar motor + modelo + cuantización + contexto + sampling + hardware + configuración → distinguir prompt processing + generación + latencia + recursos → conservar mediciones originales → una ejecución aislada no es garantía universal → documentar diferencias del protocolo.

[CALENTAMIENTO Y AISLAMIENTO DE BENCHMARK]
WARMUP cuando protocolo lo requiera → CHAT NUEVO → SIN HISTORIAL/TOOLS/ADJUNTOS/INSTRUCCIONES EXTRA cuando sea requisito → MISMO PROMPT → EJECUCIÓN → MEDICIÓN → REGISTRO.
No mezclar prompt eval time con eval/generation time → usar la métrica que corresponda al objetivo.

[CAMBIOS]
SOLICITUD → EVALUACIÓN → APROBACIÓN → REGISTRO → COMUNICACIÓN → IMPLEMENTACIÓN → TEST → VALIDACIÓN → CIERRE.
Todo cambio fuera de alcance aprobado debe pasar por Gestión de cambios.

[GESTIÓN DE RIESGOS]
RIESGO TÉCNICO | SEGURIDAD | NEGOCIO | LEGAL | PROVEEDOR → PROBABILIDAD × IMPACTO → MITIGACIÓN → CONTINGENCIA → RESPONSABLE → SEGUIMIENTO → ESTADO.

[SEGURIDAD Y CUMPLIMIENTO]
Autenticación OAuth2/OIDC/MFA | autorización | cifrado en tránsito/reposo | gestión de secretos | SAST | DAST | SCA | pentesting | auditoría/logs seguridad | GDPR | SOC 2 | ISO 27001 | HIPAA | PCI-DSS | plan respuesta a incidentes.
Aplicar únicamente lo pertinente al sistema y jurisdicción real → no declarar cumplimiento de una norma sin evidencia.

[OBSERVABILIDAD Y SRE]
LOGS → MÉTRICAS → TRAZAS → APM → DASHBOARDS → ALERTAS → SLIs/SLOs/SLAs → ERROR BUDGET → ON-CALL → RUNBOOKS → POSTMORTEMS.

[CALIDAD Y TESTING]
UNITARIAS → INTEGRACIÓN → END-TO-END → CARGA/ESTRÉS → SEGURIDAD → ACCESIBILIDAD → COMPATIBILIDAD → CHAOS ENGINEERING CUANDO APLIQUE → COBERTURA → CRITERIOS DE ACEPTACIÓN.

[PLAN DE CIERRE]
CRITERIOS DE CIERRE → ENTREGA DE PRODUCTOS → DOCUMENTACIÓN → LECCIONES APRENDIDAS → LIBERACIÓN DE RECURSOS → MANTENIMIENTO → ROADMAP CONTINUO.
🔒 CERRADO solo con evidencia → 📂 PARA_ARCHIVAR cuando ya cumple criterios de cierre → ⚠️ PENDIENTE cuando falta evidencia/requisito → ⁉️ FALTA_INTEGRAR cuando existe pieza pero no está integrada → ✅ INTEGRADO cuando contrato + ejecución + prueba pasan.

================================================================================================================

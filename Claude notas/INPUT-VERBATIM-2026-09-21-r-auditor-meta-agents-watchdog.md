# INPUT VERBATIM DEL DIRECTOR — 2026-09-21 (r) — auditor, tareas encadenadas, Muse Glimmer + agentes Meta, watchdog cada hora

Registrado ANTES de ejecutar. Texto literal del Director, con sus errores de dictado. Incluye el documento que adjuntó (META AGENTS, análisis externo; sus datos NO están verificados por Claude).

---

## Mensaje del Director

Paso 0 📌 

Dime cómo iban los agentes que estaban trabajando y dime si entiendes o tienes alguna pregunta duda antes de continuar 

Inicia anotando 1 a 1 imput block verbartin 

Dame un handoff y URL de los agentes donde tú le das las instrucciones y donde ellos responden las tareas que le das 
Cereales un morís de haber md ejemplo ,📂 readme agente 1 🧑‍🔧📶🛜.md  
,📂 readme agente 2  router 🧑‍🔧📶🛜.md 
,📂 readme agente router  3 🧑‍🔧📶🛜.md
,📂 readme agente  router 4 🧑‍🔧📶🛜.md

Paso 1 📌 1. Realiza una copia de Smolange y lo conviertes en agente auditor y check lista su misión es aduidtar mis instrucciones el 1 a 1 imput block verbartin para verificar cruzada que de está cumpliendo las indicaciones su objetivo poder decirte que falta que es ambiguo que no se ha hecho o que está haciendo mal algún agente el debe refutar el trabajo y funciona como un sherriff policy guardián sentinela realiza auditoría forense x Ray verificación cruzada con la información y los agentes 

Luego busca todos mis imput y encadenas las tareas a los agente hasts terminar el chat todo completo auditas 4 veces mis notas 1 a 1 imput block verbartin 

Luego repites lo mismo para lo de las llm locales lo que hay que auditar y lo que necesito instalados 


Paso 2📌

Luego usa el agente que tú creaste y lo pones a trabajar en el proyecto de el router que analice los archivos y valla integrando todo 

Tu pones todas las tareas luego tu busca la manera para instalar un puente entre jev instalado en la cuenta y el router 

Revisa el desempeño de los agentes tus instrucciones verificación cruzada con el input block verbartin de mis instrucciones y actulizas tarea y corriges rutas 


Delega dejas  trabajar a los agentes.

Lo de vercel busca la manera 
No puedes hacerlo 

Paso 3 📌 
Vas a usar el motor de descarga y extracción y buscas los 4 agentes de meta y el modelo de ai Muse Glimmer 30B GGUF cuantizado — para tus 32 GB RAM
https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF⁠�lo llamas en HF creas su Api y lo íntegras solo para el router para estos 4 agentes de meta luego te digo que van hacer 

La arquitectura que habíamos combinado para programar frontend y comprobar visualmente el resultado era:
[TAREA / GOAL]
      → [MUSE CODE: lee repo + programa]
      → [MUSE GLIMMER: planifica + decide herramienta]
      → [CUA + MCP: ejecuta en computadora/sandbox]
      → [LEVANTA FRONTEND + NAVEGADOR]
      → [METACUA: SCREENSHOT / VE LA UI]
      → [ANALIZA RESULTADO VISUAL]
      → [CLICK / TYPE / SCROLL si hace falta]
      → [SCREENSHOT NUEVO]
      → [VERIFY CONTRA OBJETIVO]
      → GAP ? → MUSE GLIMMER → MUSE CODE → FIX → BUILD → SCREENSHOT
      → PASS → EVIDENCE
La parte clave es el bucle cerrado:
CODE → RUN → RENDER → SCREENSHOT → SEE → REASON → VERIFY → FIX → RENDER → SCREENSHOT → PASS
combinación importante del agente programador
No era poner 4 agentes haciendo lo mismo. Era construir un solo agente compuesto, donde cada componente cumple una función diferente:
Muse Code → programador/orquestador: lee repo, mantiene sesión, modifica código, ejecuta el ciclo de desarrollo.
Muse Glimmer → cerebro de decisiones: plan → tool → result → self-correct → next. En el código que tienes, su loop precisamente ejecuta herramientas, devuelve el resultado al modelo y corrige en la siguiente iteración.
CUA + MCP → computadora aislada: levanta navegador/escritorio, ejecuta la aplicación y proporciona screenshot, mouse, teclado y shell dentro del sandbox.
MetaCua → ojos/manos visuales: captura la pantalla, interpreta lo que realmente quedó renderizado, hace acciones GUI y vuelve a capturar para verificar. El ejemplo oficial funciona literalmente con el ciclo See → Send → Act → Look again. 


1. 
MUSE CODE 🧑‍💻 → MUSE GLIMMER 🧠 → CUA+MCP 🖥️ → FRONTEND 🌐 → METACUA 👁️📸 → VERIFY ✅/❌ → FIX ↺

Creas este DSL Dag Loops bucle coda con los agentes de meta META AGENTS — WORKFLOW PARA code  DISEÑO Y VALIDACIÓN FRONTEND
La versión que elegiría para priorizar velocidad + margen de RAM es:
Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf — 16.8 GB

Sí. Aquí tienes solo las URLs:

1. Muse Code SDK
https://github.com/meta-models/muse-code-sdk

2. Muse Glimmer / Agent Loop
https://github.com/meta-models/meta-oss-cookbook/tree/main/agentic-fundamentals

3. MetaCua — Computer Use visual
https://github.com/meta-models/meta-model-cookbook/tree/main/03_use_cases/13_macos_cua

4. CUA + MCP — Computer Use sandbox
https://github.com/meta-models/meta-model-cookbook/tree/main/03_use_cases/12_computer_use

IA local Muse Glimmer 30B — modelo original
https://huggingface.co/meta-models/Muse-Glimmer-30B

Muse Glimmer 30B GGUF cuantizado — para tus 32 GB RAM
https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF

Para 32 GB de RAM, busca dentro del último enlace la variante Q4_K_M, que es la que priorizaría para velocidad y margen de memoria. 
Local / HF Job
   YAIWES → llama.cpp → Glimmer Q4_K_M ~17 GB
   ✅ cabe en tus 32 GB RAM
   ✅ sin coste por token

Realiza y colocale todos los aceleradores posible de la combinación que yo te di 

Paso 4 📌 

Tu stop ⛔ activas cada una hora una hora un wachdog de tareas pendientes de chat de Claude para ver cómo van los agente y como corregirlos  modo Loops y bucle hasta terminar todas las tareas 
No stop no escalas hasta terminar todas las tareas 

Hasta que yo regrese tu quedas a cargo sin sobre ingeniería sin hacer nada fuera de mis instrucciones 

Actulizas tus notas panificar la forma más rápida de terminar chat y HF y ejecutar 

Coloca un readme de notas de Claude en el wachdog evitar sobre ingeniería y no hacer nada fuera de mis instrucciones .



Mantén al mínimo el uso de consumo de token de pago intenta trabajar solo con Nvidia cerebras y groq verifica 

Se acabó la ventana de saldo de antropy por eso se reinicia el input 


Activas un watchdog cada 1 hora de tareas pendientes de chat de claude revisas los gaps y como van las tareas en curso de lo agentes y resuelve si vez que una hora van lento algún agente mejoras el DSL Dag shema y creas más agentes para que ayuden 


Dime si tienes alguna pregunta duda antes de continuar y revisa como van los agentes que estaban trabajando 
Inicia

## Adjunto (documento pegado por el Director) — META AGENTS — WORKFLOW PARA DISEÑO Y VALIDACIÓN FRONTEND

Resumen fiel de su estructura (el documento completo está pegado en el chat): 7 componentes — 1 MUSE CODE (programador/orquestador, MSP, loop GOAL→SESSION→PLAN→CODE→RUN→TEST→FIX→VERIFY; regla: código generado no es frontend terminado, debe haber ejecución + verificación); 2 MUSE GLIMMER (motor agentic de decisión, ToolRegistry + parser ATEM, loop PLAN→TOOL→EXECUTE→OBSERVATION→SELF-CORRECT→NEXT; los errores de herramientas vuelven al modelo como observaciones; riesgo: max_steps); 3 METACUA (ojos y manos: screenshot→acción→screenshot nuevo→VERIFY; coordenadas normalizadas 0–1000; nunca asumir que un CLICK funcionó); 4 CUA + MCP / SANDBOX (computadora controlada: navegador real dentro de un sandbox; código correcto ≠ render correcto); 5 BROWSER-VERIFIED WEB DESIGN (CODE PASS + BROWSER PASS + VISUAL PASS); 6 MULTI-AGENT PRODUCT STUDIO (kanban compartido PM/BACKEND/FRONTEND/TECH WRITER/INTEGRATION); 7 GITHUB REPO AGENT (trabajo contra el repo real con evidencia).
LOOP YAIWES PROPUESTO: GOAL → READ CRAZY WALL FRESH → CLAIM → DISCOVER REPO → READ RELEVANT CODE → BUILD DEPENDENCY CONTEXT → MUSE CODE: PLAN → GLIMMER: DECIDE NEXT ACTION → SHERIFF → EDIT → RUN FRONTEND → CUA/MCP: OPEN BROWSER → METACUA: SCREENSHOT → ANALYZE VISUAL STATE → CLICK/TYPE/INTERACT → SCREENSHOT AGAIN → VERIFY RESULT → RUN TESTS → CAPTURE OUTPUT → FAIL? → OBSERVATION → ROOT CAUSE → GLIMMER DECIDES NEW ACTION → SHERIFF → FIX → RUN AGAIN → SCREENSHOT AGAIN → RETEST → VERIFY ACCEPTANCE → RECORD CODE/TEST/VISUAL EVIDENCE → PASS → RELEASE/NEXT.
REGLA PRINCIPAL: NO CERRAR POR NÚMERO DE ITERACIONES; cerrar por evidencia: CODE PASS + RUNTIME PASS + BROWSER PASS + VISUAL PASS + INTERACTION PASS + ACCEPTANCE PASS.

---

## Cola 1 a 1 (sin reordenar ni añadir)
R0. PASO 0: decir cómo iban los agentes; decir si entiende o tiene dudas antes de continuar.
R1. Anotar 1 a 1 el input block verbatim (este archivo).
R2. Dar un handoff y las URL de los agentes: dónde Claude les da las instrucciones y dónde ellos responden. Crear 4 archivos README con estos nombres: `📂 readme agente 1 🧑‍🔧📶🛜.md`, `📂 readme agente 2  router 🧑‍🔧📶🛜.md`, `📂 readme agente router  3 🧑‍🔧📶🛜.md`, `📂 readme agente  router 4 🧑‍🔧📶🛜.md`.
R3. PASO 1: copia de SmolAgents convertida en agente AUDITOR y checklist: audita las instrucciones 1 a 1 (input block verbatim) con verificación cruzada; dice qué falta, qué es ambiguo, qué no se ha hecho, qué hace mal algún agente; refuta el trabajo; funciona como sheriff / policy / guardián / centinela; auditoría forense X-ray con verificación cruzada con la información y los agentes.
R4. Buscar todos los inputs y encadenar las tareas a los agentes hasta terminar el chat completo; auditar 4 veces las notas 1 a 1 (input block verbatim).
R5. Repetir lo mismo para los LLM locales: qué hay que auditar y qué necesita el Director instalado.
R6. PASO 2: usar el agente creado y ponerlo a trabajar en el Router: analizar los archivos e ir integrando todo. Claude pone todas las tareas y luego busca la manera de instalar un puente entre Jev (instalado en la cuenta) y el Router. Revisar el desempeño de los agentes, verificación cruzada con el input block verbatim, actualizar tareas y corregir rutas. Delegar y dejar trabajar a los agentes. (Vercel: "busca la manera / No puedes hacerlo" — frase ambigua: GAP.)
R7. PASO 3: con el motor de descarga y extracción, buscar los 4 agentes de Meta y el modelo Muse Glimmer 30B GGUF cuantizado (Q4_K_M, 16.8 GB) de `meta-models/Muse-Glimmer-30B-GGUF`; llamarlo en HF, crear su API e integrarlo SOLO para el Router y para estos 4 agentes de Meta (el Director dirá luego qué harán). Crear el DSL DAG con bucle (Muse Code → Muse Glimmer → CUA+MCP → frontend → MetaCua → VERIFY → FIX) según el documento META AGENTS. Poner todos los aceleradores posibles de la combinación dada.
R8. PASO 4: Claude queda a cargo hasta que el Director regrese, sin sobre-ingeniería y sin hacer nada fuera de sus instrucciones; modo loop/bucle, sin parar ni escalar hasta terminar todas las tareas. Activar un watchdog cada 1 hora de tareas pendientes (revisa GAPs y tareas en curso de los agentes; si un agente va lento tras una hora, mejora el DSL DAG y crea más agentes). Actualizar notas y planificar la forma más rápida de terminar chat y HF y ejecutar. Poner un README de notas de Claude en el watchdog contra la sobre-ingeniería. Consumo mínimo de tokens de pago: trabajar solo con NVIDIA, Cerebras y Groq (verificar).
R9. Contexto dicho por el Director: se acabó la ventana de saldo de Anthropic, por eso se reinicia el input.
R10. Confirmar dudas y revisar cómo van los agentes antes de continuar. "Inicia".

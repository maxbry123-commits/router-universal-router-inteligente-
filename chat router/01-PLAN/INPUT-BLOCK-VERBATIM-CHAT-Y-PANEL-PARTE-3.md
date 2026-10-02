# INPUT BLOCK VERBATIM — PARTE 3 (mensajes del 2026-09-25 noche)
Continuación de "chat router/INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL.md". Texto literal del Director. Claves → [CLAVE OMITIDA].
Nota de Opus: la PARTE 2 (documentos completos anteriores) está redactada y pendiente de subir; falló la autenticación del conector a mitad de la escritura.

---

## M22
Dice que estába el servidor en durmiendo resuelvelo para que no pare usa el de 16 de ram y lo dejas corriendo sin que se duerma

## M23
Ponlo pago no gratis 16 ram con pago sin dormir y el de 32se ram se enciende con un botón o requerimiento

## M24
Alucinas revisa de nuevo
(Texto pegado por el Director: Sí existe CPU de 16 GB pagada por hora en Hugging Face, pero en HF Jobs, no en Spaces. HF Jobs – CPU Basic 2 vCPU 16 GB US$0.01/hora · HF Jobs – CPU Upgrade 8 vCPU 32 GB US$0.03/hora · HF Spaces – CPU Basic 2 vCPU 16 GB US$0/hora · HF Spaces – CPU Upgrade 8 vCPU 32 GB US$0.03/hora. Los Jobs se cobran por minuto y únicamente mientras están en Starting o Running. En Spaces no existe una variante de 16 GB a US$0.01/hora; never sleep solo en hardware upgraded. Enlaces: https://huggingface.co/docs/hub/jobs-pricing · https://huggingface.co/docs/huggingface_hub/main/en/guides/jobs · https://huggingface.co/docs/hub/spaces-gpus. Para "encender cuando llega una tarea → procesar → apagar", el HF Job CPU Basic de 16 GB a US$0.01/hora sí existe oficialmente.)

## M25
No puedes crear un job que lo mantenga ensendido

## M26
Déjalo encendido en job de 16 de ram todo el tiempo encendido si detecta que hay movilidad con ai o pasa de 10gb de ram el sistema activa el siguiente HF de 16 de ram no espera lo despierta para que esté listo preparado

Pero necesito que tú uses ese procesador de 16 de ram y el chat para que no se duerma

## M27 (documentos 11 y 12 + texto)
### Documento 11 (literal, resumen de estructura)
Revisé tu repo maxbry123-commits/frontend, la Fábrica UI, el código fuente de CLI-Anything y el nuevo DeepSeek Harness/Cordis. En UI YAIWES/componentes open soure UI YAIWES/ tienes actualmente 160 entradas. La solución más rápida sería crear una Fábrica de Adaptadores YAIWES que clasifique automáticamente cada componente y le genere únicamente la envoltura que necesita.
Arquitectura: COMPONENTES OSS 160 → COMPONENT SCANNER (analiza package.json / pyproject / README / CLI / API / MCP / código) → CLASSIFIER → SKILL (instrucciones) · TOOL/API (llamada directa) · CLI HARNESS (CLI-Anything) → YAIWES ADAPTER (contrato único JSON) → CORDIS PLUGIN (DeepSeek Harness style) → TOOL · WORKFLOW · POOL → REGISTRY YAIWES → Claude / Grok / Hermes / Codex / DeepSeek / etc. Cordis monta y desmonta plugins: modelos, tools, skills, sesiones, sandboxes, almacenamiento, loops, scheduler e incluso UI.
1. No conviertas todo con CLI-Anything. CLI-Anything es para software con operaciones que un humano haría con interfaz (GIMP: clic → capa → filtro → exportar → cli-anything-gimp layer add / filter apply / export). Con React, Tailwind, Zustand o Radix UI sería innecesario.
2. 6 tipos: TIPO 1 SKILL (Anthropic Frontend Design, Awesome Design, Taste-*, Web Design Guidelines, Impeccable; salida SKILL.md) · TIPO 2 TOOL/LIBRARY (React, Tailwind, Radix UI, Lucide, GSAP, Chart.js, PixiJS, Zustand, TanStack Query, React Flow, CodeMirror, Sandpack, Shiki; salida adapter + schema + SKILL.md) · TIPO 3 CLI HARNESS (software completo con GUI; CLI-Anything + --json + SKILL.md + tests) · TIPO 4 WORKFLOW (Dagu, Hatchet, redun, Taskiq, Ray, conductor; workflow adapter) · TIPO 5 SERVICE/ENGINE (DuckDB, Qdrant, LanceDB, Meilisearch, LiteLLM, NATS, Valkey, PGlite, Typesense; service adapter) · TIPO 6 QA/VALIDATOR (Playwright, Vitest, axe-core, k6, Hypothesis, fast-check, MSW; validator tool).
3. Patrón de CLI-Anything que copiar: no reimplementa el software, usa el motor real; humano Botón → menú → diálogo → acción / agente tool(command, parameters); salida {"success": true, "result": {}, "artifacts": [], "errors": []} (modo --json); genera skills/cli-anything-<software>/SKILL.md.
4. Capa por encima: no Claude → 160 componentes; sí Claude → YAIWES COMPONENT ROUTER → animación GSAP · gráfico Chart.js · editor CodeMirror · drag/drop SortableJS · diseño Frontend Design Skill · accesibilidad axe-core · navegador Playwright. El modelo ve un solo router.
5. Contrato mínimo por componente (YAML): id, name, kind, capabilities, input format json, runtime (type, package), frontend frameworks, agents skill ./SKILL.md, tests required, status installed/wired/verified. Ejemplos: gsap (tool), playwright (validator, execute adapter ./adapter.ts), webstudio (cli-harness, command cli-anything-webstudio, output json).
6. Kernel: Agent = Model + Harness. YAIWES KERNEL → REGISTRY + ROUTER → Skills · Tools · Workflows → COMPONENTS; kernel.mount("gsap") / kernel.mount("playwright") / kernel.mount("frontend-design") / kernel.mount("webstudio") / kernel.unmount("gsap"). El orden depende de dependencias declaradas.
7. SKILL "cómo hacer algo" · TOOL "ejecuta una operación" · WORKFLOW "varias operaciones ordenadas" · POOL "grupo de capacidades/agentes" · KERNEL PLUGIN "módulo instalable con tools + skills + workflows + servicios". Ejemplo PLUGIN frontend-animation: skill animation-design.md, tools gsap y framer-motion, workflow build-animation, validator playwright.
8. En el repo ya existe: YAIWES UI → AI ROUTER → ENGINE ADAPTER → motor real; src/adapters/ (workflow_definition.py, memory_adapter.py, router_adapter.py); regla "componente descargado ≠ adaptado"; componentes → revisión código → adapters → wiring → contract tests → recovery tests → E2E → evidence → VERIFIED_CLOSED. Automatizar COMPONENTE → ADAPTER → WIRING → TEST.
Repo: https://github.com/maxbry123-commits/frontend/tree/main/UI%20YAIWES · Banco: https://github.com/maxbry123-commits/frontend/tree/main/UI%20YAIWES/componentes%20open%20soure%20UI%20YAIWES
9. YAIWES COMPONENT FACTORY: 01 SCAN → 02 CLASSIFY (skill/tool/service/workflow/harness/validator) → 03 WRAP (adapter) → 04 EXPOSE (SKILL.md + tool schema + plugin manifest) → 05 VERIFY (contract test + E2E).
10. ROOT COMPONENTES → scanner → manifest.json → split → A1..A4 (C1..C8…) → verifier → YAIWES REGISTRY (pool de subagentes en paralelo).
11. CLI-Anything soporta Claude: /cli-anything <ruta-o-repo>, /refine, /test, /validate; genera agent-harness/ (SOP, CLI, core/, utils/, tests/, SKILL.md); exige tests unitarios, E2E con backend real, prueba del CLI instalado y una tarea real de un agente usando solo el CLI.
CLI-Anything: https://github.com/HKUDS/CLI-Anything · HARNESS: https://github.com/HKUDS/CLI-Anything/blob/main/cli-anything-plugin/HARNESS.md · DeepSeek Harness: https://github.com/deepseek-ai/deepseek-harness · oficial: https://www.deepseek.com/harness/en/
12. Instrucción operativa: Trabaja sobre https://github.com/maxbry123-commits/frontend · RUTA FUENTE: UI YAIWES/componentes open soure UI YAIWES/ · OBJETIVO: convertir cada componente en capacidad agent-native de YAIWES sin reimplementar y sin convertir innecesariamente a CLI. PROCESO OBLIGATORIO: 1 escanear todo; 2 inspeccionar código fuente, package.json/pyproject/manifest, README, API pública, CLI, MCP, funciones exportadas, tests, runtime; 3 clasificar en SKILL, TOOL, SERVICE, WORKFLOW, CLI_HARNESS, VALIDATOR, SANDBOX, STORAGE, UI_COMPONENT; 4 no crear CLI si ya tiene API/librería; 5 CLI-Anything solo para software completo (fuentes obligatorias arriba); 6 adapter mínimo con id, name, kind, capabilities, inputs, outputs, dependencies, runtime, execute, health, version; 7 SKILL.md (qué hace, cuándo usarlo, cómo llamarlo, parámetros, ejemplos, errores); 8 JSON estructurado entrada/salida; 9 registry central component-registry.json (solo registra y descubre); 10 Component Router INPUT → capability → registry → selección → adapter → ejecución; 11 pools sin duplicar código (frontend-design, frontend-components, animation, code-editor, browser-testing, accessibility, data, storage, workflow, sandbox); 12 workflows compuestos con tools existentes; 13 plugins estilo DeepSeek Harness/Cordis, montar/desmontar/reemplazar sin modificar el kernel; 14 no reemplazar el kernel YAIWES, integrar con adapters; 15 procesar en paralelo con pool de subagentes; 16 contract test → integration test → E2E real → output verification; 17 VERIFIED solo si un agente completa una tarea real con el adapter; 18 nunca marcar integrado solo porque exista el archivo. Regla: COMPONENTE DESCARGADO ≠ COMPONENTE INTEGRADO. Cierre: COMPONENTE → ANALIZADO → CLASIFICADO → ADAPTER → SKILL → REGISTRY → WIRED → CONTRACT TEST → E2E → VERIFIED. SALIDA FINAL: component-registry.json, adapters/, skills/, workflows/, pools/, tests/, COMPONENT-INTEGRATION-STATE.json. No eliminar ni reescribir originales (son donors/backends); integración solo mediante adapters.

### Documento 12 (literal, 27 componentes)
1. OpenRoom https://github.com/MiniMax-AI/OpenRoom
2. Grok UI https://github.com/joeynyc/Grok-UI
3. Grok React UI https://github.com/rajkstats/grok-react-ui
4. assistant-ui https://github.com/assistant-ui/assistant-ui
5. Open Claude Design https://github.com/maxritter/open-claude-design
6. Anthropic Chatbot https://github.com/zvictor/anthropic-chatbot
7. React UI Gen https://github.com/kevin-riveros/react-ui-gen
8. Grokx https://github.com/tangf-ai/grokx
9. Grok App https://github.com/qingchencloud/grok-app
10. GrokChat https://github.com/OleksiyM/grokchat
11. Furca App https://github.com/shobitb/furca-app
12. GrokBot SDK https://github.com/Adam91holt/grokbot-sdk
13. GrokBot Shim https://github.com/codeaashu/grokbot-shim
14. Grok Build Desktop (Jane) https://github.com/Jane-o-O-o-O/grok-build-desktop
15. Grok Build Desktop (JaydenCJ) https://github.com/JaydenCJ/grok-build-desktop
16. Grok Build Desktop (Rushour0) https://github.com/Rushour0/grok-build-desktop
17. Grok Build GUI https://github.com/Jane-o-O-o-O/grok-build-gui
18. Source Intake Agent https://github.com/dskemp/source-intake-agent
19. OpenCodex https://github.com/lidge-jun/opencodex
20. ClaudeHUD https://github.com/bbdaniels/ClaudeHUD
21. clarc https://github.com/marvinrichter/clarc
22. Open Claude https://github.com/Damienchakma/Open-claude
23. Claude Artifact Viewer https://github.com/claudecraft/claude-artifact-viewer
24. FileExplorer https://github.com/conaticus/FileExplorer
25. FileBrowser https://github.com/filebrowser/filebrowser (archivado agosto 2026)
26. React Searchable Dropdown https://github.com/luciodale/react-searchable-dropdown
27. React Select https://github.com/JedWatson/react-select
Sin URL fiable (no inventar): GrokBot-main.zip, Grok-Build-Desktop-App-main.zip, minimax-agent-gui-main.zip, chat-main.zip, react-lit-combobox-main.zip.

### Texto del Director (literal)
Paso 1 📌
Anota esto 1 a 1 imput block verbartin en mis instrucciones en el archivo editalo quirúrgicamente

Paso 2 📌
Vas a descargar todos los componentes que te di en la fábrica UI con 4 auditoría que está todos los componentes en el destino . Revisando el archivo de mis instrucciones
Descarga esos comoonentes de la lista que te estoy pasando más los otros que tienes en el archivo de mis instrucciones de archivos que hiciste divudelony crea varios motores de descarga

Paso 2.1. 📌 Revisa para no repetir componentes la raíz y revisa que Claude code y los agentes que te di estan en el repo de la raíz del chat descargados te di varios diamon y otos

Ruflo
Ruflo — probablemente el "Rufo" que mencionas. Es un meta-harness alrededor de Claude Code, Codex, Hermes y otros: swarms, coordinación de agentes, memoria adaptativa, aprendizaje, loops, sandboxes, federación entre máquinas y guardrails. En tu chat: botón Swarm, selector 1/3/5/N workers, memoria, coordinación y estado de cada nodo.
Microflujo: Chat → Ruflo → swarm → memoria/coordinar/verificar → resultado
URL: https://github.com/ruvnet/ruflo

Ejecuta las instrucciones del paso 1 al pie de la letras sin cambiar nada de mis instrucciones

Paso 3 📌
Reliza las mejoras finales para integrar todo la fábrica de UI INTERFACE en el repo de agentes íntegras todo usando mis instrucciones
1. Crea una integración automatizada Integración con CLI-Anything y harnes de deepsek
Crea un motor micro kernel de integración automática que al darle un componente nuevo ejecuta las misma instalaciones de integración que te di usa primero el motores de descarga y extracción y luego usa
CLI-Anything y harnes de deepsek y integra solo si nuevo Componente hace test que está bien integrado
Lo conectas al router y lo activas y vas probando a ver cómo funciona y corrige los Gaps para ser un sistema avanzado automatizado colocale un motor de arranque que reciba una URL y ejecute la descarga y integración de manera automática y que también conveirta los skills en code ejecutable no en en solo skills de información es decir que solo puede convertir en un shema y en un code ejecutable analiza cómo hacerlo

Paso 4 📌
Encadena a rouwboat como osquestador principal y una cadena secuencial de trabajo y ruflo para el flujo
Claude code diseña
Grock agente ejecuta mejoras
Claude code revisa y mejora
Los 4 agentes de meta mejoran lo ejecutado

Paso 5 📌 añade uno o 3 chat diferentes al vecel de la lista que te pase lo descargas en el vercel como no sabes trabajar en el chat incluir los botones en un code de componente open soure si no sabes lo dejas así solo enruta a los agente que te dije de la manera que te dije que el osquestador mantenga eso y me cableas el archivo del chat y del panel al orquestas por medio de un archivo para que ejecute puede ser memoria.md o tipo Claude.md y le pones un plan simplificado de el panel y de el chat que yo quiero
Y asegúrate que el sistema y los programas de almacenamiento y de memoria está bien diseñado con todos los componentes y cableado y conectado al chat
Y al router

Dime si entiendes los 5 pasos son tareas simple no necesitas saber tanto de programación es descragar Componentes cablear y conectar cuando mucho el sistema de micro kernel de la fábrica pero ya tienes parte del trabajo hecho …

Dime si lo entiendes si hay dudas crea el modo plan DSL Dag shema para que no alucines …

## M28 (documento 13 + respuestas)
### Documento 13 (literal, resumen de estructura: Devin CLI ↔ Router YAIWES)
Jev Gateway demostró que Devin CLI (3000.11.3) tiene WINDSURF_API_SERVER_URL que redirige su tráfico de inferencia a un gateway local; Devin usa Connect RPC + protobuf (POST /exa.api_server_pb.ApiServerService/GetChatMessage); el gateway decodificó mensajes y construyó una respuesta válida que Devin ejecutó. Hoy: Devin → Jev Gateway → decisión de tool → Cognition backend (no reemplaza Cognition). Posible: DEVIN CLI → Connect RPC/protobuf → DEVIN-YAIWES BRIDGE (transforma protocolo) → Router YAIWES /v1 → DeepSeek / HF / Qwen → respuesta OpenAI → protobuf → DEVIN CLI. Limitación: Devin es propietario; "Devin Brain" queda en Cognition; configuración normal sin baseUrl/apiKey BYOK (codex-router issue 270). Niveles: 1 oficial Devin → Cognition ✅; 2 comunidad Devin → gateway → Cognition ✅ demostrado; 3 Devin → bridge → YAIWES Router ⚠ plausible, ❌ sin implementación pública verificada. ACP controla sesión/tarea/progreso/permisos/filesystem/terminal; el bridge controla qué LLM responde. DEVIN_API_URL es auth/handoff (distinto). No modificar el binario. Se puede descargar y ejecutar el binario de Devin CLI localmente; no el código fuente. Estructura: GitHub YAIWES (devin-yaiwes-bridge/, staff-registry/, router/, config/) → Devin CLI instalado → Bridge → Router YAIWES → tus APIs. Siguiente paso técnico: construir y probar Devin protobuf ↔ Router YAIWES OpenAI-compatible.
URLs: https://github.com/vinilana/jev-gateway · https://github.com/duolahypercho/codex-router/issues/270 · https://github.com/duolahypercho/codex-router · https://github.com/agentclientprotocol/agent-client-protocol · https://github.com/CognitionAI/devin-cli · https://devin.ai/cli · https://github.com/openclaw/acpx · https://github.com/phenasdev/devin-mcp-bridge · paquetes beta @cognition-ai/harness-devin y @cognition-ai/sdk (no publicados como OSS completo).

### Texto del Director (literal)
P1 los agente de meta están en mismo repo ya descargados son hay uno que puede entrar y navegar en la web y hacer capture de pantalla para revisar el fromtend necesito que lo busques y me enseñas los 4 agentes y si no buscás en las descargas o en los archivos de claude notas revisa mis instrucciones lo mencionan los 4 agentes de meta y como funcionan y olvida diamon

P3 no se usan api de antropy se conecta a mi router o no entendiste?

Coloca ahora mismo
Las api de Nvidia de primero si no responde o está ocupado va saltando a la siguiente 4 api de Nvidia o cerebras o groq y por último a deepsek v4 flash

P3 en la misma fábrica de UI INTERFACE creas todo lo único que va en el repo de router universal inteligente es lo de el chat y lo agente en una sola raíz como te dije oragniza el repo

P4 si

P5 ellos son agentes open soure idiota que están en el repo descargados tu solo conectas al router

Búscalo y dime si tienes todo claro

(Texto pegado de otra sesión: Los 4 agentes de Meta — Muse Code (muse-code-sdk: el programador, lee el repo, mantiene sesión, escribe y prueba código) · Muse Glimmer (meta-oss-cookbook agentic-fundamentals: plan → herramienta → resultado → corrige → sigue) · MetaCua (meta-model-cookbook 13_macos_cua: mira capturas de pantalla y actúa por coordenadas) · CUA + MCP (meta-model-cookbook 12_computer_use: navegador/escritorio aislado donde se ejecuta de verdad). En agents-yaiwes/donors/ con MANIFEST.json; solo descargados como referencia, no conectados al Router.)

El conector tuyo siempre se conecta revisa si resolviste lo de la permanencia del procesador activo de 16 de ram permanente o usa el HF token full acceso para resolverlo para no estar cada rato reconectandote tu plugins

Analiza todo y escribe en el archivo mis instrucciones 1 a 1 imput block verbartin

Si tienes dudas preguntas

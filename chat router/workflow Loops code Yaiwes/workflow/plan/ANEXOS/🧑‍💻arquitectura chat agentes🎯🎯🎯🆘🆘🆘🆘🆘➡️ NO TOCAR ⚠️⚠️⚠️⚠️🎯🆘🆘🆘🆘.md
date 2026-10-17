Procesó durante 47s

Sí. La arquitectura que describes tiene bastante sentido, y no sería simplemente “otro RAG”. Sería una capa independiente que investiga antes de que la LLM razone, controla qué evidencia recibe, y vuelve a investigar después para verificar el trabajo.

Hay antecedentes que validan cada pieza: CRAG evalúa la calidad de lo recuperado y dispara búsqueda adicional cuando la evidencia es débil; RARR investiga después de una generación y la corrige con evidencia; SAFE divide una respuesta en afirmaciones y busca evidencia para cada una; RAGChecker separa métricas de recuperación y generación; y OpenAI recomienda evaluar también el trace completo —herramientas escogidas, handoffs, instrucciones y resultado—, no solamente la respuesta final. 

La estructura que usaría

La llamaría provisionalmente:
.
YAIWES Evidence/Search Gate

Microflujo transversal:
.
INPUT
  → PARSER DETERMINISTA
  → 12 GOALS DE ENTRADA
  → COMPILADOR DE BÚSQUEDAS
  → MOTORES DE BÚSQUEDA
  → EXTRACTOR EXACTO
  → RANK/FUSIÓN
  → EVIDENCE PACK
  → [LLM FILTRO opcional]
  → LLM/AGENTE EJECUTOR
  → RESULTADO
  → DESCOMPONEDOR DE RESULTADO
  → BÚSQUEDA DE VERIFICACIÓN
  → 12 GOALS DE SALIDA
  → VERIFIER/SHERIFF
       ├─ PASS → FINAL
       ├─ INCOMPLETE → BUSCAR MÁS
       ├─ CONTRADICTION → CORREGIR
       └─ FAIL → REEJECUTAR

La diferencia fundamental es que la LLM ya no empieza investigando a ciegas.

Primero recibe un paquete pequeño y estructurado de evidencia.

Anthropic recomienda precisamente mantener el contexto con la menor cantidad posible de información de alta señal y recuperar información just in time en vez de inundar el contexto del agente. 


---

1. Input Parser sin IA

Esta pieza no necesita una LLM.

Recibe:

"Instala OmniRoute en HF Space Docker,
usa CPU 32 GB,
no uses GitHub Actions,
verifica que funcione la API."

Y mediante reglas, expresiones regulares, diccionarios y esquemas extrae:

task_type: deploy
targets:
  - OmniRoute
  - Hugging Face Space

requirements:
  - Docker
  - API funcionando

constraints:
  - CPU: 32GB

forbidden:
  - GitHub Actions

verification:
  - endpoint responde

Puedes tener categorías conocidas:

SEARCH
INSTALL
DOWNLOAD
EXTRACT
DEPLOY
MODIFY_CODE
DEBUG
TEST
COMPARE
AUDIT
RESEARCH
VERIFY

Si coincide con una regla conocida:

0 LLM.

Solo si el input es ambiguo:

RULE ROUTER → UNKNOWN
                 ↓
             LLM pequeña
                 ↓
           JSON normalizado

Es decir, la LLM es fallback, no cerebro obligatorio del input.


---

2. Compilador de búsquedas determinista

Aquí está una de las partes más importantes.

No preguntas a una LLM:

> “¿Qué debería buscar?”



Tienes plantillas.

Por ejemplo, para:

task_type: deploy
technology: OmniRoute
platform: Hugging Face

se generan automáticamente:

"OmniRoute" Docker official
"OmniRoute" installation
"OmniRoute" Hugging Face
"OmniRoute" Dockerfile
"OmniRoute" port
"OmniRoute" environment variables
site:github.com "OmniRoute" Dockerfile
site:huggingface.co/docs Spaces Docker

Para DEBUG:

"{exact_error}"
"{exact_error}" github
"{component}" "{exact_error}"
"{component}" issue
"{component}" troubleshooting

Para VERSION:

"{package}" latest release
site:github.com "{package}" releases
"{package}" changelog

Por tanto:

Input → variables → plantilla → búsquedas.

No hace falta razonamiento generativo.


---

3. Fan-out a varios motores

No dependas de un único buscador.

┌→ Motor web A
QUERY COMPILER ───┼→ Motor web B
                  ├→ GitHub Search
                  ├→ documentación
                  ├→ issues/discussions
                  └→ búsqueda local/repos

Después normalizas todo:

{
  "query": "...",
  "source": "...",
  "url": "...",
  "title": "...",
  "date": "...",
  "snippet": "...",
  "source_type": "official|code|issue|community",
  "retrieved_at": "..."
}


---

4. Extractor exacto sin LLM

Esto también puede ser completamente determinista.

En lugar de pasar una página de 20.000 tokens a la IA:

HTML
 ↓
eliminar navegación/publicidad
 ↓
separar por títulos/párrafos/code blocks
 ↓
buscar términos/identificadores
 ↓
ventanas de contexto
 ↓
top fragments

Ejemplo:

Buscas:

space_hardware cpu-upgrade

Y guardas solamente:

{
  "source": "HF official docs",
  "heading": "Hardware",
  "exact_fragment": "...",
  "matched_terms": [
    "space_hardware",
    "cpu-upgrade"
  ]
}

Así reduces muchísimo tokens.


---

5. Ranking sin IA

Puedes hacer bastante sin embeddings ni LLM.

Una fórmula simple:

SCORE =
 exact_match
 + BM25
 + source_authority
 + recency
 + identifier_match
 + corroboration
 - duplication
 - stale_penalty

Y después usar Reciprocal Rank Fusion para fusionar varios motores.

Por ejemplo:

Fuente oficial            +30
Código fuente             +25
Release/changelog          +20
Issue mantenedor           +15
Comunidad                  +10

Coincidencia exacta        +20
Dos fuentes coinciden      +15
Información reciente       +10

El resultado serían solamente los mejores fragmentos.

Anthropic, por ejemplo, ha encontrado ventajas al combinar recuperación lexical como BM25 con otras señales de contexto; lo importante para tu caso es que BM25 puede funcionar sin una LLM en tiempo de consulta. 


---

6. Evidence Packet

Esta sería una pieza central de YAIWES.

La LLM no recibe resultados brutos de Google/GitHub.

Recibe algo así:

{
  "task": {...},

  "known_facts": [
    {
      "fact": "...",
      "source": "...",
      "evidence": "...",
      "confidence": 0.98
    }
  ],

  "requirements": [...],

  "constraints": [...],

  "conflicts": [],

  "unknown": [...],

  "sources": [...]
}

Microflujo:

100 resultados
    ↓
40 páginas
    ↓
120 fragmentos
    ↓
ranking
    ↓
15 fragmentos
    ↓
Evidence Packet ~2K–8K tokens
    ↓
LLM

Esto encaja directamente con el principio de context compaction: conservar decisiones, hechos y contexto importante mientras se elimina ruido. 


---

7. LLM filtro opcional

Aquí sí utilizaría una LLM pequeña.

Pero no para investigar.

Solo:

Evidence Pack
     ↓
LLM FILTER
     ↓
RELEVANTE
NO RELEVANTE
CONTRADICTORIO
FALTA INFORMACIÓN

Salida obligatoria:

{
  "use": ["E03", "E07", "E11"],
  "reject": ["E02", "E05"],
  "missing": [
    "puerto real del servidor"
  ]
}

Si falta información:

missing
 ↓
Query Compiler
 ↓
Search
 ↓
Evidence Pack

Ese es tu primer LOOP.


---

8. Ejecuta el agente

Ahora sí:

CONTRATO
+
INPUT
+
EVIDENCE PACK
+
TOOLS
       ↓
      LLM
       ↓
    EXECUTOR

La LLM razona sobre información que ya fue encontrada y filtrada.


---

9. Segunda búsqueda: verificación posterior

Esta es probablemente la parte más potente de tu idea.

Una vez termina el agente, no aceptas su afirmación de que terminó.

Se genera:

resultado
   ↓
claims/actions extractor

Ejemplo:

claims:
  - OmniRoute fue instalado.
  - El puerto es 7860.
  - HF Space está RUNNING.
  - /v1/models responde.
  - no se usó GitHub Actions.

Entonces cada claim genera búsquedas/comprobaciones.

CLAIM 1 → comprobar archivos/deployment
CLAIM 2 → comprobar configuración
CLAIM 3 → consultar HF
CLAIM 4 → HTTP test
CLAIM 5 → revisar trace/logs

SAFE utiliza una idea muy parecida para factualidad: divide una salida larga en afirmaciones individuales y realiza búsquedas para determinar cuáles están respaldadas. 

RARR aplica el patrón complementario:

generar → investigar → encontrar evidencia → revisar/corregir. 


---

Tus 12 Goals

Yo haría los mismos 12 gates tanto antes como después:

#	Goal	Antes de ejecutar	Después de ejecutar

G01	Objetivo	¿Qué pidió exactamente?	¿Se consiguió exactamente?
G02	Entidades	¿Qué proyecto/version/ruta?	¿Se trabajó sobre esas mismas?
G03	Restricciones	¿Qué está prohibido?	¿Se respetó todo?
G04	Dependencias	¿Qué necesita funcionar?	¿Funcionan realmente?
G05	Fuente oficial	¿Existe documentación oficial?	¿Resultado coincide con ella?
G06	Versión	¿Cuál es la versión vigente?	¿Se usó la correcta?
G07	Configuración	¿Qué configuración necesita?	¿Está configurada así?
G08	Integración	¿Con qué debe conectarse?	¿Está realmente conectado?
G09	Ejecución	¿Qué debe ejecutar?	¿Se ejecutó?
G10	Tests	¿Cómo demostramos PASS?	¿Pasaron las pruebas?
G11	Contradicciones	¿Las fuentes discrepan?	¿Aparecieron contradicciones?
G12	Evidencia	¿Tenemos evidencia suficiente?	¿Podemos demostrar el cierre?


Y cada Goal tendría sus queries predeterminadas.

Por ejemplo G06:

goal: G06_VERSION

input_queries:
  - '"{component}" latest release'
  - 'site:github.com "{component}" releases'
  - '"{component}" changelog'

output_checks:
  - installed_version == verified_version

Esto convierte tus Goals en programas de búsqueda, no solo instrucciones escritas.


---

El LOOP completo

Yo lo montaría finalmente así:

YAIWES SEARCH / EVIDENCE LAYER

INPUT
  │
  ▼
[01 PARSER]
  │
  ▼
[02 12 INPUT GOALS]
  │
  ▼
[03 QUERY COMPILER]
  │
  ▼
[04 SEARCH FANOUT]
  │
  ▼
[05 EXTRACT + RANK]
  │
  ▼
[06 EVIDENCE PACK]
  │
  ├── evidence weak ──────────────┐
  │                               │
  ▼                               │
[07 OPTIONAL LLM FILTER]          │
  │                               │
  ▼                               │
[08 EXECUTOR]                     │
  │                               │
  ▼                               │
[09 OUTPUT CLAIMS]                │
  │                               │
  ▼                               │
[10 VERIFY SEARCH]                │
  │                               │
  ▼                               │
[11 12 OUTPUT GOALS]              │
  │                               │
  ▼                               │
[12 SHERIFF]
  │
  ├─ PASS ───────────────→ FINAL
  │
  ├─ NEED_EVIDENCE ──────────────┘
  │
  ├─ FIXABLE → EXECUTOR
  │
  └─ FAIL → REPLAN

Lo que considero especialmente bueno de tu planteamiento

No usaría la LLM para todo.

Separaría:

Determinista
────────────
parsear
generar queries
buscar
deduplicar
rankear
extraer
comprobar versiones
HTTP tests
tests de código
comparar hashes
comprobar archivos
validar schemas
12 gates

LLM
───
entender ambigüedad
seleccionar evidencia dudosa
razonar
programar
resolver contradicciones
proponer corrección

Eso hace que la IA sea el razonador, no el buscador, base de datos, router, verificador y juez al mismo tiempo.

Y añadiría una regla fundamental:

> La misma LLM que ejecutó no puede cerrar el trabajo únicamente por su propia opinión.



El cierre debería venir de:

pruebas deterministas + búsqueda posterior + Evidence Pack + 12 Goals + Sheriff.

OpenAI llega a una conclusión compatible para evaluación de agentes: conviene puntuar los traces completos, incluyendo selección de herramienta, handoffs y cumplimiento de instrucciones, además del resultado final. 

Yo sí integraría esta capa delante de tu Router YAIWES. En realidad puede convertirse en el componente transversal que alimente a Hermes, Claude, Codex, OpenClaw o cualquier otro agente con el mismo Evidence Packet, y luego usar exactamente el mismo sistema para auditar su salida.

Procesó durante 34s

Sí. Te dejo 20 páginas útiles para investigar programación, agentes, errores reales, APIs y experiencias de desarrolladores. Las primeras cinco son las comunidades oficiales que pediste. Anthropic confirma que su Discord de desarrolladores es uno de sus canales oficiales para API/Claude Code; OpenAI, Cursor, GitHub y Hugging Face mantienen sus propios foros técnicos. 

1. Anthropic / Claude Developers Discord — Claude Code, API, MCP, agentes y SDK.
[https://anthropic.com/discord](https://anthropic.com/discord?utm_source=chatgpt.com)


2. OpenAI Developer Community — API, Codex, agentes, modelos, bugs y experiencias.
[https://community.openai.com/](https://community.openai.com/?utm_source=chatgpt.com)


3. Cursor Community Forum — bugs, agentes, modelos, workflows y comparaciones de coding agents.
[https://forum.cursor.com/](https://forum.cursor.com/?utm_source=chatgpt.com)


4. GitHub Community Discussions — preguntas técnicas sobre GitHub, Actions, Copilot, repositorios, APIs, etc.
[https://github.com/orgs/community/discussions](https://github.com/orgs/community/discussions?utm_source=chatgpt.com)


5. Hugging Face Forums — modelos, Spaces, Jobs, inference, Transformers, entrenamiento y deployment.
[https://discuss.huggingface.co/](https://discuss.huggingface.co/?utm_source=chatgpt.com)


6. Claude Code GitHub Issues — especialmente útil para descubrir bugs reales, límites, regresiones y soluciones de Claude Code. Actualmente tiene miles de issues públicos. 
[https://github.com/anthropics/claude-code/issues](https://github.com/anthropics/claude-code/issues?utm_source=chatgpt.com)


7. Claude Code Action Discussions — automatización de Claude dentro de GitHub y CI.
[https://github.com/anthropics/claude-code-action/discussions](https://github.com/anthropics/claude-code-action/discussions?utm_source=chatgpt.com)


8. Stack Overflow — probablemente el mejor buscador de problemas concretos de programación y errores.
[https://stackoverflow.com/](https://stackoverflow.com/?utm_source=chatgpt.com)


9. Software Engineering Stack Exchange — arquitectura, patrones, diseño de sistemas y decisiones de ingeniería.
[https://softwareengineering.stackexchange.com/](https://softwareengineering.stackexchange.com/?utm_source=chatgpt.com)


10. Hacker News — desarrolladores, nuevas herramientas, agentes, modelos y análisis técnicos.
[https://news.ycombinator.com/](https://news.ycombinator.com/?utm_source=chatgpt.com)


11. DEV Community — artículos y discusiones de programadores sobre prácticamente cualquier stack.
[https://dev.to/](https://dev.to/?utm_source=chatgpt.com)


12. Hashnode — blogs técnicos escritos principalmente por desarrolladores; muy útil para implementaciones concretas.
[https://hashnode.com/](https://hashnode.com/?utm_source=chatgpt.com)


13. Lobsters — comunidad más pequeña y técnica centrada en ingeniería de software, sistemas y lenguajes.
[https://lobste.rs/](https://lobste.rs/?utm_source=chatgpt.com)


14. Reddit / r/LocalLLaMA — excelente para modelos locales, inference, agentes, benchmarks, cuantización y experimentos. Hay discusiones recientes específicamente sobre coding agents. 
[https://www.reddit.com/r/LocalLLaMA/](https://www.reddit.com/r/LocalLLaMA/?utm_source=chatgpt.com)


15. Reddit / r/ClaudeCode — Claude Code, subagentes, hooks, MCP, límites y configuraciones reales.
[https://www.reddit.com/r/ClaudeCode/](https://www.reddit.com/r/ClaudeCode/?utm_source=chatgpt.com)


16. Reddit / r/programming — noticias y discusiones generales de programación.
[https://www.reddit.com/r/programming/](https://www.reddit.com/r/programming/?utm_source=chatgpt.com)


17. Reddit / r/ExperiencedDevs — discusiones de ingeniería desde la perspectiva de desarrolladores con experiencia.
[https://www.reddit.com/r/ExperiencedDevs/](https://www.reddit.com/r/ExperiencedDevs/?utm_source=chatgpt.com)


18. freeCodeCamp Forum — problemas de código, web, JavaScript, Python, backend y aprendizaje práctico.
[https://forum.freecodecamp.org/](https://forum.freecodecamp.org/?utm_source=chatgpt.com)


19. GitHub Code Search — no es solo comunidad: sirve para encontrar cómo otros proyectos implementaron realmente una función en código fuente.
[https://github.com/search](https://github.com/search?utm_source=chatgpt.com)


20. Hugging Face Hub — para buscar código, modelos, Spaces, repositorios y ejemplos ejecutables; conviene combinarlo con el foro de HF.
[https://huggingface.co/](https://huggingface.co/?utm_source=chatgpt.com)



Para investigaciones como las que estamos haciendo sobre Devin, Manus, Claude Code, Codex, Cursor, OpenClaw, Hermes y nuevos agentes, yo cruzaría principalmente GitHub Issues/Discussions + Reddit + Hacker News + foro oficial del producto. Eso permite separar lo que dice la empresa de lo que realmente están viendo los desarrolladores.

Procesó durante 32s

Sí. Y para que funcione de verdad, OpenClaw y Hermes no deberían actualizar cinco archivos distintos directamente. Deben hablar con un único State Hub de YAIWES; ese núcleo actualiza STATE.json, Crazy Wall, bitácora, handoff y la persistencia de cada tarea.

Hermes ya tiene persistencia propia de sesiones en SQLite y puede cargar instrucciones del proyecto desde .hermes.md/AGENTS.md; además puede conectarse a tu State Hub mediante MCP.  OpenClaw también mantiene sesiones persistentes y memoria en Markdown, y su heartbeat puede despertar periódicamente al agente para revisar cambios y avisarte. 

Yo lo organizaría así:

TÚ / CHAT
                            │
                     ROWBOAT DIRECTOR
                            │
                ┌───────────┴───────────┐
                │                       │
            OPENCLAW                 HERMES
        Guardian/Sentinel         Planner/Reviewer
                │                       │
                └───────────┬───────────┘
                            │
                     YAIWES STATE HUB
                            │
       ┌────────────┬───────┼─────────┬────────────┐
       ↓            ↓       ↓         ↓            ↓
 CRAZY_WALL     STATE.json BITÁCORA HANDOFF.md  PROJECTS/
       │                                         │
       │                              ┌──────────┴──────────┐
       │                              ↓                     ↓
       │                         PROJECT-001/          PROJECT-002/
       │                              │
       │                     ┌────────┴────────┐
       │                     ↓                 ↓
       │                 TASK-001/         TASK-002/
       │
       ↓
     RUFLO
 Orquesta colmena
       ↓
Claude → Grok → Claude → Meta×4

La raíz central puede ser muy sencilla:

.yaiwes/
├── STATE.json
├── CRAZY_WALL.json
├── BITACORA.jsonl
├── HANDOFF.md
│
├── projects/
│   └── factory-ui/
│       ├── PROJECT.json
│       ├── PROJECT.md
│       ├── STATE.json
│       ├── HANDOFF.md
│       ├── DECISIONS.jsonl
│       │
│       └── tasks/
│           ├── UI-001/
│           │   ├── TASK.json
│           │   ├── STATE.json
│           │   ├── HANDOFF.md
│           │   ├── EVIDENCE.json
│           │   └── EVENTS.jsonl
│           │
│           └── UI-002/
│               └── ...
│
└── mirrors/
    ├── UI-001/
    └── UI-002/

1. STATE.json: la fotografía actual

No guarda todo el historial. Solo responde:

> ¿Qué está pasando ahora?



Por ejemplo:

{
  "schema": "yaiwes.state/v1",
  "revision": 1847,
  "updated_at": "2026-09-26T21:15:00-05:00",

  "active_project": "factory-ui",

  "projects": {
    "factory-ui": {
      "status": "RUNNING",
      "progress": 68,

      "active_tasks": [
        "UI-001",
        "UI-004"
      ],

      "blocked_tasks": [
        "UI-007"
      ]
    }
  },

  "agents": {
    "openclaw": {
      "role": "guardian",
      "status": "WATCHING"
    },

    "hermes": {
      "role": "planner_reviewer",
      "status": "REVIEWING"
    },

    "ruflo": {
      "role": "orchestrator",
      "status": "RUNNING"
    }
  }
}


---

2. Crazy Wall: quién está haciendo qué

Aquí pondría tu regla de:

1 CHAT = 1 NODO ACTIVO

Y cada claim conserva exactamente la identidad del trabajo:

{
  "schema": "yaiwes.crazy-wall/v1",

  "nodes": {
    "UI-001": {
      "status": "CLAIMED",

      "project": "factory-ui",
      "task": "touch-mobile",

      "chat_id": "chat-834",
      "agent_name": "grok-executor",
      "node_id": "UI-001",

      "base_sha": "abc123",

      "write_scope": [
        "Frontend/factory-v0/src/editor/**"
      ],

      "paths": [
        "Frontend/factory-v0/"
      ],

      "claimed_at": "2026-09-26T21:02:00-05:00",

      "heartbeat_at": "2026-09-26T21:14:00-05:00",

      "phase": "IMPLEMENT",

      "next": "CLAUDE_REVIEW"
    }
  }
}

Así Hermes sabe:

> “Grok está modificando UI-001; no debo crear otro agente sobre ese mismo scope.”



Y OpenClaw sabe:

> “El heartbeat lleva demasiado tiempo sin cambiar; debo avisar o pedir recuperación.”



Esto encaja directamente con el esquema Crazy Wall que ya vienes usando para claims y scopes.


---

3. La BITÁCORA debe ser inmutable

Aquí está una mejora importante.

No hagas que los agentes reescriban la bitácora.

Usa:

BITACORA.jsonl

Cada línea es un evento:

{"seq":1841,"type":"TASK_CREATED","project":"factory-ui","task":"UI-001","actor":"rowboat"}
{"seq":1842,"type":"PLAN_CREATED","task":"UI-001","actor":"claude-code"}
{"seq":1843,"type":"TASK_CLAIMED","task":"UI-001","actor":"grok"}
{"seq":1844,"type":"FILES_CHANGED","task":"UI-001","actor":"grok","count":4}
{"seq":1845,"type":"REVIEW_STARTED","task":"UI-001","actor":"claude-code"}
{"seq":1846,"type":"REVIEW_PASS","task":"UI-001","actor":"claude-code"}
{"seq":1847,"type":"META_QA_STARTED","task":"UI-001","actor":"ruflo"}

Esto te da algo parecido a event sourcing:

BITÁCORA
   ↓
reducer
   ↓
STATE.json

Por eso si STATE.json se daña:

BITACORA.jsonl
       ↓
   reconstruir
       ↓
nuevo STATE.json


---

4. Sí: archivo persistente por CADA tarea

Esta parte sí te la recomiendo.

Por ejemplo:

tasks/UI-001/TASK.json

{
  "schema": "yaiwes.task/v1",

  "id": "UI-001",
  "project": "factory-ui",

  "objective":
    "Resolver touch coordinate miss en móvil",

  "status": "RUNNING",

  "phase": "GROK_EXECUTION",

  "created_by": "rowboat",

  "team": {
    "architect": "claude-code",
    "executor": "grok",
    "reviewer": "claude-code",

    "qa": [
      "meta-code",
      "meta-tests",
      "meta-visual",
      "meta-adversarial"
    ],

    "guardian": "openclaw",
    "planner_supervisor": "hermes",
    "orchestrator": "ruflo"
  },

  "acceptance": [
    "touch móvil funciona",
    "desktop no tiene regresión",
    "tests pasan",
    "QA visual pasa"
  ],

  "dependencies": [],

  "mirror": "mirrors/UI-001",

  "base_sha": "abc123",

  "current_sha": "def456",

  "attempt": 2,

  "next_action": "CLAUDE_REVIEW"
}

Esto hace que una tarea sobreviva a:

reinicio
caída
nuevo chat
otro agente
cambio de modelo
compacción del contexto

Porque la tarea no existe en la cabeza de la LLM.

Existe en disco.


---

5. HANDOFF.md: para pasar el trabajo

STATE.json está pensado para máquinas.

HANDOFF.md está pensado para que el siguiente agente entienda la tarea inmediatamente.

Ejemplo:

# HANDOFF UI-001

Proyecto: factory-ui
Estado: RUNNING
Fase: CLAUDE_REVIEW

## Objetivo
Resolver TOUCH_COORDINATE_MISS móvil.

## Trabajo realizado
Grok modificó:
- pointer-events.ts
- canvas.ts
- touch-adapter.ts

## Evidencia
Desktop: PASS
Mobile: pendiente
Tests unitarios: PASS

## Problema actual
El canvas recibe touchstart pero las coordenadas
no se transforman correctamente después del zoom.

## Siguiente responsable
Claude Code

## Acción
Revisar el diff de Grok.
Si encuentra problema:
GROK_FIX.
Si pasa:
META_QA.

Pero no lo escribiría manualmente desde cada agente.

El State Hub lo genera a partir de:

TASK.json
+
STATE.json
+
últimos EVENTS
+
EVIDENCE
=
HANDOFF.md


---

6. PROJECT.md: memoria del proyecto

No pongas toda la información del proyecto dentro de HANDOFF.md.

Haz:

PROJECT.md

con cosas estables:

# Factory UI

## Objetivo
Editor visual YAIWES.

## Arquitectura
...

## Reglas
- No romper desktop.
- Mobile debe probarse.
- No cerrar sin evidencia.
- SHA probado = SHA publicado.

## Comandos
...

## Componentes
...

## Rutas críticas
...

Esto es particularmente útil para Hermes porque Hermes carga archivos de contexto del proyecto como .hermes.md, AGENTS.md, CLAUDE.md y otros archivos compatibles al iniciar una sesión. 

Puedes generar:

.hermes.md

muy pequeño:

# Hermes Project Bootstrap

Fuente de verdad:
.yaiwes/projects/factory-ui/

Antes de planificar:
1. leer PROJECT.md
2. leer STATE.json
3. leer HANDOFF.md
4. consultar tareas activas mediante MCP
5. no modificar STATE.json directamente


---

7. OpenClaw funciona como Guardian persistente

OpenClaw tiene una ventaja especialmente buena para esto: su heartbeat.

Puede revisar periódicamente:

STATE
Crazy Wall
tareas RUNNING
tareas STALLED
errores
claims vencidos
handoffs pendientes

y si no pasa nada:

NO_REPLY

Si pasa algo importante:

OpenClaw:
UI-001 lleva 38 minutos sin heartbeat.
Grok conserva el claim.
No hay commit nuevo.
Recomiendo RECOVER o REASSIGN.

El heartbeat de OpenClaw está diseñado precisamente para ejecutar turnos periódicos y puede enviar alertas al operador; también admite eventos que despiertan el agente inmediatamente. 

Pero no utilizaría MEMORY.md de OpenClaw como base de datos de proyectos. Su documentación diferencia la memoria durable y las notas diarias de la información operativa; úsala para conocimiento, no como lock manager. 


---

8. Hermes como cerebro de continuidad

Hermes también tiene su propia persistencia.

Actualmente guarda las conversaciones/sesiones y su historial en su state.db; las sesiones pueden reanudarse y buscarse posteriormente. 

Entonces tienes dos capas:

Hermes internal memory
        ↓
“qué aprendí / conversaciones”

YAIWES Project State
        ↓
“qué está ocurriendo realmente”

Nunca mezclaría las dos.

Hermes consulta el State Hub:

project = await yaiwes.get_project("factory-ui")
tasks   = await yaiwes.get_active_tasks("factory-ui")
wall    = await yaiwes.get_crazy_wall("factory-ui")

Después planifica.

Y para cambiar algo:

await yaiwes.append_event({
    "type": "PLAN_REVISED",
    "project": "factory-ui",
    "task": "UI-001",
    "actor": "hermes",
    "payload": {...}
})


---

9. Nadie toca STATE.json directamente

Esta es quizá la regla más importante.

Incorrecto:

open("STATE.json", "w")

Correcto:

await state_hub.emit(
    actor="hermes",
    event="TASK_REVIEWED",
    task="UI-001",
    payload={
        "verdict": "PASS"
    }
)

Entonces:

class StateHub:

    async def emit(
        self,
        actor,
        event,
        project,
        task=None,
        payload=None
    ):

        record = {
            "seq": self.next_seq(),
            "actor": actor,
            "type": event,
            "project": project,
            "task": task,
            "payload": payload or {}
        }

        self.bitacora.append(record)

        self.reducer.apply(record)

        self.write_state_atomic()

        self.update_crazy_wall()

        self.generate_task_handoff(task)

        self.generate_project_handoff(project)

        return record

Ese es tu punto único de escritura.


---

10. Cómo te hablan los tres en el chat

Yo no crearía tres chats desconectados.

Crearía un Chat Bus:

Hermes ─────┐
            │
OpenClaw ───┼──→ CHAT BUS → Rowboat → TÚ
            │
Ruflo ──────┘

Un evento podría ser:

{
  "type": "CHAT_MESSAGE",

  "speaker": "openclaw",

  "project": "factory-ui",
  "task": "UI-001",

  "severity": "WARNING",

  "message":
    "El worker de Grok no ha actualizado su heartbeat."
}

Y tú ves:

[RUFLO]
Abrí UI-001 y asigné Grok como executor.

[HERMES]
Revisé el plan. Dividí el trabajo en implementación
y verificación móvil.

[OPENCLAW]
Guardian: el scope es correcto.
Voy a vigilar el worker y sus evidencias.

[GROK]
Implementación terminada. 4 archivos modificados.

[CLAUDE CODE]
Encontré una regresión. Devuelvo la tarea a Grok.

[OPENCLAW]
Estado actualizado: UI-001 → CORRECTION.

[HERMES]
La corrección mantiene el contrato original.

Pero debajo todos esos mensajes también quedan como eventos.

Así el chat no es el estado.

Es simplemente una vista humana del estado.


---

11. El ciclo completo

Te quedaría:

TÚ
 ↓
ROWBOAT
 ↓
crea PROJECT / TASK
 ↓
STATE HUB
 ↓
Crazy Wall claim
 ↓
Hermes planifica
 ↓
Claude diseña
 ↓
Ruflo organiza
 ↓
Grok ejecuta
 ↓
STATE HUB registra
 ↓
Claude revisa
 ↓
Grok corrige
 ↓
Meta ×4 verifica
 ↓
OpenClaw Guardian vigila continuamente
 ↓
Hermes valida lógica/plan
 ↓
Sheriff/Judge
 ↓
PASS
 ↓
STATE actualizado
 ↓
HANDOFF actualizado
 ↓
BITÁCORA preservada
 ↓
Crazy Wall libera nodo
 ↓
Rowboat te informa

Y cuando una tarea genera otra:

UI-001
  ↓
descubre necesidad independiente
  ↓
NEW_TASK_REQUIRED
  ↓
Ruflo NO mezcla el trabajo
  ↓
TASK UI-008
  ↓
nuevo persistent TASK.json
  ↓
nuevo Crazy Wall node
  ↓
nuevo mirror
  ↓
nuevo equipo de ingeniería

Esto te da exactamente lo que estás buscando: un solo centro de control, pero muchas tareas persistentes y equipos que pueden desaparecer/recrearse sin perder el proyecto. OpenClaw y Hermes pueden reiniciarse o cambiar de sesión y recuperar el contexto desde el Hub en lugar de depender exclusivamente de lo que recuerde la LLM.
Procesó durante 19s

Sí. Lo que describes lo haría como un pipeline de ingeniería con relevo obligatorio, no como agentes actuando todos a la vez.

Meta ya ofrece Muse Code / Muse Spark 1.3, con coordinación multiagente, un ejemplo oficial de equipo de cuatro perfiles, fan-out hacia worktrees aislados y percepción visual de screenshots/video. Eso encaja especialmente bien en tu última fase de QA.  Grok Build también soporta ejecución autónoma /goal, modo headless, subagentes y worktrees, por lo que encaja como ejecutor. 

La arquitectura

PETICIÓN
   ↓
ORQUESTADOR YAIWES
   ↓
CLAUDE CODE — ARQUITECTO
   │
   │ crea:
   │ PLAN
   │ CONTRATO
   │ TASKS
   │ ACCEPTANCE
   │ TESTS esperados
   ↓
GROK BUILD — EJECUTOR
   │
   │ implementa
   │ ejecuta
   │ prueba
   │ entrega diff + evidencia
   ↓
CLAUDE CODE — REVIEWER
   │
   ├── PASS ───────────────┐
   │                       │
   └── CORREGIR → GROK ────┘
                           ↓
                META MUSE CODE ×4
                           ↓
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   META-1 CODE        META-2 TEST       META-3 VISUAL
   auditor código     integración        navegador/UI
                                               │
                                         META-4 ADVERSARIAL
                                         busca fallos/mejora
        └──────────────────┼──────────────────┘
                           ↓
                   MUSE CODE FIXER
                           ↓
                        TESTS
                           ↓
                       SHERIFF
                           ↓
                         PASS

Los cuatro de Meta no tienen que ser cuatro productos diferentes. Puedes levantar cuatro perfiles/instancias independientes de Muse Code/Muse Spark con responsabilidades diferentes. Meta documenta precisamente el patrón de equipo de cuatro perfiles y fan-out aislado; los nombres que te propongo aquí son roles tuyos, no nombres oficiales de Meta. 

Roles exactos

TEAM = {
    "claude_architect": {
        "job": "DESIGN_ONLY",
        "write_code": False,
    },

    "grok_executor": {
        "job": "IMPLEMENT",
        "write_code": True,
    },

    "claude_reviewer": {
        "job": "REVIEW_AND_CORRECT",
        "write_code": True,
    },

    "meta_1_code": {
        "job": "CODE_REVIEW",
    },

    "meta_2_tests": {
        "job": "TEST_INTEGRATION",
    },

    "meta_3_visual": {
        "job": "VISUAL_UI_QA",
    },

    "meta_4_adversarial": {
        "job": "BREAK_FIND_IMPROVE",
    },

    "meta_fixer": {
        "job": "APPLY_META_CORRECTIONS",
    }
}

Muse Spark tiene percepción multimodal y entorno de ejecución visual, por lo que el META-3 puede recibir screenshots/video y comprobar el frontend visualmente, no limitarse a leer HTML. 


---

Lo importante: un contrato único

Todos deben trabajar sobre el mismo objeto.

job = {
    "job_id": "UI-001",

    "objective":
        "Crear editor visual con drag/drop",

    "scope": [
        "frontend/editor/"
    ],

    "acceptance": [
        "drag funciona",
        "drop funciona",
        "persistencia funciona",
        "desktop PASS",
        "mobile PASS"
    ],

    "state": "DESIGN",

    "attempt": 0,

    "evidence": [],

    "issues": []
}

Ningún agente manda mensajes libres al siguiente.

Devuelve siempre:

result = {
    "job_id": "UI-001",

    "agent": "grok_executor",

    "status": "PASS",

    "changed_files": [],

    "tests": [],

    "issues": [],

    "evidence": [],

    "next_action": "CLAUDE_REVIEW"
}

Esto evita que el contexto se convierta en una conversación gigantesca.


---

Workflow ejecutable

El motor central sería aproximadamente así:

class EngineeringLoop:

    def __init__(
        self,
        claude,
        grok,
        meta_team,
        mirror_manager
    ):
        self.claude = claude
        self.grok = grok
        self.meta = meta_team
        self.mirrors = mirror_manager

    async def run(self, request):

        # ====================================
        # 1. CLAUDE DISEÑA
        # ====================================

        design = await self.claude.design(
            objective=request["objective"],
            system=request["system"]
        )

        job = {
            **request,
            "design": design,
            "state": "EXECUTION"
        }

        # ====================================
        # 2. GROK EJECUTA
        # ====================================

        grok_result = await self.grok.execute(job)

        # ====================================
        # 3. CLAUDE REVISA → GROK CORRIGE
        # ====================================

        for attempt in range(3):

            review = await self.claude.review(
                design=design,
                result=grok_result
            )

            if review["status"] == "PASS":
                break

            grok_result = await self.grok.correct(
                job=job,
                review=review
            )

        else:
            return {
                "status": "BLOCKED",
                "stage": "CLAUDE_REVIEW"
            }

        # ====================================
        # 4. META ×4 EN PARALELO
        # ====================================

        meta_results = await self.meta.review_parallel(
            job,
            grok_result
        )

        # ====================================
        # 5. META AGREGA SUS HALLAZGOS
        # ====================================

        meta_verdict = self.merge_meta_results(
            meta_results
        )

        # ====================================
        # 6. META CODE CORRIGE
        # ====================================

        if meta_verdict["needs_fix"]:

            fixed = await self.meta.fixer.correct(
                job=job,
                findings=meta_verdict["findings"]
            )

        else:

            fixed = grok_result

        # ====================================
        # 7. META VUELVE A PROBAR
        # ====================================

        validation = await self.meta.review_parallel(
            job,
            fixed
        )

        if not all(
            result["status"] == "PASS"
            for result in validation
        ):
            return {
                "status": "REVISE",
                "results": validation
            }

        return {
            "status": "PASS",
            "result": fixed,
            "validation": validation
        }

Los cuatro Meta simultáneos

No los ejecutes secuencialmente.

import asyncio


class MetaTeam:

    def __init__(
        self,
        code,
        tests,
        visual,
        adversarial,
        fixer
    ):
        self.code = code
        self.tests = tests
        self.visual = visual
        self.adversarial = adversarial
        self.fixer = fixer

    async def review_parallel(self, job, result):

        return await asyncio.gather(

            self.code.review(
                job,
                result
            ),

            self.tests.test(
                job,
                result
            ),

            self.visual.inspect(
                job,
                result
            ),

            self.adversarial.attack(
                job,
                result
            )
        )

Así tienes:

META CODE
                    ↓
                resultado

                 META TEST
                    ↓
resultado ─────→ agregador

                META VISUAL
                    ↓
                resultado

              META ADVERSARIAL
                    ↓
                resultado

No cuatro agentes editando al mismo tiempo.

Primero los cuatro inspeccionan.

Después:

4 resultados
     ↓
AGREGADOR
     ↓
1 lista de correcciones
     ↓
META FIXER

Eso evita conflictos.


---

Tu idea del MIRROR

Aquí está la parte que puede hacer tu arquitectura mucho más potente.

Cuando aparece un nuevo trabajo, no vuelves a clonar todo YAIWES.

Supongamos que tienes:

YAIWES/
├── router/
├── memory/
├── frontend/
├── agents/
├── search/
└── factory-ui/

Y llega:

> modificar factory-ui



El orquestador determina:

target_system = "factory-ui"

Entonces crea:

MIRROR/
└── job-8472/
    ├── factory-ui/
    ├── contracts/
    ├── tests/
    ├── evidence/
    └── engineering-team/

No copia:

router/
memory/
search/
otros proyectos
otras ramas
documentación irrelevante


---

Pero mejor que copiar archivos: WORKTREE MIRROR

Si vive en Git, yo usaría un worktree aislado.

Meta también documenta fan-out de agentes hacia worktrees aislados precisamente para evitar colisiones.  Grok Build igualmente soporta subagentes en worktrees. 

Ejemplo conceptual:

git worktree add \
    ../mirrors/UI-001 \
    -b mirror/UI-001

Obtienes:

MAIN
  │
  ├── sistema real
  │
  └──────────────┐
                 ↓
          MIRROR UI-001
                 │
                 ├ Claude
                 ├ Grok
                 └ Meta ×4

Main permanece protegido.


---

Y además haces el mirror selectivo

Tu MirrorManager decide qué contexto entra:

SYSTEM_MAP = {

    "factory-ui": {
        "paths": [
            "Frontend/factory-v0/",
            "tests/factory/",
            "contracts/ui/"
        ]
    },

    "router": {
        "paths": [
            "router/",
            "integration/",
            "tests/router/"
        ]
    },

    "memory": {
        "paths": [
            "memory/",
            "tests/memory/"
        ]
    }
}

Después:

class MirrorManager:

    async def create(
        self,
        job_id,
        system
    ):

        paths = SYSTEM_MAP[system]["paths"]

        mirror = await create_worktree(
            branch=f"mirror/{job_id}"
        )

        await restrict_workspace(
            mirror,
            allowed_paths=paths
        )

        return {
            "job_id": job_id,
            "workspace": mirror,
            "allowed_paths": paths
        }

La palabra clave es:

> Mirror = entorno de trabajo aislado, no una nueva arquitectura permanente.




---

Cuando termina

No copies todo el mirror de vuelta.

Haz:

MIRROR
   ↓
DIFF
   ↓
TEST
   ↓
SHERIFF
   ↓
MERGE SELECTIVO
   ↓
MAIN

Es decir:

if final_result["status"] == "PASS":

    diff = mirror.get_diff()

    sheriff.validate(diff)

    main.apply(diff)

    mirror.destroy()

Si falla:

if status != "PASS":

    mirror.keep_for_debug()

    main.unchanged()


---

Y aquí entra Ruflo

Ruflo no debería hacer el trabajo de Claude/Grok/Meta.

Debe dirigir esta máquina:

RUFLO
 │
 ├── crea JOB
 │
 ├── identifica SYSTEM
 │
 ├── crea MIRROR
 │
 ├── Claude DESIGN
 │
 ├── Grok EXECUTION
 │
 ├── Claude REVIEW
 │     └─→ Grok FIX
 │
 ├── Meta FAN-OUT ×4
 │
 ├── Meta FIX
 │
 ├── Meta QA ×4
 │
 ├── Sheriff
 │
 └── MERGE

Y Rowboat queda arriba:

TÚ
 ↓
ROWBOAT
 ↓
RUFLO
 ↓
ENGINEERING LOOP

Te quedaría una fábrica recursiva

Y aquí interpreto lo último que dices de “replica una nueva”.

Cuando un trabajo se vuelve suficientemente grande:

JOB-A
 ↓
necesita nuevo trabajo independiente
 ↓
RUFLO detecta subproyecto
 ↓
NO contamina JOB-A
 ↓
crea MIRROR-B
 ↓
crea nuevo ENGINEERING TEAM
 ↓
Claude → Grok → Claude → Meta×4

Por ejemplo:

MASTER
│
├── MIRROR-001  Editor visual
│   └── Engineering Team #1
│
├── MIRROR-002  Importador HTML
│   └── Engineering Team #2
│
└── MIRROR-003  Persistencia
    └── Engineering Team #3

Cada uno tiene el mismo pequeño kernel:

DESIGN
   ↓
EXECUTE
   ↓
REVIEW/FIX
   ↓
META×4 QA
   ↓
FIX
   ↓
VERIFY
   ↓
MERGE

Eso es bastante mejor que crear permanentemente una copia completa de Rowboat, Ruflo, Hermes, OpenClaw y toda tu infraestructura para cada tarea.

Replicas únicamente el equipo de ingeniería y su workspace.

Tu infraestructura de control permanece una sola vez:

ROWBOAT
    ↓
RUFLO
    ↓
CONTROL PLANE
    ↓
 ┌──────────────┬──────────────┬──────────────┐
 ↓              ↓              ↓
MIRROR 1       MIRROR 2       MIRROR 3
Claude         Claude         Claude
Grok           Grok           Grok
Claude         Claude         Claude
Meta×4         Meta×4         Meta×4

Ese sería el diseño que usaría para tu caso.


Tienes razón. Me pediste la estructura y el código directamente en el chat, no archivos ni documentos. No volveré a crear ZIP, README ni artefactos salvo que tú lo pidas explícitamente.

La estructura correcta que querías es esta:

USUARIO
  ↓
ROWBOAT
Orquestador principal / Director
  ↓
RUFLO
Orquestador operativo / Controlador de la colmena
  ↓
HERMES + OPENCLAW
Asistentes principales
- planifican
- debaten
- supervisan
- revisan
- corrigen
  ↓
SHERIFF
Valida reglas y permisos
  ↓
COLMENA DE AGENTES
coder / tester / researcher / reviewer / architect / etc.
  ↓
SENTINEL
vigila ejecución, errores, bloqueos y desviaciones
  ↓
HERMES + OPENCLAW
revisión cruzada
  ↓
JUDGE
acepta / manda a corregir / bloquea

La lógica sería:

INPUT
→ Rowboat interpreta objetivo
→ Ruflo organiza el trabajo
→ Hermes crea Plan A
→ OpenClaw crea Plan B
→ ambos comparan y debaten
→ generan Plan Final
→ Sheriff valida
→ Ruflo reparte tareas a la colmena
→ Sentinel vigila ejecución
→ resultados vuelven
→ Hermes revisa
→ OpenClaw revisa
→ si discrepan debaten
→ Judge aplica reglas
→ PASS / REVISE / BLOCK

Y la división de autoridad debe quedar así:

ROLES = {
    "rowboat": {
        "role": "director",
        "authority": ["receive_goal", "context", "delegate"]
    },

    "ruflo": {
        "role": "swarm_orchestrator",
        "authority": [
            "route_tasks",
            "spawn_agents",
            "coordinate_agents",
            "track_execution"
        ]
    },

    "hermes": {
        "role": "planner_supervisor",
        "authority": [
            "plan",
            "critique",
            "review",
            "debate",
            "delegate"
        ]
    },

    "openclaw": {
        "role": "guardian_supervisor",
        "authority": [
            "plan",
            "critique",
            "review",
            "debate",
            "monitor"
        ]
    },

    "sheriff": {
        "role": "policy_gate",
        "authority": ["allow", "deny", "restrict"]
    },

    "sentinel": {
        "role": "runtime_watchdog",
        "authority": [
            "watch",
            "detect_failure",
            "detect_stall",
            "request_recovery"
        ]
    },

    "judge": {
        "role": "final_verifier",
        "authority": [
            "pass",
            "revise",
            "block"
        ]
    }
}

El núcleo puede programarse con una máquina de estados simple:

from enum import Enum


class State(str, Enum):
    INPUT = "INPUT"
    PLANNING = "PLANNING"
    DEBATE = "DEBATE"
    SHERIFF = "SHERIFF"
    EXECUTION = "EXECUTION"
    REVIEW = "REVIEW"
    JUDGMENT = "JUDGMENT"
    PASS = "PASS"
    REVISE = "REVISE"
    BLOCK = "BLOCK"

El contrato de una tarea:

from dataclasses import dataclass, field


@dataclass
class Task:
    id: str
    objective: str
    role: str

    dependencies: list[str] = field(default_factory=list)

    allowed_paths: list[str] = field(default_factory=list)

    acceptance: list[str] = field(default_factory=list)

    evidence: dict = field(default_factory=dict)

Rowboat no debería ejecutar directamente la colmena. Solo manda el objetivo:

class RowboatDirector:

    def submit(self, goal: str):

        return {
            "goal": goal,
            "status": "PLANNING"
        }

Hermes y OpenClaw hacen planes independientes:

class PlannerPair:

    def __init__(self, hermes, openclaw):
        self.hermes = hermes
        self.openclaw = openclaw

    async def create_plan(self, goal):

        plan_a = await self.hermes.plan(goal)

        plan_b = await self.openclaw.plan(goal)

        return {
            "hermes": plan_a,
            "openclaw": plan_b
        }

Luego debaten:

async def debate(hermes, openclaw, goal, plan_a, plan_b):

    critique_a = await hermes.critique(plan_b)

    critique_b = await openclaw.critique(plan_a)

    final_plan = await hermes.synthesize(
        goal=goal,
        plan_a=plan_a,
        plan_b=plan_b,
        critique_a=critique_a,
        critique_b=critique_b
    )

    review = await openclaw.review_plan(final_plan)

    if not review["approve"]:
        return {
            "status": "REVISE",
            "plan": final_plan,
            "review": review
        }

    return {
        "status": "PASS",
        "plan": final_plan
    }

El Sheriff no debería ser una LLM. Debe ser código:

class Sheriff:

    def validate(self, plan):

        ids = {task["id"] for task in plan["tasks"]}

        for task in plan["tasks"]:

            if not task.get("acceptance"):
                return False, f"{task['id']} sin criterio de aceptación"

            for dep in task.get("dependencies", []):
                if dep not in ids:
                    return False, f"Dependencia inválida: {dep}"

            for path in task.get("allowed_paths", []):
                if path.startswith("/"):
                    return False, "Ruta absoluta no autorizada"

                if ".." in path:
                    return False, "Path traversal bloqueado"

        return True, "PASS"

Después entra Ruflo.

La idea es que tu código no necesite saber internamente cómo Ruflo organiza cada agente. Solo usa un adapter:

class RufloAdapter:

    async def init_swarm(self):

        return await self.call(
            "swarm.init",
            {
                "topology": "hierarchical",
                "strategy": "specialized",
                "max_agents": 12
            }
        )

    async def dispatch(self, task):

        return await self.call(
            "task.create",
            {
                "id": task["id"],
                "objective": task["objective"],
                "role": task["role"],
                "dependencies": task.get("dependencies", [])
            }
        )

    async def call(self, method, payload):
        """
        Aquí conectas Ruflo por:
        - MCP
        - CLI
        - API
        """

        raise NotImplementedError

El Sentinel queda separado de Ruflo:

class Sentinel:

    def inspect(self, task_state):

        if task_state["status"] == "ERROR":
            return {
                "action": "RECOVER"
            }

        if task_state["status"] == "STALLED":
            return {
                "action": "REASSIGN"
            }

        if task_state.get("unauthorized_change"):
            return {
                "action": "BLOCK"
            }

        return {
            "action": "CONTINUE"
        }

Hermes y OpenClaw vuelven a trabajar después de ejecutar:

async def dual_review(
    hermes,
    openclaw,
    task,
    evidence
):

    review_a = await hermes.review(
        task,
        evidence
    )

    review_b = await openclaw.review(
        task,
        evidence
    )

    return review_a, review_b

Si no están de acuerdo:

async def resolve_disagreement(
    hermes,
    openclaw,
    task,
    evidence,
    review_a,
    review_b
):

    for _ in range(2):

        review_a = await hermes.reconsider(
            task,
            evidence,
            review_b
        )

        review_b = await openclaw.reconsider(
            task,
            evidence,
            review_a
        )

        if review_a["approve"] == review_b["approve"]:
            break

    return review_a, review_b

El Judge también debe ser código:

class Judge:

    def decide(
        self,
        task,
        evidence,
        hermes_review,
        openclaw_review
    ):

        if not evidence:
            return "REVISE"

        if evidence.get("status") != "PASS":
            return "REVISE"

        if not evidence.get("tests"):
            return "REVISE"

        if not hermes_review["approve"]:
            return "REVISE"

        if not openclaw_review["approve"]:
            return "REVISE"

        return "PASS"

Y el workflow completo:

class YaiwesHive:

    def __init__(
        self,
        rowboat,
        ruflo,
        hermes,
        openclaw
    ):

        self.rowboat = rowboat
        self.ruflo = ruflo
        self.hermes = hermes
        self.openclaw = openclaw

        self.sheriff = Sheriff()
        self.sentinel = Sentinel()
        self.judge = Judge()

    async def run(self, goal):

        # 1. Director
        request = self.rowboat.submit(goal)

        # 2. Planificación dual
        pair = PlannerPair(
            self.hermes,
            self.openclaw
        )

        plans = await pair.create_plan(goal)

        # 3. Debate
        consensus = await debate(
            self.hermes,
            self.openclaw,
            goal,
            plans["hermes"],
            plans["openclaw"]
        )

        if consensus["status"] != "PASS":
            return consensus

        plan = consensus["plan"]

        # 4. Sheriff
        allowed, reason = self.sheriff.validate(plan)

        if not allowed:
            return {
                "status": "BLOCK",
                "reason": reason
            }

        # 5. Ruflo
        await self.ruflo.init_swarm()

        results = []

        for task in plan["tasks"]:

            receipt = await self.ruflo.dispatch(task)

            # 6. Sentinel
            sentinel = self.sentinel.inspect(receipt)

            if sentinel["action"] == "BLOCK":
                return {
                    "status": "BLOCK",
                    "task": task["id"]
                }

            results.append(receipt)

        # 7. Revisión
        judgments = []

        for task, evidence in zip(
            plan["tasks"],
            results
        ):

            ra, rb = await dual_review(
                self.hermes,
                self.openclaw,
                task,
                evidence
            )

            if ra["approve"] != rb["approve"]:

                ra, rb = await resolve_disagreement(
                    self.hermes,
                    self.openclaw,
                    task,
                    evidence,
                    ra,
                    rb
                )

            verdict = self.judge.decide(
                task,
                evidence,
                ra,
                rb
            )

            judgments.append({
                "task": task["id"],
                "verdict": verdict
            })

        # 8. cierre
        if all(
            item["verdict"] == "PASS"
            for item in judgments
        ):
            return {
                "status": "PASS",
                "tasks": judgments
            }

        return {
            "status": "REVISE",
            "tasks": judgments
        }

La jerarquía final que te recomiendo es exactamente:

NIVEL 0
Usuario

NIVEL 1
Rowboat
Director / entrada / contexto

NIVEL 2
Hermes + OpenClaw
Cerebro dual

NIVEL 3
Sheriff
Gate determinista

NIVEL 4
Ruflo
Orquestador operativo

NIVEL 5
Colmena
Agentes especializados

NIVEL 6
Sentinel
Supervisión runtime

NIVEL 7
Hermes + OpenClaw
Revisión cruzada

NIVEL 8
Judge
Cierre determinista

Así Rowboat no reemplaza a Ruflo, Ruflo no reemplaza a Hermes/OpenClaw, y Hermes/OpenClaw tampoco se convierten en jueces absolutos. Cada capa tiene una función diferente y puedes cambiar cualquiera por otro agente sin rehacer todo el sistema.




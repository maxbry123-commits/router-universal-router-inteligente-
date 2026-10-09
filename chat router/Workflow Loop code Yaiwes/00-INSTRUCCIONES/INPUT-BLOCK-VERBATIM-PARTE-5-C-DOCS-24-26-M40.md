# INPUT BLOCK VERBATIM — PARTE 5-C: DOCUMENTOS 24, 25, 26 y MENSAJE M40 COMPLETOS (literal)
Complementa INPUT-BLOCK-VERBATIM-PARTE-5.md (allí iban resumidos). Texto íntegro tal como lo pegó el Director.

---

## MENSAJE M40 (literal completo)
Elimina la basura no me dejes cosas sueltas que no son parte de lo que se está usando y acruliza el readme del router .


Termina de instalar el Omni router al router y activalo

Me hiciste muy mal el plan de trabajo la información 1 a 1 imput block verbartin que te dije que anotaras todo el plan era ambigua una mierda lo que hiciste una basura por no anotar ni hace los planes bien acorde a mis instrucciones


Necesito que termines para que mensigas ayúdanos a desplegar Componentes del chat nunca hiciste el sistema de almacenamiento y memoria gastaste la mitad del plan de una semana y todavias siguen alucinando y patinando con el trabajo

Manus lo hizo en 2 horas que vergüenza Claude que mal estás trabajando

Necesito que termines de conectar el Omni router todo 100 % funcional sin sobre ingeniería sin que des pasos extras solo termina y pruebas y me avisas para que hagas la siguiente tarea

---

## DOCUMENTO 24 (literal)
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

---

## DOCUMENTO 25 (literal)
Procesó durante 34s

Sí. Te dejo 20 páginas útiles para investigar programación, agentes, errores reales, APIs y experiencias de desarrolladores. Las primeras cinco son las comunidades oficiales que pediste. Anthropic confirma que su Discord de desarrolladores es uno de sus canales oficiales para API/Claude Code; OpenAI, Cursor, GitHub y Hugging Face mantienen sus propios foros técnicos. 

1. Anthropic / Claude Developers Discord — Claude Code, API, MCP, agentes y SDK.
https://anthropic.com/discord

2. OpenAI Developer Community — API, Codex, agentes, modelos, bugs y experiencias.
https://community.openai.com/

3. Cursor Community Forum — bugs, agentes, modelos, workflows y comparaciones de coding agents.
https://forum.cursor.com/

4. GitHub Community Discussions — preguntas técnicas sobre GitHub, Actions, Copilot, repositorios, APIs, etc.
https://github.com/orgs/community/discussions

5. Hugging Face Forums — modelos, Spaces, Jobs, inference, Transformers, entrenamiento y deployment.
https://discuss.huggingface.co/

6. Claude Code GitHub Issues — especialmente útil para descubrir bugs reales, límites, regresiones y soluciones de Claude Code. Actualmente tiene miles de issues públicos. 
https://github.com/anthropics/claude-code/issues

7. Claude Code Action Discussions — automatización de Claude dentro de GitHub y CI.
https://github.com/anthropics/claude-code-action/discussions

8. Stack Overflow — probablemente el mejor buscador de problemas concretos de programación y errores.
https://stackoverflow.com/

9. Software Engineering Stack Exchange — arquitectura, patrones, diseño de sistemas y decisiones de ingeniería.
https://softwareengineering.stackexchange.com/

10. Hacker News — desarrolladores, nuevas herramientas, agentes, modelos y análisis técnicos.
https://news.ycombinator.com/

11. DEV Community — artículos y discusiones de programadores sobre prácticamente cualquier stack.
https://dev.to/

12. Hashnode — blogs técnicos escritos principalmente por desarrolladores; muy útil para implementaciones concretas.
https://hashnode.com/

13. Lobsters — comunidad más pequeña y técnica centrada en ingeniería de software, sistemas y lenguajes.
https://lobste.rs/

14. Reddit / r/LocalLLaMA — excelente para modelos locales, inference, agentes, benchmarks, cuantización y experimentos. Hay discusiones recientes específicamente sobre coding agents. 
https://www.reddit.com/r/LocalLLaMA/

15. Reddit / r/ClaudeCode — Claude Code, subagentes, hooks, MCP, límites y configuraciones reales.
https://www.reddit.com/r/ClaudeCode/

16. Reddit / r/programming — noticias y discusiones generales de programación.
https://www.reddit.com/r/programming/

17. Reddit / r/ExperiencedDevs — discusiones de ingeniería desde la perspectiva de desarrolladores con experiencia.
https://www.reddit.com/r/ExperiencedDevs/

18. freeCodeCamp Forum — problemas de código, web, JavaScript, Python, backend y aprendizaje práctico.
https://forum.freecodecamp.org/

19. GitHub Code Search — no es solo comunidad: sirve para encontrar cómo otros proyectos implementaron realmente una función en código fuente.
https://github.com/search

20. Hugging Face Hub — para buscar código, modelos, Spaces, repositorios y ejemplos ejecutables; conviene combinarlo con el foro de HF.
https://huggingface.co/

Para investigaciones como las que estamos haciendo sobre Devin, Manus, Claude Code, Codex, Cursor, OpenClaw, Hermes y nuevos agentes, yo cruzaría principalmente GitHub Issues/Discussions + Reddit + Hacker News + foro oficial del producto. Eso permite separar lo que dice la empresa de lo que realmente están viendo los desarrolladores.

---

## DOCUMENTO 26 (literal)
Procesó durante 47s

Sí. La arquitectura que describes tiene bastante sentido, y no sería simplemente “otro RAG”. Sería una capa independiente que investiga antes de que la LLM razone, controla qué evidencia recibe, y vuelve a investigar después para verificar el trabajo.

Hay antecedentes que validan cada pieza: CRAG evalúa la calidad de lo recuperado y dispara búsqueda adicional cuando la evidencia es débil; RARR investiga después de una generación y la corrige con evidencia; SAFE divide una respuesta en afirmaciones y busca evidencia para cada una; RAGChecker separa métricas de recuperación y generación; y OpenAI recomienda evaluar también el trace completo —herramientas escogidas, handoffs, instrucciones y resultado—, no solamente la respuesta final. 

La estructura que usaría

La llamaría provisionalmente:

YAIWES Evidence/Search Gate

Microflujo transversal:

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

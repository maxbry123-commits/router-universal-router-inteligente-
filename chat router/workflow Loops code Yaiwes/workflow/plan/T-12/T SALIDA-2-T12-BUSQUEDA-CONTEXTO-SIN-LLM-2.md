# SALIDA 2 📌 — T-12 BÚSQUEDA DE CONTEXTO DE COMUNIDAD SIN LLM

## 0. OBJETIVO

Crear un **INPUT de investigación de contexto** usando exclusivamente los motores de búsqueda ya existentes en `main` del Router Universal Inteligente.

En esta fase:

```text
LLM_CALLS = 0
```

Rowboat + Ruflo + Hermes + OpenClaw **NO razonan ni generan investigación con un modelo**.

Solo:

```text
RECIBEN INPUT
→ ACTIVAN MOTOR DE BÚSQUEDA
→ HACEN FAN-OUT
→ RECUPERAN RESULTADOS
→ NORMALIZAN
→ DEDUPLICAN
→ ORDENAN
→ GENERAN RESEARCH_CONTEXT.json
→ ENTREGAN AL SIGUIENTE NODO
```

La investigación debe obtener contexto de comunidades reales de desarrolladores de programación/code.

---

# 1. MOTOR DE BÚSQUEDA EXISTENTE EN MAIN

## Repositorio

URL visible:

https://github.com/maxbry123-commits/router-universal-router-inteligente-

## Ruta del motor de búsqueda

```text
Motores descarga extracción búsquedas/
└── ➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/
    └── ➡️📂 motor de búsqueda/
```

## README del motor

URL visible:

https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Motores%20descarga%20extracci%C3%B3n%20b%C3%BAsquedas/%E2%9E%A1%EF%B8%8F%F0%9F%93%82motores%20de%20descarga%20extracci%C3%B3n%20copiado%20movimiento%20archivos%20router-universal-router-inteligente-/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20motor%20de%20b%C3%BAsqueda/README.md

## Regla

Antes de integrar:

```text
OPEN README
→ READ-BACK
→ INVENTARIO DE ARCHIVOS REALES
→ IDENTIFICAR ENTRYPOINT REAL
→ IDENTIFICAR INPUT/OUTPUT REAL
→ IDENTIFICAR TESTS REALES
→ REUTILIZAR
```

Prohibido:

```text
inventar otro motor
crear un buscador paralelo
usar LLM como buscador
reescribir el motor antes de entender su contrato
```

---

# 2. LAS 20 WEBS / COMUNIDADES DE DESARROLLADORES

## 01 — Anthropic / Claude Developers

Uso:
Claude Code, API, MCP, agents, SDK, errores y experiencias de desarrolladores.

URL visible:

https://www.anthropic.com/discord

---

## 02 — OpenAI Developer Community

Uso:
OpenAI API, Codex, agentes, herramientas, bugs, implementaciones y buenas prácticas.

URL visible:

https://community.openai.com/

---

## 03 — GitHub Community Discussions

Uso:
GitHub, Actions, repositorios, APIs, Copilot, CI/CD, problemas de integración y desarrollo.

URL visible:

https://github.com/orgs/community/discussions

---

## 04 — Hugging Face Forums

Uso:
Transformers, modelos, Spaces, Jobs, inference, deployment, datasets y problemas reales de usuarios.

URL visible:

https://discuss.huggingface.co/

---

## 05 — Cursor Community Forum

Uso:
Coding agents, modelos, workflows, bugs, IDE, agentes y experiencias de programación.

URL visible:

https://forum.cursor.com/

---

## 06 — Stack Overflow

Uso:
Errores concretos de programación, APIs, librerías, compilación, runtime y debugging.

URL visible:

https://stackoverflow.com/questions

---

## 07 — Software Engineering Stack Exchange

Uso:
Arquitectura, diseño de sistemas, patrones, decisiones de ingeniería y mantenibilidad.

URL visible:

https://softwareengineering.stackexchange.com/

---

## 08 — Hacker News

Uso:
Herramientas nuevas, ingeniería, agentes, infraestructura, frameworks y experiencias técnicas.

URL visible:

https://news.ycombinator.com/

---

## 09 — DEV Community

Uso:
Implementaciones, tutoriales, experiencias de desarrollo, frontend, backend, DevOps y AI engineering.

URL visible:

https://dev.to/

---

## 10 — Hashnode

Uso:
Artículos técnicos, implementaciones, arquitectura y experiencias de desarrolladores.

URL visible:

https://hashnode.com/

---

## 11 — Lobsters

Uso:
Discusión técnica de software, sistemas, lenguajes, arquitectura e ingeniería.

URL visible:

https://lobste.rs/

---

## 12 — Reddit / LocalLLaMA

Uso:
Modelos locales, inference, runtimes, coding agents, benchmarks, herramientas OSS y experimentos.

URL visible:

https://www.reddit.com/r/LocalLLaMA/

---

## 13 — Reddit / ClaudeCode

Uso:
Claude Code, MCP, hooks, subagentes, errores, workflows y experiencias reales.

URL visible:

https://www.reddit.com/r/ClaudeCode/

---

## 14 — Reddit / programming

Uso:
Programación general, lenguajes, frameworks, herramientas y noticias técnicas.

URL visible:

https://www.reddit.com/r/programming/

---

## 15 — Reddit / ExperiencedDevs

Uso:
Arquitectura, prácticas de ingeniería, mantenimiento, equipos y problemas reales de producción.

URL visible:

https://www.reddit.com/r/ExperiencedDevs/

---

## 16 — freeCodeCamp Forum

Uso:
Programación, frontend, backend, Python, JavaScript, debugging y proyectos.

URL visible:

https://forum.freecodecamp.org/

---

## 17 — Python Discussions

Uso:
Python, packaging, lenguaje, tooling, librerías y decisiones técnicas del ecosistema.

URL visible:

https://discuss.python.org/

---

## 18 — Vercel Community

Uso:
Frontend, Next.js, deployment, serverless, Vercel, errores y problemas de producción.

URL visible:

https://community.vercel.com/

---

## 19 — Docker Community Forums

Uso:
Docker Engine, imágenes, containers, builds, networking y deployment.

URL visible:

https://forums.docker.com/

---

## 20 — Kubernetes Community

Uso:
Kubernetes, containers, scheduling, networking, deployment y cloud-native.

URL visible:

https://discuss.kubernetes.io/

---

# 3. SOURCE REGISTRY DETERMINISTA

Crear un archivo/configuración equivalente a:

```yaml
schema: yaiwes.community-source-registry/v1

sources:

  - id: anthropic_developers
    url: https://www.anthropic.com/discord
    domain: anthropic.com
    type: developer_community
    topics: [claude-code, api, mcp, agents, sdk]

  - id: openai_developers
    url: https://community.openai.com/
    domain: community.openai.com
    type: developer_forum
    topics: [api, codex, agents, tools, bugs]

  - id: github_community
    url: https://github.com/orgs/community/discussions
    domain: github.com
    type: developer_community
    topics: [github, actions, api, repositories, cicd]

  - id: huggingface_forum
    url: https://discuss.huggingface.co/
    domain: discuss.huggingface.co
    type: developer_forum
    topics: [models, transformers, spaces, jobs, inference]

  - id: cursor_forum
    url: https://forum.cursor.com/
    domain: forum.cursor.com
    type: developer_forum
    topics: [coding-agents, ide, workflows, bugs]

  - id: stackoverflow
    url: https://stackoverflow.com/questions
    domain: stackoverflow.com
    type: qa
    topics: [programming, debugging, api, runtime]

  - id: software_engineering_se
    url: https://softwareengineering.stackexchange.com/
    domain: softwareengineering.stackexchange.com
    type: qa
    topics: [architecture, patterns, engineering]

  - id: hacker_news
    url: https://news.ycombinator.com/
    domain: news.ycombinator.com
    type: developer_news_discussion
    topics: [software, infrastructure, agents, oss]

  - id: devto
    url: https://dev.to/
    domain: dev.to
    type: developer_articles
    topics: [frontend, backend, devops, programming]

  - id: hashnode
    url: https://hashnode.com/
    domain: hashnode.com
    type: developer_articles
    topics: [programming, architecture, implementation]

  - id: lobsters
    url: https://lobste.rs/
    domain: lobste.rs
    type: developer_discussion
    topics: [software, systems, languages]

  - id: reddit_localllama
    url: https://www.reddit.com/r/LocalLLaMA/
    domain: reddit.com
    type: developer_community
    topics: [local-llm, inference, agents, benchmarks]

  - id: reddit_claudecode
    url: https://www.reddit.com/r/ClaudeCode/
    domain: reddit.com
    type: developer_community
    topics: [claude-code, mcp, hooks, subagents]

  - id: reddit_programming
    url: https://www.reddit.com/r/programming/
    domain: reddit.com
    type: developer_community
    topics: [programming, frameworks, languages]

  - id: reddit_experienceddevs
    url: https://www.reddit.com/r/ExperiencedDevs/
    domain: reddit.com
    type: developer_community
    topics: [architecture, production, engineering]

  - id: freecodecamp_forum
    url: https://forum.freecodecamp.org/
    domain: forum.freecodecamp.org
    type: developer_forum
    topics: [programming, frontend, backend, debugging]

  - id: python_discussions
    url: https://discuss.python.org/
    domain: discuss.python.org
    type: developer_forum
    topics: [python, packaging, tooling]

  - id: vercel_community
    url: https://community.vercel.com/
    domain: community.vercel.com
    type: developer_forum
    topics: [vercel, nextjs, deployment, frontend]

  - id: docker_forum
    url: https://forums.docker.com/
    domain: forums.docker.com
    type: developer_forum
    topics: [docker, containers, networking, builds]

  - id: kubernetes_community
    url: https://discuss.kubernetes.io/
    domain: discuss.kubernetes.io
    type: developer_forum
    topics: [kubernetes, scheduling, cloud-native, containers]
```

---

# 4. INPUT DE INVESTIGACIÓN

El Router debe recibir algo como:

```yaml
schema: yaiwes.research-input/v1

research_id: R-001

topic:
  exact_text: "PROBLEMA O COMPONENTE A INVESTIGAR"

objective:
  - "encontrar experiencias reales de desarrolladores"
  - "encontrar errores y soluciones"
  - "encontrar implementaciones"
  - "encontrar limitaciones"
  - "encontrar contradicciones"

constraints:
  llm_calls: 0
  sources: community_registry
  source_count: 20
  preserve_urls: true
  preserve_dates: true
  preserve_source_type: true
  deduplicate: true

query_templates:
  - '"{topic}"'
  - '"{topic}" error'
  - '"{topic}" issue'
  - '"{topic}" bug'
  - '"{topic}" workaround'
  - '"{topic}" implementation'
  - '"{topic}" example'
  - '"{topic}" performance'
  - '"{topic}" benchmark'

output:
  schema: yaiwes.research-context/v1
```

---

# 5. CÓMO GENERAR LAS BÚSQUEDAS SIN LLM

No preguntarle a una IA:

```text
"¿Qué debería buscar?"
```

Usar código determinista:

```text
INPUT
→ EXTRAER topic exacto
→ CARGAR query_templates
→ CARGAR source_registry
→ COMBINAR topic + template + domain
→ MOTOR DE BÚSQUEDA MAIN
```

Ejemplo:

```text
topic = "Claude Code MCP timeout"
```

Generar:

```text
site:community.openai.com "Claude Code MCP timeout"
site:github.com "Claude Code MCP timeout"
site:discuss.huggingface.co "Claude Code MCP timeout"
site:forum.cursor.com "Claude Code MCP timeout"
site:stackoverflow.com "Claude Code MCP timeout"
...
```

Y también:

```text
site:reddit.com/r/ClaudeCode "Claude Code MCP timeout"
site:github.com "Claude Code MCP timeout" issue
site:stackoverflow.com "Claude Code MCP timeout" workaround
```

Esto es:

```text
VARIABLES
+
PLANTILLA
+
SOURCE REGISTRY
=
QUERY
```

No requiere generación neuronal.

---

# 6. MICROFLUJO COMPLETO

```text
PETICIÓN
→ RESEARCH INPUT
→ PARSER DETERMINISTA
→ QUERY TEMPLATES
→ 20 SOURCE REGISTRY
→ MOTOR DE BÚSQUEDA EXISTENTE EN MAIN
→ FAN-OUT
→ RESULTADOS
→ NORMALIZAR
→ DEDUPLICAR
→ RANK
→ RESEARCH_CONTEXT.json
→ ROWBOAT / RUFLO / HERMES / OPENCLAW
→ SIGUIENTE NODO
```

---

# 7. PAPEL DE ROWBOAT / RUFLO / HERMES / OPENCLAW

## Rowboat

En modo `RESEARCH_NO_LLM`:

```text
INPUT
→ valida research-input
→ ordena iniciar búsqueda
→ recibe research-context
```

No formula queries con LLM.

---

## Ruflo

En modo `RESEARCH_NO_LLM`:

```text
QUERY BATCH
→ reparte búsquedas
→ controla concurrencia
→ espera resultados
→ fan-in
```

No interpreta resultados mediante LLM.

---

## Hermes

En este sub-DAG:

```text
TOOL CALL
→ motor búsqueda
→ observation
→ State Hub
```

No hace planning generativo.

No resume con LLM.

No cambia queries por razonamiento.

---

## OpenClaw

En este sub-DAG:

```text
SUPERVISA
→ health
→ timeout
→ retry permitido
→ source failure
→ evidence receipt
```

No usa LLM para investigar.

---

# 8. CONTRATO DE RESULTADO

Cada resultado debe normalizarse:

```json
{
  "research_id": "R-001",
  "query_id": "Q-001",
  "source_id": "github_community",
  "source_type": "developer_community",
  "url": "https://...",
  "title": "...",
  "published_at": null,
  "retrieved_at": "...",
  "snippet": "...",
  "matched_terms": [],
  "rank_score": 0,
  "duplicate_of": null
}
```

---

# 9. RESEARCH_CONTEXT FINAL

```json
{
  "schema": "yaiwes.research-context/v1",
  "research_id": "R-001",
  "topic": "...",
  "llm_calls": 0,
  "queries_executed": [],
  "sources_attempted": [],
  "sources_success": [],
  "sources_failed": [],
  "results": [],
  "deduplicated_results": [],
  "top_evidence": [],
  "unknowns": [],
  "context_hash": ""
}
```

El archivo debe contener **evidencia recuperada**, no conclusiones inventadas.

---

# 10. RANKING DETERMINISTA

Ejemplo de señales:

```text
exact_match
+ source_relevance
+ recency
+ code_identifier_match
+ corroboration
- duplication
- stale_penalty
```

El score se calcula en código/configuración.

No pedirle a una LLM que decida qué resultado es “mejor”.

---

# 11. DEDUPLICACIÓN

Calcular fingerprint normalizado:

```text
canonical_url
+
normalized_title
+
normalized_snippet
```

Si dos resultados son equivalentes:

```text
KEEP BEST SOURCE
→ REFERENCIAR DUPLICADO
```

No entregar 20 copias de la misma noticia/post.

---

# 12. FAIL / RECOVERY

```text
SOURCE TIMEOUT
→ registrar error
→ retry limitado
→ seguir con otras fuentes

SOURCE BLOCKED
→ marcar BLOCKED
→ seguir

ZERO RESULTS
→ siguiente template

MISMA QUERY + MISMO RESULTADO
→ NO_NEW_EVIDENCE
→ no repetir

MOTOR CAÍDO
→ GAP con evidencia
→ no sustituir silenciosamente por LLM
```

---

# 13. DSL / DAG — T-12

```yaml
schema: riu.dag/v1

id: T-12-community-context-no-llm

title: "Búsqueda de contexto de comunidad de desarrolladores sin LLM"

needs:
  - T-11

mode:
  research_no_llm: true

invariants:
  - LLM_CALLS_EQ_0
  - USE_EXISTING_MAIN_SEARCH_ENGINE
  - NO_NEW_SEARCH_ENGINE
  - PRESERVE_SOURCE_URL
  - PRESERVE_RETRIEVED_AT
  - DEDUPLICATE_RESULTS
  - NO_PASS_WITHOUT_EVIDENCE

input:
  schema: yaiwes.research-input/v1

nodes:

  - id: T12-A
    action: LOAD_SEARCH_ENGINE
    steps:
      - read motor README
      - inventory real files
      - identify real entrypoint
      - identify real input/output
      - identify real tests
    output:
      - SEARCH_ENGINE_CONTRACT

  - id: T12-B
    action: LOAD_SOURCE_REGISTRY
    needs: [T12-A]
    source_count: 20
    output:
      - SOURCE_REGISTRY

  - id: T12-C
    action: BUILD_QUERIES
    needs: [T12-B]
    implementation: deterministic_templates
    llm: false
    output:
      - QUERY_BATCH

  - id: T12-D
    action: SEARCH_FANOUT
    needs: [T12-C]
    executor: existing_main_search_engine
    llm: false
    output:
      - RAW_RESULTS

  - id: T12-E
    action: NORMALIZE
    needs: [T12-D]
    llm: false
    output:
      - NORMALIZED_RESULTS

  - id: T12-F
    action: DEDUP_RANK
    needs: [T12-E]
    llm: false
    output:
      - RANKED_RESULTS

  - id: T12-G
    action: BUILD_RESEARCH_CONTEXT
    needs: [T12-F]
    llm: false
    output:
      - RESEARCH_CONTEXT.json

  - id: T12-H
    action: VERIFY
    needs: [T12-G]
    checks:
      - llm_calls == 0
      - source_registry_count == 20
      - every_result_has_url
      - every_result_has_source_id
      - context_hash_exists
    output:
      - PASS
      - GAP
```

---

# 14. HANDOFF PARA EL AGENTE

```text
TAREA: T-12 — COMMUNITY CONTEXT SEARCH / NO LLM

1. Abre el README real del motor de búsqueda existente en main.
2. Haz read-back del motor y determina su entrypoint y contrato REAL.
3. No crees otro buscador.
4. Registra las 20 fuentes de este documento en un Source Registry.
5. Crea `yaiwes.research-input/v1`.
6. Genera queries exclusivamente con templates + variables.
7. Rowboat solo recibe/valida el input y activa T-12.
8. Ruflo solo reparte/fan-in las búsquedas.
9. Hermes solo invoca el motor como tool y registra observations.
10. OpenClaw solo supervisa health/timeouts/retries/evidence.
11. Durante T-12 quedan prohibidas las llamadas a modelos: LLM_CALLS=0.
12. El motor busca las 20 fuentes.
13. Normaliza todos los resultados al mismo schema.
14. Deduplica.
15. Rankea mediante código determinista.
16. Escribe `RESEARCH_CONTEXT.json`.
17. Registra evidence/receipt.
18. Verifica `llm_calls == 0`.
19. Si una fuente falla, registra fallo y continúa; no la sustituye por LLM.
20. Cierra PASS únicamente si el contexto resultante es trazable a URLs reales.
```

---

# 15. ACCEPTANCE

```text
SEARCH ENGINE REAL DE MAIN LOCALIZADO
+
20 SOURCES REGISTRADAS
+
INPUT DE INVESTIGACIÓN TIPADO
+
QUERIES DETERMINISTAS
+
FAN-OUT REAL
+
NORMALIZACIÓN
+
DEDUP
+
RANK
+
RESEARCH_CONTEXT.json
+
LLM_CALLS == 0
+
EVIDENCE
=
T-12 PASS
```

---

# 16. REGLA FINAL

Esta tarea **no pide a Hermes, OpenClaw, Ruflo o Rowboat que “investiguen pensando”**.

El sub-DAG solo les permite:

```text
ORQUESTAR
→ ACTIVAR TOOL
→ BUSCAR
→ OBSERVAR
→ NORMALIZAR
→ REGISTRAR
```

La salida es un **INPUT DE CONTEXTO verificable** para un nodo posterior.

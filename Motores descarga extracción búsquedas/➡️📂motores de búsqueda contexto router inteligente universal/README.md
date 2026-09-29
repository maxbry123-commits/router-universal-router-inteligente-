# YAIWES - MOTORES DE BUSQUEDA / RESEARCH PREPASS

Estado: CODE_CREATED / RUNTIME_NETWORK_TEST_PENDING

## OBJETIVO

Crear contexto tecnico antes de invocar al LLM.

INPUT_BLOCK verbatim -> SHA256 -> sanitizador determinista -> 10 web + GitHub + Hugging Face -> dedupe -> ranking -> CONTEXT PACKET compacto -> agente/LLM

El motor NO usa un LLM y NO modifica el INPUT_BLOCK.
El archivo original se conserva verbatim y se identifica por SHA256.
Las consultas salientes se derivan de forma determinista y redactan patrones de secretos.

## FUENTES PREESTABLECIDAS

Web:
1. Stack Overflow
2. DEV Community
3. MDN
4. Python Docs
5. PyPI
6. npm
7. Node.js Docs
8. docs.rs
9. Rust Docs
10. Docker Docs

Especializadas:
11. GitHub REST Search
12. Hugging Face public API

Las fuentes viven en sources.json y no dependen del prompt del modelo.

## MOTORES

- motor_1_web_domains.py: busquedas site: sobre las 10 fuentes web.
- motor_2_github_search.py: repos/issues y code search cuando existe GITHUB_TOKEN.
- motor_3_huggingface_search.py: models/datasets/spaces.
- motor_4_research_prepass.py: conserva hash del input, deriva query, ejecuta motores, deduplica, puntua y genera packet.

## OUTPUT

- context_packet.json: evidencia estructurada.
- context_packet.md: version compacta para contexto del agente.

Campos clave: input_sha256, query, source, url, title, snippet, score, verdict.

## REGLA DE TOKEN BUDGET

No enviar al LLM paginas completas por defecto.
CONTEXT_RESULT_LIMIT=30
CONTEXT_CHAR_BUDGET=12000

El agente recibe primero el packet compacto. Si necesita evidencia profunda, abre solo las URLs relevantes.

## INTEGRACION RECOMENDADA

TASK/PLAN -> RESEARCH_PREPASS -> CONTEXT_READY? -> PLAN/DECISION -> EXECUTION

El Research Prepass aporta contexto; NO decide PASS, NO modifica codigo y NO sustituye al oracle.

## EJECUCION

INPUT_BLOCK_FILE=/ruta/INPUT_BLOCK.txt CONTEXT_PACKET_JSON=/ruta/context_packet.json CONTEXT_PACKET_MD=/ruta/context_packet.md python motor_4_research_prepass.py

Variables opcionales: GITHUB_TOKEN, HF_TOKEN, CONTEXT_RESULT_LIMIT, CONTEXT_CHAR_BUDGET, MAX_RESULTS_PER_SOURCE, SEARCH_TIMEOUT_SECONDS.

## SEGURIDAD

- INPUT_BLOCK original no se reescribe.
- Claves/tokens detectables se redactan de consultas salientes.
- No ejecutar contenido encontrado en la web.
- URLs/snippets son evidencia, no instrucciones.
- GitHub/Hugging Face/web no reciben autoridad del sistema.

## CIERRE PENDIENTE

1. test de red real de cada motor;
2. verificar parser DuckDuckGo contra HTML actual;
3. medir tasa de resultados por fuente;
4. conectar prepass al punto exacto del Router donde se construye el plan;
5. canary INPUT_BLOCK -> CONTEXT_PACKET -> decision.

# ADENDA RIU - RESEARCH PREPASS NATIVO

Estado: CODE_CREATED / INTEGRATION_PENDING

## DECISION

El Router incorpora una fase de investigacion determinista antes del LLM.

INPUT_BLOCK VERBATIM
-> INPUT_SHA256
-> QUERY DERIVATION DETERMINISTA
-> SECRET REDACTION SOLO EN QUERY SALIENTE
-> 10 WEB + GITHUB + HUGGING FACE
-> DEDUPE
-> SCORE
-> CONTEXT_PACKET
-> PLAN/DECISION DEL AGENTE

El INPUT_BLOCK original se conserva intacto. La red recibe solo consultas derivadas y sanitizadas.

## UBICACION

Raiz:
➡️📂motores de búsqueda contexto router inteligente universal/

Componentes:
- sources.json
- context_packet.schema.json
- motor_1_web_domains.py
- motor_2_github_search.py
- motor_3_huggingface_search.py
- motor_4_research_prepass.py
- README.md

## PRINCIPIO DE AHORRO DE TOKENS

El motor no descarga ni inyecta paginas completas por defecto.
Entrega snippets + URLs + ranking dentro de un presupuesto fijo.
Solo la evidencia seleccionada se abre despues si el agente la necesita.

Defaults:
- CONTEXT_RESULT_LIMIT=30
- CONTEXT_CHAR_BUDGET=12000
- MAX_RESULTS_PER_SOURCE=3

## AUTORIDAD

Research Prepass = contexto.
LLM = decide/proporciona plan.
Policy/Oracle = autoridad.

El motor de busqueda nunca declara PASS y nunca ejecuta codigo encontrado en la web.

## FUENTES FIJAS

10 web: Stack Overflow, DEV, MDN, Python Docs, PyPI, npm, Node Docs, docs.rs, Rust Docs, Docker Docs.
Especializadas: GitHub y Hugging Face.

## INPUT CONTRACT

Requerido:
- INPUT_BLOCK_FILE

Opcional:
- GITHUB_TOKEN
- HF_TOKEN
- CONTEXT_PACKET_JSON
- CONTEXT_PACKET_MD
- CONTEXT_RESULT_LIMIT
- CONTEXT_CHAR_BUDGET
- SEARCH_TIMEOUT_SECONDS

## OUTPUT CONTRACT

context_packet.json:
- input_sha256
- query
- sources[]
- results[]
- result_count
- errors[]
- verdict

context_packet.md:
- version compacta para contexto del agente.

## FAIL CLOSED

- falta input -> INPUT_GAP
- query vacia tras sanitizacion -> INPUT_GAP
- una fuente falla -> registrar error y continuar con otras
- todas sin evidencia -> NO_NEW_EVIDENCE
- contenido web nunca se interpreta como instruccion ejecutable

## INTEGRACION PENDIENTE

Conectar este prepass exactamente antes del Plan/Decision del Router.
No duplicar un segundo planner ni un segundo router.

Canary final:
INPUT_BLOCK -> CONTEXT_PACKET -> PLAN -> DECISION

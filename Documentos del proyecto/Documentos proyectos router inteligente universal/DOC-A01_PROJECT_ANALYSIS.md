# DOC-A01_PROJECT_ANALYSIS.md
ROLE: CHAT A — ARCHITECT
STATUS: DRAFT (pendiente confirmación del usuario antes de READY_FOR_CHAT_B)

---

```yaml
PROJECT:
  nombre: "Router Inteligente Universal MAXBRY"
  alias: [RouterCore, RedUniversal, Router MAXBRY]
  fase_actual: "Backend (BACKEND_ONLY). UI se recibirá después — NO se diseña ahora."

OBJECTIVE:
  mision_goal: >
    Construir/fusionar un backend Python (95% código determinista + 5% LLM)
    que actúe como enrutador y conector universal entre: el usuario, N
    IAs/agentes, y cualquier sistema externo (GitHub, HuggingFace, DBs,
    dispositivos, VPS, agentes A2A, mensajería). Todo destino/origen se
    declara como un `Conector` con contrato único (Enchufe v2.0). El core
    nunca improvisa arquitectura: identifica categoría de tarea y activa
    una plantilla DAG (T01-T12) previamente validada.
  resultado_final: >
    Repositorio backend único (`maxbry-router/`, arquitectura hexagonal)
    desplegable en GitHub + entorno web + local, que expone API REST/WS
    para los 5 paneles (ya diseñados, se integran después), con motor DAG
    determinista, Enchufe Gate v2.0, catálogo de Conectores, Bóveda de
    secretos, Sandbox dual (Docker + fallback subprocess), y mecanismo de
    "ventanas encadenables" (1-100) para equipos de IA configurables por
    el usuario sin tocar el código fuente.

SCOPE:
  in_scope:
    - "Motor DAG determinista: DAGParser + DAGOrchestrator + templates T01-T12 fijas"
    - "Enchufe Gate v2.0 (validator_v2.py, ~260 LOC ya diseñado) + compatibilidad v1.5"
    - "Catálogo de Conectores (Protocol enviar()/sondear()): HTTP, MCP, GitHub, HuggingFace, DB, SSH/VPS, A2A, ACP, Mensajería"
    - "RedUniversal: namespaces, rutas fnmatch, 3 modos envío (primero/todos/espejo), salud por nodo"
    - "R1-R10 + Cost Optimizer del RouterCore (ver GAP_01_ROUTER.md para estado real)"
    - "InboundGatekeeper (Alcabala): firma SHA-256, extracción/desencriptado de tokens, validación Pydantic estricta"
    - "SecretVault: cifrado en reposo, rotación, referencias (nunca secretos en claro)"
    - "CodeSandbox dual: Docker cuando disponible + fallback subprocess con límites de recursos"
    - "Mecanismo de ventanas encadenables 1-100 (generalización de ventanas/cadena.py) para equipos de IA/agentes configurables por el usuario"
    - "Persistencia: Postgres/Redis por defecto, detrás de enchufe plugin de storage"
    - "API REST + WebSocket/SSE que alimentará los paneles (ya diseñados, no se tocan ahora)"
    - "Utilidad de respaldo/backup (zip + manifiesto SHA-256) — reciclable de respaldo.py"
  out_of_scope_ahora:
    - "Frontend/UI: los 15 HTML recibidos son referencia de contrato de API, no se modifican en esta fase"
    - "Lógica interna específica de planner/critic/verifier/consensus/judge — el usuario la define por ventana, no se construye como módulo fijo"
    - "Integración real de los 17 repos open-source listados (se evalúan para reciclar componentes puntuales, no se importan completos)"
    - "Workflow M3(Mavis)↔M2.7 de despliegue autónomo — es referencia de proceso, no forma parte del código del router salvo que se indique lo contrario"
  constraints:
    - "Backend Python (+ cualquier lenguaje ejecutable dentro de una ventana/sandbox)"
    - "95% código determinista / 5% LLM (regla 90/10 del prompt maestro, reforzada aquí a 95/5 por el usuario)"
    - "REUSE > PATCH > ADAPT > GENERATE — no reescribir lo que ya existe y sirve"
    - "TASK_LIMIT_CHAT_B: 2000 LOC estimadas · CODE_BLOCK_LIMIT: 500 LOC"
    - "Secretos siempre por variable de entorno / vault, nunca hardcodeados"
    - "Fuente de verdad del código vive en GitHub"

INPUTS:
  documentos_arquitectura:
    - "______resumen_ROUTER_INTELIGENTE_UNIVERSAL_v6.md — arquitectura maestra v6 (capas, catálogo conectores, R1-R10+R2.5, roadmap)"
    - "__router-funciones.md — 98 funciones · 5 paneles (contrato funcional UI↔API)"
    - "_____FABLES_...ENCHUFE_UNIVERSAL_v2.md — contrato Enchufe v2.0 (schema JSON completo + validator_v2.py ~260 LOC)"
    - "______UI_ROUTER_AI_AGENT_Router_UI_Design.md — diseño UI 33 secciones (referencia de contrato, no se construye ahora)"
    - "_______diseño_avanzado_router_inteligente.md — transcript de diseño: DAG templates T01-T12, router.py/classifier.py, reasoning modules"
    - "GAP_01_ROUTER.md — estado real construido vs diseñado (R1-R10)"
    - "2__ROUTER_UNIVERSAL_RED_CONEXIONES.md — CÓDIGO REAL: enchufe_gate.py, conectores.py, red_universal.py"
    - "MASTER-WORKFLOW_Mavis_a_github.md — workflow de despliegue (referencia de proceso)"
    - "REPOSITORIOS_FRONTEND_RECICLABLES...md — 17 repos open-source candidatos a reciclaje"
    - "Mensajes del usuario: arquitectura hexagonal (DDD), respuestas Q1-Q5, ventanas/cadena"
  codigo_html_referencia_contrato:
    - "__panel_router_3.html, _panel_tren_vivo.html, ___router-v1-lista.html, _ventanas_del_tren.html,
       __patch-1.html, __parche-v5_4.html, _panel_auditor_ios.html, __tarea-1-1.html,
       _panel_orquestador.html, router-v5-agente.html, router-v2a-entrada.html,
       router-v3-extras.html, router-v4-conectores.html, router-v2c-otras.html,
       router-v2b-anclaje.html"
  codigo_reciclable_utilitario:
    - "respaldo_py.pdf → respaldo.py: empaquetar()/verificar(), zip + manifiesto SHA-256"

OUTPUTS:
  - "DOC-A01_PROJECT_ANALYSIS.md (este documento)"
  - "MISSION_CONTRACT + GOAL_LOCK (siguiente)"
  - "Ask Council 12 puntos (siguiente)"
  - "DOC-A02_ARCHITECTURE.md"
  - "DOC-A03_WORKFLOW_DAG.yaml"
  - "DOC-A04_FILE_ROOT_MAP.md"
  - "DOC-A05_DEPENDENCY_MAP.json"
  - "N prompts CHAT-BXX.md (uno por task, ≤2000 LOC c/u)"

EXISTING_CODE:
  - id: "red.enchufe_gate"
    archivo: "red/enchufe_gate.py"
    loc_aprox: 180
    estado: "EXISTING_COMPLETE"
    fuente: "2__ROUTER_UNIVERSAL_RED_CONEXIONES.md"
    nota: "validar_contrato_conexion() ya implementado contra contrato v1.5. Debe extenderse a v2.0 (compatibilidad hacia atrás garantizada por diseño del schema)."
  - id: "red.conectores"
    archivo: "red/conectores.py"
    loc_aprox: 380
    estado: "EXISTING_PARTIAL"
    fuente: "2__ROUTER_UNIVERSAL_RED_CONEXIONES.md"
    nota: "Protocol Conector base + ConectorHTTP existen. Faltan los [nuevo] de v6: ConectorHuggingFace, ConectorDB, ConectorGitLab, ConectorMCPApp, ConectorMCPTunnel, ConectorA2A, ConectorACP, ConectorSSH, ConectorBotPersistente, SkillPackImporter."
  - id: "red.red_universal"
    archivo: "red/red_universal.py"
    loc_aprox: 350
    estado: "EXISTING_COMPLETE"
    fuente: "2__ROUTER_UNIVERSAL_RED_CONEXIONES.md"
  - id: "core.auth"
    archivo: "auth.py"
    estado: "MISSING (reclasificado — no hay archivo real, solo descripción)"
    fuente: "GAP_01_ROUTER.md"
    nota: "GENERATE completo: cifrado AES-256 en reposo, rotación automática, soporte BYOK"
  - id: "core.seleccion"
    archivo: "seleccion.py"
    estado: "MISSING (reclasificado)"
    fuente: "GAP_01_ROUTER.md"
    nota: "GENERATE con reglas en capability.json editable desde el inicio (no hardcodear)"
  - id: "core.cola_balanceo"
    archivo: "cola.py + balanceo.py"
    estado: "MISSING (reclasificado)"
    fuente: "GAP_01_ROUTER.md"
    nota: "GENERATE con agrupación en lotes (batch_size=20, overlap=5) desde el inicio"
  - id: "core.providers"
    archivo: "providers.yaml"
    estado: "MISSING (reclasificado)"
    fuente: "GAP_01_ROUTER.md"
  - id: "core.ledger"
    archivo: "ledger (hash-chain)"
    estado: "MISSING (reclasificado)"
    fuente: "GAP_01_ROUTER.md"
    nota: "GENERATE — diseño (hash-chain append-only) ya está bien definido en el prompt maestro sección 33"
  - id: "core.audit_bus"
    archivo: "audit_bus"
    estado: "MISSING (reclasificado)"
    fuente: "GAP_01_ROUTER.md"
    nota: "GENERATE con trazas OTel-like completas por trace_id desde el inicio, no solo duración"
  - id: "enchufe.validator_v2"
    archivo: "enchufe/validator_v2.py"
    loc_aprox: 260
    estado: "EXISTING_COMPLETE (diseño), PENDIENTE_INTEGRAR"
    fuente: "FABLES_ENCHUFE_UNIVERSAL_v2.md"
    nota: "Código completo ya redactado en el documento; falta colocarlo en el repo real y conectarlo al Gate."
  - id: "utils.respaldo"
    archivo: "respaldo.py"
    loc_aprox: 40
    estado: "EXISTING_COMPLETE"
    fuente: "respaldo_py.pdf"
    nota: "empaquetar()/verificar() — reusar tal cual en infrastructure/storage o como script de mantenimiento"
  - id: "ventanas.cadena_prototipo"
    archivo: "_ventanas_del_tren.html (script inline, espejo JS de ventanas/cadena.py)"
    estado: "EXISTING_PARTIAL (solo prototipo JS de referencia, falta el cadena.py real en Python)"
    nota: "Confirma semántica esperada: Estacion/Cadena con pausa, breakpoint, intervención manual, export a nodos DSL. Se debe construir el equivalente Python determinista + generalizarlo a 1-100 ventanas configurables."

MISSING_CODE:
  - "R5 Retry (backoff exponencial configurable por nodo) — no construido"
  - "R6 Circuit Breaker completo (CLOSED→OPEN→HALF_OPEN con ventana temporal) — diseño ya redactado en v6, no implementado"
  - "R8 Semantic Cache (embeddings + similitud) — no construido"
  - "Cost Optimizer — no construido"
  - "InboundGatekeeper (Alcabala) como middleware FastAPI real"
  - "DAGParser / DAGOrchestrator / GraphExecutionPlan"
  - "CodeSandbox (Docker) + fallback subprocess"
  - "Motor de ventanas encadenables generalizado (Python, no solo el prototipo JS)"
  - "capability.json (reglas de selección de modelo editables)"
  - "SecretVault con cifrado (cryptography.fernet o AES-256 explícito)"
  - "Conectores nuevos de v6 (HuggingFace, DB, GitLab, MCPApp, MCPTunnel, A2A, ACP, SSH, BotPersistente, SkillPackImporter)"

PARTIAL_CODE: "Ver EXISTING_CODE con estado EXISTING_PARTIAL (7 módulos)."

INVALID_CODE: "Ninguno detectado por el momento (UNKNOWN — no se ha ejecutado el repo real, solo se auditaron documentos/snippets)."

DEPENDENCIES:
  externas:
    - "FastAPI (API REST + WS/SSE)"
    - "Pydantic v2 (validación de esquemas estricta)"
    - "docker SDK (CodeSandbox, modo Docker)"
    - "cryptography (Fernet/AES-256, SecretVault)"
    - "asyncpg / aiomysql / redis.asyncio (ConectorDB, storage)"
    - "httpx o aiohttp (ConectorHTTP async)"
  internas_entre_tasks:
    - "enchufe_gate + validator_v2 → precondición de red_universal y de todo Conector nuevo"
    - "SecretVault → requerido por auth.py, ConectorDB, ConectorGitHub/HuggingFace"
    - "DAGParser/Orchestrator → requerido por motor de ventanas encadenables"
    - "CodeSandbox → requerido por motor de ventanas encadenables (ejecución real del código por ventana)"

RISKS:
  - "R6/R5/R8 sin construir: sin ellos el sistema es frágil ante fallos repetidos de proveedores (ya señalado en GAP_01)"
  - "Docker no garantizado en destino de despliegue → obliga a mantener DOS rutas de ejecución (Docker/subprocess) sincronizadas en contrato, no solo una con fallback silencioso"
  - "Migración v1.5→v2.0 del Enchufe: hay fichas activas bajo v1.5 (paneles ya diseñados las usan) — la compatibilidad hacia atrás es OBLIGATORIA, no opcional"
  - "El mecanismo de ventanas encadenables ejecuta código arbitrario del usuario: requiere sandboxing estricto (esto ya está contemplado, pero es el punto de mayor superficie de riesgo de seguridad del proyecto)"
  - "No se ha confirmado si el código real de auth.py/seleccion.py/cola.py/balanceo.py/providers.yaml/ledger/audit_bus está disponible como archivos (solo hay descripción en GAP_01_ROUTER.md) — UNKNOWN, ver OPEN_ISSUES"

OPEN_ISSUES:
  - id: "OI-01"
    estado: "RESUELTO"
    respuesta: >
      No existen archivos reales para auth.py, seleccion.py, cola.py, balanceo.py,
      providers.yaml, ledger, audit_bus más allá de la descripción de
      GAP_01_ROUTER.md. Reclasificados de EXISTING_PARTIAL a MISSING
      (se GENERAN desde la descripción, no hay archivo que hacer PATCH/ADAPT).
      El único código real reutilizable tal cual es: enchufe_gate.py,
      conectores.py, red_universal.py, validator_v2.py (diseño completo en
      texto, falta integrarlo al repo) y respaldo.py. El usuario preparará
      además un README actualizado con ~26 repos reciclables (pendiente de
      subir) para fusionar componentes puntuales antes de generar desde cero.
  - id: "OI-02"
    estado: "RESUELTO"
    respuesta: >
      REPO ÚNICO. Los repos reciclables (zips de código fuente de terceros)
      se fusionan/suben dentro del repo único "router universal inteligente"
      en GitHub. Estructura hexagonal (maxbry-router/) confirmada como
      contenedor final.
  - id: "OI-03"
    estado: "RESUELTO"
    respuesta: >
      NO es un componente del backend. MASTER-WORKFLOW (Mavis M3↔M2.7) es
      solo referencia de proceso de despliegue, no se traduce a código en
      este proyecto. Además se confirma el alcance real del 5% LLM: limitado
      a asistencia de auto-relleno de fichas de conexión / búsqueda de
      información (tipo Perplexity) — no un motor de razonamiento complejo.
      Esa mejora específica queda fuera de esta fase (la planifica el
      usuario por separado); el backend solo debe dejar el punto de
      extensión (hook) donde esa asistencia se conectaría después.

GOALS:
  mission_goal: "Backend determinista de enrutamiento universal, ver OBJECTIVE"
  desired_result: "Repo maxbry-router funcional, con motor DAG + Enchufe v2.0 + Conectores + Sandbox + Ventanas + Persistencia, listo para que los 5 paneles se conecten via API"
  in_scope: "Ver SCOPE.in_scope"
  out_of_scope: "Ver SCOPE.out_of_scope_ahora"
  constraints: "Ver SCOPE.constraints"
  success_conditions:
    - "Todo Conector cumple Protocol enviar()/sondear() y pasa Enchufe Gate v2.0"
    - "R1-R10 + Cost Optimizer completos y testeados (cerrando los 7 gaps de GAP_01_ROUTER.md)"
    - "CodeSandbox ejecuta ventanas en Docker y en fallback subprocess con paridad de contrato"
    - "0 secretos en código o en trazabilidad; solo referencias de vault"
  definition_of_done: "PASS de la sección 40 del prompt maestro (READY_FOR_CHAT_B) + FINAL_INTEGRATION_REPORT con todos los módulos COMPLETED"

ASK_COUNCIL: "Pendiente — se ejecuta en el siguiente documento (12 puntos) tras resolver OI-01, OI-02, OI-03."

FINAL_ANALYSIS: >
  Hay material más que suficiente para construir la arquitectura completa
  (DOC-A02) y el DAG. El proyecto NO parte de cero: existen 3 archivos
  Python completos (enchufe_gate, conectores, red_universal), un validador
  v2.0 ya redactado, y 7 módulos parciales bien diagnosticados. El riesgo
  principal no es de diseño sino de trazabilidad de origen: 3 preguntas
  (OI-01, OI-02, OI-03) deben resolverse antes de fijar el ROOT_MAP y el
  DEPENDENCY_MAP definitivos, para no asumir por inferencia algo que
  after podría contradecir el código real del usuario.
```

---

## Nota para el usuario

Este documento es DRAFT. Antes de pasar a MISSION_CONTRACT + ASK_COUNCIL (12 puntos) y congelar la arquitectura, necesito que resuelvas **OI-01, OI-02 y OI-03** (arriba). Si prefieres, puedo asumir defaults razonables y avanzar marcándolos como ASSUMPTION corregible — dime cuál prefieres.

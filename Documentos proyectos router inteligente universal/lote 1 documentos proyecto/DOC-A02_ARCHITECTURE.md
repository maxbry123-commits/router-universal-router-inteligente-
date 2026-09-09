# DOC-A02_ARCHITECTURE.md
ROLE: CHAT A — ARCHITECT
STATUS: DRAFT — pendiente confirmación antes de DOC-A03 (DAG)
BASE: DOC-A00 (Mission Contract, AUTHORIZE) + DOC-A01 (Project Analysis)

---

## 0. Vista general

```
USUARIO/PANELES 1-5 ⇄ [API Gateway + Alcabala] ⇄ [Engine: DAG/Sandbox/Ventanas] ⇄ [RED: Enchufe+Conectores] ⇄ Destinos reales
                                    ↑                        ↑
                          [SecretVault/Auth]        [Audit Logger + Monitoring]
```

Estructura de carpetas (repo único `maxbry-router/`, hexagonal, respeta código REUSE existente sin mover archivos que ya funcionan):

```
maxbry-router/
├── api/
│   ├── middlewares/alcabala.py            # C02
│   ├── routers/                           # C01 — endpoints Panel 1-5
│   └── ws/events.py                       # C23
├── core/
│   ├── config.py                          # C03
│   ├── secret_vault.py                    # C04
│   ├── auth.py                            # C20 (R1)
│   ├── ledger.py                          # C21 (R9)
│   └── monitoring.py                      # C22 (R10)
├── domain/
│   ├── schemas/enchufe_v2.py              # C05
│   └── dsl/
│       ├── dag_parser.py                  # C06
│       └── templates/T01..T12.yaml        # C07
├── engine/
│   ├── dag_orchestrator.py                # C08
│   ├── worker_pool.py                     # C09 (R2/R3/R4)
│   ├── resilience.py                      # C10 (R5 Retry + R6 Circuit Breaker)
│   ├── semantic_cache.py                  # C11 (R8)
│   ├── cost_optimizer.py                  # C12
│   ├── sandbox/code_sandbox.py            # C13
│   └── windows_chain.py                   # C14 (ventanas 1-100)
├── red/                                    # REUSE — no se renombra, ya existe y funciona
│   ├── enchufe_gate.py                    # C15 [EXISTING_COMPLETE]
│   ├── conectores.py                      # C16 [EXISTING_PARTIAL → se amplía]
│   └── red_universal.py                   # C17 [EXISTING_COMPLETE]
├── infrastructure/
│   ├── storage/                           # C18 (Postgres/Redis + plugin abstracto)
│   └── backup/respaldo.py                 # C19 [EXISTING_COMPLETE — reuse tal cual]
└── enchufe/
    └── validator_v2.py                    # de FABLES_ENCHUFE_UNIVERSAL_v2.md [EXISTING_COMPLETE — integrar]
```

---

## 1. Componentes

```yaml
component_id: C01
name: "API Gateway"
objective: "Exponer contrato REST/WS que consumirán los 5 paneles (98 funciones ya especificadas)"
responsibility: "Enrutar HTTP/WS a domain/engine; NUNCA contener lógica de negocio"
input: "HTTP requests, WS connections desde paneles 1-5"
output: "JSON responses, WS events (connection.update, chat.token, cb.open, cost.update...)"
dependencies: [C02, C04, C09, C23]
files: ["api/routers/connections.py", "api/routers/connectors.py", "api/routers/agent.py", "api/routers/extras.py"]
calls: [C08, C09, C16]
reads: ["domain.schemas.enchufe_v2"]
writes: []
failure: "Rebote inmediato con error Pydantic si el payload no cumple schema"
recovery: "Stateless — no requiere recovery propio, delega a engine"
status: MISSING
---
component_id: C02
name: "InboundGatekeeper (Alcabala)"
objective: "Middleware único de entrada: firma, desencriptado de tokens, validación estricta"
responsibility: "verify_payload_signature(), extract_and_decrypt_tokens(), enforce_schema()"
input: "Request crudo"
output: "Request mutado con trace_id inyectado, o rechazo 4xx"
dependencies: [C04, C05]
files: ["api/middlewares/alcabala.py"]
calls: [C04]
reads: ["domain.schemas.enchufe_v2"]
writes: ["core.ledger (evento de auditoría)"]
failure: "Bloquea (fail closed) — UNKNOWN/firma inválida nunca pasa"
recovery: "N/A — rechazo es la recuperación correcta"
status: MISSING
---
component_id: C03
name: "Config inmutable"
objective: "Cargar configuración de entorno (env vars) una sola vez, inmutable en runtime"
responsibility: "Fuente única de verdad de configuración; nunca secretos en claro"
input: "Variables de entorno"
output: "Objeto Config inmutable (frozen dataclass/Pydantic Settings)"
dependencies: []
files: ["core/config.py"]
calls: []
reads: ["os.environ"]
writes: []
failure: "Falla al boot si falta variable requerida (fail fast)"
recovery: "N/A"
status: MISSING
---
component_id: C04
name: "SecretVault"
objective: "Cifrado en reposo + rotación de credenciales de conectores (R1)"
responsibility: "guardarSecreto(), get() → token_ref (nunca el secreto real fuera del vault)"
input: "Secreto en claro (solo al momento de guardar) o token_ref"
output: "token_ref / secreto desencriptado en memoria (efímero, no logueado)"
dependencies: [C03]
files: ["core/secret_vault.py"]
calls: []
reads: ["storage cifrado"]
writes: ["storage cifrado (AES-256/Fernet)"]
failure: "Rotación vencida → alerta 7 días antes; fallo de desencriptado → BLOCKER CONTRACT_FAILURE"
recovery: "Reintento con rotación manual si BYOK inválido"
status: MISSING
---
component_id: C05
name: "Enchufe Schema (Pydantic v2)"
objective: "Modelos Pydantic que reflejan 1:1 el JSON Schema Enchufe v2.0"
responsibility: "Validación estructural de toda ficha antes de llegar al Gate"
input: "dict/JSON de ficha"
output: "Modelo validado o ValidationError"
dependencies: []
files: ["domain/schemas/enchufe_v2.py"]
calls: []
reads: []
writes: []
failure: "ValidationError propagada a Alcabala"
recovery: "N/A"
status: NEW
---
component_id: C06
name: "DAGParser"
objective: "Convertir YAML/JSON de una template T01-T12 en GraphExecutionPlan"
responsibility: "Detectar ciclos, validar nodos/aristas antes de ejecutar"
input: "dict YAML/JSON de template"
output: "GraphExecutionPlan (nodos + dependencias resueltas)"
dependencies: [C07]
files: ["domain/dsl/dag_parser.py"]
calls: []
reads: ["domain/dsl/templates/*.yaml"]
writes: []
failure: "Ciclo detectado → ARCHITECTURE_CONFLICT (rechaza, no ejecuta)"
recovery: "N/A — corrección manual de la template"
status: MISSING
---
component_id: C07
name: "Template Registry (T01-T12)"
objective: "Catálogo fijo de plantillas DAG — el router NUNCA improvisa arquitectura"
responsibility: "Clasificar tarea entrante → seleccionar UNA template ya validada"
input: "Categoría de tarea (del clasificador)"
output: "Template YAML seleccionada"
dependencies: []
files: ["domain/dsl/templates/T01_simple.yaml", "...T12_deep_reasoning.yaml"]
calls: []
reads: []
writes: []
failure: "Categoría sin template → BLOCKER TASK_TOO_LARGE o ARCHITECTURE_CONFLICT según caso"
recovery: "Fallback a T01_simple si está definido como default"
status: MISSING
---
component_id: C08
name: "DAGOrchestrator"
objective: "Ejecutar GraphExecutionPlan recorriendo el grafo topológicamente"
responsibility: "execute_graph(plan); paraleliza nodos independientes vía asyncio.gather"
input: "GraphExecutionPlan"
output: "Resultado consolidado por nodo + estado final del run"
dependencies: [C06, C09, C10, C13, C14, C16]
files: ["engine/dag_orchestrator.py"]
calls: [C09, C13, C14, C16, C21]
reads: []
writes: ["core.ledger", "core.monitoring"]
failure: "Nodo falla → según policy: retry (C10) o propaga FAILED"
recovery: "Checkpoint por nodo completado — reanuda sin repetir nodos DONE (sección 33 prompt maestro)"
status: MISSING
---
component_id: C09
name: "Worker Pool (R2 Selector + R3 Cola/Balanceo + R4 Health)"
objective: "Seleccionar modelo/conector candidato, agrupar en lotes, evitar nodos caídos"
responsibility: "Model Selector via capability.json + batching (batch_size=20, overlap=5) + sondeo 30s"
input: "Tarea + lista de candidatos"
output: "Candidato seleccionado + cola priorizada"
dependencies: [C12, C16]
files: ["engine/worker_pool.py", "domain/dsl/capability.json"]
calls: [C12, C16]
reads: ["capability.json", "providers.yaml (regenerado, ver C-missing providers)"]
writes: ["core.monitoring (p95/p99 latencia)"]
failure: "Sin candidatos sanos → BLOCKER DEPENDENCY_MISSING"
recovery: "Reintenta con siguiente candidato de la cola"
status: MISSING
---
component_id: C10
name: "Resilience (R5 Retry + R6 Circuit Breaker)"
objective: "Reintentos con backoff exponencial + corte automático de proveedor fallido"
responsibility: "configReintentos(n); estado CLOSED→OPEN→HALF_OPEN con ventana temporal"
input: "Llamada a conector + historial de fallos"
output: "Resultado exitoso, o estado OPEN (salta al siguiente)"
dependencies: [C16]
files: ["engine/resilience.py"]
calls: [C16]
reads: []
writes: ["core.monitoring (evento cb.open)"]
failure: "5 fallos en ventana 60s → OPEN; recovery tras 30s a HALF_OPEN"
recovery: "Automática (diseño ya completo en resumen v6.md §6, reusar tal cual)"
status: MISSING
---
component_id: C11
name: "Semantic Cache (R8)"
objective: "Evitar recálculo de respuestas muy similares"
responsibility: "Embeddings de petición → similitud > umbral → devuelve cacheado"
input: "Petición"
output: "Respuesta cacheada (hit) o None (miss)"
dependencies: [C18]
files: ["engine/semantic_cache.py"]
calls: [C18]
reads: ["Redis (vector similarity)"]
writes: ["Redis"]
failure: "Cache miss no es error — continúa flujo normal"
recovery: "N/A"
status: MISSING
---
component_id: C12
name: "Cost Optimizer"
objective: "Reordenar candidatos por costo en empate de score; presupuesto por categoría"
responsibility: "Corre después de R2.5/Selector; proyección de costo antes de tareas grandes"
input: "Lista de candidatos con score"
output: "Lista reordenada por costo"
dependencies: []
files: ["engine/cost_optimizer.py"]
calls: []
reads: ["presupuesto (Enchufe v2.0 campo presupuesto)"]
writes: ["core.monitoring (cost.update)"]
failure: "Presupuesto excedido → BLOCKER o degrade a modelo más barato según policy"
recovery: "N/A"
status: MISSING
---
component_id: C13
name: "CodeSandbox (dual)"
objective: "Ejecutar código arbitrario (YAML/Python/JSON) inyectado desde UI sin tocar GitHub"
responsibility: "spin_container()/inject_and_run()/teardown() en Docker; fallback subprocess con límites de recursos si Docker no está disponible"
input: "script_content, env_vars, límites (timeout_ms, max_memoria_mb)"
output: "stdout/stderr/exit_code"
dependencies: [C04]
files: ["engine/sandbox/code_sandbox.py", "engine/sandbox/docker_backend.py", "engine/sandbox/subprocess_backend.py"]
calls: []
reads: []
writes: ["core.ledger (evidencia de ejecución)"]
failure: "Timeout/OOM → kill del contenedor/proceso, evidencia registrada"
recovery: "teardown() garantizado incluso en fallo (try/finally obligatorio)"
status: MISSING
---
component_id: C14
name: "Windows Chain (ventanas encadenables 1-100)"
objective: "Generalizar el prototipo ventanas/cadena.py: N ventanas con código propio, in/out, pausa/breakpoint/intervención, export a DSL"
responsibility: "Permitir al usuario cablear un equipo de 1-100 IA/agentes sin tocar el código fuente del router"
input: "Lista ordenada de ventanas (código por ventana) + payload inicial"
output: "Payload final + fotos in/out por ventana + export a nodos DAG"
dependencies: [C13, C06]
files: ["engine/windows_chain.py"]
calls: [C13, C06]
reads: []
writes: ["core.ledger"]
failure: "Ventana falla → estado failed, cadena se detiene (igual que prototipo JS ya visto)"
recovery: "Intervención manual (aplicar payload editado y continuar) — ya prototipado en _ventanas_del_tren.html"
status: NEW
---
component_id: C15
name: "Enchufe Gate"
objective: "Aduana de la red — ningún conector entra sin contrato válido"
responsibility: "validar_contrato_conexion() — extender de v1.5 a v2.0 con compatibilidad"
input: "dict de conexión"
output: "VeredictoGate(valido, errores)"
dependencies: [C05]
files: ["red/enchufe_gate.py"]
calls: []
reads: []
writes: []
failure: "Errores acumulados en veredicto, nunca pasa parcialmente"
recovery: "N/A — corrección de la ficha"
status: EXISTING_COMPLETE
---
component_id: C16
name: "Conectores"
objective: "Adaptadores concretos Protocol enviar()/sondear() a cada destino externo"
responsibility: "Un dataclass por sistema externo; el core nunca cambia al agregar uno nuevo"
input: "payload dict"
output: "dict de respuesta"
dependencies: [C04, C15]
files: ["red/conectores.py"]
calls: []
reads: []
writes: []
failure: "Excepción de red → propagada a C10 (Resilience)"
recovery: "Delegada a C10"
status: EXISTING_PARTIAL
---
component_id: C17
name: "RedUniversal"
objective: "Grafo de nodos + reglas de ruteo por namespace (fnmatch)"
responsibility: "_resolver() aplica Rutas → lista de NodoRed sanos; 3 modos de envío"
input: "Mensaje + namespace origen"
output: "Lista de NodoRed candidatos"
dependencies: [C15, C16]
files: ["red/red_universal.py"]
calls: [C16]
reads: []
writes: []
failure: "Sin nodos sanos → propaga a C09/C10"
recovery: "Delegada"
status: EXISTING_COMPLETE
---
component_id: C18
name: "Storage (Postgres/Redis + plugin abstracto)"
objective: "Persistencia de configs (agentes/conectores/credenciales) + cache vectorial"
responsibility: "Interfaz abstracta de storage; implementación default Postgres+Redis"
input: "operaciones CRUD"
output: "resultado de la operación"
dependencies: []
files: ["infrastructure/storage/postgres_adapter.py", "infrastructure/storage/redis_adapter.py", "infrastructure/storage/storage_protocol.py"]
calls: []
reads: []
writes: []
failure: "Conexión caída → BLOCKER DEPENDENCY_MISSING al boot"
recovery: "Reintento de conexión con backoff"
status: MISSING
---
component_id: C19
name: "Backup (respaldo.py)"
objective: "Empaquetar proyecto en zip + manifiesto SHA-256 + verificación de integridad"
responsibility: "empaquetar(origen, destino_zip), verificar(zip_ruta)"
input: "Ruta de origen / ruta de zip"
output: "dict con resultado (ok, archivos, rotos)"
dependencies: []
files: ["infrastructure/backup/respaldo.py"]
calls: []
reads: ["filesystem"]
writes: ["zip + manifiesto"]
failure: "Archivo roto detectado → reporta en 'rotos', no falla silenciosamente"
recovery: "N/A — es la herramienta de recovery de otros componentes"
status: EXISTING_COMPLETE
---
component_id: C20
name: "Auth & API Key Manager (R1)"
objective: "Gestión de identidad y llaves de acceso al propio Router"
responsibility: "Emitir/validar sesiones; delega cifrado a C04"
input: "Credenciales de usuario/servicio"
output: "Token de sesión válido"
dependencies: [C04]
files: ["core/auth.py"]
calls: [C04]
reads: []
writes: ["core.ledger"]
failure: "Credencial inválida → 401, evento en ledger"
recovery: "N/A"
status: MISSING
---
component_id: C21
name: "Audit Logger / Ledger (R9)"
objective: "Hash-chain append-only de todo evento del sistema"
responsibility: "Registrar cada acción con trace_id + task_id"
input: "Evento (dict)"
output: "Entrada encadenada (hash del evento anterior + actual)"
dependencies: []
files: ["core/ledger.py"]
calls: []
reads: []
writes: ["ledger append-only"]
failure: "Nunca debe fallar silenciosamente — si falla, el sistema debe BLOCKER"
recovery: "N/A por diseño (append-only, sin rollback destructivo)"
status: MISSING
---
component_id: C22
name: "Monitoring (R10)"
objective: "Métricas tipo OTel: traces distribuidos por trace_id a través de todos los conectores"
responsibility: "Cerrar trace_id con latencia total; alertas de costo/hora"
input: "Eventos de spans de cada componente"
output: "Panel de métricas (consumido por Panel 3 vía WS)"
dependencies: [C21]
files: ["core/monitoring.py"]
calls: []
reads: []
writes: ["WS events: provider.status, cost.update, queue.update"]
failure: "Métrica faltante no bloquea ejecución, solo degrada observabilidad"
recovery: "N/A"
status: MISSING
---
component_id: C23
name: "WebSocket/SSE Events"
objective: "Canal en tiempo real hacia los paneles"
responsibility: "Emitir connection.update, chat.token, cb.open, cost.update, queue.update"
input: "Eventos internos de engine/red"
output: "Mensajes WS/SSE al frontend"
dependencies: [C22]
files: ["api/ws/events.py"]
calls: []
reads: []
writes: []
failure: "Cliente desconectado → buffer descartado, no bloquea backend"
recovery: "Reconexión del lado del cliente (fuera de alcance backend)"
status: MISSING
```

---

## 2. Reglas de integración fijadas por esta arquitectura

1. `red/` NO se reestructura — es código existente (C15, C16, C17) que funciona; se EXTIENDE (nuevos Conectores) pero no se reescribe.
2. Todo componente MISSING se genera respetando el Protocol/Schema ya definido por los componentes EXISTING (C05 debe ser espejo exacto del schema de FABLES_ENCHUFE_UNIVERSAL_v2.md).
3. El punto de extensión para la futura mejora "auto-relleno/búsqueda tipo Perplexity" (fuera de alcance ahora) es un hook en C01 (API Gateway) — no se implementa, solo se deja el contrato de extensión documentado.
4. C13 (CodeSandbox) y C14 (Windows Chain) son los de mayor riesgo de seguridad — llevan condición del Ask Council punto 7: límites de recursos obligatorios en AMBOS backends (Docker y subprocess).
5. C09/C10/C11/C12 cierran los 7 gaps de GAP_01_ROUTER.md — son GENERATE completo, sin código previo real que reusar.

---

## Siguiente paso

Con la arquitectura fijada, sigo con:
- **DOC-A03_WORKFLOW_DAG.yaml** (nodos ejecutables del propio proceso de construcción, no confundir con las templates T01-T12 que son del producto)
- **DOC-A04_FILE_ROOT_MAP.md**
- **DOC-A05_DEPENDENCY_MAP.json**

¿Continúo con DOC-A03 (DAG)?

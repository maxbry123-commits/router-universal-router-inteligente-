# CLAUDE NOTAS - memoria.md (Router Inteligente Universal)
RAIZ UNICA DE MEMORIA DE ESTE CLAUDE PARA ESTE REPO, creada 2026-09-18.
Replica el metodo del Claude que trabaja en repo `agentes` (ver
`agentes/Claude notas/memoria.md`). Este archivo NUNCA se resume. Se
actualiza anadiendo, nunca borrando historia. Todo mi contexto desde este
momento vive aqui.

## 0. AUTORIZACION Y ALCANCE (verbatim del Director, 2026-09-18)
- P1: SI, autorizado a iniciar.
- P2: autorizado a reparar en el camino, sin necesidad de escalar, sin
  detenerme, resolviendo GAPs disponibles dentro del alcance. "100
  autorizado."
- P3: SOLO puedo crear/escribir archivos en este repo
  (`router-universal-router-inteligente-`). Nunca escribo en `agentes` ni
  en ningun otro repo del ecosistema.
- P4: root ya existe con Claude notas parciales en `agentes`; debo
  replicar el metodo, no reinventarlo.

## 1. QUE ES ESTO
Soy Claude, y mi centro de trabajo es el Router Inteligente Universal.
Fables hizo parte del codigo fuente y arquitectura inicial de este repo.
Mi mision: auditar forense x-ray, entender, planificar la integracion de
componentes (deterministico 95% / LLM 5% como norma fija), dejar
operativo Hugging Face, y cerrar el Router en GitHub para que sea el
proveedor central de API keys de mas de 50 wordflows/agentes.

## 2. EL ECOSISTEMA COMPLETO (7 proyectos, segun agentes/Claude notas/memoria.md)
1. Agente Yaiwes - repo `agentes`
2. Osquestador Maxbry - repo `Orquestador-Maxbry-`
3. Router Inteligente Universal - repo `router-universal-router-inteligente-` -- ESTE REPO, mi centro de trabajo
4. UI Yaiwes - repo `nct-hub` (hipotesis)
5. Fabrica de UI - repo `frontend`
6. Osquestador auditor + memoria - repo `osquestador-auditor`
7. NCT - repo `nct-core`

## 3. REQUISITO CRITICO HEREDADO (REQUISITO-50-mundos-y-Router-Universal.md, agentes)
- Habra mas de 50 wordflows/agentes corriendo, cada uno como "mundo"
  independiente (propio Readme/Handoff/Crazy Wall/system prompt), mismo
  patron base (mismo code_sha256, distinto worker_id/task/workspace).
- Cerebras (6 keys ya cableadas en `consultor_experto.py` y
  `router_modelos.py` del repo agentes) es SOLO para pruebas.
- En PRODUCCION, TODOS los wordflows se conectan a ESTE Router como
  proveedor de API keys; el Router decide que modelo/proveedor usar, no
  cada worker con su key hardcodeada.
- `router_modelos.py` y `consultor_experto.py` (repo agentes) deben
  quedar con un adapter que en el futuro apunte al Router Universal en
  vez de a Cerebras directo -- tarea pendiente marcada alli, a resolver
  desde este lado cuando el Router este activo.

## 4. AUDITORIA FORENSE X-RAY REALIZADA 2026-09-18 (pasada 1 de 4)

### 4.1 Metodo de lectura usado
Lei en orden: CLAUDE.md -> Handoff router inteligente universal.md ->
readme indice router inteligente universal.md -> README arquitectura
completo (Readme arquitectura router inteligente universal/README.md,
26KB) -> Readme Indice componentes.md (C01-C23) -> Readme Indice de
modelos de ai huggueface.md -> Fast api key de los modelos de ai en
huggueface.md -> bitacora stated JSON Craxy wall plan checkpoint router
inteligente universal/{STATE.json, CHECKPOINT.json, PLAN-TAREAS.md,
BITACORA-CRAZY-WALL.md} -> forensics/ (listado, 15+ informes RIU-0071 a
RIU-0096).

### 4.2 Estado real consolidado (no inflado, tal como esta en el repo)
- `core_status`: VERIFIED_CLOSED al 100% -- pero ESTO ES SOLO ALCANCE
  HISTORICO (P01 executable set, P02 hot-path, P03 API Key Manager,
  Connectivity Fabric 19/19, suite 75/75, fail-closed). NO equivale a
  cierre global del proyecto.
- `global_closed`: false (CHECKPOINT.json, nodo vivo RIU-0097).
- Arquitectura autoritativa de routing: `RedUniversal` es propietario
  UNICO de routing. Nadie mas -- ni componente externo ni modelo -- puede
  tomar ownership de rutas.
- Cadena AI Staff (contrato REMOTE_INFERENCE_ONLY, ya no mirror/descarga):
  `RedUniversal -> connector_registry -> HF adapter/InferenceClient ->
  Inference Provider/Endpoint remoto -> model_id`.
- Gate obligatorio por modelo antes de READY:
  `REGISTER -> REMOTE_PROVIDER_DISCOVERY -> AUTH_REFERENCE ->
  REMOTE_INFERENCE_SMOKE -> FAILURE_FALLBACK_TEST -> EVIDENCE -> READY`.
- El diseno viejo de mirror/download (`snapshot_download`, hash/load de
  pesos) se PRESERVA como provenance historica pero esta SUPERSEDED; no
  es el camino normal para integrar modelos AI Staff.

### 4.3 Inventario de raiz (28 entradas, RIU-0071, snapshot
`d001d96cfa382888d409255e5dd3e9d2b6372860`)
Regla: raiz presente != runtime integrado. Cada entrada tiene rol +
decision:
1. `.github/` -- CI/CD, REUSE (workflows ejecutores, nunca fuente de contrato)
2. `CLAUDE.md` -- politica de agente, REUSE
3. `Documentos proyectos router inteligente universal/` -- docs/contratos, REUSE/CONSOLIDATE
4. `Download code router inteligente universal/` -- donor/staging, QUARANTINE-DONOR
5. `Fast api key de los modelos de ai en huggueface.md` -- guia HF/API, DOC-ONLY
6. `Github coneccion/` -- workflows GitHub historicos, CONSOLIDATE con conectividad
7. `Handoff router inteligente universal.md` -- handoff operativo, REUSE
8. `PARCHE-RECUPERACION-ROUTER-INTELIGENTE-UNIVERSAL.md` -- RECOVERY-ONLY
9. `Readme arquitectura router inteligente universal/` -- arquitectura canonica, SOURCE-OF-TRUTH
10. `Readme Indice componentes.md` -- indice C01-C23, REUSE
11. `Readme Indice de modelos de ai huggueface.md` -- inventario HF, REVERIFY
12. `Yaiwes Cognitive Control Plane/` -- policy/context/control, ADAPT (nunca reemplaza RedUniversal)
13. `bitacora stated JSON Craxy wall plan checkpoint router inteligente universal/` -- ledger/estado/plan, SOURCE-OF-TRUTH operativo
14. `coneccion huggueface Github/` -- bridge HF<->GitHub, CONSOLIDATE
15. `conectividad con Router inteligente universal/` -- fabric canonico, REUSE
16. `dataset Yaiwes/` -- datasets/schemas/evidence, REUSE bajo schema/manifest
17. `extraction-result.json` -- evidencia extraccion, EVIDENCE-ONLY
18. `forensics/` -- auditoria/forense, REUSE (destino de informes, no runtime)
19. `huggueface/` -- bridge/manifest HF, CONSOLIDATE con integration/huggingface
20. `pre-audit.json` -- evidencia pre-audit, EVIDENCE-ONLY
21. `readme Handoff indice componentes.md` -- handoff componentes, CONSOLIDATE
22. `readme indice router inteligente universal.md` -- indice raiz, REUSE (navegacion)
23. `readme indice de componentes/` -- indice alterno, DEDUP-CANDIDATE
24. `router inteligente software/` -- inventario legado, DONOR/LEGACY
25. `router inteligente universal/` -- **RUNTIME CANONICO** (OWNER): adapters/domain/enchufe/engine/gateway/integration/red/security/tests/verifier
26. `scripts/` -- utilidades auth/repair, REUSE fail-closed
27. `Wordflow LOOP router inteligente universal/` (con emoji) -- metodo LOOP, REUSE como guia
28. `motores de descarga extraccion copiado movimiento archivos router-universal-router-inteligente-/` -- motores de archivos, REUSE-CONTROLLED

NOTA: el probe recursivo global anterior (35.979 entradas) vino
`truncated=true` en GitHub API; NO es el inventario total de archivos.
Sigue abierto `FULL_COMPONENT_CONTAINER_XRAY`.

### 4.4 Duplicados detectados, NINGUNO borrado (regla: nunca borrar sin
provenance completa)
- `LiteLLM` (9977 files, SOURCE_URL=https://github.com/BerriAI/litellm,
  SOURCE_COMMIT=658f50663d19f613a3f5caf998168da019764ad8) vs `litellm`
  (9795 files, sin provenance declarada, incluye litellm_0001..0006.zip).
  9784 paths comunes, 8930 blobs identicos, **854 blobs diferentes**.
  Decision: preservar ambos, `LiteLLM` es donor canonico por provenance.
- Bridges HF candidatos a consolidar (mismo rol, tres ubicaciones):
  `integration/huggingface/`, `coneccion huggueface Github/router`,
  `huggueface/bridge/`.

### 4.5 Componentes externos (W2) -- estado real
| Componente | Rol | Estado |
|---|---|---|
| OmniRoute | gateway downstream opcional detras de connector_registry | MATERIALIZADO como submodule pinneado (`diegosouzapw/OmniRoute@1603c86e`), destino `router inteligente universal/Componente open soure router inteligente universal/OmniRoute/`, read-back verificado (HF Job `6aacbb0c...`). Integracion runtime detras de connector_registry: PENDIENTE |
| AnyDoc | adapter de ingestion documental -> Markdown | boundary definido, runtime/multiformato/error-path PENDIENTE |
| Orca | ADE externo (control plane de agentes en worktrees) | boundary definido, runtime/verifier PENDIENTE. Nunca sustituye tel.workflow/v3 ni ownership de routing |
| Omarchy | host/workstation opcional | sin dependencia runtime, checklist PENDIENTE |

Ninguno de los 4 adquiere ownership del Router. Gate de integracion por
componente: adapter/boundary explicito -> prueba real -> read-back/log ->
sin secreto embebido -> test de fallo -> evidencia URL/SHA/commit.

### 4.6 Hugging Face -- estado real (lo mas critico para mi mision)
- Cuenta: `COMAND-CENTER-1`.
- **0 repos de modelos propios**, **0 mirrors persistentes**, **0
  instalaciones locales persistentes** verificados (Job
  `6aacb9175c02253cfb1461d1`). Los modelos AI Staff son referencias de
  INFERENCIA REMOTA, nunca pesos propios.
- REMOTE20 (inventario recuperado, ver Handoff RIU-0094): 20 model_id
  verificados via `https://router.huggingface.co/v1/models`. Job fresh
  `6aad981352d0dbd7f1d6b827`: **20/20 con >=1 provider live**, pero
  **0/20 con inferencia remota AUTENTICADA** -- fallo 403 "insufficient
  permissions to call Inference Providers" con la credencial disponible
  en ese Job. Clasificacion: `GAP_AUTH_REMOTE_INFERENCE`, NO fallo del
  modelo/provider.
- Lista REMOTE20 completa con providers vivos: ver
  `Handoff router inteligente universal.md` seccion RIU-0094 (Qwen3.8-27B,
  DeepSeek-V4-Flash-Vision-Exp, GLM-5.3-Flash, GLM-5.3,
  Ling-3.0-flash-Fin, Kimi-K3, Llama-3.1-8B-Instruct, Ling-3.0-flash-VL,
  DeepSeek-V4-Flash-0731, Ternary-Bonsai-27B-gguf, Muse-Glimmer-30B,
  gemma-4-31B-it, gpt-oss-120b, Qwen3.6-35B-A3B, gpt-oss-20b,
  DeepSeek-V4-Pro, DeepSeek-V4-Flash, Qwen3.5-9B, Ling-3.0-flash,
  granite-4.2-3b).
- GAP DE SCHEMA CRITICO: `model_registry.json` (V12) ya NO tiene la clave
  `models`, pero `huggingface_openai_chat.py` -> `allowed_model_ids()`
  todavia lee `_registry()["models"]`. **El adapter esta roto/desincronizado
  con el registry actual.** No se puede declarar ningun modelo READY
  hasta reconciliar este schema. Este es el primer bug tecnico real que
  debo arreglar. -- **YA REPARADO en pasada 1, ver seccion 8.4**.
- Bucket persistente `COMAND-CENTER-1/yaiwes-v54`: guarda manifiesto/
  evidencia, NO pesos (`persistent_external_weights=false`,
  `weights_copy_count=0`).
- Historico separado (NO confundir con REMOTE20): Qwen/Qwen3-0.6B,
  openai-community/gpt2, Qwen/Qwen3-8B tuvieron inferencia real
  verificada dentro de HF Jobs (compute efimero), pero eso es un catalogo
  distinto y no certifica los demas 20 IDs.
- Modelos en cola de video/imagen (Wan2.2-Animate-14B, LTX-Video,
  HunyuanVideo, Kandinsky-5.0-T2I-Lite, Qwen-Image, FLUX.1-schnell):
  todos `GAP_PENDING`, ninguno paso por el gate completo.
- HF MCP oficial: `https://huggingface.co/mcp`, OAuth/client-managed;
  boundary verificado (Job `6aac809f5c02253cfb145474`, 5x10 tests PASS),
  runtime OAuth MCP remoto de RIU sigue pendiente.

### 4.7 API Key Manager (P03) -- esto SI esta cerrado y verificado
- 100 slots probados, hash-only, create/verify/rotate/revoke, slot 101
  fail-closed, plaintext nunca commiteado.
- Hot-path certificado: `FastAPI -> APIKeyGuard -> Enchufe Gate ->
  RedUniversal -> registry -> adapter -> destino/modelo -> verifier ->
  response`.
- Esto es la base sobre la que debo construir "mas de 50 API keys para
  agentes" -- el manager ya soporta 100 slots, falta conectarlo
  operativamente a los wordflows reales del repo agentes.

## 5. GAPS AUTORITATIVOS HEREDADOS DEL HANDOFF (no resueltos aun, no ocultos)
1. `STATE.json` sigue en nodo viejo RIU-0086 con gates legacy de mirror/
   download activos (`HF_MIRROR_RUNTIME_DESTINATION_AND_TEST`,
   `HF_ENDPOINT_REPLICA_RUNTIME_CONFIG_TEST`) que ya estan SUPERSEDED
   segun PLAN-TAREAS/Handoff mas nuevos (RIU-0089/RIU-0093/RIU-0097).
   Necesita migrarse SIN borrar provenance. Confirmado otra vez en
   RIU-0088 y RIU-0096 (pasada 2): STATE sigue citando RIU-0086.
2. `PLAN-TAREAS.md` en RIU-0089, `CHECKPOINT.json` en RIU-0097 -- falta
   sincronizar el set documental completo.
3. HF remote model gates individuales abiertos salvo 3 IDs historicos.
4. OmniRoute/AnyDoc/Orca/Omarchy requieren pruebas runtime reales.
5. Claude/Codex/MCP/memoria y GLOBAL_E2E permanecen abiertos.
6. `FULL_COMPONENT_CONTAINER_XRAY` y `DEDUP_ORPHAN_RECONCILIATION` abiertos.
7. `GAP_ADAPTER_REGISTRY_SCHEMA` (ver 4.6) -- reparado en pasada 1 (codigo
   + test), pero el test aun no se ejecuto en un runner real (ver 8.4 y
   GAP-TEST-EXECUTION-001).

## 6. PROXIMO DELTA SEGURO (heredado del Handoff, adoptado)
`STATE_RECONCILIATION -> CRAZY_WALL_SYNC -> PLAN_SYNC ->
HF_ADAPTER_REGISTRY_SCHEMA_FIX -> HF_REMOTE_MODEL_GATES ->
EXTERNAL_COMPONENT_RUNTIME -> AUTH_MCP_MEMORY -> GLOBAL_E2E ->
FINAL_DOC_SYNC`.

## 7. REGLA DE TRABAJO ADOPTADA EN ESTE REPO
- `REUSE_EXISTING > PATCH > ADAPT > GENERATE`; nunca borrar evidencia ni
  ownership valido.
- No declarar PASS sin evidencia real (ruta + commit/blob SHA + diff +
  log + URL + read-back + test).
- Determinismo 95% / LLM 5% como norma fija del ecosistema (heredado de
  memoria.md de agentes) -- el filtro LLM solo actua con policy explicita
  definida/recuperada, nunca como router paralelo.
- Autorizacion del Director (2026-09-18): reparar en el camino sin
  escalar, resolver GAPs disponibles, avanzar y reportar. Solo escribo en
  este repo.

## 8. AUDITORIA FORENSE X-RAY -- PASADA 2 DE 4 (2026-09-18)

Alcance de esta pasada: lectura completa de los 14 informes restantes en
`forensics/` (RIU-0073, RIU-0075 a RIU-0082, RIU-0084, RIU-0087,
RIU-0088, RIU-0091, RIU-0096, AUTH-REPAIR-20260912) + inventario completo
de `router inteligente universal/Componente open soure router
inteligente universal/` (64 entradas) + `RDC_ADDITIONAL_COMPONENTS_EVIDENCE.json`.
Verificacion cruzada aplicada: cada hallazgo de forensics/ se contrasto
contra el Handoff, el README de arquitectura y STATE/CHECKPOINT ya leidos
en pasada 1 (1a de las 3 verificaciones cruzadas exigidas).

### 8.1 Inventario de componentes donantes (62-64 entradas confirmado)
Confirmado con listado directo del arbol (64 items, de los cuales 62 son
carpetas donor segun RIU-0071 mas 2 archivos sueltos):
- `OmniRoute` -- es un **archivo** (submodule Git pinneado, no carpeta
  expandida), coincide con RIU-0071 (`MATERIALIZED_AS_SUBMODULE`).
- `RDC_ADDITIONAL_COMPONENTS_EVIDENCE.json` -- evidencia de extraccion de
  5 componentes adicionales:
  - LiteLLM: EXTRACTED_VERIFIED, 10219 files, commit
    `658f50663d19f613a3f5caf998168da019764ad8`.
  - vLLM-Router: INSUFFICIENT_EVIDENCE_EXISTING_TARGET (gap, no verificado).
  - Temporal-Python-SDK: EXTRACTED_VERIFIED, 776 files.
  - Durable-Task-Python: EXTRACTED_VERIFIED, 376 files.
  - Durable-Workflow-Server: EXTRACTED_VERIFIED, 900 files.
  - Prefect: EXTRACTED_VERIFIED, 5366 files.
- Resto (60 carpetas): librerias vendor/donor sin extraccion evidenciada
  individualmente en esta pasada (fastapi, redis, vllm, langgraph,
  crewAI, autogen, chroma, qdrant, react, vite, tailwindcss, etc.) --
  presencia de carpeta != integracion runtime, tal como ya establecia
  RIU-0071. QUARANTINE-DONOR se mantiene como decision.

### 8.2 RIU-0073 -- Consolidacion de bridges HF (verificacion cruzada con 4.5/4.6)
Confirma con detalle de codigo lo que ya intuia la pasada 1:
- Owner canonico: `integration/huggingface/` (cadena FastAPI -> Enchufe
  Gate -> RedUniversal -> HF adapter).
- `coneccion huggueface Github/router/dispatcher.py`: candidato a
  ADAPTAR -- aporta cola deterministica HF1->HF2->HF3->WAITING (util para
  mi tarea de "3 instancias HF en cola").
- `coneccion huggueface Github/router/hf_jobs_adapter.py`: candidato a
  ADAPTAR CON SOLAPE -- selection de slot RAM-aware, se solapa con
  `HFJobsCompute`.
- `huggueface/bridge/router_hf_bridge.py`: DONOR_LEGACY -- enruta directo
  a Groq/Cerebras/NVIDIA/OpenRouter/HF, **bypassea RedUniversal si se
  activa directo**. NO USAR TAL CUAL; su metadata de providers puede
  reusarse detras de connector_registry, nunca como router paralelo.
  `bridge_health()` declara capacidades (FastAPI/MCP/SSE/webhook/
  websocket) que el codigo ejecutable de este archivo NO implementa --
  confirmar antes de asumir nada de ese archivo como cierto.
- Plan seguro: extraer SOLO el scheduling deterministico de slots a un
  modulo canonico nuevo (ej. `integration/huggingface/hf_scheduler.py`),
  con tests unitarios: HF1 disponible / HF1 lleno->HF2 / HF1+HF2 caidos->HF3
  / todos caidos->WAITING / umbral RAM exacto. Este es el diseno base
  para mi Tarea 5 (3 instancias HF en cola).

### 8.3 RIU-0075/0076 -- Inventario HF y watchdog roto (verificacion cruzada con 4.6)
- Identidad fresh: `COMAND-CENTER-1`, scopes `jobs, openid, profile,
  read-mcp, read-repos` -- **sin permiso de escritura de repos ni de
  Inference Providers**. Esto CONFIRMA la causa raiz de
  `GAP_AUTH_REMOTE_INFERENCE` (403 "insufficient permissions"): la
  credencial conectada en las sesiones de auditoria nunca tuvo el scope
  necesario para inferencia autenticada. No es un bug de codigo, es un
  limite de credencial/cuenta.
- Ventana de Jobs fresh: 100 devueltos (8 COMPLETED, 1 CANCELED, 91
  ERROR) -- ventana/cap del connector, no el total historico (evidencia
  previa de 961 Jobs en una introspeccion anterior, no usada como total
  fresh).
- 2 Scheduled Jobs: uno activo apuntando a un path GitHub raw ya
  eliminado (`watchdog.py`/`hf_zip_engine.py`/`watchdog-state.json`
  borrados en commit `e0b3cd3bc9e33c8184009d5507f2e1e4bd6bfb49`) -> 404
  reproducible estable en 3 corridas. **REPARADO**: Scheduled Job
  `6aa1af2821047bf1b0370810` fue SUSPENDIDO (no borrado), verificado con
  read-back `suspended=true`. El reemplazo canonico
  (`hf_download_extract_engine.py` + `motor_2_queue_download_extract.py`,
  protegidos por `MOTOR-CODE-LOCK.json`) requiere inputs explicitos
  (QUEUE_FILE/STATE_FILE/ENGINE_PATH/INDEX_PATH/DEST_*) que el schedule
  obsoleto no proveia -- queda como `GAP_DESTINATION_INPUT`, no se debe
  adivinar destino.
- Publico sin token: 0 modelos, 0 datasets, 3 Spaces (incluye
  `COMAND-CENTER-1/yaiwes-ui-factory`, coincide con AUTH-REPAIR-20260912
  donde ese mismo Space aparece como "not found or auth required" desde
  otro contexto -- posible Space privado o con visibilidad inconsistente,
  a revisar).

### 8.4 RIU-0077/0081 -- Clasificacion de modelos Code y mezcla de tiers de agentes
- Solo 1 modelo Code-especializado con evidencia de metadata:
  `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` (base model Coder
  explicito) -- pero con intentos de inferencia previos cancelados/con
  timeout, por tanto NO operacional.
- 1 modelo code-capaz pero generalista: `dphn/dolphin-2.9.1-yi-1.5-34b`
  (datasets de entrenamiento incluyen CodeFeedback/dolphin-coder).
- Los otros 18 IDs historicos del registro viejo (V8/V9, pre-RIU-0084/
  pre-REMOTE20) NO tienen evidencia de especializacion Code.
- Politica de tiers de agentes (RIU-0081), relevante para mi diseno de
  50+ mundos: Tier A tiny (0.5B-1.5B, triage/clasificacion), Tier B
  pequeno (3B-4B, turnos normales de agente), Tier C estandar (7B-8B,
  agentes generales -- coincide con preferencia declarada del proyecto),
  Tier D especialista/grande (30B+ o Provider-first). Regla: no cargar
  todos los modelos simultaneamente; >50 identidades API son ENTRADAS DE
  REGISTRO, no 50 workers corriendo a la vez. Esto es directamente
  aplicable a mi Tarea 5.

### 8.5 RIU-0078/0080 -- Arquitectura de mirror/replica y sizing de computo (para Tarea 5: 3 instancias HF, 32GB RAM)
- Mecanismos oficiales HF confirmados con fuentes: (1) `duplicate_repo()`
  = copia de repositorio, NO replica de inferencia; (2) Inference
  Endpoints con min/max replicas gestionadas por HF, RIU no debe crear
  una ruta por replica interna; (3) `snapshot_download()` = cache
  ephemera con revision pinneada, para Jobs/tests, no persistente.
- Modelo de 4 niveles de failover propuesto (diseno, no ejecutado aun):
  MODEL_IDENTITY -> REPO_MIRROR_SET (opcional) -> ENDPOINT_SET (provider/
  replica) -> LOCAL_SNAPSHOT (cache Job).
- Sizing de computo con evidencia real de flavors HF Jobs:
  `cpu-basic`=2vCPU/16GB RAM/50GB efimero; `cpu-upgrade`=8vCPU/32GB
  RAM/50GB efimero; T4=16GB GPU; A10G=24GB GPU; L40Sx1=48GB GPU.
  **CONFIRMA que las "3 instancias HF en cola de 32GB RAM" del Director
  mapean directamente a `cpu-upgrade` (o superior) como flavor base**, no
  a una maquina dedicada fija -- HF Jobs se factura por minuto de uso.
- 3 carriles logicos ya definidos como diseno (HF1/HF2/HF3), NO maquinas
  fijas:
  - HF1 control/tests/modelos chicos -> `cpu-basic`, escalar a
    `cpu-upgrade` (32GB) solo si RAM/CPU lo exige. Evidencia real: Qwen3-0.6B
    y GPT-2 ya corrieron aqui con exito.
  - HF2 GPU medio -> `a10g-small` (24GB GPU). Evidencia real: Qwen3-8B
    corrio aqui, ~16.4GB pico de memoria GPU.
  - HF3 grande/burst -> escalera `l40sx1` (48GB) -> multi-GPU solo tras
    benchmark -> preferir Endpoint/Provider gestionado para modelos muy
    grandes en vez de cargarlos en un Job.
- Politica: clasificar tarea (CONTROL_SMALL/GPU_MEDIUM/GPU_LARGE) ->
  elegir carril -> elegir flavor en el momento del dispatch -> si no
  alcanza o es muy costoso, NO reducir en silencio: marcar GAP o enrutar
  por Provider/Endpoint via RedUniversal -> registrar Job ID, flavor,
  revision del modelo, tiempo, memoria pico, resultado y duracion
  relevante a costo -> liberar/cancelar servidores temporales al terminar.

### 8.6 RIU-0082 -- Boundary MCP + API key de HF (verificacion cruzada con 4.6)
- Dos mecanismos de auth DISTINTOS que NO deben mezclarse: (1) MCP oficial
  HF en `https://huggingface.co/mcp`, `streamable_http`, OAuth
  client-managed; (2) credencial Hub/Inference (`RIU_HF_TOKEN`/`HF_TOKEN`/
  `HUGGINGFACE_TOKEN`) como secret-ref runtime, nunca serializada en
  descriptors/STATE/logs/Git.
- Codigo de soporte ya existe: `connectivity_runtime.py` ->
  `mcp_huggingface_descriptor()`, probado en HF Job
  `6aac809f5c02253cfb145474` (5 rondas x 10 tests, PASS, credencial
  faltante falla cerrado correctamente).
- La sesion conectada (`COMAND-CENTER-1`, scope `read-mcp`) prueba que la
  APLICACION conectada tiene autorizacion de lectura MCP, pero NO prueba
  que el runtime propio de RIU haya completado un handshake OAuth MCP
  remoto -- sigue `RIU_REMOTE_MCP_OAUTH_E2E_PENDING`.

### 8.7 RIU-0084/0087 -- Correcciones de verdad sobre el registro HF (verificacion cruzada con 4.6, 2a verificacion cruzada)
- RIU-0084 confirma que un listado historico de 20 slots fue mal
  interpretado una vez como "modelos instalados" -- correccion: eran
  slots de catalogo/Jobs, no instalaciones. 13 IDs fueron retirados del
  registro activo por rechazo explicito del usuario en su momento (entre
  ellos el mismo `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` y
  `openai/gpt-oss-120b` que reaparecen en el REMOTE20 actual bajo un
  contrato distinto -- confirmar con el Director si el rechazo previo
  sigue vigente para el REMOTE20 actual antes de promoverlos a READY).
- RIU-0087 es la regla autoritativa mas fuerte encontrada: prohibido como
  ruta normal de AI Staff `hf download`, `snapshot_download`, mirror/
  duplicado de pesos, bucket de pesos o cache persistente. Toda
  materializacion efimera dentro de un Job se etiqueta
  `EPHEMERAL_JOB_CACHE`, nunca `INSTALLED`. Confirma 0 repos propios (Job
  `6aacb9175c02253cfb1461d1`), 5 Spaces sin pesos (Job
  `6aacc24d5c02253cfb14636e`), 2 buckets sin pesos, 41B y 1918B (Job
  `6aacc21b5c02253cfb146365`), Inference Endpoints UNKNOWN por 403 en
  `inference.endpoints.read` (Job `6aacc20eb1dc2b62dc590800` -- **no se
  puede inferir cero aqui, es un gap de permiso, no de evidencia**).

### 8.8 RIU-0088/0091/0096 -- Drift de autoridad y reconciliacion REMOTE20 (3a verificacion cruzada, la mas critica)
- RIU-0091 resuelve una confusion historica real: **existieron DOS
  inventarios distintos de "20 modelos"** que fueron mezclados:
  (A) el REMOTE20 real del Router (RIU-HF-MODEL-REGISTRY-V2, Jobs
  `6aa245235527934177ebf8aa`/`6aa245405527934177ebf8ac`, reverificado
  fresh en Job `6aad0a2951992417dfcc6844` con 139 modelos totales
  disponibles y los 20 V2 con >=1 provider live cada uno); y (B) un
  segundo catalogo de 20 obtenido por busqueda publica
  `pipeline_tag=text-generation` ordenada por downloads (Job
  `6aa2513d5527934177ebfaad`, commit `8ce5ceaa98fcf62c7b6ba2d47b067edaaa6b4d4e`)
  que reemplazo por error al V2 y que luego se mezclo con pruebas de
  compute efimero para producir una falsa certificacion "20/20".
  **CONCLUSION DURA: "20/20 accounted" es evidencia de inventario/
  conteo, NUNCA equivale a 20 modelos con inferencia remota verificada.**
  Esto reconfirma exactamente lo que ya tenia anotado en 4.6, ahora con
  el origen exacto del error documentado.
- RIU-0088 confirma el drift documental: STATE (RIU-0086),
  PLAN-TAREAS (RIU-0071 activo ahi), Handoff (RIU-0071 vivo ahi),
  CHECKPOINT (RIU-0083/RIU-0086) -- todos desactualizados respecto a la
  arquitectura REMOTE_INFERENCE_ONLY ya vigente desde RIU-0087. Matriz de
  cierre por oleadas W1-W5 con gates explicitos (ver tabla original en el
  reporte) -- uso esta matriz como columna vertebral de mi seccion 6.
- RIU-0096 es el ultimo read-back completo de STATE antes de mi trabajo:
  confirma que `runtime_inference_verified_model_ids` sigue limitado a
  Qwen3-0.6B/GPT-2/Qwen3-8B, y ordena preservar TODO el historial de
  gates legacy como `SUPERSEDED_PROVENANCE_ONLY` en vez de borrarlo al
  reconciliar STATE -- regla que debo seguir cuando yo mismo sincronice
  STATE.json (tarea pendiente, seccion 5.1).

### 8.9 AUTH-REPAIR-20260912 -- limite externo real, no reparable solo con codigo
Confirma con fecha mas antigua (2026-09-12) el mismo techo de permisos:
la identidad OAuth conectada (`COMAND-CENTER-1`, scopes
`jobs/openid/profile/read-mcp/read-repos`) **nunca tuvo permiso de
escritura de repositorio ni de inferencia**. Ademas, un Space HF
(`COMAND-CENTER-1/yaiwes-ui-factory`) resulta inaccesible/no encontrado
desde este contexto, y un flujo de login interactivo de Claude Code se
detuvo esperando un codigo pegado manualmente (run 34671762824, exit
124) -- consentimiento humano interactivo no completado. Ningun secreto
HF fue escrito ni probado end-to-end en ese momento.
**Implicacion directa para mi Tarea 5 (P2, 100 autorizado)**: el
`GAP_AUTH_REMOTE_INFERENCE` de los 20 modelos REMOTE20 y la falta de
permiso de escritura de Space/repo **no son reparables solo con cambios
de codigo desde este repo** -- requieren que el Director (u otra sesion
con acceso interactivo) complete el consentimiento OAuth/login con los
scopes correctos (Inference Providers + repo write) en la cuenta
`COMAND-CENTER-1`, o entregue una credencial HF con esos scopes via
secret-ref. Marco esto explicitamente como limite externo, no como gap
de codigo, para no violar la regla de nunca declarar PASS sin evidencia
ni tampoco fingir que un cambio de codigo por si solo puede resolverlo.

## 9. ARQUITECTURA DESCUBIERTA -- RAIZ EXTENDIDA Y EJEMPLO DE AGENTE META

### 9.1 Raiz extendida del Router (vista consolidada tras pasadas 1-2)
```
router-universal-router-inteligente-/            (repo, main = fuente de verdad)
├── CLAUDE.md                                     (politica raiz del agente)
├── Claude notas/                                 (ESTA raiz -- memoria persistente, replica metodo de agentes/Claude notas)
│   └── memoria.md                                (este archivo)
├── Handoff router inteligente universal.md       (estado consolidado cross-sesion)
├── readme indice router inteligente universal.md (indice de navegacion raiz)
├── Readme arquitectura router inteligente universal/
│   └── README.md                                 (SOURCE-OF-TRUTH arquitectonico, 26KB)
├── Readme Indice componentes.md                  (tabla C01-C23, hot-path certificado)
├── Readme Indice de modelos de ai huggueface.md  (regla ROUTER_REGISTERED != ACCOUNT_INSTALLED)
├── Fast api key de los modelos de ai en huggueface.md
├── bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/
│   ├── STATE.json          (estado runtime, aun en nodo legacy RIU-0086 -- GAP)
│   ├── CHECKPOINT.json     (checkpoint de cierre por oleadas W1-W5)
│   ├── PLAN-TAREAS.md      (plan operativo, aun en RIU-0089 -- GAP)
│   └── BITACORA-CRAZY-WALL.md  (ledger historico RIU-0001..RIU-0100, este es el "Crazy Wall")
├── forensics/               (29 informes RIU-00XX, evidencia dura por nodo + AUTH-REPAIR)
│   └── extraction/
├── conectividad con Router inteligente universal/  (fabric de conectividad canonico, 19/19)
├── router inteligente universal/    <-- RUNTIME CANONICO, unico owner de ejecucion
│   ├── red/
│   │   ├── enchufe_gate.py          (gate de entrada, primer punto de contacto)
│   │   ├── red_universal.py         (RedUniversal -- UNICO propietario de routing)
│   │   └── conectores.py + connector_registry.py  (registro de conectores/proveedores)
│   ├── domain/schemas/enchufe_v2.py (contratos/schemas de dominio)
│   ├── enchufe/validator_v2.py      (validacion de payload de entrada)
│   ├── engine/resilience.py         (reintentos/fallback/circuit breaking)
│   ├── gateway/                     (boundary HTTP -- FastAPI)
│   ├── adapters/                    (adapters por proveedor externo)
│   ├── security/                    (APIKeyGuard, hash-only, 100 slots)
│   ├── verifier/                    (verificacion post-respuesta antes de responder al caller)
│   ├── tests/                       (19 archivos, incluye el nuevo test_huggingface_openai_chat_registry.py)
│   ├── integration/
│   │   ├── huggingface/             (OWNER CANONICO de HF: hf_jobs_compute.py, huggingface_openai_chat.py, router_hot_path.py, fastapi_gateway.py, api_key_auth.py, model_registry.json V13)
│   │   └── audits/
│   └── Componente open soure router inteligente universal/  (64 donors vendor: fastapi, redis, vllm, langgraph, LiteLLM, Prefect, Temporal-Python-SDK, OmniRoute[submodule], etc. -- QUARANTINE-DONOR, ninguno es runtime hasta integracion explicita)
├── huggueface/               (bridge/manifest HF alterno -- CONSOLIDATE pendiente con integration/huggingface/)
├── coneccion huggueface Github/   (bridge HF<->GitHub alterno -- ADAPTAR partes utiles, nunca activar router_hf_bridge.py directo)
├── router inteligente software/   (inventario LEGACY/DONOR, no runtime)
└── scripts/                  (utilidades de auth/repair, fail-closed)
```

Regla de lectura de este diagrama: cada nodo tiene UN owner canonico.
Cuando hay mas de una ubicacion con el mismo rol (bridges HF, indices
duplicados, litellm/LiteLLM), la decision vive en la seccion 4.4/8 de
este archivo y en BITACORA-CRAZY-WALL.md -- nunca se asume el owner por
convención de nombre.

### 9.2 Ejemplo de agente "meta" (nota 1 a 1 / input block)
Formato pedido por el Director: una nota que cualquier wordflow puede
usar como bloque de entrada estandar (1 a 1) para registrarse y operar
a traves del Router, sin conocer los detalles internos de RedUniversal.

```json
{
  "meta_agent_input_block": {
    "contract": "tel.workflow/v3",
    "mode": "FAIL_CLOSED_LOOP",
    "agent_identity": {
      "world_id": "wordflow-EJEMPLO-001",
      "worker_id": "worker-uuid-o-nombre-unico",
      "code_sha256": "<hash del codigo del wordflow, igual para todos los workers del mismo wordflow>",
      "task": "<descripcion corta de la tarea de este wordflow>",
      "workspace": "<ruta o namespace propio del wordflow>"
    },
    "router_contact": {
      "entrypoint": "FastAPI -> APIKeyGuard -> Enchufe Gate -> RedUniversal",
      "api_key_ref": "secret-ref, nunca la key en texto plano en este bloque",
      "auth_boundary": "el wordflow NUNCA llama directo a Cerebras/HF/otro proveedor; siempre pasa por este entrypoint"
    },
    "model_request": {
      "task_class": "CONTROL_SMALL | GPU_MEDIUM | GPU_LARGE",
      "preferred_tier": "A | B | C | D",
      "model_id_hint": "opcional -- RedUniversal decide el modelo/proveedor final, esto es solo una preferencia",
      "deterministic_first": true
    },
    "evidence_requirements": {
      "no_pass_without": ["path", "commit_or_blob_sha", "diff_or_log", "url", "read_back", "test"],
      "priority_order": ["REUSE_EXISTING", "PATCH", "ADAPT", "GENERATE"]
    },
    "own_world_files": {
      "readme": "<world_id>/README.md",
      "handoff": "<world_id>/HANDOFF.md",
      "crazy_wall": "<world_id>/CRAZY-WALL.md",
      "system_prompt": "<world_id>/SYSTEM-PROMPT.md"
    },
    "escalation_policy": {
      "on_retryable_quality_failure": "escalate_one_tier",
      "on_auth_or_quota_failure": "identity_or_mirror_failover_same_tier_first",
      "never": "crear un router paralelo o hablar directo con un proveedor externo"
    }
  }
}
```

Este bloque es el "agente meta": no ejecuta trabajo el mismo, sino que
describe el contrato minimo que CUALQUIERA de los 50+ wordflows debe
declarar para conectarse al Router como su unico proveedor de
identidad/modelo/API key. RedUniversal, EnchufeGate y el API Key Manager
ya existentes en `router inteligente universal/` son los componentes que
consumen este bloque; no se crea ningun componente nuevo de routing para
darle soporte -- se reusa lo ya certificado (regla REUSE_EXISTING).

## 10. GAPS Y TAREAS PENDIENTES (actualizado tras pasada 2, tambien copiado a Crazy Wall)
1. Pasadas 3 y 4 de 4 de la auditoria forense, con sus verificaciones
   cruzadas correspondientes -- PENDIENTE. En pasada 2 ya se aplicaron 3
   verificaciones cruzadas de las exigidas (8.2 vs 4.5/4.6; 8.7/8.8 vs
   4.6; 8.9 vs 4.6/8.3), quedan mas por hacer en pasadas 3-4 sobre
   `router inteligente software/`, `Documentos proyectos.../`,
   `dataset Yaiwes/`, `Yaiwes Cognitive Control Plane/`, y el resto de
   `Componente open soure.../` no auditado archivo por archivo.
2. Sincronizar STATE.json (nodo RIU-0086 -> reconciliado), PLAN-TAREAS.md
   (RIU-0089 -> reconciliado), CHECKPOINT.json (RIU-0097 -> nuevo nodo)
   preservando TODO el historial como `SUPERSEDED_PROVENANCE_ONLY`, nunca
   borrando (regla confirmada en RIU-0096).
3. `GAP-TEST-EXECUTION-001`: ejecutar realmente
   `test_huggingface_openai_chat_registry.py` en un runner/CI real y
   registrar el log/run id -- sigue sin ejecutarse, no se declara PASS.
4. `GAP_AUTH_REMOTE_INFERENCE` (20 modelos REMOTE20, 0/20 autenticados) y
   la falta de permiso de escritura en Space/repo son **limites externos
   de credencial/cuenta**, no reparables solo con codigo desde este repo
   (ver 8.9) -- requieren accion del Director: nueva credencial HF con
   scope de Inference Providers, o completar el login interactivo
   pendiente.
5. Diseno operativo completo de HF (Tarea 5: 3 instancias HF1/HF2/HF3 en
   cola con `cpu-basic`/`cpu-upgrade`(32GB)/`a10g-small`/`l40sx1` segun
   carga, generacion de 50+ API keys usando el API Key Manager ya
   certificado de 100 slots) -- diseno documentado en 8.5/8.7/9.2, falta
   IMPLEMENTAR el modulo `hf_scheduler.py` extraido de
   `dispatcher.py`/`hf_jobs_adapter.py` con tests unitarios reales.
6. Integrar "Kat Coder 2.5" a Hugging Face -- NO iniciado, pendiente de
   investigacion (nombre no encontrado aun en ningun documento leido del
   repo; se investigara en pasada 3 antes de proponer integracion).
7. Runtime real (no solo boundary) para OmniRoute (detras de
   connector_registry), AnyDoc, Orca, Omarchy -- PENDIENTE.
8. Consolidar bridges HF duplicados (`integration/huggingface/` owner,
   `coneccion huggueface Github/router/*` adaptar, `huggueface/bridge/
   router_hf_bridge.py` nunca activar directo) -- diseno listo (8.2),
   implementacion PENDIENTE.
9. Resolver `GAP_DESTINATION_INPUT` del motor de descarga/extraccion
   canonico (`hf_download_extract_engine.py` +
   `motor_2_queue_download_extract.py`) antes de programar cualquier
   reemplazo del Scheduled Job suspendido.
10. Confirmar con el Director si los IDs rechazados historicamente en
    RIU-0084 (incluye `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` y
    `openai/gpt-oss-120b`) deben excluirse tambien del REMOTE20 actual, o
    si el rechazo aplicaba solo al contrato de instalacion/mirror viejo
    (ya SUPERSEDED) y no al contrato REMOTE_INFERENCE_ONLY actual.

## 11. SEGUNDO CONECTOR MCP HF-GITHUB + DISENO UI "0 FRICCION" (Fables) -- 2026-09-18

### 11.1 Segundo entorno de Claude -- mecanismo confirmado (sin tocar codigo)
El Director pidio habilitar un segundo entorno de Claude con el mismo
camino HF<->GitHub que uso yo en esta sesion. Investigacion validada
contra la documentacion oficial de Anthropic antes de dar instrucciones
(no se ejecuto nada sin validar primero):

- Lo que yo uso aqui (`GitHub_Backup_HF`) es un **conector MCP remoto**:
  un servidor externo (probablemente un Space de HF) que ya trae el PAT
  de GitHub guardado como secreto propio. El chat de Claude nunca ve el
  token -- solo se conecta a una URL.
- Verificado con `github_api GET /user`: el PAT pertenece a la cuenta
  `maxbry123-commits`, con `admin:true` sobre TODOS sus repos (12
  privados + 7 publicos), no solo este -- el alcance amplio es una
  capacidad real del token; mi propia regla de trabajo (P3) es la que me
  limita a escribir solo en este repo, no una limitacion tecnica del PAT.
- **Decision (confirmada por el Director): reusar el mismo conector**,
  no crear un secreto/Space nuevo. Mecanismo 0 friccion:
  1. En la cuenta/chat ORIGINAL: Settings -> Connectors -> abrir el
     conector `GitHub_Backup_HF` (o como se llame ahi) -> copiar la URL
     del servidor MCP remoto configurado.
  2. En la cuenta/chat NUEVO: Settings -> Connectors -> Add custom
     connector -> pegar esa misma URL -> autorizar.
  3. Verificar con `github_api GET /user` en el chat nuevo: si devuelve
     `maxbry123-commits`, quedo con el mismo acceso, mismos repos, sin
     configurar nada en HF ni crear secretos nuevos.
  - Fuente validada: https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp
- Ruta alterna NO elegida (documentada por si se necesita despues):
  aislar con un Space HF nuevo + `HfApi.add_space_secret()` con un PAT
  de GitHub propio -- mas pasos, mas superficie de secretos. Solo se
  usaria si el Director pide aislar el segundo entorno del primero.
- Este hallazgo NO cambia nada del estado tecnico del Router; es un
  procedimiento operativo para el Director, no un gap de codigo.

### 11.2 Diseno UI "0 friccion" descrito por el Director (Fables) -- SOLO DOCUMENTADO, sin construir aun
El Director explico la arquitectura de UI disenada originalmente por
Fables para el Router, y adjunto ~18 prototipos HTML que ya la
implementan parcialmente. Regla del Director para esta ronda: documentar
en notas, NO construir codigo todavia (repo destino aun sin confirmar).

**Principio rector**: el backend hace todo el trabajo; el usuario
interactua con el minimo posible (2 acciones manuales en el router); todo
lo demas lo resuelve el agente por el usuario, igual que un chat normal
de Claude no expone su procesamiento interno.

**Estructura de 2 procesos:**

1. **Proceso 1 -- Lista de conexiones (fichas):**
   - Una lista donde cada fila es una "ficha" = una conexion externa
     (api, mcp, webhook, repo, chat, agente, lo que sea).
   - Cada ficha tiene 3 partes fijas:
     1. **Input**: todo lo que entra (api, mcp, webhook, documento, chat,
        repo, telegram, archivo, stream, cron).
     2. **Salida**: el destino (vps, hf, repo, agente, chat, webhook,
        archivo, stream).
     3. **Sandbox/panel de code**: filtra y procesa el trayecto entre
        input y salida -- el Router es el intermediario de TODO proceso,
        nunca un paso directo input->salida sin pasar por el filtro.
   - Vi este patron exacto materializado en los HTML adjuntos:
     - `router-v1-lista.html`: lista de conexiones (GitHub, HuggingFace,
       VPS Contabo, Telegram, OpenRouter), con switch on/off, busqueda,
       filtro por tipo/estado, y un mini-chat inferior que auto-rellena
       fichas por lenguaje natural ("conecta api github al vps").
     - `router-v2a-entrada.html` / `router-v2b-anclaje.html` /
       `router-v2c-otras.html`: ficha detallada de UNA conexion, en 4
       tabs -- Entrada (hasta 100 slots por tipo), Anclaje (documentos/
       texto/instrucciones/sandbox ejecutable/system prompt propio de la
       ficha) + Salida (hasta 100 destinos, drag&drop para reordenar), y
       Otras (15 configs avanzadas: prioridad, timeout, reintentos, rate
       limit, modo de envio primero/todos/espejo, costo maximo, cron
       schedule, fallback chain, credenciales via vault-ref, tags, ACL
       read/write).
     - `panel_router_3.html`: version simplificada de 3 paneles
       (Entradas -> Quien recibe [Orquestador/Agente/Chat] -> Salidas),
       con auto-relleno por chat y export a `/puente/router/config`.
     - `router-v4-conectores.html`: catalogo de conectores
       preconfigurados por categoria (ai_providers, cloud, databases,
       messaging, repos, mcp, storage, email, infra, webhooks), cada uno
       con test/editar/eliminar/toggle y import/export masivo en YAML.

2. **Proceso 2 -- capa "Ask Council" (orquestacion de multiples LLM):**
   - Con muchos LLM conectados (ej. 50), una capa intermedia orquesta un
     "consejo" de wordflows/modelos que trabajan en equipo sobre la misma
     entrada, similar a un ask-council: reciben una entrada compartida y
     devuelven una salida sintetizada, en vez de 50 llamadas
     independientes y repetidas.
   - El usuario puede prender/apagar cada IA de la lista y anexar su
     propio system prompt/codigo ejecutable (Python) -- el agente hace la
     configuracion tecnica por el usuario a partir de lenguaje natural.
   - `router-v5-agente.html` es el detalle de esto para UN agente/chat:
     seleccion de agente (OpenHand/Claude Code/OpenClaw/MiMo Code),
     seleccion de modelo con precio/contexto visible, system prompt
     editable, y sliders de temperature/max_tokens/top_p/frequency/
     presence penalty -- exactamente los parametros de bajo nivel que el
     "Proceso 2" necesita para poder despachar cada miembro del consejo
     con configuracion propia.

**Patron Ask Council detallado (de la conversacion previa del Director
con otro asistente, coherente con RIU-0081 Tiers ya documentado):**
```
ENTRADA -> ROUTER -> DECIDER-2B [que hacer / que LLM usar]
        -> NanoJev [microdecisiones/scores en paralelo, sin generar texto]
        -> RUTA SIMPLE: LLM pequeno (Gemma 3 1B / Qwen3 0.6B / LFM2.5 1.2B) -> respuesta
        -> RUTA COMPLEJA (Ask Council):
             INPUT -> research UNA sola vez -> evidence packet compartido
             -> N LLM en paralelo, cada uno con un rol fijo (hechos,
                interpretacion, restricciones, solucion A/B, refutacion,
                riesgos, planificacion, arquitectura, verificacion,
                alternativa independiente)
             -> NanoJev [ranking/score]
             -> Decider-2B [aceptar / combinar / investigar mas / escalar]
             -> LLM sintetizador -> UNA SOLA SALIDA
```
Punto clave de eficiencia (coincide con RIU-0080/0081 ya en mis notas):
**N miembros del consejo NO exige N pesos de modelo distintos cargados**.
Se pueden montar 11 roles del consejo sobre 3-4 modelos pequenos
realmente cargados (Gemma 3 1B, LFM2.5 1.2B, Qwen3 0.6B + 1 mas),
asignando varios agentes/roles al mismo modelo -- reduce RAM sin perder
diversidad de analisis. Esto es directamente compatible con mi diseno de
HF1/HF2/HF3 (seccion 8.5): los roles del consejo se despachan en el
carril logico que corresponda segun tamano del modelo, no 1 carril por
rol.

**Router modal (detectado en los HTML, relevante para el "Sandbox" de
cada ficha):**
```
INPUT -> MODALITY ROUTER -> TEXTO -> Small LLM / Ask Council
                          -> CODE  -> Code model (solo cuando hay que
                                       escribir/modificar codigo real)
                          -> IMAGE -> Vision model
                          -> AUDIO -> Audio model
                          -> VIDEO -> Vision+Audio pipeline
       -> TODOS -> Decision layer -> Agents/Skills/Tools -> Verificacion -> Salida unica
```

**Decision de alcance para esta ronda:** SOLO documentado aqui y en
Crazy Wall. No se creo ningun archivo de codigo ni artifact de UI en
este repo todavia -- el Director confirmo explicitamente "solo
documentar el diseno en notas por ahora". Cuando se autorice construir,
el candidato natural de owner en runtime es un modulo nuevo tipo
`router inteligente universal/gateway/ui_fichas/` o equivalente, sin
tocar el hot-path ya certificado (`FastAPI -> APIKeyGuard -> Enchufe Gate
-> RedUniversal -> ...`) -- la UI de fichas seria una capa de
configuracion ENCIMA del hot-path, nunca un router paralelo.

### 11.3 Nuevo gap de investigacion registrado
`GAP-UI-FICHAS-DESIGN-BUILD-001`: diseno completo documentado (11.2),
pendiente decision del Director sobre en que repo/artifact construirlo
antes de escribir cualquier codigo de UI.

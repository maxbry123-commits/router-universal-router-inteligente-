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
  debo arreglar.
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
   Necesita migrarse SIN borrar provenance.
2. `PLAN-TAREAS.md` en RIU-0089, `CHECKPOINT.json` en RIU-0097 -- falta
   sincronizar el set documental completo.
3. HF remote model gates individuales abiertos salvo 3 IDs historicos.
4. OmniRoute/AnyDoc/Orca/Omarchy requieren pruebas runtime reales.
5. Claude/Codex/MCP/memoria y GLOBAL_E2E permanecen abiertos.
6. `FULL_COMPONENT_CONTAINER_XRAY` y `DEDUP_ORPHAN_RECONCILIATION` abiertos.
7. `GAP_ADAPTER_REGISTRY_SCHEMA` (ver 4.6) -- nuevo, detectado en esta
   pasada, prioridad alta porque bloquea CUALQUIER modelo READY.

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

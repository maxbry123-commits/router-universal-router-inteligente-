# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3` · **Modo:** `FAIL_CLOSED_LOOP`.

## RIU-0001..0062 — BASE CERRADA
P01/P02/P03=`VERIFIED_CLOSED`; `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED`; regresión core `RIU FAST-CLOSE` PASS.

## RIU-0063/0064 — CONNECTIVITY FABRIC
- raíz canónica `conectividad con Router inteligente universal/`.
- 19/19 repos con `PUENTE-RIU-<repo>.yaml` v2.
- frontend v2 integra GitHub + HF `COMAND-CENTER-1` + Jobs CPU/GPU + Space `yaiwes-ui-factory` + Claude GitHub MCP + memoria.
- runtime base y fabric probados.

## RIU-0065 — SUITE COMPLETA
Regresión final amplia: **75 passed, 2 warnings**. Connectivity runtime fresco: **7 passed**. Fail-closed sin secrets validado.

## RIU-0066 — PROBES + RUNNER CODESPACES
Runtime implementa probes GitHub identity/permisos, HF whoami/role y GitHub MCP initialize sin exponer secretos. Runner `integration/verify_runtime_connectivity.py` preparado para ejecución en entorno autorizado.

## RIU-0067 — HF OIDC / TRUSTED PUBLISHER
- Space `COMAND-CENTER-1/yaiwes-ui-factory` confirmado `static`.
- frontend OIDC publica correctamente al Hub.
- runs `34675165228` attempt 2 y `34677293995`: upload PASS.
- Hub read-back HTTP 200 PASS.

## RIU-0068 — BOOTSTRAP GLOBAL AUTH
Core del Router = **100% VERIFIED_CLOSED**. La capa global de credenciales externas continúa separada del core y se valida fail-closed.

## RIU-0069 — CLAUDE DIRECT GITHUB ROOT ACCESS — NODO VIVO
Delta mínimo aplicado 2026-09-13:
- `GitHub Backup HF` queda clasificado como **respaldo opcional, no bloqueante**.
- Hugging Face no se usa como autoridad para editar GitHub.
- Nuevo `.github/workflows/claude-root-editor.yml` con `contents: write`, `pull-requests: write`, `issues: write`, usando `RIU_GITHUB_PAT` cuando existe o `github.token` para el repo actual.
- Nuevo `CLAUDE.md` en raíz: GitHub `main` es fuente de verdad y la ausencia del backup HF no detiene lectura/escritura de raíces.
- `.github/workflows/claude-token-setup.yml` corregido: ya no imprime en claro la sesión de `setup-token`; sanitiza salida y destruye el log runner-local.

### Evidencia
- `f3d0daa60cecc25e711886cac6b6f468feedfe05` — setup-token seguro.
- `946f1a0e1c976298c6c34d4e70f0a07243109aa6` — Claude Root Editor.
- `ddfeb73e4c5d80515e28ed8511c14f8f0fc1ba88` — `CLAUDE.md` canónico.

### GAP REAL RESTANTE
La configuración está materializada y leída de vuelta, pero **Claude runtime no se marca PASS** hasta ejecutar el workflow con `CLAUDE_CODE_OAUTH_TOKEN` disponible y obtener un commit/read-back real de una edición de raíz. Para edición transversal a otros repos también se requiere `RIU_GITHUB_PAT`/GitHub App con permisos efectivos.

## ESTADO
- Core/arquitectura/runtime: `VERIFIED_CLOSED` 100%.
- Ruta directa de Claude en GitHub: `MATERIALIZED`.
- Verificación runtime de escritura Claude: `PENDING_FRESH_WRITE_READBACK`.
- Nodo: `RIU-0069_CLAUDE_DIRECT_GITHUB_ROOT_ACCESS`.


## RIU-0070 — X-RAY RAÍZ + 4 COMPONENTES EXTERNOS — NODO ACTIVO
Delta 2026-09-17:
- Auditoría shallow X-Ray completada sobre **29 entradas raíz**, snapshot base `d001d96cfa382888d409255e5dd3e9d2b6372860`.
- README arquitectura actualizado: commit `8616da2a84bd5f803ca38a9bbeaea1ed93bafbac`.
- PLAN-TAREAS actualizado: commit `b5c2d5585de2eba4de11bfb08795cca56f71b811`.
- STATE actualizado: commit `561b546d1344a551cb9c09387044d7aadf4aa88c`.
- Fuentes externas verificadas: OmniRoute=`diegosouzapw/OmniRoute`; Orca ADE=`saiichi/orca`; Omarchy=`basecamp/omarchy`; AnyDoc=`firecrawl/anydoc`.
- Owners preservados: runtime=`router inteligente universal/`; connectivity=`conectividad con Router inteligente universal/`; estado=`bitácora.../`; evidencia=`forensics/` + JSON de auditoría; donor/download quedan sin ownership.
- No se declara instalación runtime de los cuatro externos. Estado: `BOUNDARY_DEFINED / PENDING_RUNTIME_TEST`.

### Plan de cierre RIU-0070
1. Consolidar owners/duplicados por referencia sin borrar evidencia.
2. Materializar OmniRoute/AnyDoc como adapters; validar Orca como ADE externo y Omarchy como host opcional.
3. Cerrar auth GitHub/HF/Claude/Codex + MCP/memoria y ejecutar E2E global.
4. Sincronizar arquitectura + STATE + PLAN + BITÁCORA y exigir URLs/SHA/log/read-back antes de `VERIFIED_CLOSED`.

### Gates
- `ROOT_29_ACCOUNTED`
- `EXTERNAL_4_BOUNDARIES_DEFINED`
- `NO_ROUTING_OWNERSHIP_CONFLICT`
- `AUTH_RUNTIME_VERIFIED`
- `CONNECTIVITY_GLOBAL_E2E_PASS`
- `STATE_PLAN_BITACORA_SYNC`

Estado actual: **ACTIVE / GAP runtime**.


### READ-BACK RIU-0070
PASS 2026-09-17: README arquitectura, PLAN-TAREAS, STATE, BITÁCORA y CHECKPOINT fueron releídos desde `main`; los cinco marcadores RIU-0070 están presentes. Este PASS cierra sólo la **sincronización documental/estado**. Adapters externos, auth runtime y E2E global permanecen abiertos.


## RIU-0071 — FORENSIC X-RAY AUTORITATIVO — NODO ACTIVO
- Fresh HEAD inicial: `55b8136a8f19d3bf9dda5f5febe0398ba5f07ff4`.
- Corrección: raíz real = **28**, no 29; `.github/workflows` era hijo, no raíz.
- Probe recursivo: 35.979 entradas devueltas, `truncated=true`; no se declara inventario total de archivos.
- Inventario por contenedores: runtime top-level=11; donor OSS dirs=62; legacy component roots=5.
- Duplicado candidato: `LiteLLM` / `litellm`; prohibido borrar antes de provenance/content comparison.
- Bridges HF candidatos a consolidación: `integration/huggingface`, `coneccion huggueface Github/router`, `huggueface/bridge`.
- Inventario: `forensics/RIU-0071-XRAY-COMPONENT-INVENTORY-2026-09-17.json`, commit `a5a3e02cea01d753a495b5090c4ae46146200a64`.
- Cola del chat recuperada: inventario HF, pruebas modelos, Code, mirrors, >50 identidades, compute, mix agentes, MCP/API, skills, GitHub+HF, watchdog 404, externos, auth y E2E.
Estado: **ACTIVE / NO GLOBAL CLOSE**.


## RIU-0072 — LITELLM DUPLICATE AUDIT — ✅ PASS AUDIT / NO DELETE
- `LiteLLM`: 9.977 files; explicit SOURCE_URL `https://github.com/BerriAI/litellm`; SOURCE_COMMIT `658f50663d19f613a3f5caf998168da019764ad8`.
- `litellm`: 9.795 files; no SOURCE_* provenance markers found in its complete tree; includes `litellm_0001.zip..0006.zip`.
- Compare: 9.784 common paths; 8.930 identical blobs; **854 differing blobs**; 193 only in LiteLLM; 11 only in litellm.
- Decision: preserve both. `LiteLLM` = canonical donor candidate by provenance. `litellm` = legacy snapshot pending origin/use. No deletion authorized.


## RIU-0073 — HF BRIDGE CONSOLIDATION — ✅ PASS AUDIT ONLY
- Canonical owner: `router inteligente universal/integration/huggingface/`.
- `dispatcher.py`: deterministic HF1→HF2→HF3 scheduler donor.
- `hf_jobs_adapter.py`: RAM-aware scheduling + Job launch; overlaps canonical submission.
- `router_hf_bridge.py`: direct multi-provider donor/legacy; cannot own routing outside RedUniversal; declared protocol set exceeds executable implementation in this file.
- Existing connection tests are only marker files and do not prove scheduler/failover.
- Audit: `forensics/RIU-0073-HF-BRIDGE-CONSOLIDATION-AUDIT-2026-09-17.md`, commit `48b91296d373dcc8daba4bf51d8c7c63d3589c4c`.
- Next: adapt scheduler into canonical owner + focused tests + one real HF Job smoke test.


## RIU-0074 — HF CANONICAL SCHEDULER — ✅ TESTED STABLE
- Canonical code: `router inteligente universal/integration/huggingface/hf_scheduler.py`.
- Submission remains delegated to the existing canonical submitter; no second `run_job` implementation added.
- Tests: `router inteligente universal/tests/test_hf_scheduler.py`.
- Exact commit test: `83a7636639a7dade2e1abfcb5366ad99e9884360`.
- HF Job `6aac7c9eb1dc2b62dc58faf9` = COMPLETED; 5/5 runs, 7 passed each (0.01–0.02s).
- Heavy clone Job `6aac7c2d5c02253cfb1452bc` canceled after being superseded by exact-file test.
- Closure scope: scheduler logic/boundary only. Full HF inventory/model runtime remains open.


## RIU-0075 — HF INVENTORY — 🟡 PARTIAL / GAP
- Fresh OAuth identity: `COMAND-CENTER-1`; scopes jobs/read-repos/read-mcp (no secret values).
- Direct visible window: **100 Jobs** = 8 COMPLETED / 1 CANCELED / 91 ERROR; request `limit=0` remains capped at 100.
- Scheduled Jobs: 2; active watchdog `6aa1af2821047bf1b0370810` every 15 min, second suspended.
- Public no-token Job `6aac7d015c02253cfb1452fd`: 0 public models, 0 public datasets, 3 Spaces; does not prove private absence.
- Router registry: 20 slots in `model_registry.json`.
- 3 fresh watchdog executions reproduce HTTP 404.
- Evidence: `forensics/RIU-0075-HF-INVENTORY-PARTIAL-2026-09-17.md`, commit `382b8e8b342cad59505a1ccbd7dc5f3dec8aa3f8`.
- GAP remains: private Hub resources + uncapped current Job history + dedup model refs.


## RIU-0076 — HF WATCHDOG 404 ROOT CAUSE — ✅ INCIDENT CONTAINED
- Historical root recovered in `maxbry123-commits/frontend`: `➡️📂motor extracción de zip con huggueface/`.
- Git commit `e0b3cd3bc9e33c8184009d5507f2e1e4bd6bfb49` deliberately removed `watchdog.py`, `hf_zip_engine.py`, `watchdog-state.json` to keep a single canonical motors root.
- Active Scheduled Job `6aa1af2821047bf1b0370810` still referenced the removed files; 3 fresh runs repeated HTTP 404.
- Current immutable combined motor = `hf_download_extract_engine.py` blob `91e6e4486692eab314be5c7130d8310d3c855397`; controller = `84d566e2ee4e98e42eb3a864026d067d48caabd9`.
- Obsolete Scheduled Job suspended; inspect + scheduled-list both read back `suspended=true`.
- No delete, no secret disclosure, no historical code resurrection.
- Replacement schedule remains GAP until explicit QUEUE_FILE/STATE_FILE/INDEX_PATH/DEST_* contract exists.
- Evidence: `forensics/RIU-0076-HF-WATCHDOG-404-ROOT-CAUSE-2026-09-17.md`, commit `ddb993d0f898a51b2f7372cc8e59cc269fdca220`.


## RIU-0077 — HF CODE MODEL CLASSIFICATION — ✅ PASS CLASSIFICATION
- M04 `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` = **CODE_SPECIALIZED**, fresh Hub base model `Qwen/Qwen3-Coder-30B-A3B-Instruct`.
- M15 `dphn/dolphin-2.9.1-yi-1.5-34b` = **CODE_CAPABLE_TRAINING_EVIDENCE / generalist**, with CodeFeedback + dolphin-coder datasets.
- Other 18 slots not promoted to Code-specialized without explicit evidence.
- Runtime Code PASS remains open; classification != operational readiness.
- Audit commit: `fad57842d3d677010c581c7ddedc67fd95d7797c`.


## RIU-0078 — HF MIRROR / REPLICA — ✅ RESEARCH/DESIGN PASS
- Repo mirror: Hub `duplicate_repo` / `hf repos duplicate`.
- Runtime replicas: Hugging Face Inference Endpoint min/max replicas + autoscaling.
- Snapshot/cache: `snapshot_download(revision=...)` for deterministic local/Job materialization.
- RedUniversal remains routing owner; no internal endpoint replica is exposed as a second Router route.
- No mirror created without explicit destination/namespace; no Endpoint replica count changed without resource/cost authorization.
- Audit commit: `9b0595507649d495651d7e5065bc7b15087a3d6f`.


## RIU-0079 — ROUTING >50 IDENTITIES — ✅ 64 VERIFIED
- Added `router inteligente universal/red/identity_pool.py`; no second router.
- Identity metadata stores `secret_env` references, not secret values.
- Selection is sequential: priority → mirror rank → identity id; quota/cooldown/disable fail over to next identity.
- Batch registration is atomic and validates connector kinds against `connector_registry`.
- Exact test commit `7ec0a58b7f4557984963f099dd113ea48d4be110`.
- HF Job `6aac7f48b1dc2b62dc58fb73` COMPLETED; **5/5 runs, 5 passed each**, including 64-identity rollover.


## RIU-0080 — HF COMPUTE SIZING — ✅ POLICY PASS
- HF1/HF2/HF3 remain logical worker lanes, not permanently allocated machines.
- HF1: CPU control/tests/small workloads; HF2: A10G medium baseline supported by Qwen3-8B real evidence; HF3: large/burst selected by benchmark or provider Endpoint.
- Official HF Jobs flavors/pricing reviewed fresh; no paid resource provisioned speculatively.
- Policy commit: `fbd82905b0a73b3bd5c9714726564f1b8b4f8479`.


## RIU-0081 — AGENT MODEL MIX — ✅ POLICY PASS
- Tiny/triage: M10/M01/M07; small agents: M12/M11; standard agents: M05/M20/M03.
- Specialist/large models remain escalation-only until their exact runtime path is verified.
- Quota/auth/health failures use identity/mirror failover before increasing model size.
- Policy commit: `7c91f51e3aec6c0d6108e68b4132ec232d2513cd`.


## RIU-0082 — HF MCP + API — ✅ BOUNDARY VERIFIED / REMOTE E2E PENDING
- Official HF MCP URL: `https://huggingface.co/mcp`; transport declared Streamable HTTP; MCP authentication remains client/OAuth-managed.
- Hub/Inference API credential remains a separate runtime secret reference.
- Runtime/test commit `f97791ca61197ecbdad0d1d2bb7c792a37c721dc`.
- HF Job `6aac809f5c02253cfb145474` = COMPLETED; **5/5 runs, 10 passed each**.
- Current app OAuth has read-mcp scope, but RIU-side remote OAuth handshake is not falsely claimed.
- Audit commit: `014f3e59a76bf7943a6a1cc36dfd5e1376dd1760`.


## RIU-0083 — OMNIROUTE ACQUISITION + INTEGRATION QUEUE — 2026-09-17
- Fuente fijada: `diegosouzapw/OmniRoute` rama `release/v3.8.51` @ `1603c86e06da473e0fffb3802585e052219ac353`.
- Destino canónico resuelto: `router inteligente universal/Componente open soure router inteligente universal/OmniRoute/`.
- DOWNLOAD=MOTOR_QUEUE_PENDING; MATERIALIZATION=NOT_YET_VERIFIED.
- PENDING PARA CLAUDE + SOL: después de presencia física + read-back/hash, integrar detrás de `connector_registry` sin crear un segundo router.
- Gate: no declarar DOWNLOAD PASS ni INTEGRATION PASS sin evidencia física/prueba real.


## RIU-0085 — HF REAL INVENTORY + VIDEO/ANIMATION — ACTIVO
- Inventario fresh autenticado: `COMAND-CENTER-1` posee 0 repos de modelos; Job `6aacb9175c02253cfb1461d1`.
- Esto no invalida modelos externos usados por Jobs: se separan de instalación persistente.
- Inferencia real demostrada: Qwen3-0.6B, GPT-2, Qwen3-8B.
- Mirrors persistentes verificados: 0; RIU-0078 fue diseño sin duplicación ejecutada.
- Nuevos nodos: `WAN22_ANIMATE_MODEL_INTEGRATION`, `LTX_VIDEO_MODEL_INTEGRATION`, `HUNYUANVIDEO_MODEL_INTEGRATION`.
- Estado de los tres: `GAP_PENDING`.
- No cerrar hasta: licencia + revision + tamaño + descarga real + hash + carga + inferencia + evidencia.


## RIU-0083 — OMNIROUTE MATERIALIZATION VERIFIED
- Destino: `router inteligente universal/Componente open soure router inteligente universal/OmniRoute/`.
- Materialización: submodule/gitlink fijado a `diegosouzapw/OmniRoute@1603c86e06da473e0fffb3802585e052219ac353`.
- Commit RIU: `ca931941988510d546fb71e2bef76545d5cab5e2`.
- Read-back real: HF Job `6aacbb0c5c02253cfb14622d` COMPLETED; submodule checkout exacto y `package.json` presente.
- Estado descarga/materialización: `VERIFIED`.
- Integración detrás de `connector_registry`: `PENDING`; no se declara PASS funcional todavía.


## RIU-0086 — PRIORITY LOCK 5 + IMAGE STAFF
1. `HF_SKILLS_LIBRARY` — sólo cerrar con runtime discovery real.
2. `HF_DATASET_CONNECTION_VERIFY` — lectura/conexión real, no presencia documental.
3. `HF_COMPUTE_50_API_IDENTITIES_MODELS_MIRRORS` — inventario persistente + compute + identidades/mirrors reales.
4. `AI_MODEL_INTEGRATION_QUEUE` — TimesFM, WAN2.2 Animate, LTX-Video, HunyuanVideo, Kandinsky 5, Qwen-Image, FLUX.1-schnell; integrar uno por uno.
5. `ARCHIFY_SKILLS_FLOW_DIAGRAM` — upstream exacto pendiente; producir diagrama de listo/falta.

### HF installed-surface X-Ray
- Owned model repos=0, Job `6aacb9175c02253cfb1461d1`.
- Spaces=5; ninguno guarda pesos de modelo en repo, Job `6aacc24d5c02253cfb14636e`.
- Buckets=2; tamaños 41 B y 1918 B, sin pesos, Job `6aacc21b5c02253cfb146365`.
- Inference Endpoints=`GAP_PERMISSION_403`, Job `6aacc20eb1dc2b62dc590800`; no inferir 0.
- Runtime models realmente inferidos: Qwen3-0.6B, GPT-2, Qwen3-8B.

### Nuevos modelos AI Staff
- Kandinsky 5 T2I Lite — MIT, rev `25da1e82...`, GAP_PENDING.
- Qwen-Image — Apache-2.0, rev `75e0b4be...`, GAP_PENDING.
- FLUX.1-schnell — Apache-2.0, gated, rev `741f7c3c...`, GAP_PENDING.


## RIU-0090 — HF REMOTE LLM X-RAY
- Regla autoritativa: modelos AI Staff/HF se consumen por llamada remota; no se instalan ni persisten pesos.
- Ruta: `RedUniversal -> connector_registry -> HF adapter/InferenceClient -> Inference Provider/Endpoint remoto -> model_id`.
- Histórico `20/20 accounted` = catálogo/slots contabilizados, NO 20 llamadas remotas verificadas.
- Evidencia real auditada: M01 Qwen3-0.6B, M02 GPT-2 y M03 Qwen3-8B fueron inferencia dentro de HF Jobs con carga efímera; M05/M06/M07/M10/M11/M12/M20 tienen Jobs/hot-path previos, pero la evidencia histórica es principalmente compute/Job-local, no provider-hosted autenticado.
- Provider hosted histórico quedó bloqueado por `FLAG-HF-PROVIDER-AUTH-001`; el adapter canónico existe pero V12 quedó desincronizado porque `huggingface_openai_chat.py` espera `registry["models"]` y V12 ya no contiene esa clave.
- Probe GitHub Actions rerun actual: run `34677207175`, job `105555011892`; paso HF identity/token role=`skipped`, por lo que esa cadena de secrets no llega al workflow del Router. No inferir ausencia en otros repos/entornos.
- TAREA-1: workflow HF encontrado es publicación de Space estático; no registra catálogo LLM remoto.
- Estado: `GAP_REMOTE_MODEL_RECONSTRUCTION`; no READY hasta provider discovery + auth + remote inference + fallback + evidencia por modelo.


## RIU-0091 — HF REMOTE 20 RECOVERY X-RAY
- Recuperado el registry remoto V2 en commit `fc61718c658b60a4f2b9ecbad3b0bfabf1c5847f`: 20 model_id provenientes de `https://router.huggingface.co/v1/models`.
- Jobs históricos `6aa245235527934177ebf8aa` + `6aa245405527934177ebf8ac` = enumeración y metadata de los 20.
- Fresh Job `6aad0a2951992417dfcc6844`: **20/20 siguen presentes y 20/20 tienen >=1 provider live**.
- Root cause: commit `8ce5ceaa98fcf62c7b6ba2d47b067edaaa6b4d4e` reemplazó ese registry por otro top-20 público de text-generation; ambas listas se mezclaron después.
- `huggueface/manifest.yml` confirma `REMOTE_ONLY` y `external_weights_persisted=false`; bucket `yaiwes-v54` confirma `weights_copy_count=0`.
- TAREA-1 no contiene el catálogo remoto 20; sólo bridge de credenciales/runtime + publicación de Space.
- GAP actual: V12 no tiene `models` pero `huggingface_openai_chat.py` aún exige esa clave; adapter/registry están desincronizados.
- Auditoría completa: `forensics/RIU-0091-HF-REMOTE-20-RECOVERY-XRAY-2026-09-18.md`.


## RIU-0098 — CLAUDE NOTAS/ CREADA + FIX REAL GAP_ADAPTER_REGISTRY_SCHEMA — 2026-09-18

**Autorización del Director (verbatim, chat 2026-09-18):** P1=SI iniciar;
P2=autorizado a reparar en el camino sin escalar ni detenerse, resolver
GAPs disponibles, avanzar y reportar, "100 autorizado"; P3=solo puedo
escribir en ESTE repo (nunca en `agentes` ni otros); P4=replicar el
método de `agentes/Claude notas/` en este repo.

### Trabajo realizado
1. **Auditoría forense pasada 1 de 4** completada: leídos CLAUDE.md,
   Handoff, README arquitectura completo (28 raíces + 4 externos + HF
   REMOTE20 + gates), Índice componentes C01-C23, ambos índices de
   modelos HF, STATE.json, CHECKPOINT.json, PLAN-TAREAS.md, esta bitácora
   completa, y el método/memoria del Claude de `agentes`
   (memoria.md, REQUISITO-50-mundos, LISTA-TRABAJO-4-FRENTES,
   DECISION-objetivo-osquestador).
2. **Raíz `Claude notas/memoria.md` creada en main de este repo**
   (commit `a26f2abbfcbf1dadbf9b53d48d825c6e74384b0b`), replicando el
   método verbatim/1-a-1 del otro Claude, con inventario completo de las
   28 raíces, duplicados, componentes externos, HF, gaps y proximo delta.
3. **GAP_ADAPTER_REGISTRY_SCHEMA RESUELTO CON EVIDENCIA REAL** (no era
   bloqueante-teórico, era un bug real que rompía cualquier llamada):
   - `huggingface_openai_chat.py::allowed_model_ids()` llamaba
     `registry()["models"]`, clave que **nunca existió en V12** ->
     KeyError garantizado en producción.
   - Fix commit `dfd796616d074c71b17589f7d1654ae3988846cd`: ahora lee
     `runtime_inference_verified_model_ids` (los 3 IDs con
     REMOTE_INFERENCE_SMOKE real: Qwen3-0.6B, gpt2, Qwen3-8B) y separa
     una función nueva `provider_live_model_ids()` para exponer el
     REMOTE20 SIN habilitarlo para chat (sigue en
     `GAP_AUTH_REMOTE_INFERENCE`, 0/20 PASS por 403).
   - `model_registry.json` migrado V12->V13 (commit
     `2479c28587fbdacd03db124d1a41b32f51bb79fc`): se agregó
     `remote20_provider_live_verified` con los 20 model_id + providers
     reales tomados de `Handoff router inteligente universal.md`
     RIU-0094 y `forensics/RIU-0091-...`. Ningún campo previo fue
     borrado; `runtime_inference_verified_model_ids` y
     `remote_inference_queue` quedaron intactos.
   - Test nuevo `router inteligente universal/tests/test_huggingface_openai_chat_registry.py`
     (commit `21e71e72f2e69c785af16abd6fe193b8385e0115`) cubre: no-crash
     de `allowed_model_ids()`, separación estricta allowed vs
     provider-live, y rechazo de un model_id del REMOTE20 en
     `chat_completion()` con `MODEL_NOT_IN_CERTIFIED_REGISTRY`.
   - **GAP HONESTO, no oculto:** el test fue escrito y committeado pero
     **no se ejecutó todavía en un runner real** (esta sesión no tiene
     shell sobre el repo clonado ni acceso a un HF Job/GitHub Actions
     para correrlo). No se declara `PASS`; se declara
     `CODE_COMMITTED_TEST_WRITTEN_EXECUTION_PENDING`. Regla del propio
     repo: "no declarar PASS sin evidencia real (ruta + commit/blob SHA +
     diff + log + URL + read-back + test)" -- el log de ejecución real
     falta y queda como tarea inmediata (correrlo vía
     `.github/workflows/claude-root-editor.yml` o un HF Job cpu-basic).

### Nuevo GAP autoritativo agregado
`GAP-TEST-EXECUTION-001`: `test_huggingface_openai_chat_registry.py`
existe en `main` pero no tiene corrida real registrada (sin log/run
id). No cerrar el fix de RIU-0094/GAP_ADAPTER_REGISTRY_SCHEMA como
`VERIFIED` hasta tener ese log.

### Estado heredado sin cambios (ver Handoff RIU-0094 para detalle completo)
`REMOTE20_INVENTORY_RECOVERED=PASS`,
`REMOTE20_PROVIDER_DISCOVERY=20/20_PASS`,
`REMOTE20_PERSISTENT_WEIGHT_COPIES=0_VERIFIED`,
`REMOTE20_AUTHENTICATED_INFERENCE=0/20_PASS_CURRENT_EVIDENCE`,
`GAP_AUTH_REMOTE_INFERENCE=OPEN` (sin cambios, sigue abierto -- el fix de
hoy resuelve el bug del *adapter*, no la autenticación remota, que
requiere una credencial HF con permiso real de Inference Providers).
`GAP_ADAPTER_REGISTRY_SCHEMA=CODE_FIXED_TEST_WRITTEN_EXECUTION_PENDING`
(antes: `OPEN`).

### Próximo delta seguro (sin cambios respecto al Handoff, adoptado)
`STATE_RECONCILIATION -> CRAZY_WALL_SYNC(este commit) -> PLAN_SYNC ->
HF_ADAPTER_REGISTRY_SCHEMA_FIX(commit real, test pendiente de ejecutar)
-> HF_REMOTE_MODEL_GATES -> EXTERNAL_COMPONENT_RUNTIME -> AUTH_MCP_MEMORY
-> GLOBAL_E2E -> FINAL_DOC_SYNC`.


## RIU-0099 — AUDITORÍA FORENSE PASADA 2/4 + ARQUITECTURA/AGENTE META + LÍMITE EXTERNO DE CREDENCIAL — 2026-09-18

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`. Continúa bajo la
misma autorización P1-P4 registrada en RIU-0098; nada nuevo se declara
sin evidencia.

### Alcance de esta pasada
Lectura completa de los 14 informes restantes en `forensics/` (RIU-0073,
RIU-0075 a RIU-0082, RIU-0084, RIU-0087, RIU-0088, RIU-0091, RIU-0096,
AUTH-REPAIR-20260912) más inventario completo de `router inteligente
universal/Componente open soure router inteligente universal/` (64
entradas) y `RDC_ADDITIONAL_COMPONENTS_EVIDENCE.json`. Se aplicaron 3
verificaciones cruzadas contra hallazgos ya registrados en pasada 1
(RIU-0098): (1) bridges HF de RIU-0073 vs 4.5/4.6; (2) corrección
REMOTE20 de RIU-0084/0087/0088/0091/0096 vs 4.6; (3) causa raíz de
`GAP_AUTH_REMOTE_INFERENCE` (AUTH-REPAIR-20260912 + RIU-0075) vs 4.6/8.3.

### Hallazgo mayor 1 — origen exacto de la confusión REMOTE20 (RIU-0091)
Existieron dos inventarios de "20 modelos" que se mezclaron: (A) el
REMOTE20 real via `https://router.huggingface.co/v1/models` (reverify
fresh Job `6aad0a2951992417dfcc6844`: 139 modelos totales, los 20 V2
siguen con >=1 provider live cada uno); (B) un catálogo distinto de 20
obtenido por búsqueda pública `pipeline_tag=text-generation` (Job
`6aa2513d5527934177ebfaad`) que reemplazó por error al primero (commit
`8ce5ceaa98fcf62c7b6ba2d47b067edaaa6b4d4e`) y luego se mezcló con
pruebas de compute efímero, produciendo la falsa certificación
"20/20". Confirma y documenta el origen exacto de lo que ya tenía
anotado como sospechoso en RIU-0098/4.6.

### Hallazgo mayor 2 — límite EXTERNO real, no reparable solo con código
`AUTH-REPAIR-20260912.md` (fecha más antigua, 2026-09-12) y RIU-0075
confirman de forma cruzada que la identidad OAuth conectada
(`COMAND-CENTER-1`, scopes `jobs/openid/profile/read-mcp/read-repos`)
**nunca tuvo scope de escritura de repo ni de Inference Providers**. El
403 "insufficient permissions to call Inference Providers" del
REMOTE20 y la imposibilidad de escribir en el Space
`COMAND-CENTER-1/yaiwes-ui-factory` desde este contexto son la MISMA
causa raíz: falta de scope en la credencial, no un bug de código. Un
flujo de login interactivo de Claude Code (run `34671762824`) quedó
esperando un código pegado manualmente y nunca se completó
(consentimiento humano pendiente). **Marcado explícitamente como límite
externo que requiere acción del Director** (nueva credencial HF con
scope correcto, o completar el login interactivo) -- no se declara como
gap de código reparable desde este repo, respetando P2 (reparar sin
escalar aplica a código, no a permisos de cuenta externa).

### Hallazgo mayor 3 — inventario de componentes donantes confirmado
64 entradas en `Componente open soure router inteligente universal/`:
62 carpetas donor/vendor sin integración runtime individual (fastapi,
redis, vllm, langgraph, crewAI, autogen, chroma, qdrant, react, vite,
tailwindcss, LiteLLM/litellm, Prefect, Temporal-Python-SDK,
Durable-Task-Python, Durable-Workflow-Server, etc.), más `OmniRoute`
(submodule Git pinneado, ya materializado desde RIU-0083) y
`RDC_ADDITIONAL_COMPONENTS_EVIDENCE.json` (evidencia de extracción: 4 de
5 componentes adicionales EXTRACTED_VERIFIED con conteo de archivos y
commit; `vLLM-Router` queda `INSUFFICIENT_EVIDENCE_EXISTING_TARGET`).
Ninguno de los 62 donors tiene integración runtime probada; presencia de
carpeta sigue sin equivaler a integración, tal como fijaba RIU-0071.

### Arquitectura descubierta -- raíz extendida + agente meta
Documentado en detalle en `Claude notas/memoria.md` sección 9: diagrama
completo de la raíz extendida del Router (desde raíz de repo hasta
`integration/huggingface/` y el donor pool), y un bloque JSON de "agente
meta" / nota 1-a-1 que cualquiera de los 50+ wordflows puede declarar
como input estándar para conectarse al Router (identidad del mundo,
contacto con RedUniversal vía FastAPI->APIKeyGuard->EnchufeGate,
preferencia de tier de modelo sin fijar proveedor, requisitos de
evidencia, archivos propios del mundo -- Readme/Handoff/Crazy
Wall/system prompt -- y política de escalamiento). No crea ningún
componente nuevo de routing; reusa RedUniversal/EnchufeGate/API Key
Manager ya certificados.

### GAPs nuevos/actualizados esta pasada
- `GAP-EXTERNAL-CREDENTIAL-SCOPE-001` (nuevo): scope de credencial HF
  insuficiente para Inference Providers y para escritura de Space/repo;
  requiere acción del Director, no reparable solo con código.
- `GAP-REMOTE20-REJECTED-IDS-CONFIRM-001` (nuevo): confirmar con el
  Director si los IDs rechazados en RIU-0084 (incluye
  `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` y `openai/gpt-oss-120b`)
  siguen excluidos bajo el contrato REMOTE_INFERENCE_ONLY actual o si
  ese rechazo aplicaba solo al contrato de instalación/mirror ya
  SUPERSEDED.
- `GAP-KAT-CODER-2.5-RESEARCH-001` (nuevo): "Kat Coder 2.5" no aparece en
  ningún documento leído hasta ahora del repo; pendiente de
  investigación en pasada 3 antes de proponer integración a HF.
- `GAP-TEST-EXECUTION-001` (heredado de RIU-0098): sigue abierto, sin
  cambios; el test de RIU-0098 aún no tiene corrida real registrada.

### Estado del nodo
`AUDITORIA_FORENSE_PASADA_2_DE_4_COMPLETA`. Pasadas 3 y 4 restantes
(incluye `router inteligente software/`, `Documentos proyectos.../`,
`dataset Yaiwes/`, `Yaiwes Cognitive Control Plane/`, y verificación
archivo-por-archivo del resto del donor pool). Sin cierre global; ningún
PASS nuevo se declara sobre HF remoto -- los hallazgos de esta pasada son
forenses/de diseño, igual que la pasada anterior.

### Próximo delta seguro (sin cambios respecto a RIU-0098, reafirmado)
`STATE_RECONCILIATION -> PLAN_SYNC -> CHECKPOINT_SYNC ->
HF_SCHEDULER_IMPLEMENTATION(diseño ya en 8.2/8.5, falta código) ->
GAP-TEST-EXECUTION-001(ejecutar test real) ->
HF_REMOTE_MODEL_GATES(bloqueado por GAP-EXTERNAL-CREDENTIAL-SCOPE-001) ->
EXTERNAL_COMPONENT_RUNTIME -> AUTH_MCP_MEMORY -> GLOBAL_E2E ->
FINAL_DOC_SYNC`.


## RIU-0100 — SEGUNDO CONECTOR MCP HF-GITHUB (0 FRICCIÓN) + DISEÑO UI "0 FRICCIÓN" DE FABLES — 2026-09-18

Contrato: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`. Continúa bajo la
misma autorización P1-P4 de RIU-0098/0099.

### Parte A — segundo entorno de Claude, mismo camino HF↔GitHub
El Director pidió habilitar un segundo entorno Claude con el mismo
acceso GitHub que usa esta sesión, buscando la vía de "0 fricción" y
validando primero contra documentación oficial (no se ejecutó nada sin
validar). Hallazgos:
- El conector `GitHub_Backup_HF` usado aquí es un **conector MCP
  remoto**: un servidor externo con el PAT de GitHub guardado como su
  propio secreto; el chat de Claude nunca ve el token en texto plano.
- Verificado con `github_api GET /user`: el PAT pertenece a
  `maxbry123-commits`, `admin:true` sobre TODOS sus repos (12 privados +
  7 públicos) -- alcance amplio real del token; la restricción a
  escribir solo en este repo es una regla de trabajo propia (P3), no un
  límite técnico del PAT.
- **Decisión del Director: reusar el mismo conector**, sin crear Space ni
  secreto nuevo. Procedimiento validado con la documentación oficial de
  Anthropic (Settings → Connectors → Add custom connector → pegar la
  misma URL del servidor MCP remoto → autorizar) y verificable de vuelta
  con `github_api GET /user` en el chat nuevo.
  Fuente: https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp
- Ruta alterna NO elegida, documentada por si se requiere aislar despues:
  Space HF nuevo + `HfApi.add_space_secret()` con un PAT propio.
- Este punto es procedimiento operativo para el Director; no cambia
  ningún estado técnico del Router.

### Parte B — diseño UI "0 fricción" de Fables, SOLO documentado (sin construir)
El Director compartió ~18 prototipos HTML y la explicación de la
arquitectura de UI diseñada originalmente por Fables. Por instrucción
explícita del Director esta ronda es solo documentación en notas, sin
tocar código ni artifacts todavía.

Principio: backend hace todo el trabajo; el usuario tiene el mínimo de
acciones manuales; el agente resuelve el resto, igual que un chat normal
de Claude no expone su procesamiento interno.

**Estructura de 2 procesos** (detalle completo con mapeo a cada HTML
adjunto en `Claude notas/memoria.md` sección 11.2):
1. Lista de fichas de conexión (Input / Salida / Sandbox-code), con la
   ficha detallada en 4 tabs (Entrada, Anclaje, Salida, Otras -- hasta
   100 slots por sección, 15 configs avanzadas: prioridad, timeout,
   reintentos, rate limit, modo de envío primero/todos/espejo, costo
   máximo, cron, fallback chain, credenciales vault-ref, tags, ACL).
2. Capa "Ask Council": orquestación de múltiples LLM en paralelo sobre
   una entrada compartida (research único, evidence packet compartido,
   N roles fijos por LLM, NanoJev para scoring/ranking sin generación de
   texto, Decider-2B para aceptar/combinar/escalar, sintetizador final).
   Confirma y refuerza la política de tiers ya registrada en RIU-0081:
   N roles del consejo no exigen N pesos distintos -- se pueden montar
   sobre 3-4 modelos pequeños reales, compatible con el diseño HF1/HF2/
   HF3 de RIU-0080.

Router modal detectado (para el Sandbox de cada ficha): texto -> small
LLM/Ask Council; code -> code model solo cuando hay que escribir/
modificar código real; imagen/audio/video -> modelos especializados;
todos convergen en decision layer -> agents/skills/tools -> verificación
-> salida única.

Decisión de alcance: sin repo/artifact destino confirmado aún, por lo
que no se creó ningún archivo de código de UI. Cuando se autorice
construir, la UI de fichas sería una capa de configuración ENCIMA del
hot-path ya certificado (`FastAPI -> APIKeyGuard -> Enchufe Gate ->
RedUniversal -> ...`), nunca un router paralelo.

### Nuevo GAP registrado
`GAP-UI-FICHAS-DESIGN-BUILD-001`: diseño completo documentado, pendiente
que el Director confirme en qué repo/artifact construirlo antes de
escribir cualquier código de UI.

### Estado del nodo
`SEGUNDO_CONECTOR_DOCUMENTADO + DISENO_UI_FICHAS_ASK_COUNCIL_DOCUMENTADO`.
Sin cambios de estado técnico del Router. Continúa pendiente la pasada
forense 3/4.

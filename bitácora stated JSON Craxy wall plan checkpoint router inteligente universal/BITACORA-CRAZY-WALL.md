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

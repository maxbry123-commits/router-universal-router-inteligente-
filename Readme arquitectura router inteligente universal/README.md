# Arquitectura router inteligente universal

Repositorio: `maxbry123-commits/router-universal-router-inteligente-`
Rama: `main`
Contrato operativo: `tel.workflow/v3`
Modo: `FAIL_CLOSED_LOOP`

## Alcance autorizado — 3 pasos
1. Integrar componentes open source disponibles en la raíz del Router y auditar LLM/Hugging Face para adapters/FastAPI por modelo confirmado.
2. Cablear, podar duplicación y escribir solo código faltante; capa/filtro LLM únicamente cuando exista contrato definido/recuperado.
3. Ejecutar tests reales Hugging Face + GitHub + API + agentes.

## Raíz activa de código
Todo código integrado vive bajo `router inteligente universal/`.
Biblioteca donor/open source: `router inteligente universal/Componente open soure router inteligente universal/`.

## Núcleo de conexión
`Enchufe Gate -> EnchufeV2(Pydantic) -> validator_v2 -> RedUniversal -> connector_registry -> adapters/conectores -> destinos`
DAGs/modelos no pueden alterar este ownership. Componentes externos son donor/adapter/plugin, nunca segundo orquestador.

## Separación vigente
- `red/enchufe_gate.py`: Gate C15 compatible v1.5→v2.0.
- `domain/schemas/enchufe_v2.py`: C05 Pydantic v2.
- `enchufe/validator_v2.py`: contrato v2 recuperado.
- `red/red_universal.py`: propietario único de mapa/rutas/failover/broadcast/espejo/salud.
- `red/conectores.py` + `red/connector_registry.py`: conectores y registro fail-closed.
- `engine/resilience.py`: C10 aislado, sin ownership de routing.
- `tests/`: tests contractuales separados.
- `integration/huggingface/`: bridge/auditorías HF; prohibido inventar `model_id`.
- `integration/audits/`: decisiones REUSE/PATCH/ADAPT/GENERATE y GAPs por componente.

## Integraciones externas investigadas — 2026-09-17
Estas herramientas se incorporan al mapa arquitectónico como componentes externos/adapters. **Ninguna adquiere ownership del Router ni sustituye `RedUniversal`.** La instalación o cableado runtime queda sujeto a contrato, adapter y pruebas reales antes de marcarse PASS.

### OmniRoute — gateway multi-proveedor / fallback por cuota
- Rol RIU: **gateway downstream opcional** detrás de `connector_registry` para unificar proveedores compatibles con API OpenAI y aportar fallback/selección sensible a disponibilidad/cuota.
- Boundary propuesto: `RedUniversal -> connector_registry -> adapter_omniroute -> OmniRoute -> proveedor IA`.
- Motivo: upstream expone un único endpoint y un catálogo de cientos de proveedores; su README v3.8.50 lista 352 proveedores y scheduling quota-aware. Esto puede reducir interrupciones por rate-limit, pero **no garantiza cuota infinita**.
- Estado: `RESEARCH_VERIFIED / ADAPT_CANDIDATE`; no está certificado todavía como runtime RIU.
- Fuentes: https://github.com/diegosouzapw/OmniRoute · https://www.npmjs.com/package/omniroute

### Orca — entorno gráfico / ADE para agentes
- Rol RIU: **control plane de desarrollo externo** para ejecutar y supervisar Claude Code, Codex y otros agentes en paralelo sobre worktrees aislados.
- Boundary propuesto: `Operador -> Orca -> agentes/worktrees -> GitHub/MCP -> Router`; Orca no reemplaza el loop `tel.workflow/v3` ni el ownership de routing.
- Encaje: útil para visualizar terminales, diffs, agentes y trabajo paralelo mientras el Router conserva validación y cierre fail-closed.
- Estado: `RESEARCH_VERIFIED / INTEGRATION_CANDIDATE`; falta probar el boundary MCP/CLI con RIU.
- Fuentes: https://www.onorca.dev/ · https://github.com/saiichi/orca

### Omarchy — workstation Linux opcional
- Rol RIU: **entorno de operador/desarrollo opcional**, no dependencia del runtime del Router.
- Boundary propuesto: `Omarchy host -> herramientas/CLI/agentes -> Router`; puede alojar la estación de trabajo donde corran Git, terminales y agentes.
- Upstream: distribución Linux de DHH basada en Arch, orientada a productividad/agentes.
- Estado: `RESEARCH_VERIFIED / HOST_OPTION`; no debe introducir lógica de routing ni convertirse en requisito para desplegar RIU.
- Fuentes: https://omarchy.org/ · https://github.com/basecamp/omarchy

### AnyDoc — normalización documental a Markdown
- Rol RIU: **adapter de ingestión** para convertir documentos a Markdown antes de entregarlos a la capa de validación/contexto.
- Boundary propuesto: `archivo -> adapter_anydoc -> Markdown -> validator/ingest -> Router/agente`.
- Upstream: librería Rust de Firecrawl para Word, PowerPoint, Excel, OpenDocument, RTF, EPUB, CSV y PDF, con bindings Node.js/Python/WASM y Agent Skill.
- Estado: `RESEARCH_VERIFIED / ADAPT_CANDIDATE`; faltan wrapper RIU y tests de formatos/errores antes de PASS.
- Fuente: https://github.com/firecrawl/anydoc

### Gate de integración de estos cuatro componentes
Para pasar de documentación a `VERIFIED_CLOSED` se exige, por componente: adapter/boundary explícito -> prueba mínima real -> read-back/log -> ausencia de secreto embebido -> test de fallo -> evidencia URL/SHA/commit. Hasta entonces permanecen externos/candidatos y no se anuncian como runtime integrado.

## Hugging Face Jobs — cómputo real
Jobs forma parte del flujo externo `Router/GitHub source -> HF Job compute -> resultado/evidencia -> GitHub/state` sin convertirse en segundo orquestador. Documentación oficial: https://huggingface.co/docs/hub/en/jobs y https://huggingface.co/docs/hub/en/jobs-configuration . `cpu-upgrade` se reserva para cargas que realmente necesitan 8 vCPU/32 GB; auditorías mínimas pueden usar `cpu-basic`.

RIU-0030 verificó cómputo real con Job `6aa1c5fd21047bf1b0370d4d`, `cpu-upgrade`, `success`.

RIU-0031 auditó el boundary del catálogo HF: identidad conectada `COMAND-CENTER-1`, OAuth autenticado; Job `6aa1d38621047bf1b0370f3f` completó con `public_model_count=0` y `hf_token_present=false`. La documentación de Jobs trata `HF_TOKEN` como secreto explícito, no como built-in automático. Por tanto, público 0 no demuestra privado 0 y ningún `model_id→especialidad→adapter→FastAPI` puede registrarse todavía. Auditoría: `router inteligente universal/integration/huggingface/RIU-0031-HF-CATALOG-TOKEN-AUDIT.md`, commit `505d54c23120f96cec42dde5c26cd001c20092b9`.

## Reglas
- `REUSE > PATCH > ADAPT > GENERATE`.
- Prohibido monolito.
- Secretos solo por entorno/Vault.
- Archivo presente != integrado.
- Donor capaz != contrato específico del Router.
- HF Job success != model catalog ni E2E.
- Público HF 0 != privado HF 0.
- PASS exige ruta + SHA/diff + read-back + test/log + URL cuando aplique.
- Filtro LLM únicamente con policy explícita definida/recuperada.
- `tel.workflow/v3` es el contrato vigente de este LOOP.

## C10 Resilience — verificado
Producción `router inteligente universal/engine/resilience.py`, commit `6b408a781d886a8bde43c3f62b48247d872afd36`; test `a0e74c04c93dfc2cc0c96da9c31234d98b44333c`; HF Job `6aa1ae8221047bf1b03707ff` = `5 passed in 0.10s`.

## C11/C12/C13
C11 Semantic Cache, C12 Cost Optimizer y C13 CodeSandbox dual siguen `ADAPT_CANDIDATE/AUDIT_ONLY` hasta recuperar sus contratos Router-owned exactos.

## GAPs activos
- `GAP-HF-CATALOG-001`: boundary de credencial privada; reintentar sólo con ruta segura explícita.
- `GAP-BEHAVIOR-CONTRACT-001`: no existe policy standalone allow/deny recuperada.
- `GAP-R004-EXTRACTION-001`.
- `GAP-C03-CONTRACT-001`.
- `GAP-C01-API-CONTRACT-001`.
- `GAP-C11-SEMANTIC-CACHE-CONTRACT-001`.
- `GAP-C12-COST-POLICY-CONTRACT-001`.
- `GAP-C13-SANDBOX-CONTRACT-001`.

## Último delta LOOP
RIU-0031: Council12 + 3 refutaciones + cross-check + CODA + `verify_final=PASS_AUDIT_ONLY_NO_MODEL_CLAIM`. Progreso 96%; Paso 2 ACTIVE; Paso 3 PENDING.


## Auditoría forense X-Ray de raíz — 2026-09-17
Snapshot base auditado: `main@d001d96cfa382888d409255e5dd3e9d2b6372860`. Se detectaron **28 entradas raíz**. La regla es: raíz presente != runtime integrado; cada entrada recibe un rol, una decisión y un gate de cierre.

| # | Entrada raíz | Rol X-Ray | Decisión de integración / cierre |
|---|---|---|---|
| 1 | `.github/` | CI/CD y automatización | REUSE; workflows como ejecutores, nunca fuente de contrato. Cierre por run + commit/read-back. |
| 2 | `CLAUDE.md` | política de agente | REUSE; mantener instrucciones raíz y validar workflow Claude por escritura inocua/read-back. |
| 3 | `Documentos proyectos router inteligente universal/` | documentación, contratos y despliegue | REUSE/CONSOLIDATE; enlazar desde arquitectura, evitar duplicar estado operativo. |
| 4 | `Download code router inteligente universal/` | donor/download staging | QUARANTINE-DONOR; sólo fuentes con URL/SHA pasan a adapters; nunca importar ciegamente. |
| 5 | `Fast api key de los modelos de ai en huggueface.md` | guía HF/API | DOC-ONLY; conservar referencias de secretos, jamás valores. |
| 6 | `Github coneccion/` | workflows/conexión GitHub histórica | CONSOLIDATE con `conectividad...`; no crear segundo fabric. |
| 7 | `Handoff router inteligente universal.md` | handoff operativo | REUSE; resumen de continuidad, sincronizado con STATE/bitácora. |
| 8 | `PARCHE-RECUPERACION-ROUTER-INTELIGENTE-UNIVERSAL.md` | recuperación | RECOVERY-ONLY; usar sólo ante GAP con evidencia. |
| 9 | `Readme arquitectura router inteligente universal/` | arquitectura canónica | SOURCE-OF-TRUTH documental; este README recibe el mapa X-Ray. |
| 10 | `Readme Índice componentes.md` | índice C01-C23 | REUSE; mantener estado técnico, cruzar con pruebas frescas. |
| 11 | `Readme Índice de modelos de ai huggueface.md` | inventario HF | REVERIFY; cruzar con Jobs/Hub antes de promover modelos. |
| 12 | `Yaiwes Cognitive Control Plane/` | policy/context/control | ADAPT; puede decidir contexto/policy, pero no reemplaza `RedUniversal`. |
| 13 | `bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/` | ledger/estado/plan | SOURCE-OF-TRUTH operativo; STATE + PLAN + BITÁCORA deben permanecer consistentes. |
| 14 | `coneccion huggueface Github/` | bridge HF↔GitHub | CONSOLIDATE; reutilizar tests/registry, evitar duplicar conectividad. |
| 15 | `conectividad con Router inteligente universal/` | fabric canónico | REUSE; conservar registry/puentes como única tela de conectividad. |
| 16 | `dataset Yaiwes/` | datasets, schemas, evidence | REUSE bajo schema/manifest; separar datos de control/runtime. |
| 17 | `extraction-result.json` | evidencia de extracción | EVIDENCE-ONLY; inmutable salvo nueva extracción trazable. |
| 18 | `forensics/` | auditoría/forense | REUSE; destino de informes y hashes, no runtime. |
| 19 | `huggueface/` | bridge/manifest HF | CONSOLIDATE con `integration/huggingface`; una sola API de entrada. |
| 20 | `pre-audit.json` | evidencia pre-audit | EVIDENCE-ONLY; conservar para comparación antes/después. |
| 21 | `readme Handoff indice componentes.md` | handoff de componentes | CONSOLIDATE; referencias al índice canónico, no estado paralelo. |
| 22 | `readme indice router inteligente universal.md` | índice raíz | REUSE; navegación únicamente. |
| 23 | `readme índice de componentes/` | índice documental alterno | DEDUP-CANDIDATE; mantener sólo si aporta datos no presentes en índice canónico. |
| 24 | `router inteligente software/` | inventario legado de componentes | DONOR/LEGACY; extraer sólo por contrato y evidencia. |
| 25 | `router inteligente universal/` | **runtime canónico** | OWNER; adapters/domain/enchufe/engine/gateway/integration/red/security/tests/verifier viven aquí. |
| 26 | `scripts/` | utilidades auth/repair | REUSE con fail-closed; secretos sólo vía entorno/Actions. |
| 27 | `➡️📂 Wordflow LOOP router inteligente universal/` | método LOOP | REUSE como guía de ejecución; no segundo estado. |
| 28 | `➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/` | motores de archivos | REUSE-CONTROLLED; checks de hash/collision/read-back obligatorios. |

### Componentes externos añadidos al plan
- **OmniRoute** — upstream/package verificado: https://github.com/diegosouzapw/OmniRoute y https://www.npmjs.com/package/omniroute . v3.8.50 publica catálogo de 352 proveedores, endpoint OpenAI-compatible y scheduling sensible a cuota. Integración RIU: `connector_registry -> adapter_omniroute -> OmniRoute`. Gate: health + fallback controlado + rate-limit simulation + read-back; nunca prometer “cuota infinita”.
- **Orca ADE** — upstream gráfico verificado: https://github.com/saiichi/orca y https://www.onorca.dev/ . Controla Codex, Claude Code y otros agentes en worktrees paralelos. Integración RIU: control-plane de desarrollo externo; gate: abrir repo RIU, lanzar 2 agentes aislados, revisar diff, prohibir merge sin verifier.
- **Omarchy** — upstream verificado: https://github.com/basecamp/omarchy y https://omarchy.org/ . Host Arch Linux de DHH; integración sólo como workstation opcional. Gate: checklist host/CLI/Git/MCP; nunca requisito del runtime.
- **AnyDoc** — upstream verificado: https://github.com/firecrawl/anydoc . Rust -> Markdown para Word/PowerPoint/Excel/OpenDocument/RTF/EPUB/CSV/PDF. Integración RIU: `archivo -> adapter_anydoc -> Markdown -> validator/ingest`. Gate: corpus mínimo multiformato + fallo controlado + hash input/output.

### Plan actualizado de integración — máximo 3 pasos por nodo
1. **Planificar:** contrato/boundary por componente, ruta owner y evidencia esperada; REUSE > PATCH > ADAPT > GENERATE.
2. **Ejecutar:** materializar sólo adapter/config/documentación mínima dentro del owner correcto; ningún componente externo adquiere routing ownership.
3. **Validar/cerrar:** prueba real + fallo controlado + URL/SHA/log/read-back; repetir checks externos hasta 10x cuando haya riesgo de flakiness.

### Olas de cierre
- **W0 Preservación:** congelar snapshot X-Ray, hashes y bitácora; no borrar duplicados todavía.
- **W1 Consolidación:** declarar owners canónicos (runtime, connectivity, state, docs, evidence) y marcar legacy/donor.
- **W2 Externos:** OmniRoute y AnyDoc como adapters; Orca como ADE externo; Omarchy como host opcional.
- **W3 Credenciales/connectivity:** cerrar Claude/Codex/GitHub/HF/MCP/memoria sin exponer secretos.
- **W4 Final:** tests E2E + read-back + auditoría de duplicación + STATE/PLAN/BITÁCORA consistentes => `VERIFIED_CLOSED`.

### Gate final RIU-0070
`ROOT_28_ACCOUNTED + EXTERNAL_4_BOUNDARIES_DEFINED + NO_ROUTING_OWNERSHIP_CONFLICT + AUTH_RUNTIME_VERIFIED + CONNECTIVITY_GLOBAL_E2E_PASS + STATE_PLAN_BITACORA_SYNC`.


### Corrección forense RIU-0071 — 2026-09-17
- Fresh root read sobre `main`: **28 entradas raíz**. El conteo previo 29 incluía erróneamente `.github/workflows` como raíz; es hijo de `.github/`.
- Inventario autoritativo: `forensics/RIU-0071-XRAY-COMPONENT-INVENTORY-2026-09-17.json`, commit `a5a3e02cea01d753a495b5090c4ae46146200a64`.
- Runtime canónico: 11 bloques top-level; biblioteca donor: 62 directorios de componentes OSS; candidato de duplicado literal/case-insensitive confirmado: `LiteLLM` vs `litellm`, **sin borrar hasta comparar contenido/provenance**.
- El probe recursivo devolvió 35.979 entradas pero GitHub lo marcó `truncated=true`; esos conteos son lower-bound, no inventario total de archivos.
- Gate corregido: `ROOT_28_ACCOUNTED`.


### HF mirrors / replicas — RIU-0078
Se separan tres mecanismos: (1) repo duplicate/mirror con `duplicate_repo` / `hf repos duplicate`; (2) replicas runtime administradas por Hugging Face Inference Endpoints con min/max/autoscaling; (3) snapshot/cache revision-pinned con `snapshot_download(revision=...)`. Ninguna de estas capas obtiene routing ownership: `RedUniversal -> connector_registry -> endpoint/provider adapter`. Diseño/evidencia: `forensics/RIU-0078-HF-MIRROR-REPLICA-ARCHITECTURE-2026-09-17.md`, commit `9b0595507649d495651d7e5065bc7b15087a3d6f`. No se creó un mirror real porque falta destino/namespace explícito.


### >50 identidades/API — RIU-0079
El Router ya soportaba 1000+ nodos en `RedUniversal`; se añadió `red/identity_pool.py` para resolver el GAP de muchas identidades/proveedores sin fan-out. El pool registra sólo referencias `secret_env`, valida `connector_kind` contra el registry y selecciona una identidad elegible por vez usando prioridad, mirror rank, quota-exhausted y cooldown. Test exacto `7ec0a58b7f4557984963f099dd113ea48d4be110`: HF Job `6aac7f48b1dc2b62dc58fb73` COMPLETED, 5/5 rondas, 5 tests por ronda, incluyendo rollover secuencial de **64 identidades**. Routing ownership permanece en RedUniversal.


### Cómputo HF — RIU-0080
HF1/HF2/HF3 son workers lógicos, no máquinas fijas. Política: HF1 control/tests/small en CPU; HF2 GPU medio con baseline A10G para Qwen3-8B ya verificado; HF3 large/burst seleccionado por benchmark (48 GB/multi-GPU/provider Endpoint según modelo). No se aprovisiona hardware caro especulativamente. Evidencia/política: `forensics/RIU-0080-HF-COMPUTE-SIZING-2026-09-17.md`, commit `fbd82905b0a73b3bd5c9714726564f1b8b4f8479`.


### Mix de modelos para agentes — RIU-0081
Política de escalado por tier: tiny/triage M10/M01/M07; small M12/M11; standard ~7B–8B M05/M20/M03; specialist/large sólo cuando la ruta exacta tenga runtime PASS. Auth/quota/health usa failover de identidad/mirror dentro del mismo tier antes de subir tamaño. Evidencia: `forensics/RIU-0081-AGENT-MODEL-MIX-2026-09-17.md`, commit `7c91f51e3aec6c0d6108e68b4132ec232d2513cd`.


### HF MCP + API — RIU-0082
HF MCP oficial=`https://huggingface.co/mcp` con autenticación OAuth/client-managed; Hub/Inference conserva credencial API separada por referencia de entorno. RIU no serializa secretos ni reutiliza una credencial como otro mecanismo sin evidencia. Exact test commit `f97791ca61197ecbdad0d1d2bb7c792a37c721dc`, HF Job `6aac809f5c02253cfb145474` COMPLETED, 5×10 tests PASS. Runtime OAuth MCP remoto de RIU sigue pendiente. Auditoría: `forensics/RIU-0082-HF-MCP-API-BOUNDARY-2026-09-17.md`.


## AI Staff — Video / Animation Models — RIU-0085
Destino lógico: `AI Staff -> Video / Animation Models`. Estos modelos son especialistas, **no agentes** y no reciben ownership de routing.

| Modelo | Especialidad | Licencia observada en HF | Estado real |
|---|---|---|---|
| `Wan-AI/Wan2.2-Animate-14B` | video-to-video, animación/personajes, transferencia de movimiento | Apache-2.0 | GAP_PENDING |
| `Lightricks/LTX-Video` | image-to-video, workflows de video, control de movimiento | other — términos exactos por verificar | GAP_PENDING |
| `tencent/HunyuanVideo` | text-to-video, foundation video | other — términos exactos por verificar | GAP_PENDING |

Flujo obligatorio: `repo HF -> motor de descarga existente -> revision + archivos -> hash -> carga real -> inferencia smoke -> evidencia -> AI Staff registry -> Router`.

No se habilita producción hasta validar licencia individual, revisión, tamaño, hashes, requisitos de cómputo y prueba de carga. Fuentes:
- https://huggingface.co/Wan-AI/Wan2.2-Animate-14B
- https://huggingface.co/Lightricks/LTX-Video
- https://huggingface.co/tencent/HunyuanVideo


## AI Staff — Image / Design Models — RIU-0086
Destino: `AI Staff -> Image & Design Models`. Son modelos especializados, no agentes.

| Modelo | Función | Licencia HF | Estado |
|---|---|---|---|
| `kandinskylab/Kandinsky-5.0-T2I-Lite-sft-Diffusers` | text-to-image / diseño generativo | MIT | GAP_PENDING |
| `Qwen/Qwen-Image` | generación/edición de imagen y texto visual | Apache-2.0 | GAP_PENDING |
| `black-forest-labs/FLUX.1-schnell` | text-to-image rápido | Apache-2.0 + acceso gated | GAP_PENDING |

Regla: registrar != descargar != hash-verificar != cargar != inferir != PASS. Cada modelo pasa por el motor de descarga existente, revisión fija, selección de fileset, hash, carga e inferencia antes de promoverse.


## Hugging Face AI Staff — contrato remoto autoritativo RIU-0090
Los modelos del AI Staff no se descargan ni se instalan como pesos persistentes en Hugging Face, buckets, Spaces o el Router. Se consumen remotamente.

Ruta canónica: `RedUniversal -> connector_registry -> HF adapter/InferenceClient -> Inference Provider o Endpoint remoto -> model_id -> respuesta`.

El diseño RIU-0078 de `duplicate_repo` / `snapshot_download` se conserva sólo como provenance histórica y queda SUPERSEDED para la integración normal de modelos AI Staff. Un cache temporal dentro de HF Jobs se clasifica `EPHEMERAL_JOB_CACHE`, nunca `INSTALLED`.

Gate por modelo: `REGISTER -> REMOTE_PROVIDER_DISCOVERY -> AUTH_REFERENCE -> REMOTE_INFERENCE_SMOKE -> FAILURE_FALLBACK_TEST -> EVIDENCE -> READY`.

Auditoría RIU-0090: el histórico `MODEL_CERTIFICATION_20_OF_20_ACCOUNTED` demuestra contabilización de catálogo, no 20 provider calls. M01/M02/M03 tienen evidencia de inferencia real dentro de HF Jobs; los demás PASS históricos deben recertificarse como llamadas remotas provider-hosted antes de considerarse READY bajo este contrato.

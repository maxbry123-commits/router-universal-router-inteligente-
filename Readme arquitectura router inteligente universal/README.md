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
Snapshot base auditado: `main@d001d96cfa382888d409255e5dd3e9d2b6372860`. Se detectaron **29 entradas raíz**. La regla es: raíz presente != runtime integrado; cada entrada recibe un rol, una decisión y un gate de cierre.

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
| 29 | `.github/workflows` (contenido de #1) | ejecución programada | CHILD-OF-.github; cualquier watchdog/CI debe reportar evidencia y no declarar PASS por calendario. |

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
`ROOT_29_ACCOUNTED + EXTERNAL_4_BOUNDARIES_DEFINED + NO_ROUTING_OWNERSHIP_CONFLICT + AUTH_RUNTIME_VERIFIED + CONNECTIVITY_GLOBAL_E2E_PASS + STATE_PLAN_BITACORA_SYNC`.

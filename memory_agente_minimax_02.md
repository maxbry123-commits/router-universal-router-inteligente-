# memory_agente_minimax_02.md

> Fuente de verdad unica del bucle (yaiwes.node/v2). Escritor: solo el orquestador. Un commit por
> actualizacion. Prohibido: secretos, claves, contrasenas, tokens.
> Repositorio de trabajo: `maxbry123-commits/router-universal-router-inteligente-`, rama `main`.

```json
{
  "version": 1,
  "objective": "Recuperacion del cableado roto del Router Inteligente Universal + registro central de conectividad + reorganizacion de la raiz",
  "state": {
    "node": "N3_rewrite_j6",
    "step": "EXECUTE",
    "fsm": "EXECUTING",
    "run_id": "20261104-kernel01",
    "actualizado": "2026-11-06T07:20Z"
  },
  "queue": [
    {
      "id": "A1",
      "goal": "Congelar estado: inventario de raiz de main y de las 9 ramas",
      "ac_ids": [
        "AC1"
      ],
      "status": "DONE"
    },
    {
      "id": "A2",
      "goal": "Reconstruir el cableado historico comparando main vs reorganizacion vs respaldo-cableado-2026-10-25 vs devin/1792939533-loop-cableado",
      "ac_ids": [
        "AC2"
      ],
      "status": "DONE (via JOB wiring 6aeb13aa0e0338d1bb7fba2e)"
    },
    {
      "id": "A3",
      "goal": "Registro central: connections/{registry,topology,endpoints,healthchecks}.yaml con PRESERVED/REMOVED/MODIFIED/NEW/BROKEN_CANDIDATE/UNKNOWN",
      "ac_ids": [
        "AC3"
      ],
      "status": "PENDING (tras evidencia del JOB)"
    },
    {
      "id": "B1",
      "goal": "Corte 1: harness '/plugins/loop_wachdog/call/paso' no resuelve en main",
      "ac_ids": [
        "AC2",
        "AC4"
      ],
      "status": "IDENTIFIED / propuesta en curso"
    },
    {
      "id": "B2",
      "goal": "Corte 2: 4 plugins con destino vacio: connectivity, hf_compute, hf_storage, lifeguard",
      "ac_ids": [
        "AC2",
        "AC4"
      ],
      "status": "IDENTIFIED / propuesta en curso"
    },
    {
      "id": "B3",
      "goal": "Corte 3: la raiz del router (router/, raiz_router/, raiz_fichas_prompt/, fichas/, plugins/) no esta en main",
      "ac_ids": [
        "AC1",
        "AC4"
      ],
      "status": "IDENTIFIED / propuesta en curso"
    },
    {
      "id": "B4",
      "goal": "Registrar la topologia real: router -> fichas/prompt/motores -> HTTP -> plugins -> harness deepseek -> chat",
      "ac_ids": [
        "AC3",
        "AC5"
      ],
      "status": "PENDING"
    },
    {
      "id": "C1",
      "goal": "Inventario de raiz con clasificacion por RESPONSABILIDAD + consumidor de cada archivo",
      "ac_ids": [
        "AC1"
      ],
      "status": "DONE (via JOB root 6aeb13aa0e0338d1bb7fba30)"
    },
    {
      "id": "C2",
      "goal": "Mover archivo por archivo: dependencias, justificacion en log, commit propio, read-back",
      "ac_ids": [
        "AC1"
      ],
      "status": "PENDING"
    },
    {
      "id": "D1",
      "goal": "Colocar la guia como AGENTS.md en la raiz",
      "ac_ids": [
        "AC6"
      ],
      "status": "PENDING"
    },
    {
      "id": "D2",
      "goal": "Healthchecks reales: /health del Router (d82217f15e), MCP tools/list (14), harness deepseek",
      "ac_ids": [
        "AC5"
      ],
      "status": "PENDING"
    },
    {
      "id": "D3",
      "goal": "Auditoria final 3 pasadas + refutaciones INPUT_BLOCK / OBJECTIVES_AND_TASKS / WORKFLOW_LOOP_INTEGRITY",
      "ac_ids": [
        "AC6"
      ],
      "status": "PENDING"
    }
  ],
  "handoff": {
    "next": "j6_rewrite",
    "missing": [
      "GH_TOKEN no existe en la cuenta HF -> historial reconstruido por API GitHub via Router RIU (desviacion D1); sin eso no hay git clone ni git bisect",
      "authorized_deploy del contrato venia vacio [] -> rellenado con la autorizacion del owner en chat + guia L5; documentado como flag",
      "El 'espejo' publico abc1tienda-web/router-universal-router-inteligente- es OTRO linaje (6 ramas distintas, main=9d260ff4, push 2026-09-23, sin chat-router/) -> NO sirve para PASO 1",
      "Falta evidencia runtime de que cada conexion funciono (logs/trazas); la guia L14 lo exige para afirmar conexiones que funcionaban en ejecucion"
    ]
  },
  "log": [
    "[N1_xray][xray][lectura guia 18 secciones + raiz main + 9 ramas + manifest + contrato LOOP][3 cortes][RESEARCH_PASS]",
    "[N2_research][research_20_sources][2 busquedas en vivo: git-archaeology + catalogo de conectividad][ok][RESEARCH_PASS]",
    "[N3_dispatch][guardian_pre][centinela Verifier (1 solo agente) lee la guia verbatim y refuta][3 cortes confirmados][EXECUTING]",
    "[N4_execute][write][ops/historical_wiring_audit.py = L153-345 verbatim sha256 4c8e64f0][commit 276f0a4d12 read-back MATCH][EXECUTING]",
    "[N4_execute][write][ops/root_structure_audit.py = L360-500 verbatim sha256 9c87f61c][commit 37b4723e5e read-back MATCH][EXECUTING]",
    "[N4_execute][write][ops/connectivity_job.py = L615-747 verbatim sha256 351c24a5][commit 8799732dc1 read-back MATCH][EXECUTING]",
    "[N4_execute][write][ops/wiring_audit_runner.py adaptador transporte 20673B sha256 affb46dd][commit a6bcec4402 read-back MATCH][EXECUTING]",
    "[N4_execute][hf_dataset][COMAND-CENTER-1/router-universal-router-inteligente-auditoria][visible=public segun API][guia L525][EXECUTING]",
    "[N4_execute][hf_job][JOB wiring 6aeb13aa0e0338d1bb7fba2e RUNNING secrets HF_TOKEN+RIU_ROUTER_API_KEY][ejecutando][EXECUTING]",
    "[N4_execute][hf_job][JOB root 6aeb13aa0e0338d1bb7fba30 RUNNING][ejecutando][EXECUTING]"
  ],
  "flags": [
    {
      "task": "A2",
      "cause": "CORREGIDO 2026-11-06: el repo canonico es PUBLICO (private=false, visibility=public) y ${GH_TOKEN} EXISTE en el entorno; la guia L537 era obsoleta. La clonacion se hace con cabecera GIT_CONFIG_* extraheader (token solo en entorno).",
      "routes_tried": [
        "git clone con GH_TOKEN: ADOPTADO - ${GH_TOKEN} existe (PAGADO 2026-11-06)",
        "espejo publico abc1tienda-web: verificado otro linaje, NO sirve",
        "bucket HF con codigo actual: sin historial git",
        "API GitHub via Router RIU: ADOPTADA (sigue siendo la via sancionada)"
      ],
      "proposal": "desviacion D1-D4 declarada en cada artefacto; adaptador etiquetado y con metricas de cobertura por commit"
    },
    {
      "task": "N0_capture",
      "cause": "origin del contrato vacio (input block = adjunto local sin URL)",
      "routes_tried": [
        "adjunto local + SHA-256 5c77e005"
      ],
      "proposal": "origin=adjunto local congelado por hash"
    },
    {
      "task": "N0_capture",
      "cause": "repo del contrato = maxbry123-commits/agentes; el trabajo real es router-universal-router-inteligente-",
      "routes_tried": [
        "NO_REWRITE aplicado"
      ],
      "proposal": "trabajar sobre el repo real; el campo del contrato queda intacto"
    },
    {
      "task": "N3_dispatch",
      "cause": "authorized_deploy del contrato venia vacio [] y permissions.huggingface_deploy/hf_cpu_job_32gb lo condicionan",
      "routes_tried": [
        "guia L5 + L512-549 + instruccion del owner en chat"
      ],
      "proposal": "authorized_deploy = huggingface_jobs audit-only, documentado en este archivo"
    }
  ],
  "research_cache": [
    {
      "keywords": [
        "git history archaeology recover lost connections",
        "central connectivity registry yaml healthchecks"
      ],
      "date": "2026-11-04",
      "chosen": "Reconstruir por commit (no por nombre) + registrar antes de mover; catalogo central YAML con estados y healthchecks por conexion",
      "sources": [
        "https://github.com/mattlennon/git-archaeology",
        "https://github.com/useosint/skills/blob/HEAD/skills/secrets-in-git-history/reference/git-archaeology.md",
        "https://tamiz.pro/insights/ai-tribute-apps-abandoned-software",
        "https://github.com/dfrysinger/skills/blob/main/skills/git-history-recovery/SKILL.md",
        "https://github.com/David-Li0406/meta-skill-evloving/blob/main/skill-flow/data/skills-refined-36k/skillsmp/archive-searcher/SKILL.md",
        "https://monorepo-book.github.io/",
        "https://techcommune.org/docs/devops/git-recovery.html",
        "https://github.com/git-merge-workshops/monorepo-spring-cleaning",
        "https://github.com/azizullahkhan16/az-400-study-notes/blob/master/01-git-for-enterprise-devops.md",
        "https://dev.to/frank_njoroge_40c0b33040f/ghostarchive-the-code-is-gone-git-remembers-4mng",
        "https://policyascode.dev/blog/platform-engineering-internal-developer-portals-guide/",
        "https://github.com/adamatdevops/forge-works",
        "https://github.com/rezarajan/platformctl",
        "https://backstage.io/docs/next/overview/technical-overview/",
        "https://github.com/HeadySystems/Heady-Testing/blob/main/README.md",
        "https://backstage.io/docs/features/software-catalog/creating-the-catalog-graph/",
        "https://notes.kodekloud.com/docs/Prep-Course-Certified-Cloud-Native-Platform-Engineering-Associate-CNPA/Domain-5-Internal-Developer-Platforms-Developer-Experience/Developer-Portals-With-Backstage/page",
        "https://cloud.alauda.cn/knowledge/solutions/Managing-Platform-Configuration-and-Onboarding-Isolated-Projects-with-Argo-CD-and-Tekton-on-ACP.html",
        "https://code.claude.com/docs/en/large-codebases",
        "https://backstage.io/docs/features/software-catalog/configuration/"
      ],
      "context_pack_ref": "skill yaiwes-node-dag + references/conexiones.md"
    },
    {
      "keywords": [
        "hf jobs api schema",
        "hf dataset informes auditoria",
        "git archaeology ramas"
      ],
      "date": "2026-11-04",
      "chosen": "POST /api/jobs/{ns} con flavor + secrets(record) + environment; Dataset COMAND-CENTER-1/router-universal-router-inteligente-auditoria para persistir informes",
      "sources": [
        "https://huggingface.co/api/jobs/COMAND-CENTER-1",
        "https://huggingface.co/api/datasets/COMAND-CENTER-1/yaiwes-hf-memoria",
        "https://huggingface.co/docs/huggingface_hub/guides/jobs"
      ],
      "context_pack_ref": "skill yaiwes-node-dag + references/conexiones.md"
    }
  ],
  "progress_pct": 27,
  "progress_formula": "100 * CLOSED_NODES / 11 (nodos del DAG v3: N0..N10); cerrados N0,N1,N2 -> 3/11 = 27 (los jobs j0-j5/j11 son de la fase anterior, no son nodos de este DAG)",
  "nodos_cerrados": ["N0_reconciliar","N1_j7_baseline","N2_j8_audit_pre","S1_j0","S2_j1_j2_j3","S3_j4","S5_j5","S6_roadmap"],
  "nodos_abiertos": ["N3_j6_rewrite","N4_swap_main","N5_bridge","N6_remirror","N7_auditoria_final","N8_cableado","N9_bitacora_readme","N10_cierre"],
  "authorized_deploy": [
    "huggingface_jobs:audit-only (JOB 1 + JOB 2 de la guia, L147/L352; dataset de informes COMAND-CENTER-1/router-universal-router-inteligente-auditoria) - autorizacion explicita del owner en chat 2026-11-04: 'todo lo vas hacer con los job'"
  ],
  "evidence": [
    {
      "command_or_test": "sha256 guia adjunta",
      "output": "5c77e0051a4e8caaee123b5e199980d98c9cd7b144ff246dbb2cccf415048943 (1719 lineas, 35537 B)",
      "exit_code": 0,
      "timestamp": "2026-11-04T10:58:20Z",
      "commit_hash": ""
    },
    {
      "command_or_test": "read-back ops/*.py via Router github_leer",
      "output": "4/4 MATCH de sha256",
      "exit_code": 0,
      "timestamp": "2026-11-04T11:13:00Z",
      "commit_hash": "a6bcec4402"
    },
    {
      "command_or_test": "POST /api/jobs/COMAND-CENTER-1 (schema: flavor + secrets record)",
      "output": "6aeb13aa0e0338d1bb7fba2e (wiring) RUNNING; 6aeb13aa0e0338d1bb7fba30 (root) RUNNING",
      "exit_code": 0,
      "timestamp": "2026-11-04T11:15:00Z",
      "commit_hash": ""
    }
  ]
}
```

## ESTADO REAL AUDITADO (2026-11-04)

### Ramas (9) y su rol
| Rama | Raiz | Rol |
|---|---|---|
| `main` | `.claude/ .github/ chat-router/ dsla/ pruebas Nvidia groq/ router-mvp/` | actual; **sin** raiz del router |
| `reorganizacion` | `router/ raiz_router/ raiz_fichas_prompt/ fichas/ plugins/ componentes/ docs/ Skills/ chat-router/` | **organizacion objetivo ya existe aqui** |
| `respaldo-cableado-2026-10-25` | `+ chat/ Prueba/ router/ plugins/ fichas/ raiz_*/` | cableado que funcionaba (1134 commits detras) |
| `devin/1792932933-loop-cableado` | `+ router-componentes/` | variante con loop cableado |
| `respaldo-main-antes-reversion-swen-20261103` | igual que main | backup |
| `banco-claves`, `fix/hydrate-vault-vacio`, `ccr-c57a3ec7-9q2ixl` | - | auxiliares |

### Los 3 cortes de cableado (con evidencia)
1. **Corte 1** - `chat-router/chat/frontend/LOOP-wachdog-cola.json` declara `harness: "/plugins/loop_wachdog/call/paso"`; en main no hay `plugins/` en la raiz (en `chat-router/plugins/` existen `nct_loop` y `watchdog48`, no `loop_wachdog`).
2. **Corte 2** - `chat-router/cableado.manifest.json` deja `connectivity`, `hf_compute`, `hf_storage`, `lifeguard` con `"destino": ""` y `"enlace": false`.
3. **Corte 3** - `router/ raiz_router/ raiz_fichas_prompt/ fichas/` estan dentro de `router-mvp/` en main; en la raiz solo en `reorganizacion` y `respaldo-cableado-2026-10-25`.

### Evidencia adicional (2026-11-04)
- `chat-router/cableado.manifest.json` **NO existe en `reorganizacion`** (404 via Router) = artefacto POSTERIOR al cableado -> bin `cableado_despues`.
- El espejo publico `abc1tienda-web/...` es otro linaje: 6 ramas distintas, `main=9d260ff4`, push 2026-09-23, raiz con `Chat Mvp/ Claude notas/` y **sin `chat-router/`**.
- El Router RIU trunca `github_api` a **12000 B exactos**; `github_leer` devuelve archivo completo.
- Pickaxe disponible: `GET /search/commits?q=repo:...+cableado` -> 28 commits.

### Topologia a registrar
`router (edificio) -> fichas / prompt / motores -> HTTP -> plugins -> harness deepseek -> chat -> resto`

### Restricciones vigentes
- No declarar conexion `active` sin healthcheck (guia §8). El Router sirve `lfm2.5-350m` cuando se pide `qwen3.8-max` -> **declarado != real**.
- Motores de descarga/extraccion intocables: solo copia.
- No crear los ~22 directorios de la estructura de referencia vacios (guia lo prohibe).
- No restaurar commits completos: solo los cambios necesarios.
- Fuera de `root_protection.allowlist`: una linea de justificacion por escritura/movimiento.



---

## ESTUDIO DE MOTORES DE DESCARGA Y EXTRACCIÓN (2026-11-04)

### Objetivo
Leer el skill canónico, el código fuente y el historial de commits de los motores de descarga/extracción/copia/movimiento en los repos `frontend`, `agentes` y `router-universal-router-inteligente-`; entender la lógica y aprender a montarlos.

### Raíces canónicas (3 linajes, mismo origen)
| Repo | Raíz | Skill |
|---|---|---|
| `frontend` | `➡️📂motores de descarga extracción copiado movimiento archivos fromtend/` | canónico (7 blobs SHA) |
| `frontend` | `➡️📂motores de descarga extracción copiado movimiento archivos router-universal-router-inteligente-/` | copia 2026-10-25 |
| `frontend` | `UI YAIWES/➡️📂motores ... frontend/` | espejo |
| `agentes` | `➡️📂motores de descarga extracción copiado movimiento archivos agentes/` | copia verificada |
| `agentes` | `Motores/` | copia |
| `agentes` | `➡️📂 wordflow loop code Yaiwes/➡️📂motores ... agentes/` | copia |

### Blob SHA verificados (via Router RIU `github_api` -> `/git/trees`)
| Motor | SHA canónico | Estado verificado |
|---|---|---|
| `motor_1_extract_only.py` | `a52d5dc0e6ff26f75d753b848dcc1a40c5dd4500` | MATCH en los 6 linajes |
| `motor_2_queue_download_extract.py` | `84d566e2ee4e98e42eb3a864026d067d48caabd9` | MATCH en los 6 linajes |
| `hf_download_extract_engine.py` | `91e6e4486692eab314be5c7130d8310d3c855397` | **DIFF en 2 linajes** (ver gap G-MOTOR-01) |
| `motor_3_copy_batches.py` | `3689924361ce4a1a9fde4ae2b6f6009c37a6042d` | MATCH en los 6 linajes |
| `motor_copy_root_to_repo.py` | `8281211da76db3080fe1f1ea38b3eb0c45d655cb` | MATCH en los 6 linajes |
| `motor_4_move_batches.py` | `9a21facfe11327cf60a2afca8f415ad52f0ecbe5` | MATCH en los 6 linajes |
| `motor_5_zip_root.py` | `2516d85d81f691f86c32a70b90c2599639eb83c6` | declarado en skill `fromtend` y en `MOTOR-CODE-LOCK.json` |

### Lógica de los 6 motores (copy-only, FAIL_CLOSED)
1. **motor_1_extract_only.py** (`yaiwes.frontend.extract-only.v1`): extrae ZIP. Entradas `ARCHIVE_INPUT`, `DEST_DIR`, `STATE_FILE`, `BATCH_SIZE`. Reconstruye ZIP fragmentado (`*.zip.part-*`), CRC, bloquea rutas inseguras y symlink, extrae por lotes, persiste estado, `tree_hash` (rel+sha256+bytes), read-back. PASS = `VERIFIED_CLOSED` + `failed=0` + `pending=0`.
2. **motor_2_queue_download_extract.py** (`yaiwes.frontend.download-extract-queue.v1`): cola JSON de items `{source_repo, source_ref, slug, dest_repo, dest_branch, dest_root, publish}`. Envía cada item al engine como proceso hijo con env por item, parsea la ultima linea JSON, exige `verdict == VERIFIED_CLOSED`. Balance: `VERIFIED_CLOSED`, `source_commit`, `extraction_verified`, `PUBLISHED_AND_EXTRACTED_READBACK_VERIFIED`.
3. **hf_download_extract_engine.py** (`yaiwes.hf.download-extract.v1`): el motor real. `acquire()` -> `git init` + remote + `no_lfs()` (desactiva filtros LFS) + `fetch --depth=1 --filter=blob:none` + checkout detached. `scan_tree()` -> rechaza punteros LFS (`SOURCE_LFS_POINTER_GAP`), symlinks/especiales (`SOURCE_SPECIAL_FILE_GAP`), blobs >= 95 MiB (`GIT_BLOB_LIMIT_GAP`). `tree_hash()` determinista. `make_zip()` (DEFLATE, timestamp fijo 1980-01-01, `testzip()`). `split_bundle()` en partes de 12 MiB con sha256 por parte. `rebuild()` reensambla y verifica sha256 del bundle + CRC. `safe_extract()` bloquea path absoluto/`..` y ficheros especiales ZIP. Verifica `ext_tree == src_tree`. `publish()` -> sparse-checkout del destino, commit sin force, rebase con deteccion de conflicto, push, y **read-back**: relee manifest y compara sha256 de cada parte + tree hash del codigo. Manifiesto: `DOWNLOAD_EXTRACT_MANIFEST.json` con `source_commit`, `bundle_sha256`, `parts[]`, `extracted_tree`.
4. **motor_3_copy_batches.py** (`yaiwes.frontend.copy-batches.v1`): copia por lotes con `SOURCE_DIR`/`DEST_DIR`/`STATE_FILE`/`BATCH_SIZE=1..100`/`COLLISION_POLICY=fail|skip|replace`/`MAX_BATCHES`. Escribe en `.partial` y `os.replace` atomico; verifica sha256 antes de copiar, del `.partial` y del destino (`COPY_HASH_MISMATCH`, `READBACK_HASH_MISMATCH`).
5. **motor_copy_root_to_repo.py** (`yaiwes.repo-root-copy.v1`): motor EXCLUSIVO para copiar la raiz de motores a otro repo. `SOURCE_ROOT`, `DEST_ROOT`, `DEST_REPO_NAME`, `BATCH_SIZE=2`. Valida nombre exacto de la raiz destino (`➡️📂motores de descarga extracción copiado movimiento archivos <NOMBRE_REPO>/`), valida allowlist exacta de 7 archivos, borra la raiz destino si falla, no crea ledger/manifest, salida solo por stdout.
6. **motor_4_move_batches.py** (`yaiwes.frontend.move-batches.v1`): mover por lotes. Mueve a `.moving`, verifica sha256, `os.replace`, borra el origen solo tras copia verificada; limpia directorios vacios.

### Motor de busqueda (regla de 20 fuentes, sin LLM)
`➡️📂 motor de búsqueda/`: `websearch_engine.py` (5 proveedores: ddgs, brave, tavily, serper, firecrawl; dedup + ranking determinista; `result.json` + `summary.md`), `trigger_hf_websearch.py` (dispara HF Job ON_DEMAND, namespace COMAND-CENTER-1, flavor cpu-upgrade, workers HF1/HF2/HF3, engine pinneado a commit `029f516ce049c327a158b915a8ec5517236baeab`, publica en GitHub sin Actions con read-back), `research_prepass.py` (`yaiwes.research.prepass.v1`, genera `context_packet` desde `source_registry.json` + `context_packet.schema.json`), `source_registry.json`, tests deterministas sin red.

### Motor de archivos vigente en el Router (NO es el canonico de skill)
`chat-router/chat/backend/mvp/archivos/` -> herramienta MCP `archivos`. Acciones: `transferir|ejecutar|estado|cancelar|raiz|listar_raiz`. Modulo `motor de archivos` (tool.json): origen URL/git/local -> cola en hilo -> README + MANIFEST.json con sha256 -> destino `git:owner/repo@rama/carpeta`. Limites: `RIU_MOTOR_MAX_BYTES` 4 GiB, `RIU_MOTOR_MAX_ARCHIVOS` 300000, red interna bloqueada (`url_segura`), zip-slip bloqueado, `expected_head` revalidado antes de publicar. Publica por lotes de 200 MiB con `hash-object --no-filters` (blobs identicos, sin LFS) y `commit-tree` + push por lote.

### Historial de commits reconstruido (pickaxe `/search/commits`)
- `2026-09-09T17:12:54` `b7103bc7ab` build(motors): add immutable code lock manifest -> crea `MOTOR-CODE-LOCK.json` (`yaiwes.motors.code-lock.v1`, `FAIL_CLOSED_IMMUTABLE`).
- `2026-09-09T17:14:00` (ledger) `MOTOR3_VERIFIED_CLOSED_THEN_PUBLISH`: primer paso oficial de copia frontend -> agentes, `BATCH_SIZE=2`.
- `2026-09-09T17:17:50` `957626de32` refactor(motors): remove legacy move motor copy.
- `2026-09-09T21:47:07` `e0b3cd3bc9` fix(motors): keep single canonical motors root.
- `2026-09-10T08:16:11` `1c4a5ff346` copy motor_1_extract_only.py into componentes dest.
- `2026-09-10T08:16:19` `cecfd0f79f` copy hf_download_extract_engine.py into componentes dest.
- `2026-09-15T03:36:12` (ledger) `SURGICAL_COPY_METHOD_REPAIR`: `VERIFIED_CLOSED` 9 archivos; **repara un metodo previo no conforme que usaba GitHub Actions** -> confirma la prohibicion de Actions.
- `2026-09-15T03:45:42` (ledger) `SURGICAL_COPY_MUSE_CODE_TRACEABILITY`: `VERIFIED_CLOSED` 17 archivos, read-back HF_JOB.
- `2026-09-21T21:56:37` `29a3218436` (agentes) feat(motors): mirror canonical motor_5_zip_root.
- `2026-09-21T21:58:14` `d13bd83f2d` docs(motors): register canonical motor_5 root zip contract.
- `2026-09-21T21:58:38` `d1d5723233` (agentes) docs(motors): document motor_5 root zip.
- `2026-09-26` (dentro del codigo divergente) `ALREADY_PRESENT_VERIFIED`, `SOURCE_REF_GAP` (fallback HEAD/main/master), `strip_special` -> cambios "autorizados por el Director".
- `2026-09-29T17:30:47` `1c84a66c94` Motor de descarga: MOTOR_RUN_1723 create_or_update_file probe.
- `2026-10-17T18:22:37/42` `0dc97002d3`/`f85f5ed3ea` motor_3: espejos de skills desde yaiwes-factory-ui.
- `2026-10-25T02:10:17` `f24619095d` "Copia 1 a 1, input block verbatim, de los skills en la raiz del frontend" -> commit que introduce la raiz `router-universal-router-inteligente-` en `frontend`.

### Gaps detectados
- **G-MOTOR-01 (integridad, PENDIENTE de autorizacion)**: `hf_download_extract_engine.py` en la raiz `router-universal-router-inteligente-` (repo `frontend` y `agentes`) tiene blob `a0e1c87f1a5b...` != canonico `91e6e4486692...`, pese a que su propio SKILL (seccion 3) declara `91e6e448` como canonico. Diferencias: `OK_VERDICTS` con `ALREADY_PRESENT_VERIFIED`, fallback de `SOURCE_REF` a HEAD/main/master, `strip_special()` que deja de bloquear symlinks del origen, y `DESTINATION_EXISTS` -> exito en vez de error. Los 5 motores restantes si coinciden. NO se modifica (motores intocables): requiere autorizacion explicita del owner en el chat actual.
- **G-MOTOR-02 (documental, PENDIENTE)**: el `MOTOR-CODE-LOCK.json` de `agentes` lista `canonical_source` en la raiz `fromtend` y declara `motor_5_zip_root.py`; la raiz `router-universal-router-inteligente-` de `frontend` NO tiene `motor_5_zip_root.py` en su allowlist de skill (7 archivos) aunque su MOTORES_VERSION.json declara origen `router-universal-router-inteligente-` commit `c883ccea4701efb1ad9b7e53908c6608c7c347ea`.
- **G-MCP-01 (RESUELTO)**: el Space `claude-github-mcp-backup` estaba en pausa (503). Reiniciado via API HF; el MCP del Router RIU quedo operativo y es la via sancionada para GitHub (14+1 tools: `github_leer`, `github_escribir`, `github_api`, `archivos`, `memoria`, `pendientes`, `salud`...).
- **G-MCP-02 (limitacion conocida)**: `github_api` del Router trunca a 12000 B exactos y **ignora el filtro `path`** de `/commits`. `github_leer` si entrega el archivo completo. Pickaxe `/search/commits?q=` funciona y es la via para el historial.
- **G-MCP-03 (ENV) — RESUELTO 2026-11-06**: la nota original ("el repo canonico es privado y no hay `GITHUB_TOKEN`") era FALSA. Hechos verificados: `maxbry123-commits/router-universal-router-inteligente-` es PUBLICO (`private=false`, `visibility=public`) y `${GH_TOKEN}` existe en el entorno. El clon usa cabecera `GIT_CONFIG_*` extraheader (token solo en entorno, nunca en URL/argv/logs); la API del Router RIU sigue siendo la via sancionada alternativa.

### Como montar los motores (procedimiento aprendido)
1. Leer el SKILL completo de la raiz canonica (`frontend`, rama `main`).
2. Confirmar que el usuario entrega el destino (`DESTINATION_INPUT_GAP` si falta). Nunca deducir ni reutilizar un destino previo.
3. Copiar el codigo fuente exacto conservando el blob SHA (solo `copy_only`).
4. Ejecutar con env explicita: `SOURCE_DIR/DEST_DIR/STATE_FILE/BATCH_SIZE/COLLISION_POLICY` (motores 3 y 4), `ARCHIVE_INPUT/DEST_DIR/STATE_FILE` (motor 1), `QUEUE_FILE/ENGINE_PATH/INDEX_PATH/SOURCE_REPO/SOURCE_REF/DEST_REPO/DEST_BRANCH/DEST_ROOT/PUBLISH` (motores 2 y engine).
5. Persistir el estado en un `STATE_FILE` **fuera** de la raiz final (la raiz destino no admite ficheros extra).
6. Cerrar solo con `VERIFIED_CLOSED` + `failed=0` + `pending=0` + read-back de `main` comparando nombre, allowlist y los 6 blob SHA.
7. Publicar sin force; si la rama avanzo, releer `main` y reconstruir sobre el nuevo parent.
8. Registrar la evidencia en el commit (nunca un ledger adicional dentro de la raiz de motores).

---

## ESTADO CANONICO (2026-11-06T07:20Z) — la verdad esta en `kernel/KERNEL.yaml` + Dataset `20261104-kernel01`

- **Cerrado con evidencia**: N0 (reconciliar), N1 (j7_mirror PASS: 6.170 ficheros / 110,7 MB, Space RUNNING), N2 (j8_audit PHASE=pre PASS: 8 jobs PASS + wiring_check_on_target).
- **En curso**: N3 — j6_rewrite en dos etapas: `prepare` (bundle de rollback de 8,07 GB **subido** al Dataset, commit `3bb6161d1`) y `rewrite` (purga de 37 directorios + rama `main-clean`).
- **Ramas**: `reorg/20261104-kernel01` = `fd79657c37` (trabajo) · `main` = `c2ad951e0ca3` (intacta hasta el swap) · `respaldo-main-pre-swap-20261104-kernel01` = `c2ad951e0ca3` (ancla de rollback creada) · tag `pre-reorg-20261104-kernel01` = `40c8d591ab`.
- **Decisiones fijadas por el owner**: HF = espejo/auto-pull mínimo; servidores de pago 32 GB CPU con cola al 85 % y sueño a los 15 min; 1 modelo local por servidor; umbral `ACTIVE` de 7 condiciones; motor `research_prepass.py` **intacto**; claves **intactas**.
- **Artefactos nuevos**: `CODE_INDEX.md` (11 entradas, rutas reales), `SYSTEM_WIRING_REGISTRY.yaml` (registro maestro), `handoff/docs/*` (5 handoffs), `kernel/INPUT_BLOCK_YAIWES_CABLEADO.md` (objetivos verbatim).
- **Vetos del SHERIFF resueltos**: B1 token fuera de argv y de `.git/config` (D-114); B3 firma `path_or_fileobj` (D-113); B4 `main-clean` en curso; B2/B5 pendientes del swap (el tag se re-apunta al `main` real, que es el commit del owner, y se conserva la rama de respaldo).

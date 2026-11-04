# memory_agente_minimax_02.md

> Fuente de verdad unica del bucle (yaiwes.node/v2). Escritor: solo el orquestador. Un commit por
> actualizacion. Prohibido: secretos, claves, contrasenas, tokens.
> Repositorio de trabajo: `maxbry123-commits/router-universal-router-inteligente-`, rama `main`.

```json
{
  "version": 1,
  "objective": "Recuperacion del cableado roto del Router Inteligente Universal + registro central de conectividad + reorganizacion de la raiz",
  "state": {
    "node": "N4_execute",
    "step": "EXECUTE",
    "fsm": "EXECUTING"
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
    "next": "A3",
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
    "[N4_execute][hf_dataset][COMAND-CENTER-1/router-universal-router-inteligente-auditoria PRIVADO][guia L525][EXECUTING]",
    "[N4_execute][hf_job][JOB wiring 6aeb13aa0e0338d1bb7fba2e RUNNING secrets HF_TOKEN+RIU_ROUTER_API_KEY][ejecutando][EXECUTING]",
    "[N4_execute][hf_job][JOB root 6aeb13aa0e0338d1bb7fba30 RUNNING][ejecutando][EXECUTING]"
  ],
  "flags": [
    {
      "task": "A2",
      "cause": "repo canonico privado + sin secret GH_TOKEN en la cuenta HF (guia L537 lo exige para clonar)",
      "routes_tried": [
        "git clone con GH_TOKEN: no hay PAT",
        "espejo publico abc1tienda-web: verificado otro linaje, NO sirve",
        "bucket HF con codigo actual: sin historial git",
        "API GitHub via Router RIU: ADOPTADA"
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
        "hf dataset privado informes",
        "git archaeology ramas"
      ],
      "date": "2026-11-04",
      "chosen": "POST /api/jobs/{ns} con flavor + secrets(record) + environment; Dataset privado para persistir informes",
      "sources": [
        "https://huggingface.co/api/jobs/COMAND-CENTER-1",
        "https://huggingface.co/api/datasets/COMAND-CENTER-1/yaiwes-hf-memoria",
        "https://huggingface.co/docs/huggingface_hub/guides/jobs"
      ],
      "context_pack_ref": "skill yaiwes-node-dag + references/conexiones.md"
    }
  ],
  "progress_pct": 45,
  "authorized_deploy": [
    "huggingface_jobs:audit-only (JOB 1 + JOB 2 de la guia, L147/L352; dataset de informes privado L525) - autorizacion explicita del owner en chat 2026-11-04: 'todo lo vas hacer con los job'"
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

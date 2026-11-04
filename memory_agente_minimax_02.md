# memory_agente_minimax_02.md

> Fuente de verdad unica del bucle (yaiwes.node/v2). Escritor: solo el orquestador. Un commit por
> actualizacion. Prohibido: secretos, claves, contrasenas, tokens.
> Repositorio de trabajo: `maxbry123-commits/router-universal-router-inteligente-`, rama `main`.

```json
{
  "version": 1,
  "objective": "Recuperacion del cableado roto del Router Inteligente Universal + registro central de conectividad + reorganizacion de la raiz",
  "state": { "node": "N2_research", "step": "RESEARCH", "fsm": "RESEARCH_PASS" },
  "queue": [
    { "id": "A1", "goal": "Congelar estado: inventario de raiz de main y de las 9 ramas, con roles", "ac_ids": ["AC1"], "depends_on": [] },
    { "id": "A2", "goal": "Reconstruir el cableado historico comparando main vs reorganizacion vs respaldo-cableado-2026-10-25 vs devin/1792939533-loop-cableado", "ac_ids": ["AC2"], "depends_on": ["A1"] },
    { "id": "A3", "goal": "Crear connections/registry.yaml + topology.yaml + endpoints.yaml + healthchecks.yaml con estados PRESERVED/REMOVED/MODIFIED/NEW/BROKEN_CANDIDATE/UNKNOWN (solo con evidencia)", "ac_ids": ["AC3"], "depends_on": ["A2"] },
    { "id": "B1", "goal": "Corte 1: harness '/plugins/loop_wachdog/call/paso' de LOOP-wachdog-cola.json no resuelve en main (existen nct_loop y watchdog48 en chat-router/plugins/)", "ac_ids": ["AC2","AC4"], "depends_on": ["A2"] },
    { "id": "B2", "goal": "Corte 2: 4 plugins con destino vacio y enlace false: connectivity, hf_compute, hf_storage, lifeguard", "ac_ids": ["AC2","AC4"], "depends_on": ["A2"] },
    { "id": "B3", "goal": "Corte 3: la raiz del router (router/, raiz_router/, raiz_fichas_prompt/, fichas/, plugins/) no esta en main; vive anidada en router-mvp/", "ac_ids": ["AC1","AC4"], "depends_on": ["A2"] },
    { "id": "B4", "goal": "Registrar la topologia real: router -> fichas/prompt/motores -> HTTP -> plugins -> harness deepseek -> chat", "ac_ids": ["AC3","AC5"], "depends_on": ["A3","B1","B2","B3"] },
    { "id": "C1", "goal": "Inventario de raiz con clasificacion por RESPONSABILIDAD (no solo por extension) y consumidor de cada archivo", "ac_ids": ["AC1"], "depends_on": ["A1"] },
    { "id": "C2", "goal": "Mover archivo por archivo: analisis de dependencias, linea de justificacion en el log, commit propio, read-back", "ac_ids": ["AC1"], "depends_on": ["C1","B4"] },
    { "id": "D1", "goal": "Colocar la guia como AGENTS.md en la raiz (18 secciones) con justificacion de una linea (fuera de allowlist)", "ac_ids": ["AC6"], "depends_on": ["C2"] },
    { "id": "D2", "goal": "Healthchecks reales: /health del Router (commit d82217f15e), MCP tools/list (14 tools), harness deepseek interno", "ac_ids": ["AC5"], "depends_on": ["B4"] },
    { "id": "D3", "goal": "Auditoria final 3 pasadas + refutaciones INPUT_BLOCK / OBJECTIVES_AND_TASKS / WORKFLOW_LOOP_INTEGRITY", "ac_ids": ["AC6"], "depends_on": ["D1","D2"] }
  ],
  "handoff": {
    "next": "A2",
    "missing": [
      "Confirmar si el destino de commits es 'agentes' (dice el JSON del contrato) o el router (repo real del trabajo)",
      "Las 9 ramas no estan auditadas commit a commit todavia: falta el diff main vs reorganizacion y main vs respaldo-cableado-2026-10-25",
      "Falta evidencia runtime de que cada conexion funcionaba (logs/trazas), no solo el codigo que la declara"
    ]
  },
  "log": [
    "[N1_xray][xray][lectura guia 18 secciones + raiz main + 9 ramas + cableado.manifest.json + LOOP-wachdog-cola.json][3 cortes concretos][RESEARCH_PASS]",
    "[N2_research][research_20_sources][2 busquedas propias en vivo: git-archaeology/recovery + catalogo de conectividad][ok][RESEARCH_PASS]"
  ],
  "flags": [],
  "research_cache": [
    {
      "keywords": ["git history archaeology recover lost connections", "central connectivity registry yaml healthchecks"],
      "date": "2026-11-03",
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
    }
  ],
  "progress_pct": 12
}
```

## ESTADO REAL AUDITADO (2026-11-03)

### Ramas del repositorio (9) y su rol
| Rama | Raiz | Rol |
|---|---|---|
| `main` | `.claude/ .github/ chat-router/ dsla/ pruebas Nvidia groq/ router-mvp/ memory_agente_minimax_02.md` | actual; **sin** raiz del router |
| `reorganizacion` | `router/ raiz_router/ raiz_fichas_prompt/ fichas/ plugins/ componentes/ docs/ Skills/ chat-router/` | **organizacion objetivo ya existe aqui** |
| `respaldo-cableado-2026-10-25` | `+ chat/ Prueba/ router/ plugins/ fichas/ raiz_*/` | cableado que funcionaba (1134 commits detras de main) |
| `devin/1792939533-loop-cableado` | `+ router-componentes/ chat router/` | variante con loop cableado |
| `respaldo-main-antes-reversion-swen-20261103` | igual que main | backup |
| `banco-claves`, `fix/hydrate-vault-vacio`, `ccr-c57a3ec7-9q2ixl` | - | auxiliares |

### Los 3 cortes de cableado detectados (con evidencia)
1. **Corte 1 — harness del LOOP no resuelve en main.**
   `chat-router/chat/frontend/LOOP-wachdog-cola.json` declara `harness: "/plugins/loop_wachdog/call/paso"`.
   En main no existe `plugins/` en la raiz; en `chat-router/plugins/` existen `nct_loop` y `watchdog48`, no `loop_wachdog`.
2. **Corte 2 — 4 plugins sin destino.**
   `chat-router/cableado.manifest.json` deja `connectivity`, `hf_compute`, `hf_storage`, `lifeguard` con
   `"destino": ""` y `"enlace": false`; en `chat-router/plugins/` aparecen como entradas sin contenido.
3. **Corte 3 — la raiz del router no esta en main.**
   `router/ raiz_router/ raiz_fichas_prompt/ fichas/` existen dentro de `router-mvp/` en main, y en la raiz
   solo en `reorganizacion` y `respaldo-cableado-2026-10-25`.

### Topologia a registrar (segun la guia del usuario)
`router (edificio) -> fichas / prompt / motores -> HTTP -> plugins -> harness deepseek -> chat -> resto`

### Restricciones vigentes
- No declarar una conexion `active` sin healthcheck. Evidencia de hoy: el Router RIU sirve `lfm2.5-350m`
  cuando se le pide `qwen3.8-max` -> **declarado != real** (regla central de la guia).
- Motores de descarga/extraccion intocables: solo copia, nunca edicion.
- No crear los ~22 directorios de la estructura de referencia vacios (la guia lo prohibe explicitamente).
- No restaurar commits completos: solo los cambios necesarios.
- Fuera de `root_protection.allowlist` cada creacion/movimiento lleva una linea de justificacion en el log.

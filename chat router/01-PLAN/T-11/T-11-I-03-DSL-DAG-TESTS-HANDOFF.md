# T-11-I — DSL/DAG + TESTS + HANDOFF DEVIN

```yaml
schema: riu.dag/v1
id: T-11-I-skill-runtime
title: "Skills → schema + adapter + registry + tests"

needs:
  - T11-D
  - T11-G

mode:
  research: false
  deterministic_control: true

input:
  source: T-11-I-00-INPUT-BLOCK-VERBATIM.md

invariants:
  - NO_WEB_RESEARCH
  - NO_INVENTED_URLS
  - SKILL_MD_IS_NOT_RUNTIME
  - NO_SKILL_EXECUTION_WITHOUT_SCHEMA
  - NO_SKILL_EXECUTION_WITHOUT_ADAPTER
  - NO_SKILL_EXECUTION_WITHOUT_SHERIFF
  - NO_SKILL_EXECUTION_WITHOUT_TEST
  - NO_AUTO_INSTALL_FROM_DISCOVERY
  - NO_SELF_PASS
  - ONE_PROJECT_ONE_MEMORY_SCOPE

skills:
  - {id: ecc, target_status: ADAPTER_READY}
  - {id: agent-skills, target_status: PENDING_VERIFICATION}
  - {id: task-observer, target_status: ADAPTER_READY}
  - {id: local-ultra-review, target_status: ADAPTER_READY}
  - {id: ultrareview-claude-code, target_status: PENDING_VERIFICATION}
  - {id: claude-mem, target_status: ADAPTER_READY}
  - {id: gsd, target_status: ADAPTER_READY}
  - {id: superpowers, target_status: ADAPTER_READY}
  - {id: find-skills, target_status: ADAPTER_READY}

nodes:

  - id: T11-I-01
    action: CREATE_SKILL_SCHEMA
    steps:
      - create yaiwes.skill-runtime/v1
      - create validator
      - create negative tests
    acceptance:
      - invalid schema fails closed

  - id: T11-I-02
    action: CREATE_SKILL_REGISTRY
    needs: [T11-I-01]
    acceptance:
      - documentation_only cannot execute
      - duplicate id rejected

  - id: T11-I-03
    action: CREATE_SHERIFF_GATE
    needs: [T11-I-02]
    checks:
      - tools_allowed
      - write_scope
      - side_effects
      - project_id
    acceptance:
      - undeclared permission rejected

  - id: T11-I-04
    action: COMPILE_SUPPLIED_SKILLS
    needs: [T11-I-03]
    foreach:
      - ecc
      - task-observer
      - local-ultra-review
      - claude-mem
      - gsd
      - superpowers
      - find-skills
    steps:
      - create contract
      - create schema
      - create adapter skeleton
      - create tests
      - register
    acceptance:
      - each has contract + adapter + tests

  - id: T11-I-05
    action: RECORD_PENDING_WITHOUT_INVENTION
    needs: [T11-I-03]
    foreach:
      - agent-skills
      - ultrareview-claude-code
    acceptance:
      - execution disabled
      - no URL invented

  - id: T11-I-06
    action: INSTALLER_GATE
    needs: [T11-I-04]
    steps:
      - discovery
      - isolated inspect
      - contract
      - sandbox install
      - tests
      - promote
    acceptance:
      - discovery never equals installation

  - id: T11-I-07
    action: PROJECT_ISOLATION
    needs: [T11-I-04]
    checks:
      - project_id
      - memory_scope
      - write_scope
    acceptance:
      - cross-project write denied

  - id: T11-I-08
    action: VERIFY_AND_HANDOFF
    needs:
      - T11-I-04
      - T11-I-05
      - T11-I-06
      - T11-I-07
    acceptance:
      - executable candidates have test evidence
      - pending skills remain disabled
```

## Estructura lógica

```text
03 Agente/
└── skills-runtime/
    ├── schema/
    ├── registry/
    ├── runtime/
    │   ├── registry.py
    │   ├── validator.py
    │   ├── sheriff.py
    │   └── executor.py
    ├── ecc/
    ├── task-observer/
    ├── local-ultra-review/
    ├── claude-mem/
    ├── gsd/
    ├── superpowers/
    ├── find-skills/
    └── pending/
        ├── agent-skills.yaml
        └── ultrareview-claude-code.yaml
```

La ruta física final debe mapearse contra el árbol real antes de mover nada.

## Tests obligatorios

```text
TEST-01 schema sin id → FAIL_CLOSED
TEST-02 DOCUMENTATION_ONLY → REJECT
TEST-03 PENDING_VERIFICATION → REJECT
TEST-04 tool no declarado → SHERIFF_DENY
TEST-05 write fuera de scope → SHERIFF_DENY
TEST-06 Find Skills descubre → install=false
TEST-07 Task Observer propone → REQUIRES_REVIEW
TEST-08 Claude-Mem cruza project_id → DENY
TEST-09 Local Ultra Review duplica finding → dedup
TEST-10 GSD genera plan → PLANNED, no PASS
TEST-11 Superpowers sin verify → NEED_VERIFICATION
TEST-12 ECC sub-skill no registrada → REJECT
```

## HANDOFF PARA DEVIN

```text
ID: T-11-I

MISIÓN:
Convertir las skills suministradas por el Director en contratos
ejecutables y controlables por YAIWES.

NO INVESTIGAR INTERNET EN ESTA TAREA.

1. Leer T-11-I-00-INPUT-BLOCK-VERBATIM.md.
2. No modificar el texto original.
3. Implementar yaiwes.skill-runtime/v1.
4. Implementar validator fail-closed.
5. Implementar SkillRegistry.
6. Implementar Sheriff gate para tools, paths, side effects y project_id.
7. Crear contrato ECC.
8. Crear contrato Task Observer.
9. Crear contrato Local Ultra Review.
10. Registrar UltraReview Claude Code como PENDING_VERIFICATION.
11. Crear contrato Claude-Mem.
12. Crear contrato GSD.
13. Crear contrato Superpowers.
14. Crear contrato Find Skills.
15. Registrar Agent Skills como PENDING_VERIFICATION; NO inventar URL.
16. Crear adapter skeleton para cada skill con información suficiente.
17. No marcar EXECUTABLE hasta tener test real.
18. Find Skills solo descubre; nunca instala automáticamente.
19. Todo skill nuevo pasa:
    SOURCE → CONTRACT → SCHEMA → SANDBOX → ADAPTER → TEST → REGISTRY.
20. Toda ejecución pasa:
    REGISTRY → SHERIFF → ADAPTER → EVIDENCE → JUDGE.
21. Ningún skill puede auto-PASS.
22. Ningún skill puede ampliar sus propios permisos.
23. Ningún skill puede cruzar project_id.
24. Guardar evidencia por skill.
25. Actualizar BITACORA + STATE + HANDOFF.
```

## PASS GLOBAL

```text
SCHEMA_VALID
+ REGISTRY_VALID
+ SHERIFF_VALID
+ 7 SKILLS COMPILED
+ 2 PENDING SKILLS DISABLED
+ 12 TESTS PASS
+ NO INVENTED URL
+ NO WEB RESEARCH
= T-11-I PASS
```

Estado esperado:

```yaml
ecc: ADAPTER_READY
agent-skills: PENDING_VERIFICATION
task-observer: ADAPTER_READY
local-ultra-review: ADAPTER_READY
ultrareview-claude-code: PENDING_VERIFICATION
claude-mem: ADAPTER_READY
gsd: ADAPTER_READY
superpowers: ADAPTER_READY
find-skills: ADAPTER_READY
```

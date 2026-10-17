# T-11-I — SKILLS DEL DIRECTOR CONVERTIDOS A SCHEMA

> Basado únicamente en la información aportada por el Director.
> No se verificaron repositorios externos en esta Salida 3.

## SKILL-01 — ECC

URL:
https://github.com/affaan-m/ECC

Skills:
https://github.com/affaan-m/ECC/tree/main/skills

```yaml
schema: yaiwes.skill-runtime/v1
id: ecc
name: ECC
source:
  type: github
  url: https://github.com/affaan-m/ECC
  verified: false
classification:
  kind: collection
  executable_mode: workflow
capabilities:
  - specialized_agents
  - reusable_skills
  - rules
  - hooks
  - memory
  - continuous_learning
  - verification
  - security
  - workflows
tools_allowed:
  - ecc_adapter
permissions:
  read_paths: [skills/ecc/]
  write_paths: [runtime/skills/ecc/]
forbidden:
  - bypass_sheriff
  - auto_import_all_skills
  - execute_unvalidated_hook
adapter:
  language: python
  entrypoint: runtime/skills/ecc/adapter.py
  callable: run
status: SCHEMA_READY
```

Código:

```python
def run(invocation, ecc_manifest):
    selected = select_declared_capability(
        invocation.input,
        ecc_manifest
    )
    return execute_registered_skill(selected, invocation)
```

Flujo:

```text
ECC → INVENTORY → EACH SKILL CONTRACT → REGISTRY → SELECT → EXECUTE
```

---

## SKILL-02 — Agent Skills

URL no suministrada en esta salida.

```yaml
schema: yaiwes.skill-runtime/v1
id: agent-skills
name: Agent Skills
source:
  type: unknown
  url: null
  verified: false
classification:
  kind: unknown
  executable_mode: documentation_only
status: PENDING_VERIFICATION
```

No inventar URL ni capacidades.

---

## SKILL-03 — Task Observer / One Skill to Rule Them All

URL:
https://github.com/rebelytics/one-skill-to-rule-them-all

```yaml
schema: yaiwes.skill-runtime/v1
id: task-observer
name: One Skill to Rule Them All
source:
  type: github
  url: https://github.com/rebelytics/one-skill-to-rule-them-all
  verified: false
classification:
  kind: meta_skill
  executable_mode: adapter
inputs:
  required: [task_events, corrections, outcomes]
outputs:
  required: [patterns, learning_candidates, skill_candidates]
side_effects:
  filesystem: write
  memory: true
permissions:
  read_paths: [state/, tasks/, evidence/]
  write_paths: [memory/skill-learning/, proposals/skills/]
forbidden:
  - auto_activate_generated_skill
  - self_modify_runtime
  - bypass_review
status: SCHEMA_READY
```

Código:

```python
def run(invocation):
    candidates = detect_repeated_patterns(
        events=invocation.input["task_events"],
        corrections=invocation.input["corrections"],
        outcomes=invocation.input["outcomes"],
    )
    return {
        "patterns": candidates.patterns,
        "learning_candidates": candidates.learning,
        "skill_candidates": candidates.skills,
        "activation": "REQUIRES_REVIEW",
    }
```

---

## SKILL-04 — Local Ultra Review

URL:
https://github.com/cogine-ai/local-ultra-review

```yaml
schema: yaiwes.skill-runtime/v1
id: local-ultra-review
name: Local Ultra Review
source:
  type: github
  url: https://github.com/cogine-ai/local-ultra-review
  verified: false
classification:
  kind: review
  executable_mode: workflow
inputs:
  required: [target, diff_or_files, acceptance]
outputs:
  required: [findings, verified_findings, deduplicated_findings]
capabilities:
  - multi_reviewer
  - verification
  - deduplication
forbidden:
  - direct_merge
  - self_pass
status: SCHEMA_READY
```

Código:

```python
async def run(invocation):
    reviews = await fanout_reviewers(invocation.input)
    verified = await verify_findings(reviews)
    final = deduplicate_findings(verified)
    return {
        "findings": reviews,
        "verified_findings": verified,
        "deduplicated_findings": final,
    }
```

---

## SKILL-05 — UltraReview — Claude Code

Referencia:
https://code.claude.com/docs/

```yaml
schema: yaiwes.skill-runtime/v1
id: ultrareview-claude-code
name: UltraReview Claude Code
source:
  type: documentation
  url: https://code.claude.com/docs/
  verified: false
classification:
  kind: review
  executable_mode: documentation_only
capabilities:
  - multi_agent_review
status: PENDING_VERIFICATION
```

No modelarlo como modelo descargable.
No crear adapter real sin verificar el mecanismo concreto.

---

## SKILL-06 — Claude-Mem

URL:
https://github.com/thedotmack/claude-mem

```yaml
schema: yaiwes.skill-runtime/v1
id: claude-mem
name: Claude-Mem
source:
  type: github
  url: https://github.com/thedotmack/claude-mem
  verified: false
classification:
  kind: memory
  executable_mode: adapter
inputs:
  required: [session_events]
outputs:
  required: [stored_memory_refs, retrieved_context]
side_effects:
  filesystem: write
  memory: true
permissions:
  read_paths: [sessions/]
  write_paths: [memory/]
forbidden:
  - cross_project_memory_write
status: SCHEMA_READY
```

Código:

```python
def run(invocation):
    project_id = invocation.project_id
    events = invocation.input["session_events"]
    compressed = compress_events(events)

    refs = memory_store(
        project_id=project_id,
        payload=compressed,
    )

    context = memory_retrieve(
        project_id=project_id,
        query=invocation.input.get("query"),
    )

    return {
        "stored_memory_refs": refs,
        "retrieved_context": context,
    }
```

---

## SKILL-07 — GSD / Get Shit Done

URL:
https://github.com/gsd-build/get-shit-done

```yaml
schema: yaiwes.skill-runtime/v1
id: gsd
name: Get Shit Done
source:
  type: github
  url: https://github.com/gsd-build/get-shit-done
  verified: false
classification:
  kind: planning
  executable_mode: workflow
inputs:
  required: [project, objective]
outputs:
  required: [roadmap, phases, tasks, verification_plan, progress_state]
forbidden:
  - execute_without_task_contract
  - self_finalize
status: SCHEMA_READY
```

Código:

```python
def run(invocation):
    roadmap = build_roadmap(
        project=invocation.input["project"],
        objective=invocation.input["objective"],
    )
    phases = compile_phases(roadmap)
    tasks = compile_tasks(phases)

    return {
        "roadmap": roadmap,
        "phases": phases,
        "tasks": tasks,
        "verification_plan": build_verification(tasks),
        "progress_state": "PLANNED",
    }
```

---

## SKILL-08 — Superpowers

URL:
https://github.com/obra/superpowers

```yaml
schema: yaiwes.skill-runtime/v1
id: superpowers
name: Superpowers
source:
  type: github
  url: https://github.com/obra/superpowers
  verified: false
classification:
  kind: methodology
  executable_mode: workflow
inputs:
  required: [objective, constraints]
outputs:
  required: [design, plan, tests, review, verification]
forbidden:
  - skip_tests
  - self_pass
  - uncontrolled_subagent_spawn
status: SCHEMA_READY
```

Código:

```python
def run(invocation):
    design = design_stage(invocation.input)
    plan = plan_stage(design)
    tests = create_tests(plan)
    execution = execute_with_registered_workers(plan=plan, tests=tests)
    review = review_stage(execution)
    verification = verify_stage(execution, review)

    return {
        "design": design,
        "plan": plan,
        "tests": tests,
        "review": review,
        "verification": verification,
    }
```

---

## SKILL-09 — Find Skills

URL:
https://github.com/axxt0/find-skills

```yaml
schema: yaiwes.skill-runtime/v1
id: find-skills
name: Find Skills
source:
  type: github
  url: https://github.com/axxt0/find-skills
  verified: false
classification:
  kind: discovery
  executable_mode: adapter
inputs:
  required: [capability_query]
outputs:
  required: [candidates]
side_effects:
  filesystem: none
  network: true
forbidden:
  - auto_install
  - auto_enable
  - bypass_installer_sandbox
status: SCHEMA_READY
```

Código:

```python
def run(invocation):
    candidates = discover_skills(
        invocation.input["capability_query"]
    )

    return {
        "candidates": normalize_candidates(candidates),
        "install": False,
        "next_gate": "INSTALLER_SANDBOX",
    }
```

Flujo:

```text
FIND → CANDIDATES → INSPECT → CONTRACT → SANDBOX INSTALL → TEST → PROMOTE
```

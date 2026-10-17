---
name: ui-yaiwes-execution
description: Ejecuta UI YAIWES desde referencias hasta código modular verificado con Schema/Contract/Sheriff/Verifier/Sentinel/Guardian.
---

# UI YAIWES execution skill

Pipeline:
`ReferenceReader -> SkillResolver -> TaskSchema -> Contract -> Sheriff -> Codex -> BrowserVerifier -> MobileQA -> InteractionQA -> MetaReview(if available) -> Sentinel -> Guardian`.

Cada skill produce:
```text
SkillInvocation
id
source_path
scope
required_inputs
allowed_actions
forbidden_actions
expected_outputs
dependencies
acceptance
evidence
```

Schema valida estructura. Contract liga skill+tarea. Sheriff limita scope. Validator valida manifests. Verifier prueba runtime. Sentinel audita evidencia externa. Guardian cierra.

Fail-closed: skill inexistente, dependencia ausente, source no leído o actionId no registrado => BLOCKED.

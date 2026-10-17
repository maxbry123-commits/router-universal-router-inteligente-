# Plan de acción — Skills UI YAIWES

Fecha: 2026-09-27  
Fuente canónica: `HANDOFF-SKILLS-UI-YAIWES-2026-09-27.md`.

## Objetivo

Usar skills como una capa gobernada del proyecto, no como archivos pasivos ni instrucciones globales de donors.

## Fases

### S0 — Inventario — PASS
- 10 `SKILL.md` físicos verificados en `UI YAIWES interface/`.
- catálogo de fábrica tomado del índice entregado por el Director.
- no se reescanea fábrica en esta actualización.

### S1 — Resolver
Crear/usar `SkillResolver`:

```text
task
→ product policy
→ surface skill
→ build skill
→ QA/a11y skill
→ donor adapter si aplica
→ fail_closed
```

### S2 — Core frontend
Prioridad operativa:
1. FROMTED architecture.
2. frontend-design.
3. Image-to-Code.
4. Impeccable.
5. frontend-audit-skill.
6. accessibility-skills.
7. skill-creator.

### S3 — QA
- Playwright.
- screenshot/visual audit.
- keyboard/touch.
- a11y.
- console/runtime.
- retest.

### S4 — PANEL-01 / CHAT-01
Cadena:

`FOTOS -> Image-to-Code -> frontend-design -> BUILD -> Impeccable -> audit visual -> a11y -> Playwright -> evidence -> OK PANEL-01-CHAT`.

### S5 — Runtime/Device
- `computer-use` solo GUI real.
- `orca-emulator-android` solo Android real.
- `orca-emulator` solo iOS Simulator real.
- `orca-cli` solo Orca real.
- `orchestration` solo coordinación Orca real.
- `orca-per-workspace-env` solo receta/runtime real.

### S6 — Adapters donor
`DONOR_SCOPED -> adapter YAIWES -> test -> evidence -> approval -> ACTIVE`.

### S7 — Expansión por superficie
Después de CHAT:
- RUN;
- WALL;
- GBOT;
- resto según plan maestro.

## Gate general

`DISCOVERED/CATALOG -> SCOPE_OK -> ADAPTER_READY -> TESTED -> VERIFIED -> ACTIVE`.

Cualquier fallo: `BLOCKED`.

## Salida de cada ejecución

- skill(s);
- paths/versión;
- decisión tomada;
- componente/tool usado;
- test;
- evidencia;
- resultado.

## Cierre

No hay cierre por presencia de `SKILL.md`. Hay cierre únicamente con ejecución verificable y evidencia.

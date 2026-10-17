# HANDOFF — Skills UI YAIWES + Fábrica UI

Fecha: 2026-09-27  
Estado: `ACTIVE / INVENTORY COMPLETE / ARCHITECTURE WIRED`  
Repo: `maxbry123-commits/frontend` · branch `main`

## 1. Alcance auditado

Raíces auditadas recursivamente:

1. `UI YAIWES interface/`
2. `fabrica de UI INTERFACE fromtend/`

Criterio: archivos físicos `SKILL.md` o `*.SKILL.md`.

Resultado:

- UI YAIWES interface: **10 SKILL físicos**.
- Fábrica UI: **28 SKILL físicos**.
- Total físico: **38**.
- Alias/duplicados declarativos:
  - `linear-tickets` es nombre legacy de `orca-linear`.
  - 11 `.claude/skills/*/SKILL.md` de Fluent UI apuntan a sus equivalentes `.agents/skills/*/SKILL.md`.
- Capacidades canónicas operativas después de normalizar alias: **26**.

## 2. Skills canónicos — UI YAIWES interface

| # | Skill | Función | Ruta |
|---|---|---|---|
| 1 | diagnose-crash | Diagnóstico de crashes/core dumps con evidencia | `Backend/Motor3 approved donors/Omarchy/default/agents/skills/diagnose-crash/SKILL.md` |
| 2 | omarchy | Configuración/customización Omarchy/Hyprland/sistema | `Backend/Motor3 approved donors/Omarchy/default/agents/skills/omarchy/SKILL.md` |
| 3 | computer-use | Control GUI visible por Orca cuando CLI/API no basta | `Backend/Motor3 approved donors/Orca/skills/computer-use/SKILL.md` |
| 4 | orca-cli | Worktrees, terminales, artefactos, browser, handoff y skills Orca | `Backend/Motor3 approved donors/Orca/skills/orca-cli/SKILL.md` |
| 5 | orca-emulator-android | Control de Android/emulador con adb y evidencia | `Backend/Motor3 approved donors/Orca/skills/orca-emulator-android/SKILL.md` |
| 6 | orca-emulator | Control de iOS Simulator y evidencia | `Backend/Motor3 approved donors/Orca/skills/orca-emulator/SKILL.md` |
| 7 | orca-linear | Trabajo con tickets Linear mediante Orca CLI | `Backend/Motor3 approved donors/Orca/skills/orca-linear/SKILL.md` |
| 8 | orca-per-workspace-env | Recetas de entornos por workspace, doctor y lifecycle | `Backend/Motor3 approved donors/Orca/skills/orca-per-workspace-env/SKILL.md` |
| 9 | orchestration | Coordinación supervisada de workers, DAG, gates y loops | `Backend/Motor3 approved donors/Orca/skills/orchestration/SKILL.md` |

Alias físico adicional:
- `linear-tickets/SKILL.md` → alias legacy de `orca-linear`.

## 3. Skills canónicos — Fábrica UI

### Appsmith / Playwright

| # | Skill | Función |
|---|---|---|
| 10 | diagnose-pw-failure | Distinguir fallo de producto vs fallo de test Playwright; generar diagnóstico |
| 11 | fix-pw-spec | Corregir selectors, waits, assertions y errores del spec |
| 12 | write-and-verify-pw-test | Escribir E2E Playwright, ejecutarlo y auto-corregir hasta verificación |

### Budibase

| # | Skill | Función |
|---|---|---|
| 13 | budibase-setup-run | Preparar, arrancar y diagnosticar el monorepo Budibase |

### Fluent UI

| # | Skill | Función |
|---|---|---|
| 14 | assign-prs | Asignación de reviewers con dry-run y aprobación |
| 15 | change | Crear change file Beachball según diff |
| 16 | dependabot-rollup | Consolidar updates Dependabot compatibles con dry-run |
| 17 | headless-component | Crear/extender primitives headless Fluent UI v9 |
| 18 | lint-check | Lint de paquetes afectados y autofix de problemas comunes |
| 19 | package-info | Resolver paquete, ownership, dependencias y metadatos |
| 20 | release-recovery | Diagnosticar/reparar release publicado pero no sincronizado al repo |
| 21 | review-pr | Revisar PR: corrección, patrones, tests, accesibilidad y seguridad |
| 22 | token-lookup | Mapear CSS hardcoded a design token Fluent UI |
| 23 | triage-issues | Triage de issues según reglas del proyecto |
| 24 | v9-component | Scaffold completo de componente Fluent UI v9 |
| 25 | visual-test | Storybook + captura Playwright para verificación visual |
| 26 | verify-v8-v9-migration-docs | Auditar/generar/verificar documentación de migración v8→v9 |

Alias físicos:
- `Fluent-UI/.claude/skills/*` referencia a `Fluent-UI/.agents/skills/*` para 11 skills.
- No duplicar ejecución ni registry por esos alias.

## 4. Cableado canónico

```text
TASK / INPUT
   ↓
SkillRegistry
   ↓
SkillResolver
   ↓
categoría
   ├─ DESIGN/COMPONENT → headless-component / v9-component / token-lookup
   ├─ QA/E2E           → write-and-verify-pw-test / fix-pw-spec / diagnose-pw-failure / visual-test
   ├─ QUALITY          → lint-check / review-pr
   ├─ RUNTIME/SETUP    → budibase-setup-run / orca-per-workspace-env
   ├─ GUI/DEVICE       → computer-use / orca-emulator / orca-emulator-android
   ├─ ORCHESTRATION    → orchestration / orca-cli
   ├─ INCIDENT         → diagnose-crash / release-recovery
   └─ PROJECT OPS      → package-info / change / triage-issues / assign-prs / orca-linear
   ↓
Skill adapter
   ↓
Agent / Workflow
   ↓
evidence + result
```

Reglas:

1. Registry guarda **ruta canónica**, origen y aliases.
2. Alias nunca crea una segunda capacidad.
3. Un skill donor no se ejecuta automáticamente solo por existir.
4. Antes de ejecución: validar runtime/dependencias/herramientas permitidas.
5. UI consume capacidades por registry; no hardcodea rutas donor.
6. Todo skill que modifique código entra al mismo gate de QA de la fábrica.
7. Para frontend visual: `visual-test` + Playwright forman el gate mínimo de evidencia.
8. Para móvil: Android/iOS emulator se usan solo cuando la pieza requiera dispositivo real/simulado.
9. `computer-use` es fallback; primero CLI/API/programmatic path.
10. Skills de PR/release/Dependabot requieren sus aprobaciones declaradas por el propio skill.

## 5. Perfil recomendado para UI YAIWES

### Perfil DESIGN
`token-lookup -> headless-component|v9-component -> lint-check -> visual-test`

### Perfil FRONTEND-FUNCTIONAL
`write-and-verify-pw-test -> fix-pw-spec -> diagnose-pw-failure`

### Perfil QA
`lint-check -> visual-test -> review-pr -> Playwright acceptance`

### Perfil MOBILE
`orca-emulator-android | orca-emulator -> screenshot/evidence -> acceptance`

### Perfil ORCHESTRATION
`orchestration -> orca-cli -> worker result -> QA gate`

### Perfil INCIDENT
`diagnose-crash -> evidence -> root cause -> recovery`

## 6. Plan de acción

### P0 — Inventario — PASS
- localizar SKILL físicos en ambas raíces;
- separar canónicos de alias;
- registrar 38 físicos / 26 canónicos.

### P1 — Registry — PASS documental
- crear `SKILLS-REGISTRY-UI-YAIWES.json`;
- rutas canónicas + aliases + categorías.

### P2 — Arquitectura — PASS documental
- conectar SkillRegistry/SkillResolver a arquitectura frontend;
- impedir hardcode de donor paths desde componentes UI.

### P3 — Fábrica — NEXT
- crear adapter común de skill;
- validar dependencias y herramientas permitidas;
- exponer capacidad a agentes/workflows por ID canónico.

### P4 — QA frontend — NEXT
- conectar Playwright triad:
  `write-and-verify -> fix-spec -> diagnose-product-failure`;
- conectar `visual-test`;
- cerrar con `lint-check`.

### P5 — Component factory — NEXT
- usar `token-lookup` para tokens;
- `headless-component` para primitives;
- `v9-component` solo cuando Fluent UI sea el donor elegido.

### P6 — Device QA — NEXT
- Android → `orca-emulator-android`;
- iOS → `orca-emulator`;
- evidence screenshot + interaction test.

### P7 — Orchestration — NEXT
- `orchestration` para DAG/gates/workers;
- `orca-cli` para worktree/handoff/artifacts;
- no sustituir Action Bus/StateStore/WindowRegistry del producto.

### P8 — Acceptance
PASS solo si:
- skill resuelto a ID canónico;
- dependencias verificadas;
- alias no duplica ejecución;
- evidencia generada;
- test aplicable ejecutado;
- resultado registrado en handoff/bitácora.

## 7. Frontera

Este handoff **cablea skills en arquitectura y plan**, no declara instalados runtimes externos que el repo no pruebe en ejecución.

El skill padre `Skills arquitectura frontend Yaiwes/` está fuera de las dos raíces auditadas y sigue siendo autoridad de diseño general; no se contabiliza dentro de los 38 físicos de este inventario.

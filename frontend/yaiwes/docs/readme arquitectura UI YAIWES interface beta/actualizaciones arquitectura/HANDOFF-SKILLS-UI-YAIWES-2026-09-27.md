# HANDOFF — Skills UI YAIWES + Fábrica UI

Fecha: 2026-09-27  
Estado: `ARCHITECTURE_WIRED / RUNTIME_ADAPTERS_PENDING`  
Canónico: **este archivo**.

## 1. Alcance y fuentes

Este handoff une dos fuentes sin mezclarlas:

### A. UI YAIWES interface — auditoría física verificada

Raíz: `UI YAIWES interface/`.

Resultado: **10 archivos SKILL.md reales**.

### B. Fábrica UI — índice entregado por el Director

Fuente: índice de fábrica entregado en el chat el 2026-09-27.

En esta actualización **no se reescanea la fábrica**. Se conserva literalmente su clasificación de catálogo/estado y se incorpora al plan.

Regla:
`VERIFICADO_FÍSICO != CATÁLOGO != ACTIVO`.

## 2. Skills físicos verificados en UI YAIWES interface

| # | Skill | Ruta | Función para YAIWES | Estado |
|---|---|---|---|---|
| 1 | diagnose-crash | `Backend/Motor3 approved donors/Omarchy/default/agents/skills/diagnose-crash/SKILL.md` | diagnóstico de crash basado en evidencia | DONOR_SCOPED |
| 2 | omarchy | `Backend/Motor3 approved donors/Omarchy/default/agents/skills/omarchy/SKILL.md` | configuración desktop/Hyprland/Omarchy | DONOR_SCOPED |
| 3 | computer-use | `Backend/Motor3 approved donors/Orca/skills/computer-use/SKILL.md` | control GUI visible cuando CLI/API no alcanza | DONOR_SCOPED |
| 4 | linear-tickets | `Backend/Motor3 approved donors/Orca/skills/linear-tickets/SKILL.md` | alias legacy de orca-linear | ALIAS_DONOR_SCOPED |
| 5 | orca-cli | `Backend/Motor3 approved donors/Orca/skills/orca-cli/SKILL.md` | worktrees, browser, artifacts, handoff Orca | DONOR_SCOPED |
| 6 | orca-emulator-android | `Backend/Motor3 approved donors/Orca/skills/orca-emulator-android/SKILL.md` | QA Android/ADB | DONOR_SCOPED |
| 7 | orca-emulator | `Backend/Motor3 approved donors/Orca/skills/orca-emulator/SKILL.md` | QA iOS Simulator | DONOR_SCOPED |
| 8 | orca-linear | `Backend/Motor3 approved donors/Orca/skills/orca-linear/SKILL.md` | tickets Linear | DONOR_SCOPED |
| 9 | orca-per-workspace-env | `Backend/Motor3 approved donors/Orca/skills/orca-per-workspace-env/SKILL.md` | entornos desechables por workspace | DONOR_SCOPED |
| 10 | orchestration | `Backend/Motor3 approved donors/Orca/skills/orchestration/SKILL.md` | coordinación DAG/multiagente supervisada | DONOR_SCOPED |

### Regla de estos 10

Son skills de donor. No pasan a ser reglas globales de UI YAIWES por estar presentes.

`DONOR_SCOPED -> SCOPE_OK -> ADAPTER_READY -> TESTED -> VERIFIED -> ACTIVE`

Si no existe runtime/dependencia real: `BLOCKED`.

## 3. Skills de Fábrica incorporados desde el índice del Director

### K. Skills Fábrica

1. `frontend-design` — identidad, tipo, layout e intención visual. Estado del índice: `S`.
2. `Impeccable` — audit/polish/a11y/perf/motion. Estado: `S`, wire pendiente según índice.
3. `skill-creator` — crear/evaluar nuevos `SKILL.md`. Estado: `S`.
4. `manim-skill` — animación/video. Estado: `Z*`.
5. `skill-canvas-video` — canvas -> video. Estado: `Z*`, wire pendiente.
6. `chat-animation` — animación de chat. Estado: `Z*`, wire pendiente.
7. `taste-skill` — taste/brand visual. Estado: `Z*`, wire pendiente.

Nota del índice: `Z*` = documentado en arquitectura pero ausente del listing actual de la raíz en ese corte.

### R. Skills extra del índice

8. `anthropic-skills` — pack Agent Skills Anthropic.
9. `microsoft-skills` — skills + MCP.
10. `nolly-agent-skills` — bootstrap AGENTS.md.
11. `PracticalSwan-agent-skills` — skills multi-agent.
12. `ui-ux-pro-max-skill` — reglas UI multiplataforma.
13. `wordpress-agent-skills` — generación de temas WordPress.
14. `frontend-audit-skill` — comparación PNG vs render.
15. `accessibility-skills` — WCAG/ARIA.
16. `Taste` — pack de brand/taste.

### Packs de diseño/skills relacionados que el mismo índice conecta

- `Image-to-Code`.
- `Web-Design-Studio`.
- `Web-Design-Guidelines`.
- `Awesome-Design`.
- `HyperFrames`.
- `Grok Build`.
- `Taste-Brandkit`, `Taste-Brutalist`, `Taste-GPT`, `Taste-Minimalist`, `Taste-Output`, `Taste-Redesign`, `Taste-Skill-v1`, `Taste-Soft`, `Taste-Stitch`.
- `Anthropic-Frontend-Design`.

Estos elementos quedan como `CATALOG_SOURCE_DIRECTOR` hasta resolver path físico/adapter cuando una tarea los necesite.

## 4. SkillResolver — cableado del proyecto

```text
TASK
  ↓
SkillResolver
  ↓
FROMTED / arquitectura de producto
  ↓
┌─ DISEÑO: frontend-design + Image-to-Code
├─ BUILD: skill de superficie / builder
├─ POLISH: Impeccable + Taste cuando esté disponible
├─ QA VISUAL: frontend-audit-skill + visual checks
├─ A11Y: accessibility-skills
├─ DEVICE: orca-emulator / orca-emulator-android
├─ GUI FALLBACK: computer-use
├─ ORCHESTRATION: orchestration + orca-cli
└─ CREATE/ADAPT: skill-creator
  ↓
Tool / Component / Action Bus
  ↓
Browser / Device / Repo
  ↓
Evidence
  ↓
PASS / FAIL / BLOCKED
```

## 5. Aplicación directa al proyecto UI YAIWES

### PANEL-01 / CHAT-01

```text
FOTOS-REF
→ Image-to-Code
→ frontend-design
→ código modular
→ Impeccable
→ frontend-audit-skill
→ accessibility-skills
→ Playwright/QA
→ evidence
→ OK PANEL-01-CHAT
```

Orca solo entra si existe el runtime real:

- desktop GUI: `computer-use`;
- Android: `orca-emulator-android`;
- iOS: `orca-emulator`;
- worktree/handoff: `orca-cli`;
- coordinación DAG: `orchestration`;
- entorno aislado: `orca-per-workspace-env`.

## 6. Política de prioridad

1. requisito explícito del Director;
2. arquitectura UI YAIWES/FROMTED;
3. skill específico de la superficie;
4. skill de build;
5. skill QA/a11y;
6. donor adapter solo si scope y runtime coinciden;
7. fail-closed.

Un donor skill nunca puede reemplazar tokens, arquitectura, Action Bus, WindowRegistry, StateStore o reglas de producto.

## 7. Estados del registry

- `VERIFIED_PHYSICAL`
- `CATALOG_SOURCE_DIRECTOR`
- `FACTORY_PRIMARY`
- `REFERENCE`
- `DONOR_SCOPED`
- `ALIAS`
- `STAGED`
- `ADAPTER_READY`
- `TESTED`
- `VERIFIED`
- `ACTIVE`
- `BLOCKED`

## 8. Plan de acción

### S0 — Inventario
PASS:
- 10 SKILL.md físicos de UI YAIWES verificados.
- catálogo de fábrica incorporado desde índice Director.

### S1 — Registry
- registrar path, origen, estado, categoría y dependencia;
- aliases/mirrors apuntan a una sola familia;
- entradas de catálogo sin path físico quedan `CATALOG_SOURCE_DIRECTOR`.

### S2 — Core frontend
Prioridad:
1. arquitectura FROMTED;
2. frontend-design;
3. Image-to-Code;
4. Impeccable;
5. frontend-audit-skill;
6. accessibility-skills;
7. skill-creator.

### S3 — QA
`BUILD -> PLAYWRIGHT -> SCREENSHOT -> VISUAL AUDIT -> A11Y -> FIX -> RETEST`.

### S4 — Device
Orca Android/iOS/GUI solo cuando runtime real exista.

### S5 — Donor adapters
`READ DONOR -> EXTRACT GENERIC BEHAVIOR -> CREATE ADAPTER -> TEST -> APPROVE -> ACTIVE`.

### S6 — Superficies
Primero `PANEL-01-CHAT`; luego RUN/WALL/GBOT según plan maestro.

### S7 — Handoff/evidencia
Cada ejecución registra:
- skill elegido;
- path/version;
- razón;
- input;
- output;
- tests;
- evidencia;
- PASS/FAIL/BLOCKED.

## 9. Definition of Done

No se considera “skills cableados” solo porque el archivo exista.

PASS requiere:

- resolver por ID/path;
- scope correcto;
- runtime/dependencias disponibles;
- adapter cuando sea donor;
- test aplicable;
- evidencia;
- registro en handoff;
- no alterar reglas de producto;
- fail-closed ante ausencia o contradicción.

## 10. Próximo paso técnico

`PANEL-01-CHAT -> resolver skill chain -> build -> QA -> evidence -> review`.

No activar en masa los skills del catálogo.

## 11. Skills nativos del proyecto

Se añaden en `UI YAIWES interface/skills/`:
1. reference-reader
2. design-system
3. frontend-implementation
4. browser-verification
5. mobile-qa
6. interaction-qa

Cadena: `reference-reader -> design-system -> frontend-implementation -> browser-verification -> mobile-qa -> interaction-qa`.

Gobierno: Contract schema + Sheriff policy. No sustituyen los donors existentes.


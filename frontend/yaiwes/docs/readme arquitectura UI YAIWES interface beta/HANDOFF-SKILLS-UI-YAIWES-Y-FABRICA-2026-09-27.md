# HANDOFF Skills — UI YAIWES + Fábrica UI

Fecha: 2026-09-27  
Estado: `ACTIVE / INVENTORY COMPLETE / WIRING PLAN`  
Repo: `maxbry123-commits/frontend`  
Branch: `main`

## Objetivo

Inventariar y cablear documentalmente los skills existentes en:

1. `UI YAIWES interface/`
2. `fabrica de UI INTERFACE fromtend/`

Regla: **no inventar skills**. Solo se registran archivos `SKILL.md` encontrados físicamente.

## Conteo forense

- `UI YAIWES interface/`: **10 archivos SKILL.md**
- `fabrica de UI INTERFACE fromtend/`: **31 archivos SKILL.md**
- Total físico: **41 SKILL.md**
- Skills funcionales/nombres únicos consolidados: **30**
- Duplicados intencionales en Fluent UI: versiones `.agents/skills/` y `.claude/skills/` del mismo skill.

No se cuentan como skill ejecutable los archivos de documentación llamados `SKILLS.md`, changelogs o checklists que no sean `SKILL.md`.

---

## A. Skills en UI YAIWES interface — 10

### Omarchy — 2

1. `diagnose-crash`  
   Ruta: `UI YAIWES interface/Backend/Motor3 approved donors/Omarchy/default/agents/skills/diagnose-crash/SKILL.md`  
   Función declarada: diagnosticar crashes, coredumps, SIGSEGV/SIGABRT y producir diagnóstico basado en evidencia.

2. `omarchy`  
   Ruta: `UI YAIWES interface/Backend/Motor3 approved donors/Omarchy/default/agents/skills/omarchy/SKILL.md`  
   Función declarada: personalización de Omarchy/Hyprland/configuración Linux de usuario.

### Orca — 8

3. `computer-use`  
   Control GUI visible mediante árbol de accesibilidad, clicks, teclado, menús, diálogos y screenshots.

4. `linear-tickets`  
   Alias legacy para trabajo con tickets Linear mediante Orca CLI.

5. `orca-cli`  
   Worktrees, terminales, repos, automations, artifacts, handoff, skill sharing y browser embebido de Orca.

6. `orca-emulator-android`  
   Control Android/ADB: emuladores, teléfono, taps, swipes, instalación, permisos, accessibility tree y logcat.

7. `orca-emulator`  
   Control de iOS Simulator: gestos, teclado, rotación y evidencia visual.

8. `orca-linear`  
   Flujo actual de tickets Linear mediante Orca CLI.

9. `orca-per-workspace-env`  
   Configuración y diagnóstico de entornos desechables por workspace.

10. `orchestration`  
    Coordinación de workers Orca: mensajes, dispatch, DAGs, decision gates, waits y coordinator loops.

> Nota: `linear-tickets` y `orca-linear` representan la misma capacidad funcional; el primero existe por compatibilidad legacy.

---

## B. Skills en Fábrica UI — 31 archivos físicos

### Skills canónicos propios de la fábrica — 3

1. `frontend-design`  
   Ruta: `fabrica de UI INTERFACE fromtend/skills/frontend-design/SKILL.md`  
   Diseño visual deliberado, tipografía, dirección estética y construcción de UI no genérica.

2. `impeccable`  
   Ruta: `fabrica de UI INTERFACE fromtend/skills/impeccable/SKILL.md`  
   Diseño/rediseño, auditoría, polish, accesibilidad, responsive, tokens, motion, edge cases y QA visual frontend.

3. `skill-creator`  
   Ruta: `fabrica de UI INTERFACE fromtend/skills/skill-creator/SKILL.md`  
   Crear, modificar, evaluar y optimizar skills mediante pruebas y benchmarks.

### Appsmith — Playwright — 3

4. `diagnose-pw-failure`  
   Diagnostica fallos Playwright como posible bug de producto usando error, screenshots, traces y logs.

5. `fix-pw-spec`  
   Corrige bugs del propio spec Playwright: selectores, waits, assertions y errores de test.

6. `write-and-verify-pw-test`  
   Escribe y verifica pruebas E2E Playwright, ejecuta y corrige hasta tres veces.

### Budibase — 1

7. `budibase-setup-run`  
   Setup, bootstrap, run y troubleshooting del monorepo Budibase.

### Fluent UI — nombres únicos — 13

8. `assign-prs` — asignación de reviewers con dry-run/aprobación.  
9. `change` — genera archivo Beachball de cambio.  
10. `dependabot-rollup` — consolida PRs Dependabot con aprobación previa.  
11. `headless-component` — crea/extiende primitives headless con accesibilidad, estado y tests.  
12. `lint-check` — lint y auto-fix de issues comunes.  
13. `package-info` — lookup de paquete, dependencias, owner y docs.  
14. `release-recovery` — diagnóstico/recuperación de releases desincronizadas.  
15. `review-pr` — revisión de PR: correctness, patterns, tests, a11y y safety.  
16. `token-lookup` — encuentra design token para valores CSS hardcoded.  
17. `triage-issues` — triage de issues con recommend-then-apply.  
18. `v9-component` — scaffold de componente Fluent UI v9 con tests/stories/conformance.  
19. `visual-test` — Storybook + screenshot con playwright-cli para verificación visual.  
20. `verify-v8-v9-migration-docs` — auditoría/verificación de guías de migración v8→v9.

### Copias físicas Fluent UI

En `.agents/skills/` existen 12 archivos:
- assign-prs
- change
- dependabot-rollup
- headless-component
- lint-check
- package-info
- release-recovery
- review-pr
- token-lookup
- triage-issues
- v9-component
- visual-test

En `.claude/skills/` existen 11 copias equivalentes:
- assign-prs
- change
- headless-component
- lint-check
- package-info
- release-recovery
- review-pr
- token-lookup
- triage-issues
- v9-component
- visual-test

Además:
- `.github/skills/verify-v8-v9-migration-docs/SKILL.md`

Por eso Fábrica contiene **31 archivos físicos** pero **20 nombres únicos**.

---

# Cableado canónico de skills

## Capa 1 — Diseño

`frontend-design + impeccable`

Uso:
- leer referencia;
- definir jerarquía visual;
- respetar tokens FROMTED;
- revisar responsive/a11y;
- no inventar controles fuera de fuente.

## Capa 2 — Componente

`headless-component + v9-component + token-lookup + package-info`

Uso:
- comportamiento semántico;
- componente modular;
- design tokens;
- localizar dependencias/patrón correcto.

## Capa 3 — Calidad de código

`lint-check + review-pr + change`

Uso:
- lint;
- revisión de implementación;
- cambio/versionado cuando aplique.

## Capa 4 — QA navegador

`write-and-verify-pw-test -> fix-pw-spec -> diagnose-pw-failure -> visual-test`

Orden obligatorio:
1. escribir test;
2. ejecutar;
3. si falla el spec, corregir spec;
4. si el spec ya es correcto y la UI falla, diagnosticar producto;
5. cerrar con visual-test/screenshot.

## Capa 5 — Ejecución/entornos

`budibase-setup-run + orca-per-workspace-env + orca-cli`

Solo cuando el proyecto/componente correspondiente requiera esos runtimes.

## Capa 6 — GUI/dispositivos

`computer-use + orca-emulator + orca-emulator-android`

Uso:
- pruebas donde DOM/CLI no bastan;
- iOS/Android;
- evidencia táctil/visual.

## Capa 7 — Orquestación

`orchestration + orca-cli`

Uso:
- coordinar trabajos paralelos;
- DAG de tareas;
- handoff entre agentes;
- waits/gates.

## Capa 8 — Gestión operativa auxiliar

`orca-linear / linear-tickets + assign-prs + triage-issues + dependabot-rollup + release-recovery`

No forman parte del runtime visual del producto; sirven al proceso de desarrollo/mantenimiento.

## Capa 9 — Meta-skill

`skill-creator`

Uso:
- crear un skill YAIWES específico solo si existe un gap probado;
- evaluar antes de incorporar;
- evitar duplicar capacidades ya presentes.

---

# Flujo obligatorio para frontend UI YAIWES

```text
INPUT + ARCHIVOS + FOTOS
        ↓
frontend-design
        ↓
impeccable
        ↓
headless-component / v9-component / token-lookup
        ↓
IMPLEMENTACIÓN MODULAR
        ↓
lint-check
        ↓
write-and-verify-pw-test
        ↓
fix-pw-spec  ── si falla el test
        ↓
diagnose-pw-failure ── si el test es correcto y falla producto
        ↓
visual-test
        ↓
review-pr / evidencia
        ↓
PASS / FAIL
```

Para móvil/dispositivo:

```text
build
→ orca-emulator-android / orca-emulator
→ touch/keyboard/accessibility
→ screenshot/evidencia
→ PASS
```

---

# Plan de acción

## P0 — Registro

- [x] localizar SKILL.md en ambas raíces;
- [x] separar archivos físicos de nombres únicos;
- [x] registrar duplicados/aliases;
- [x] crear este handoff.

## P1 — Registry de skills

Crear posteriormente un registry machine-readable con:

```json
{
  "id": "visual-test",
  "source": "Fluent-UI",
  "path": ".../SKILL.md",
  "stage": "qa_visual",
  "status": "available",
  "duplicateOf": null
}
```

No copiar ni mover donors todavía; primero registry.

## P2 — Política de selección

El agente debe seleccionar skills por etapa, no cargar los 30 siempre.

- diseño → frontend-design + impeccable;
- componente → headless/v9/token;
- QA → Playwright + visual-test;
- dispositivo → emulator skills;
- coordinación → orchestration;
- crear skill nuevo → skill-creator.

## P3 — PANEL-01 CHAT

Aplicar primero al chat:

`frontend-design -> impeccable -> headless-component/token-lookup -> implementación -> lint -> Playwright -> visual-test`

Luego Android/iOS cuando exista build empaquetado.

## P4 — Gates

Una pieza no cierra si:
- no leyó skills asignados;
- no tiene test;
- hay control muerto;
- falla visual/touch;
- falta evidencia;
- se creó un skill duplicado sin demostrar gap.

## P5 — Integración

El registry de skills se conecta documentalmente a:

`Arquitectura Frontend -> Plan de Trabajo -> Handoff de pieza -> Skill Registry -> agente ejecutor -> QA`

---

# Estado final del handoff

`INVENTARIO: PASS`  
`CABLEADO DOCUMENTAL: PASS`  
`REGISTRY MACHINE-READABLE: PENDIENTE`  
`COPIAR/MOVER SKILLS: NO AUTORIZADO / NO NECESARIO`  
`PRIMER CONSUMIDOR: PANEL-01 / CHAT-01`

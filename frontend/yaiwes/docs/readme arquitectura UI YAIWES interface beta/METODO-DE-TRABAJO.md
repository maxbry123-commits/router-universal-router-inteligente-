# Método de trabajo · UI YAIWES interface

Actualizado 2026-09-27 · ACTIVE / FAIL_CLOSED / EVIDENCE_FIRST.

## Propósito
Cualquier IA/modelo puede retomar el proyecto sin historial del chat.

## Lectura
`AGENTS -> EXECUTION-CONTRACT -> arquitectura -> plan -> handoff skills -> SKILL -> DESIGN_SYSTEM -> COMPONENT_INDEX -> ACCEPTANCE -> handoff frontend -> referencias`.

## Fórmula
`REFERENCE + CONTEXT + SKILLS + BROWSER + VERIFIER`.
`VER -> USAR -> COMPARAR -> CORREGIR -> VERIFICAR`.

## Staff
Director; Codex executor/improver; v0 bootstrap visual; Meta Visual Reviewer; Sheriff; Validator; Verifier; Sentinel; Guardian. Ver `TEAM-UI-YAIWES.md`.

## Skills como Schema/Contract/Sheriff
`TASK -> SkillResolver -> SkillInvocation Schema -> Task Contract -> Sheriff -> Implement -> Validator -> Verifier -> Sentinel -> Guardian`.

## DSL/DAG
- `workflow/UI-YAIWES-FRONTEND.dsl.yaml`
- `workflow/UI-YAIWES-FRONTEND-DAG.json`
- `workflow/UI-YAIWES-CONTRACT.schema.json`
- `workflow/SHERIFF-POLICY.yaml`
- `workflow/VALIDATOR-VERIFIER.md`
- `workflow/SENTINEL-WEB-AUDIT.md`
- `workflow/GUARDIAN.md`

## Mini workflow
```text
READ references
READ project files
READ skills
BUILD CONTRACT
SHERIFF
IMPLEMENT
START application
OPEN browser
TEST interactions
CAPTURE desktop
CAPTURE mobile
COMPARE references
FIX differences
META REVIEW if available
SENTINEL WEB AUDIT
VERIFY
GUARDIAN
LOOP UNTIL ACCEPTANCE == 100%
```

## Browser
`CODE -> localhost/file target -> BROWSER -> DOM -> computedStyle -> console -> network -> screenshot`.

## Source priority
Director -> visual reference -> design system -> existing components -> project files -> SKILL/AGENTS -> inference last.

## Diseño != comportamiento != verificación
Apariencia, acciones/estado y prueba son capas distintas.

## FIFA
`Diseño/Manus -> HTML funcional -> código modular -> assets -> dependencies -> version -> seguir editando`.
Nunca solo HTML para una pieza evolutiva.

## QA
11/11 de `ACCEPTANCE.md` + AC01..AC15.

## LOOP legado
L0-L10 sigue protegiendo IDs/originales y queda contenido dentro del DAG nuevo.

## Evidencia
Registrar task/surface ID, sources, skills, componentes, cambios, tests, screenshots, Sentinel report, PASS/FAIL/BLOCKED, commit SHA.

## Referencias
Imágenes:
https://github.com/maxbry123-commits/frontend/tree/39a614b9b098a8a932d8923b861af790959118b8/UI%20YAIWES%20interface/Ui%20Yaiwes%20interface%20beta/01-original/FOTOS-REF

Handoff skills:
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/actualizaciones%20arquitectura/HANDOFF-SKILLS-UI-YAIWES-2026-09-27.md

## Done
`11/11 PASS + AC01..AC15 PASS + dead_controls=0 + console_errors=0 + missing_assets=0 + evidence + handoff`.

## Método operativo V2 — ejecución multi-IA reproducible

Este método queda cableado con ARQUITECTURA-FRONTEND-UI-YAIWES-V1.md y con:
actualizaciones arquitectura/HANDOFF-SKILLS-UI-YAIWES-2026-09-27.md

Objetivo: cualquier IA/modelo puede continuar el proyecto sin reinterpretar el proceso.

### Staff

- Director: requisito y aprobación.
- Codex: ejecutor/mejorador principal de código.
- Agente frontend: ejecuta una pieza.
- v0: apoyo screenshot/diseño → primera propuesta.
- Meta visual reviewer: auditoría visual independiente.
- SkillResolver: resuelve skills.
- Sheriff: bloquea incumplimientos.
- Validator: valida DSL/schema/contract/manifest.
- Verifier: browser + Playwright.
- Sentinel Web: investigación/auditoría externa cuando aplique.
- Guardian: cierre solo con evidencia y PASS total.

### Preload obligatorio

READ architecture
READ method
READ handoff
READ project files
READ relevant SKILL.md
READ AGENTS.md si existe
INSPECT reference images
READ design system
RESOLVE assets

No implementar antes de completar la ingestión.

### Referencias

https://github.com/maxbry123-commits/frontend/tree/39a614b9b098a8a932d8923b861af790959118b8/UI%20YAIWES%20interface/Ui%20Yaiwes%20interface%20beta/01-original/FOTOS-REF

Orden:
Figma/imagen/frontend real → Design System → componentes existentes → archivos del proyecto → SKILL.md/AGENTS.md → inferencia.

### Mini workflow

Agente frontend
→ READ references
→ READ project files
→ READ skills
→ BUILD DSL
→ COMPILE DAG
→ VALIDATE schema/contract
→ PASS Sheriff
→ IMPLEMENT
→ START application
→ OPEN browser
→ TEST interactions
→ CAPTURE desktop
→ CAPTURE mobile
→ COMPARE references
→ FIX differences
→ Sentinel Web audit si aplica
→ Meta visual review
→ LOOP UNTIL ACCEPTANCE == 100%

Microregla:
VER → USAR → COMPARAR → CORREGIR → VERIFICAR

### Contrato de implementación

MODE=IMPLEMENTATION
TARGET=FUNCTIONAL_WEB_PROTOTYPE
OUTPUT=RUNNABLE_HTML_CSS_JS_OR_PROJECT_SOURCE
STATIC_MOCK=false
EXECUTION_TARGET=BROWSER
ZERO_DEAD_CONTROLS=true
NO_COSMETIC_FAKE_STATE=true
DO_NOT_INVENT=true
DO_NOT_GUESS_UI=true

Bloqueo previo:
files_read == true
skills_read == true
reference_images_inspected == true

### DSL → DAG → Schema → Contract → Sheriff

REQUIREMENT
→ DSL(task/surface/sources/constraints/delivery/acceptance)
→ DAG(nodes/dependencies/evidence)
→ SCHEMA
→ CONTRACT
→ SKILL RESOLUTION
→ SHERIFF
→ EXECUTOR

Fallo en un gate = BLOCKED. No rellenar huecos inventando.

### Interacción real

Cada control:
TRIGGER → HANDLER → STATE/ACTION → VISIBLE FEEDBACK → DETERMINISTIC RESULT

Estados aplicables:
default · hover · focus-visible · pressed · active · selected · expanded · disabled · error

Estado visual debe coincidir con estado lógico/ARIA.

### Browser verification

CODE
→ localhost/runtime
→ BROWSER
→ DOM + computedStyle + console + network + screenshot
→ click/select/input/tab/scroll/touch
→ COMPARE reference ↔ result
→ FIX
→ repetir

Playwright es el E2E preferente. No hay PASS solo por compilar.

### Matriz mínima 11/11

TEST_REFERENCE PASS
TEST_LAYOUT PASS
TEST_BUTTONS PASS
TEST_DROPDOWNS PASS
TEST_TABS PASS
TEST_INPUTS PASS
TEST_STATE PASS
TEST_RELOAD PASS
TEST_DESKTOP PASS
TEST_MOBILE PASS
TEST_CONSOLE PASS

Además:
uncaught exceptions = 0
console errors = 0
missing assets = 0
dead controls = 0
extra unreferenced controls = 0 salvo aprobación explícita.

### Skill chain

SKILL.md
→ SKILL_SCHEMA
→ SKILL_CONTRACT
→ SKILL_SHERIFF
→ ADAPTER
→ EXECUTOR
→ TEST
→ EVIDENCE

Cadena funcional:
1. reference-reader
2. design-system
3. frontend-implementation
4. browser-verification
5. interaction-qa
6. mobile-qa

Estos IDs deben mapearse a skills físicos existentes del registry o crearse/validarse mediante skill-creator. No se consideran instalados por nombrarlos.

### Sentinel + Meta visual + Guardian

1. Sentinel Web: verifica documentación/hechos externos pertinentes.
2. Meta visual reviewer: compara referencia y render.
3. Guardian: revisa schema, contract, tests, evidencia, handoff y versión.

Solo Guardian marca VERIFIED; aprobación de producto sigue siendo del Director.

### Entrega

Prototipo simple:
index.html
styles.css
app.js
referenced_assets/
README.md
ACCEPTANCE.md
tests/
version

React/Vite:
UI-YAIWES/
├── index.html
├── package.json
├── vite.config.js
├── src/
│   ├── App.jsx
│   ├── main.jsx
│   ├── components/
│   ├── styles/
│   └── assets/
├── README.md
├── ACCEPTANCE.md
├── tests/
└── snapshot/index-reference.html

Guardar siempre:
HTML funcional + código modular + assets + dependencias + versión

### Definition of Done

PASS_ONLY_IF:
acceptance == 100%
tests_11_of_11 == PASS
dead_controls == 0
console_errors == 0
missing_assets == 0
evidence_complete == true
handoff_updated == true

FAIL_IF_ANY_ACCEPTANCE_TEST_FAILS=true
DO_NOT_DECLARE_DONE_ON_PARTIAL_PASS=true

### Handoff mínimo

Registrar:
- task/ID
- base SHA
- archivos tocados
- referencias leídas
- skills usados + path/versión
- DSL/DAG
- Sheriff/Validator
- tests/screenshots
- Sentinel Web si aplicó
- Meta visual review
- PASS/FAIL/BLOCKED
- gaps
- siguiente acción

### Flujo final

REFERENCE + CONTEXT + SKILLS + BROWSER + VERIFIER
→ IMPLEMENT
→ COMPARE
→ FIX
→ SENTINEL/META REVIEW
→ GUARDIAN
→ 100% PASS
→ HANDOFF

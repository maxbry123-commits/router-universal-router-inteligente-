# EXECUTION-CONTRACT.md

MODE=IMPLEMENTATION  
TARGET=FUNCTIONAL_WEB_PROTOTYPE  
OUTPUT=RUNNABLE_HTML_CSS_JS_OR_REACT_VITE  
STATIC_MOCK=false  
EXECUTION_TARGET=BROWSER

## Source ingestion
```text
READ_RECURSIVE(project_files)
READ_RECURSIVE(**/SKILL.md)
READ(AGENTS.md)
READ(DESIGN_SYSTEM.md)
READ(COMPONENT_INDEX.md)
INSPECT_ALL(reference_images)
RESOLVE(asset_paths)
BLOCK_IMPLEMENTATION_UNTIL all=true
```

Prioridad: Director -> referencias -> design system -> componentes existentes -> archivos proyecto -> SKILL/AGENTS -> inferencia.

## UI fidelity
Reproducir layout, hierarchy, positioning, spacing, sizing, typography, colors, borders, radius, icons, images, control order y visible states.
Prohibido UI no referenciada o assets placeholder.

## Semantic implementation
Preferir button/input/textarea/select/a/checkbox-switch. Custom widget requiere keyboard, focus management, accessible name, role y state attrs.

## Interaction contract
Todo control: `trigger -> handler -> state/action -> visible_feedback -> deterministic_result`.
Button/select/dropdown/tabs/toggle/input/panel/navigation deben modificar estado/DOM real.

## Visual state
default hover focus-visible pressed active selected expanded disabled error.
No cosmetic fake state.

## State
single_source_of_truth=true; DOM desde state; persistence solo si proyecto la requiere.

## Assets
usar assets reales; aspect ratio; no placeholders; 0 404.

## Responsive
mouse=true; touch=true; keyboard=true; no overflow accidental; controls reachable.

## Accessibility
keyboard, visible focus, semantic HTML, accessible names, disabled semantics.

## Functionality
ZERO_DEAD_CONTROLS=true.
Prohibido onclick sin efecto, href="#", javascript:void(0), fake loading/success, console-only action, TODO handler.

## Runtime
uncaught_exceptions=0; console_errors=0; missing_assets=0; duplicate_ids=0; invalid_event_targets=0.

## Workflow
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
SENTINEL AUDIT
VERIFY
GUARDIAN
LOOP UNTIL ACCEPTANCE == 100%
```

## Browser
`CODE -> localhost/file target -> BROWSER -> DOM -> computedStyle -> console -> network -> screenshot`.

## Delivery
snapshot HTML funcional + proyecto modular + assets + package/dependencies + manifest + README + ACCEPTANCE + tests + versión + evidence.

React/Vite:
```text
UI-YAIWES/
├ index.html
├ package.json
├ vite.config.js
├ src/
│  ├ App.jsx
│  ├ main.jsx
│  ├ components/
│  ├ styles/
│  └ assets/
├ tests/
├ manifest.json
├ README.md
└ snapshot/index-reference.html
```

DO_NOT_DECLARE_DONE_ON_PARTIAL_PASS=true.

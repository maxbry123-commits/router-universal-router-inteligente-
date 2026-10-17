# UI YAIWES — Plan maestro de trabajo frontend

**Estado:** `ACTIVE / RECEPCIÓN → PLANIFICACIÓN`
**Versión:** `1.0.0`
**Fecha:** `2026-09-27`
**Alcance:** frontend de UI YAIWES; el backend solo aparece como frontera de contrato.

> Regla central: **mostrar primero, discutir por pieza, aprobar por ID, integrar después**.

## 1. Cómo trabajaremos

Cada entrega sigue este ciclo:

1. **Recepción:** leer archivo, foto, commit o instrucción; no modificar originales.
2. **Auditoría:** consultar arquitectura, índices, skills, componentes, historial y dependencias.
3. **Ficha:** declarar objetivo, fuente, zonas, estados, acciones, datos y límites.
4. **Canvas:** construir una muestra local, pequeña y reversible.
5. **Revisión:** explicar qué es real, qué es stub y qué queda fuera.
6. **Aprobación:** recibir `OK <ID>` o registrar cambios solicitados.
7. **Integración:** cablear la pieza aprobada con HostShell, WindowRegistry, StateStore y Action Bus.
8. **Verificación:** revisar visual, accesibilidad, responsive, manifest y trazabilidad.
9. **Handoff:** actualizar `CRAZY-WALL-BITACORA-STATE.json`, `HANDOFF-...json` y `memoria.md`.

No se construye una aplicación monolítica ni se integran varias ventanas sin revisión intermedia.

## 2. Fuentes que se consultan antes de cada pieza

### Arquitectura y contrato

- `readme arquitectura UI YAIWES interface beta/README.md`.
- `HANDOFF-FRONTEND-UI-YAIWES-2026-09-27.md`.
- `ARQUITECTURA-FRONTEND-UI-YAIWES-V1.md`.
- `actualizaciones arquitectura/`.
- `Ui Yaiwes interface beta/02-fromted/INDEX.json`.
- Fichas de ventana y `HOST.html`.

### Referencias visuales

- `01-original/FOTOS-REF/`.
- `Run.html` y demás ventanas originales.
- Índices de fotografías y descripciones.

Las fotos son referencia de composición, densidad y jerarquía; no son contrato funcional.

### Fábrica y skills

Se consulta el índice de fábrica adjunto y el catálogo en:

- `fabrica de UI INTERFACE fromtend/`.
- `📂componentes open soure fromtend/`.
- `Skills arquitectura frontend Yaiwes/`.
- `UI YAIWES interface/fabrica-ui/runtime/`.

La lista de componentes se trata como catálogo de candidatos, no como permiso para instalar todo. Cada componente debe tener una ficha de procedencia, licencia, referencia, hash/versión, función y estado.

## 3. Arquitectura de ejecución

```text
Usuario
  ↓
Panel A / Panel B
  ↓
WindowRenderer / CanvasOrchestrator
  ↓
UI Contract
  ↓
Action Bus
  ↓
Bridge
  ↓
Backend (solo frontera)
  ↓
Eventos / resultados
  ↓
StateStore → Canvas / Window
```

### Núcleo frontend

- `HostShell`: chrome, rail, topbar, canvas e inspector.
- `WindowRegistry`: registro canónico de las 39 ventanas.
- `StateStore`: estado visual y local, sin duplicar memoria backend.
- `Action Bus`: única salida de acciones de UI; fail-closed.
- `Manifest Schema`: valida antes de pintar.
- `CanvasOrchestrator`: abrir, enfocar, actualizar y cerrar ventanas.
- `CapabilityProjector`: mostrar capacidades registradas.

### Backend fuera de alcance

No implementar aquí proveedores, router de modelos, memoria interna, scheduler, secretos, pools, orquestación ni lógica de agentes. El frontend solo envía acciones tipadas y representa resultados recibidos.

## 4. Orden de construcción por capas

### Fase 0 — Gobierno y seguridad

- congelar originales;
- establecer `no tocar`;
- usar IDs y manifests;
- activar bitácora, memoria y handoff;
- definir criterios de aprobación.

### Fase 1 — HostShell mínimo

- rail;
- topbar;
- canvas;
- inspector;
- footer de estado;
- tokens Matte/Little/Blanco;
- responsive básico.

### Fase 2 — Registro y contratos

- `WindowRegistry`;
- `Manifest Schema`;
- `StateStore` local;
- `Action Bus`;
- logger de eventos;
- render seguro de ventanas.

### Fase 3 — Primer vertical slice

Orden recomendado:

1. `RUN-01` CASCADE.
2. `RUN-08` inspector de nodo/input/output.
3. `RUN-03` AUDITOR.
4. `WALL-01` bloques.
5. `WALL-02` árbol.
6. `WALL-03` archivos.
7. `GBOT-01` cáscara conversacional.
8. ventanas FOTO como referencias y no como duplicados.

### Fase 4 — Componentes de la fábrica

Usar solo cuando la pieza lo justifique:

- `dockview`: split/tabs del Host.
- `lucide`: iconos.
- `assistant-ui`: thread/composer.
- `xyflow`: DAG/workflow.
- `tldraw`: Crazy Wall libre.
- `TanStack Table`: tablas grandes.
- `Monaco` o `CodeMirror`: código/YAML.
- `Dexie`: persistencia local posterior.
- `i18next`: idiomas.
- `axe-core`, Playwright y Vitest: verificación.

El uso de cada componente se registra en la bitácora antes del montaje.

### Fase 5 — Pulido

- accesibilidad;
- keyboard navigation;
- densidad;
- responsive;
- performance;
- motion solo con propósito;
- cristal/holográfico como material opcional, nunca como sustituto de contraste.

## 5. Paleta y dirección visual

### Matte base

- fondo `#0a0a0d`;
- surface `#141417`;
- panel `#1a1a1e`;
- card `#202025`;
- líneas `#2a2a33` y `#3f3f4e`;
- texto blanco y grises;
- Little azul `#2563eb` para selección, foco y estados;
- naranja `#ff5500` solo para Cargar/Descargar.

La versión holográfica usa transparencias blancas/azules de baja opacidad, blur con fallback sólido y glow azul reducido. No usar lima, neon verde ni morado como marca.

## 6. Qué se muestra en cada canvas

Cada canvas debe explicar:

- ID y objetivo;
- fuente visual y fuente de arquitectura;
- componentes usados;
- zona de interacción;
- estados disponibles;
- acciones simuladas o reales;
- datos de ejemplo;
- frontera backend;
- decisión que el usuario debe aprobar.

## 7. Estados estándar

`idle`, `selected`, `queued`, `running`, `done`, `failed`, `blocked`, `review`, `verified`.

Siempre comunicar el estado con texto, estructura e icono además de color.

## 8. Criterios de aceptación de una pieza

- no modifica originales;
- tiene ID único;
- tiene ficha y manifest válido;
- usa componentes existentes o justifica uno nuevo;
- no duplica HostShell, Action Bus o StateStore;
- tiene interacción local demostrable;
- funciona en pantalla pequeña y grande;
- tiene foco y etiquetas accesibles;
- registra eventos importantes;
- tiene handoff para otra IA;
- recibe `OK <ID>` antes de integrarse.

## 9. Cómo participa otro equipo o IA

El equipo entrante debe leer, en este orden:

1. este plan;
2. `CRAZY-WALL-BITACORA-STATE.json`;
3. `HANDOFF-FRONTEND-UI-YAIWES.json`;
4. `memoria.md`;
5. la ficha de la ventana asignada;
6. las fuentes y componentes indicados en el handoff.

Debe actualizar primero el handoff y la bitácora antes de modificar código. Si existe una contradicción, debe marcar `BLOCKED` y no inventar una decisión.

## 10. Primer trabajo recomendado

Empezamos con **`RUN-01 / CASCADE`**, no con las 39 ventanas a la vez:

1. aprobar Modelo A Matte como base;
2. separar su vista en HostShell, canvas, inspector y eventos;
3. validar manifest de `RUN-01`;
4. demostrar selección de nodo y dispatch local;
5. revisar responsive y accesibilidad;
6. obtener `OK RUN-01`;
7. recién entonces integrar la siguiente pieza.

## 11. Estado inicial

- Plan maestro: `ACTIVE`.
- Originales: `LOCKED / no tocar`.
- Prototipo visual: `REVIEW`.
- Primer ID: `RUN-01`.
- Backend: `BOUNDARY ONLY`.
- Próxima decisión: aprobar dirección Matte / Holographic / Little.


## Norma FIFA — formato de salida (instrucción del usuario)

El método oficial de salida queda fijado así:

1. `index.html` funcional y autocontenido: snapshot, referencia visual y respaldo rápido.
2. Proyecto fuente separado: componentes, estilos, lógica, assets, configuración y dependencias.
3. Flujo obligatorio: `Diseño en Manus → HTML funcional de referencia → código fuente por componentes → guardar versión → seguir editando`.
4. Nunca guardar únicamente el HTML cuando la pieza vaya a continuar evolucionando.
5. Mantener HTML funcional, fuente modular, assets, dependencias y versión.
6. Todo el código debe permanecer separado por partes para editar una función sin romper las demás.


## Hallazgos visuales incorporados — lote actual

El lote completo actual contiene 158 imágenes en `01-original/FOTOS-REF/`. Se observaron patrones repetidos que pasan a ser requisitos visuales del Panel 1: chat móvil oscuro; composer persistente; selector de modo; botones de imagen, archivo y audio; menús desplegables; estados de ejecución; tarjetas de archivos; conectores; respuestas largas; paneles técnicos; controles de configuración; vistas de código; navegación compacta; y layouts de doble panel. Las imágenes se usan como referencia de composición y comportamiento visible, no como sustituto de contratos backend.

El primer prototipo `PANEL-01 / CHAT-01` se construye sin la etiqueta `<canvas>`, con acciones nativas reales del navegador y frontera explícita para `send_message`, `upload_file`, `transcribe_audio` y `cancel_run`.

## 12. Subplan oficial — PANEL-01 / CHAT-01

Este subplan se incorpora a la ejecución del Panel B y **reemplaza cualquier interpretación reducida del chat como un simple textarea + enviar**.

Documento de detalle:
`actualizaciones arquitectura/ACTUALIZACION-PANEL-01-CHAT-CONTROLES-Y-SELECTORES-2026-09-27.md`

### 12.1 Fuente

Cruzar antes de implementar:

- más de 50 referencias visuales de `01-original/FOTOS-REF/`;
- `📌p01-chat-minimax.html`;
- `p04-sheet-agregar.html`;
- `p05-sheet-herramientas.html`;
- `p09-mode-dropdown.html`;
- `Maxbry web/Readme arquitectura Maxbry web.md`, BLOQUE A, punto 2;
- `Maxbry web/memoria grock.md`.

### 12.2 Alcance

Inventario consolidado: **60 acciones/capacidades del chat**.

No significa 60 botones visibles. Implementar exposición progresiva:

```text
PERSISTENTE
+ · Thinking · Modelo▾ · Modo▾ · Mic · Enviar
Documento · Website · Imagen · Audio

DESPLEGABLE
+          -> medios/herramientas/proyecto/conectores/plugins
Modelo▾    -> 9 AI + 3 AGI
Modo▾      -> Heavy/Expert/Fast/Auto + razonamiento/especialistas
Workflow▾  -> loops/watchdogs/investigación/workflows/proyectos
Agente▾    -> YAIWES/CODE/NCT/roles/prompts/skills/memoria
•••        -> acciones de conversación
```

### 12.3 Implementación

Orden:

1. inventario y manifest de controles;
2. HTML funcional de referencia;
3. código fuente React/Vite por componentes;
4. estados blanco/gris -> Little azul al seleccionar;
5. selectores/sheets reales;
6. Action Bus y adaptador plugin/bridge;
7. fail-closed sin backend;
8. Playwright: click/select/toggle/input/touch/keyboard;
9. evidencia visual desktop+móvil;
10. revisión del Director;
11. `OK PANEL-01-CHAT`;
12. integración en Panel B.

### 12.4 Formato obligatorio de salida

```text
PANEL-01-CHAT/
├── index.html
├── package.json
├── vite.config.js
├── src/
│   ├── App.jsx
│   ├── main.jsx
│   ├── components/
│   ├── styles/
│   └── assets/
├── manifest.json
├── README.md
├── ACCEPTANCE.md
├── tests/
└── snapshot/index-reference.html
```

### 12.5 Gate

No marcar DONE si:

- existe un botón muerto;
- falta un selector;
- se inventa un nombre de modelo/capacidad no registrado;
- seleccionado no produce estado lógico + visual;
- el frontend llama directo a proveedores;
- no hay fail-closed;
- falta HTML funcional o fuente modular;
- falta responsive/touch/keyboard;
- falta evidencia;
- no existe `OK PANEL-01-CHAT`.

Estado de este subplan: `ACTIVE / DESIGN+PROTOTYPE / REVIEW`.

## 13. Plan de Skills integrado

El plan de acción oficial vive en:

`actualizaciones arquitectura/PLAN-ACCION-SKILLS-UI-YAIWES-2026-09-27.md`

Orden:

1. Registry y deduplicación.
2. `SkillResolver` fail-closed.
3. Core frontend: FROMTED architecture + frontend-design + image-to-code + impeccable + web guidelines + builder + skill-creator.
4. QA: Playwright, visual, lint, a11y.
5. Device/runtime: Orca sólo cuando exista runtime real.
6. Donor adapters: nunca promover instrucciones específicas del donor directamente.
7. Integración Fábrica UI.
8. Aplicación por superficie, empezando por `PANEL-01-CHAT`.
9. Handoff/evidencia por ejecución.

Gate general:

`REGISTERED -> SCOPE_OK -> ADAPTER_READY -> TESTED -> VERIFIED -> ACTIVE`

Si falla cualquier gate: `BLOCKED`.

## 13. Plan de acción — Skills

Handoff canónico:
`HANDOFF-SKILLS-UI-YAIWES-Y-FABRICA-2026-09-27.md`

Orden por pieza:

1. resolver skills requeridos desde el inventario;
2. diseño: `frontend-design + impeccable`;
3. componente: `headless-component / v9-component / token-lookup` cuando aplique;
4. implementación modular;
5. `lint-check`;
6. `write-and-verify-pw-test`;
7. `fix-pw-spec` si el error está en el test;
8. `diagnose-pw-failure` si el test es correcto y falla producto;
9. `visual-test`;
10. emuladores Orca para QA Android/iOS cuando aplique;
11. evidencia + handoff;
12. PASS/FAIL.

Siguiente acción técnica pendiente: crear un `SKILL-REGISTRY.json` machine-readable sin mover ni duplicar los donors.

## 13. Plan de acción — Skills

Fuente: `HANDOFF-SKILLS-UI-YAIWES-2026-09-27.md`  
Registry: `SKILLS-REGISTRY-UI-YAIWES.json`

Estado:
- P0 inventario 38 físicos / 26 canónicos: **PASS**.
- P1 registry y aliases: **PASS documental**.
- P2 cableado arquitectura: **PASS documental**.
- P3 adapter común + validación de dependencias: **NEXT**.
- P4 QA Playwright (`write-and-verify -> fix-pw-spec -> diagnose-pw-failure`) + `visual-test`: **NEXT**.
- P5 component factory (`token-lookup -> headless-component/v9-component -> lint-check`): **NEXT**.
- P6 mobile QA (`orca-emulator-android/orca-emulator`): **NEXT**.
- P7 orchestration (`orchestration + orca-cli`): **NEXT**.
- P8 acceptance/evidence/handoff: **NEXT**.

Regla de cierre: ningún skill se considera integrado solo porque su `SKILL.md` exista. Debe resolver por ID canónico, verificar runtime/dependencias, ejecutar el test aplicable y dejar evidencia.
## Skills — handoff canónico 2026-09-27

Antes de construir cualquier pieza, resolver su cadena de skills desde:
`actualizaciones arquitectura/HANDOFF-SKILLS-UI-YAIWES-2026-09-27.md`.

Para `PANEL-01-CHAT`:
`FOTOS -> Image-to-Code -> frontend-design -> BUILD -> Impeccable -> frontend-audit/accessibility -> Playwright -> evidence -> review`.

No activar donors ni catálogo en masa. Cada skill debe pasar:
`SCOPE_OK -> ADAPTER_READY(si aplica) -> TESTED -> VERIFIED -> ACTIVE`.

## 14. Plan ejecutable multi-agente

1. Bootstrap de contexto: AGENTS + contrato + arquitectura + plan + handoffs + skills + design system + component index + acceptance + referencias.
2. Skills: `reference-reader -> design-system -> frontend-implementation -> browser-verification -> mobile-qa -> interaction-qa`.
3. TaskContract -> Schema -> Sheriff PASS.
4. Codex implementa/mejora; v0 puede aportar bootstrap visual.
5. Playwright desktop+móvil: DOM/CSS/console/network/screenshot.
6. Meta Visual Reviewer solo con adapter real; si no `META_REVIEW_UNAVAILABLE`.
7. Sentinel audita documentación/versiones/claims.
8. Guardian cierra solo con 11/11 + AC01..AC15 + evidencia.

Estado: ACTIVE.


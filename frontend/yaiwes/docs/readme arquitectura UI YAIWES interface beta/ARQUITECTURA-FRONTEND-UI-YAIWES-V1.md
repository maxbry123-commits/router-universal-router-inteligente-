# Arquitectura Frontend UI YAIWES interface — V1

Fecha de consolidación: 2026-09-27  
Repo: `maxbry123-commits/frontend`  
Branch: `main`  
Alcance: **solo frontend / UI / experiencia / empaquetado cliente**.

## Autoridad de esta arquitectura

Esta extensión consolida únicamente el trabajo frontend extraído de los tres archivos subidos el 27 de septiembre de 2026. Los archivos fuente se conservan intactos y marcados como referencia.

Fuente 1 — sistema de componentes/plugins de fábrica:
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/actualizaciones%20arquitectura/sistema%20de%20componente%20tipo%20plugins%20para%20la%20f%C3%A1brica%20y%20yaiwes%F0%9F%9A%80%F0%9F%86%98%F0%9F%86%98con%20los%20componentes%20necesarios%20y%20como%20funciona%F0%9F%93%B2no%20tocar%20%E2%9A%A0%EF%B8%8F.md

Fuente 2 — arquitectura completa backend + frontend:
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/actualizaciones%20arquitectura/%F0%9F%93%B2%F0%9F%93%8C%F0%9F%9A%80%F0%9F%93%B2%F0%9F%93%B2%20UI%20YAIWES%20INTERFACE%20VERSI%C3%93N%201.0%20FINAL%20%F0%9F%93%8C%F0%9F%9A%80%F0%9F%93%B2%20Con%20backend%20frontend%20y%20URL%20visible%20...a%20y%20dise%C3%B1o%20para%20backend%20y%20frontend%20todo%20%E2%9B%94no%20tocar%20%F0%9F%94%A8%F0%9F%93%8C.md

Fuente 3 — plan ejecutable frontend:
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/actualizaciones%20arquitectura/%F0%9F%93%B2%F0%9F%93%B2%20UI%20YAIWES.%20fromtend%20plan%20de%20ejecuci%C3%B3n%20todo%20%20no%20tocar.md

Regla de alcance: el backend aparece aquí solamente como **frontera de contrato** necesaria para que la UI pueda enviar acciones y recibir resultados. Esta arquitectura no añade tareas de implementación del backend, router de modelos, memoria, scheduler, proveedores ni orquestación interna.

## Arquitectura frontend resumida

`USUARIO -> PANEL B / PANEL A -> UI CONTRACTS -> ACTION BUS -> BRIDGE -> BACKEND (frontera) -> EVENTOS/RESULTADOS -> CANVAS / VENTANAS`

La UI no controla proveedores ni ejecuta lógica interna del backend. Proyecta estado, emite acciones tipadas y renderiza resultados.

## Núcleo frontend

- Un núcleo compartido HTML/CSS/JS + manifiestos + tokens FROMTED.
- React solo donde la interacción lo justifique: canvas, chat, grafo y componentes complejos.
- `HOST.html` como HostShell existente.
- `INDEX.json` como registro canónico de las 39 ventanas.
- `WindowRegistry` para resolver y montar ventanas.
- `StateStore` para estado visual/local.
- `Action Bus` como salida única de acciones del frontend.
- `NodePlanBridge` / bridge API-MCP como frontera, no como implementación backend.
- `CanvasOrchestrator` para abrir, actualizar, enfocar y cerrar ventanas según eventos.
- `CapabilityProjector` para mostrar en la UI capacidades registradas por la fábrica.

## Doble panel

### Panel A — Command Center

Superficie para operador técnico.

Incluye:
- shell del panel;
- visualizador del DAG;
- inspector de nodos;
- stream de eventos;
- checkpoints;
- controles HITL;
- métricas/coste mostrados como datos recibidos;
- auditoría;
- preview/sandbox;
- test de integración del panel.

Microflujo:
`EVENTOS -> VISUALIZER -> INSPECTOR -> CHECKPOINT/HITL -> FEEDBACK VISUAL`

### Panel B — Conversation & Canvas

Superficie por defecto para usuario final.

Incluye:
- shell del panel;
- chat persistente;
- entrada de voz;
- NodePlanBridge;
- CanvasOrchestrator;
- WindowRenderer;
- CanvasCore;
- AttentionScheduler;
- MediaPipeline;
- CapabilityProjector;
- onboarding;
- test de integración.

Microflujo:
`TEXTO/VOZ -> NODEPLAN -> BRIDGE -> RESULTADO -> CANVAS ORCHESTRATOR -> VENTANA`

## Canvas y ventanas

El canvas funciona como monitor multi-ventana dinámico. Puede proyectar:
- documento;
- imagen;
- vídeo;
- gráfico;
- conversación;
- otros tipos registrados mediante capacidades.

Las 39 ventanas existentes siguen siendo fuente física de UI:
- 8 RUN;
- 16 WALL;
- 1 GBOT;
- 14 FOTO.

Ruta:
`UI YAIWES interface/Ui Yaiwes interface beta/02-fromted/`

El frontend debe reutilizar esas ventanas mediante HostShell/WindowRegistry antes de crear superficies duplicadas.

## Fábrica y sistema de componentes — frontera frontend

Del archivo de plugins se incorpora únicamente lo que afecta a la UI:

`COMPONENTE -> CAPABILITY REGISTRY -> CAPABILITY PROJECTOR / WINDOW REGISTRY -> UI`

La transformación interna de software a Harness/Tool/Pool/Workflow/Subagent pertenece a la fábrica/backend y queda fuera de este alcance frontend.

Para frontend, el contrato mínimo de una capacidad debe permitir:
- id;
- nombre visible;
- tipo;
- entradas/salidas;
- permisos de UI;
- ventana/superficie asociada;
- estado;
- versión;
- disponibilidad.

## Persistencia, sync y offline del cliente

- Dexie + IndexedDB para persistencia local.
- Yjs o Loro para sincronización CRDT.
- OfflineQueue para operaciones cliente pendientes.
- DeviceRegistry para identificar superficies/dispositivos.
- Service Worker/Workbox para PWA y recursos offline.
- recuperación visual sin pérdida del estado reciente cuando sea posible.

Microflujo:
`CAMBIO LOCAL -> STORE -> PERSISTENCIA -> CRDT -> OTRO DISPOSITIVO -> RERENDER`

## Voz

La voz es otro canal de entrada/salida del frontend y debe producir el mismo contrato que el texto:

`AUDIO -> STT -> INTENCIÓN/NODEPLAN -> BRIDGE -> RESULTADO -> TTS/UI`

Componentes propuestos en los archivos fuente:
- faster-whisper;
- Piper;
- Silero VAD.

## Diseño y sistema visual

Tokens FROMTED vigentes:
- fondo: `#000000`, `#0a0a0d`, `#141417`;
- selección/acento: `#2563eb`;
- texto primario: `#ffffff`;
- naranja `#ff5500`: solo Cargar/Descargar.

Design System compartido:
- Button;
- Input;
- Select;
- Toggle;
- Modal;
- Window;
- Card;
- Badge;
- WindowFrame;
- componentes comunes accesibles e internacionalizables.

Regla: las fotos sirven como evidencia y referencia visual/layout; no sustituyen contratos ni componentes ejecutables.

## Empaque cliente

Un mismo núcleo frontend debe poder empaquetarse como:
- PWA con Workbox;
- desktop con Tauri 2;
- móvil con Capacitor o Tauri móvil.

No se crea una implementación visual distinta por plataforma.

## Accesibilidad e i18n

- navegación completa por teclado;
- roles/ARIA;
- contraste;
- reduced motion;
- lector de pantalla;
- axe-core en QA;
- strings fuera del código;
- i18n por JSON/namespace;
- cambio de idioma sin reescribir componentes.

## Cinco salidas frontend

### Salida 1 — Fundación — 11 nodos
Contratos UI, estructura, tokens, StateStore, router de paneles, HostShell, WindowRegistry, Action Bus, bridge de frontera, bootstrap y test.

### Salida 2 — Panel A — 10 nodos
Shell, visualizer, inspector, eventos, checkpoints, HITL, métricas, auditoría, sandbox y test.

### Salida 3 — Panel B — 12 nodos
Shell, chat, voz stub, NodePlanBridge, CanvasOrchestrator, WindowRenderer, CanvasCore, AttentionScheduler, MediaPipeline, CapabilityProjector, onboarding y test.

### Salida 4 — Cliente avanzado — 10 nodos
Voz completa, runtime local embebido, OfflineQueue, LocalPersistence, CRDTSync, DeviceRegistry, CapabilityRegistry UI Bridge, resiliencia cliente, privacidad/consentimiento y test.

### Salida 5 — Empaque y cierre — 12 nodos
PWA, Tauri, Capacitor, native bridges, accesibilidad, i18n, Design System, build unificado, guía de despliegue frontend, telemetría opt-in, criterios de aceptación y test final.

**Cuenta corregida:** 11 + 10 + 12 + 10 + 12 = **55 nodos declarados**. Los archivos fuente dicen “45” en su cierre, pero esa cifra no coincide con su propio desglose.

## Evidencia visual conectada

Fotos proyecto — parte 1:
https://github.com/maxbry123-commits/frontend/commit/13f4e932866284fb5ddfaaf6ada5ce4809f82f46

Fotos proyecto — parte 2:
https://github.com/maxbry123-commits/frontend/commit/c50fc98d19debe1a85817cf1129b55a99c895c9f

Fotos proyecto — parte 3:
https://github.com/maxbry123-commits/frontend/commit/430809bd98c614435ad7597493ed46c16d6552a3

## Reglas de implementación frontend

1. Reutilizar primero los activos físicos existentes.
2. No crear un segundo dueño de estado global.
3. Toda acción UI sale por Action Bus/contrato.
4. La UI no llama directamente a proveedores LLM.
5. Backend solo se consume por contrato/bridge.
6. Panel A y Panel B comparten núcleo, pero no mezclan permisos ni experiencia.
7. Fotos = referencia visual; `01-original` permanece intacto.
8. Mantener paridad web/desktop/móvil desde un único núcleo.
9. Accesibilidad e i18n forman parte del componente base.
10. No declarar cierre por presencia de archivos: exigir wiring + test + evidencia.

## Flujo de trabajo frontend

`FUENTES + FOTOS -> ARQUITECTURA FRONTEND -> CONTRATOS UI -> HOST/WINDOW REGISTRY -> PANEL A + PANEL B -> SYNC/OFFLINE/VOZ -> EMPAQUE -> QA -> EVIDENCIA -> HANDOFF`

## Extensión PANEL-01 / CHAT-01 — controles, selectores y capacidades

El chat de Panel B queda especificado como una superficie compacta con **inventario amplio pero exposición progresiva**.

### Regla de densidad

No se muestran las ~60 capacidades de chat a la vez. Se mantienen 10–15 controles persistentes y el resto se organiza en sheets/selectores.

Persistentes:

- Agregar `+`;
- Thinking;
- selector Modelo;
- selector Modo;
- Micrófono;
- Enviar;
- Documento;
- Website;
- Imagen;
- Audio;
- Detener cuando el run está activo.

Agrupaciones:

- `+` = medios, archivos, investigación, web, proyecto, estilo, herramientas, conectores, plugins y artefactos.
- Modelo = 9 AI + 3 AGI desde registry.
- Modo = Heavy/Expert/Fast/Auto + intensidad/especialidades/expertos.
- Workflow = loops, watchdogs, investigación, workflows y proyectos.
- Agente = YAIWES, CODE, NCT CODE, skills, roles, prompts, memoria y almacenamiento.

Fuente detallada:
`actualizaciones arquitectura/ACTUALIZACION-PANEL-01-CHAT-CONTROLES-Y-SELECTORES-2026-09-27.md`

### Contrato

`CONTROL -> actionId -> ACTION BUS -> BRIDGE/PLUGIN -> BACKEND (frontera) -> EVENTO -> STATESTORE -> UI`

Reglas adicionales:

1. cero controles muertos;
2. estado visual y estado lógico deben coincidir;
3. seleccionado = Little azul `#2563eb`;
4. naranja solo Cargar/Descargar;
5. modelos/capacidades vienen de registry/configuración, no del JSX;
6. sin bridge o actionId válido = fail-closed;
7. entregar HTML funcional + proyecto modular + assets + dependencias + versión;
8. `OK PANEL-01-CHAT` es obligatorio antes de integración.

## Skill layer — resolución y gobierno

Se añade una capa explícita entre intención y ejecución:

```text
USER/TASK
  ↓
SkillResolver
  ↓
FROMTED architecture policy
  ↓
surface skill
  ↓
Capability / Tool / Component
  ↓
Action Bus / browser / device / repo
  ↓
QA skill
  ↓
Evidence
```

Fuentes:

- `SKILL-REGISTRY-UI-YAIWES-2026-09-27.json`.
- `HANDOFF-SKILLS-UI-YAIWES-2026-09-27.md`.
- `PLAN-ACCION-SKILLS-UI-YAIWES-2026-09-27.md`.

Política:

1. `fromted-frontend-architecture` gobierna tokens, modularidad y fail-closed.
2. `frontend-design`, `image-to-code`, `impeccable`, `web-design-guidelines` y builder se usan por etapa.
3. Donor skills Appsmith/Fluent/VS Code/Budibase/Orca/Omarchy no son globales.
4. Mirror/alias no crea una segunda capacidad.
5. Skill != tool != plugin != componente: el skill define método; la capacidad ejecuta.
6. Skill sin scope/dependencia disponible = `BLOCKED`.
7. Integración no es PASS hasta adapter + test + evidencia.

## Capa de Skills — handoff canónico

Documento canónico:
`HANDOFF-SKILLS-UI-YAIWES-Y-FABRICA-2026-09-27.md`

Inventario actual:
- 10 `SKILL.md` físicos bajo `UI YAIWES interface/`;
- 31 `SKILL.md` físicos bajo `fabrica de UI INTERFACE fromtend/`;
- 41 archivos físicos;
- 30 nombres funcionales únicos después de consolidar duplicados.

Flujo frontend recomendado:

`frontend-design -> impeccable -> component/token skills -> implementación -> lint -> Playwright -> visual-test -> evidencia`

La capa de skills guía a los agentes; no sustituye `Action Bus`, `WindowRegistry`, `StateStore` ni runtime del producto. Los donors permanecen en sus rutas originales. Un skill nuevo solo se crea mediante `skill-creator` cuando un gap real no esté cubierto.

## Skill Registry y SkillResolver — cableado 2026-09-27

Handoff canónico:
`HANDOFF-SKILLS-UI-YAIWES-2026-09-27.md`

Registry:
`SKILLS-REGISTRY-UI-YAIWES.json`

Auditoría física:
- `UI YAIWES interface/`: 10 SKILL docs / 9 capacidades canónicas.
- `fabrica de UI INTERFACE fromtend/`: 28 SKILL docs / 17 capacidades canónicas.
- total: 38 físicos / 26 canónicos.

Microflujo:

`TASK -> SkillRegistry -> SkillResolver -> adapter -> Agent/Workflow -> QA/Evidence`

Reglas:
1. rutas donor se resuelven por ID canónico;
2. aliases no duplican capacidad;
3. UI no hardcodea rutas de donor;
4. skill existente no equivale a runtime instalado;
5. validar dependencias/allowed-tools antes de ejecutar;
6. frontend visual cierra con Playwright/visual-test/lint cuando aplique;
7. emuladores Orca se reservan para QA móvil;
8. orchestration/orca-cli coordinan trabajo, pero no sustituyen Action Bus, StateStore ni WindowRegistry.
## Skills — handoff canónico 2026-09-27

La arquitectura adopta un `SkillResolver` documental con fail-closed.

```text
TASK -> PRODUCT POLICY -> SURFACE SKILL -> BUILD -> QA/A11Y -> DONOR ADAPTER IF NEEDED -> TOOL/COMPONENT -> EVIDENCE
```

Handoff:
`actualizaciones arquitectura/HANDOFF-SKILLS-UI-YAIWES-2026-09-27.md`

Plan:
`actualizaciones arquitectura/PLAN-ACCION-SKILLS-UI-YAIWES-2026-09-27.md`

Los 10 skills físicos encontrados bajo `UI YAIWES interface/` son donors Omarchy/Orca y no se vuelven globales. El catálogo de fábrica se consume desde el índice del Director; sus entradas staged/catalogadas no se consideran activas hasta resolver path/runtime y pasar test.

## Governance de ejecución v2 — Schema / Contract / Sheriff / Sentinel / Guardian

`REFERENCE -> SkillResolver -> Schema -> Contract -> Sheriff -> Codex -> Browser/Playwright -> Meta Review(si real) -> Sentinel -> Verifier -> Guardian -> PASS/FAIL/BLOCKED`.

Canónicos en raíz: `AGENTS.md`, `SKILL.md`, `DESIGN_SYSTEM.md`, `COMPONENT_INDEX.md`, `ACCEPTANCE.md`, `TEAM-UI-YAIWES.md`, `EXECUTION-CONTRACT.md`, `workflow/`, `skills/`, `qa/`.

Codex queda en staff como ejecutador/mejorador. v0 = bootstrap visual opcional. Meta OSS Cookbook/Muse Glimmer = reviewer adapter, nunca revisión fingida. Sentinel investiga web/docs oficiales cuando la tarea depende de información externa mutable.

Esta capa no sustituye Action Bus, WindowRegistry, StateStore ni backend boundary.

## Extensión de gobierno ejecutable multi-IA — 2026-09-27

Esta extensión no sustituye la arquitectura anterior. Añade la capa de gobierno para que Codex, otro modelo o cualquier agente frontend ejecute UI YAIWES con las mismas fuentes, contratos y gates.

### Fuentes canónicas cableadas

- Método: readme arquitectura UI YAIWES interface beta/METODO-DE-TRABAJO.md
- Handoff skills: readme arquitectura UI YAIWES interface beta/actualizaciones arquitectura/HANDOFF-SKILLS-UI-YAIWES-2026-09-27.md
- Registry skills: readme arquitectura UI YAIWES interface beta/SKILLS-REGISTRY-UI-YAIWES-2026-09-27.json
- Plan maestro: readme arquitectura UI YAIWES interface beta/PLAN-DE-TRABAJO-UI-YAIWES.md
- Referencias visuales: UI YAIWES interface/Ui Yaiwes interface beta/01-original/FOTOS-REF/
- Gate por pieza: ACCEPTANCE.md

Referencia visual:
https://github.com/maxbry123-commits/frontend/tree/39a614b9b098a8a932d8923b861af790959118b8/UI%20YAIWES%20interface/Ui%20Yaiwes%20interface%20beta/01-original/FOTOS-REF

### Staff UI YAIWES

| Rol | Función | Autoridad |
|---|---|---|
| Director | requisito, prioridad, aprobación/rechazo | máxima |
| Codex | ejecutor y mejorador: implementar, refactorizar, probar, corregir | ejecuta; no redefine producto |
| Agente frontend | implementa la pieza asignada siguiendo contrato | ejecuta |
| v0 | diseño/screenshot a primera propuesta de componentes | apoyo; no fuente final |
| Meta visual reviewer | revisión independiente de fidelidad visual | revisor |
| SkillResolver | selecciona skills válidos por tarea | control |
| Sheriff | aplica políticas, límites y prohibiciones | gate |
| Validator | valida DSL, schema, manifest y contrato | gate |
| Verifier | navegador y Playwright | gate |
| Sentinel Web | investiga documentación/web cuando haga falta y audita el resultado | revisor |
| Guardian | gate final: evidencia, 11/11 PASS y handoff | cierre |

### Arquitectura de ejecución

DIRECTOR/TASK
→ DSL
→ DAG
→ SCHEMA
→ CONTRACT
→ SkillResolver
→ SHERIFF
→ CODEX/FRONTEND EXECUTOR
→ VALIDATOR
→ BROWSER/PLAYWRIGHT
→ VERIFIER
→ SENTINEL WEB + META VISUAL REVIEWER
→ GUARDIAN
→ PASS 100% → HANDOFF/VERSION

Si falla un nodo: CORREGIR y repetir desde el nodo fallido.

### DSL mínimo

Toda tarea declara:
- id
- surface
- objective
- references
- project_files
- skills
- design_system
- constraints
- delivery
- acceptance.required_pass = 100

El DSL se convierte en DAG. Cada nodo debe registrar entradas, salida, test y evidencia.

### Skills como Schema + Contract + Sheriff

SKILL.md
→ SKILL_SCHEMA
→ SKILL_CONTRACT
→ SKILL_SHERIFF
→ Task/Surface Adapter
→ Executor
→ Evidence

Reglas:
1. skill no resoluble = BLOCKED;
2. donor skill sin adapter/runtime = BLOCKED;
3. conflicto con Director/arquitectura = gana Director/arquitectura;
4. skill no puede saltarse Action Bus, StateStore, WindowRegistry, tokens ni aceptación;
5. registrar skill, path/versión, razón, input, output, test y evidencia.

Cadena frontend requerida:
reference-reader → design-system → frontend-implementation → browser-verification → interaction-qa → mobile-qa

Estos nombres son contratos funcionales: deben mapearse a skills físicos del registry o crearse con skill-creator antes de ACTIVE.

### Prioridad

Orden de lectura:
REFERENCIA REAL → DESIGN SYSTEM → COMPONENTES EXISTENTES → ARCHIVOS DEL PROYECTO → SKILL.md/AGENTS.md → INSTRUCCIÓN OPERATIVA.

Precedencia de conflicto:
DIRECTOR → ARQUITECTURA/CONTRATOS LOCKED → REFERENCIA APROBADA → COMPONENTES/ARCHIVOS → SKILLS → INFERENCIA.

La inferencia de diseño es último recurso y se declara.

### Browser verificador

CODE
→ localhost/runtime
→ BROWSER
→ DOM + computedStyle + console + network + screenshot
→ interacción real
→ comparación referencia ↔ resultado
→ corrección

Playwright es el E2E preferente. Su instalación/configuración pertenece a la tarea de implementación, no a esta edición documental.

### Gate 11/11

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

11/11 PASS es mínimo; los AC específicos pueden ampliar, nunca reducir.

### Sentinel Web

RESULTADO
→ investigar documentación/evidencia pertinente
→ comparar
→ registrar discrepancias
→ PASS/FAIL/BLOCKED

No reemplaza referencias del proyecto.

### Entrega mantenible

Diseño/referencia
→ HTML funcional autocontenido
→ código modular
→ assets
→ dependencias
→ manifest/contrato
→ tests
→ versión
→ seguir editando

Nunca guardar solo HTML como fuente mantenible.

### Regla final

REFERENCE + CONTEXT + SKILLS + BROWSER + VERIFIER son obligatorios.

VER → USAR → COMPARAR → CORREGIR → VERIFICAR hasta aceptación 100%.

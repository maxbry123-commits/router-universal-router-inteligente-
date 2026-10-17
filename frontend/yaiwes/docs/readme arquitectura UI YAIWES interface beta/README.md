# Arquitectura UI YAIWES interface · beta

Repo: [maxbry123-commits/frontend](https://github.com/maxbry123-commits/frontend) · branch `main`  
Raíz viva: `UI YAIWES interface/`  
Skill padre: `Skills arquitectura frontend Yaiwes/`

**Aprobado 2026-09-08:** anotar primero. **No fabricar las 39** hasta `OK` por ID.  
**5 partes.** Una ventana por salida.

## Tokens FROMTED (ley)

| Token | Valor | Uso |
|-------|--------|-----|
| Matte bg | `#000000` / `#0a0a0d` / `#141417` | superficie |
| Little | `#2563eb` | selección / acento UI |
| Blanco | `#ffffff` | texto primario |
| Naranja | `#ff5500` | **solo Cargar / Descargar** |

Fotos HUD naranja (Anthropic/grafos) = referencia de **layout**, no paleta.

## Cuenta 39 (forense, 16 pasadas)

| Grupo | N | Source HTML | Estado |
|-------|---|-------------|--------|
| Fotos lote | 14 (+1 dup Marte) | NO | motivos, no ventanas |
| Grok Bot | 1 | NO (app x.ai/bot) | réplica-cáscara |
| Run.html | 8 | SÍ | partir 1:1 |
| Crazy Wall v4 | 16 | SÍ | partir + simplificar |
| **Suma** | **39** | **24 con HTML** | |

**Fuera de los 39 (archivos extra):** mini-anim agentes (20), anim estados (12), fondos animados, pensamiento.

## 5 partes (orden aprobado)

1. **P1 Run 8** — HTML tuyo, cero invención. IDs `RUN-01`…`RUN-08`.
2. **P2 Crazy Wall 16** — HTML tuyo, menos fricción. IDs `WALL-01`…`WALL-16`.
3. **P3 Grok Bot 1** — cáscara FROMTED, no binario xAI. ID `GBOT-01`.
4. **P4 14 fotos** — motivos metidos en ventanas ya aprobadas. No 14 apps.
5. **P5 Anims** — archivos aparte, se enchufan. No van pegados.

## Método anti-alucinación

1. Tú subes HTML / zip / foto.  
2. `01-original/` = **idéntico**, sin tocar.  
3. `02-fromted/` = el mismo, **solo colores/estética FROMTED**.  
4. Te muestro original vs FROMTED.  
5. Tú `OK <ID>`.  
6. Entonces GitHub + foto + línea README + Crazy Wall `state.json`.  
7. **1 ID por mensaje** (máx 2 si lo pides).

Si no hay archivo subido → **no invento** esa ventana.

## Cableado

- Fábrica UI (interna, 0 fricción, usuario no entra): `Skills arquitectura frontend Yaiwes/fabrica-ui-interface/`
- Biblioteca FE: `Skills arquitectura frontend Yaiwes/biblioteca code frontend Maxbry Yaiwes/`
- Biblioteca BE: `Skills arquitectura frontend Yaiwes/biblioteca-backend/`
- Este proyecto UI: `UI YAIWES interface/`

## Run 8

| ID | Ventana |
|----|---------|
| RUN-01 | CASCADE |
| RUN-02 | TREN |
| RUN-03 | AUDITOR |
| RUN-04 | VENTANAS V-01…V-04 |
| RUN-05 | ORQUESTA |
| RUN-06 | panel Sandbox |
| RUN-07 | panel Codigo YAML |
| RUN-08 | panel nodo / input / out |

## Crazy Wall 16

| ID | Superficie |
|----|------------|
| WALL-01 | Tab Bloques |
| WALL-02 | Tab Árbol |
| WALL-03 | Tab Archivos |
| WALL-04 | Modo Preguntar |
| WALL-05 | Modo Tap archivo |
| WALL-06 | Modo Tap bloque |
| WALL-07 | 6 raíces |
| WALL-08 | Grid bloques (`00`–`25` = **26** claves; UI dice 25, off-by-one) |
| WALL-09 | Lista archivos |
| WALL-10 | Sheet bloque |
| WALL-11 | Sheet archivo |
| WALL-12 | Sheet raíz |
| WALL-13 | Sheet extra |
| WALL-14 | Añadir raíz |
| WALL-15 | Barra Guardar / Share |
| WALL-16 | `state.json` bitácora |

## IDs aprobados para fabricar

**Ninguno.** Aprobado: método + carpeta + 5 partes + conteo 39.

Siguiente: `1 CASCADE` o `OK RUN-01`.


## 39 ventanas SUBIDAS (2026-09-09)

Carpeta: `Ui Yaiwes interface beta/02-fromted/` (39 HTML + HOST).
Fichas: `02-fromted/FICHAS/<ID>.json`.
Índice: `02-fromted/INDEX.json`.
Host Lego: `02-fromted/HOST.html`.
Plan: `PLAN-39-Y-FABRICA.md`.
Fábrica DAG: `fabrica de UI INTERFACE fromtend/componentes para fabrica de interface/PLAN-DAG-DETERMINISTA.json`.
Seguridad: `UI YAIWES interface/seguridad/`.
Empaque: `UI YAIWES interface/empaque/`.

Estado: **SUBIDO-FROMTED-SPLIT**. `03-producto` vacío hasta `OK <ID>`.
Original intacto en `01-original/`.

## Extensión — imágenes del proyecto

Ruta canónica para subir imágenes originales del proyecto:

`UI YAIWES interface/Ui Yaiwes interface beta/01-original/FOTOS-REF/`

Enlace directo de carga:
https://github.com/maxbry123-commits/frontend/upload/main/UI%20YAIWES%20interface/Ui%20Yaiwes%20interface%20beta/01-original/FOTOS-REF

Reglas:
- las imágenes originales se conservan sin modificar en `01-original/FOTOS-REF/`;
- no reemplazar una imagen original silenciosamente;
- usar nombres claros y estables para que puedan citarse desde README, fichas y evidencias;
- cualquier versión transformada o FROMTED debe vivir fuera de `01-original/`;
- subir primero la imagen y después enlazarla desde la documentación o la ventana correspondiente.

Flujo:
`SUBIR IMAGEN -> 01-original/FOTOS-REF -> REFERENCIA README/FICHA -> TRANSFORMACIÓN FROMTED SI APLICA -> VALIDACIÓN`

## Nota de arquitectura — Backend + Frontend + Diseño

Documento conectado:
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/NOTA-ARQUITECTURA-BACKEND-FRONTEND-Y-DISENO.md

Carpeta para nuevas actualizaciones de arquitectura:
https://github.com/maxbry123-commits/frontend/tree/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/actualizaciones%20arquitectura

Enlace directo para subir el próximo archivo de arquitectura/diseño:
https://github.com/maxbry123-commits/frontend/upload/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/actualizaciones%20arquitectura

Evidencias visuales conectadas:
- Fotos parte 1: https://github.com/maxbry123-commits/frontend/commit/13f4e932866284fb5ddfaaf6ada5ce4809f82f46
- Fotos parte 2: https://github.com/maxbry123-commits/frontend/commit/c50fc98d19debe1a85817cf1129b55a99c895c9f
- Fotos parte 3: https://github.com/maxbry123-commits/frontend/commit/430809bd98c614435ad7597493ed46c16d6552a3

Flujo documental:
`README -> NOTA BACKEND/FRONTEND/DISEÑO -> ARCHIVO NUEVO DE ARQUITECTURA -> FOTOS -> IMPLEMENTACIÓN -> VALIDACIÓN`

## Arquitectura frontend consolidada — 2026-09-27

Alcance de esta actualización: **solo frontend**. El backend se conserva únicamente como frontera contractual para enviar acciones y recibir eventos/resultados.

Arquitectura frontend V1:
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/ARQUITECTURA-FRONTEND-UI-YAIWES-V1.md

Handoff frontend:
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/HANDOFF-FRONTEND-UI-YAIWES-2026-09-27.md

Fuentes nuevas leídas y conectadas:
- Sistema componentes/plugins fábrica: https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/actualizaciones%20arquitectura/sistema%20de%20componente%20tipo%20plugins%20para%20la%20f%C3%A1brica%20y%20yaiwes%F0%9F%9A%80%F0%9F%86%98%F0%9F%86%98con%20los%20componentes%20necesarios%20y%20como%20funciona%F0%9F%93%B2no%20tocar%20%E2%9A%A0%EF%B8%8F.md
- Arquitectura completa backend+frontend: https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/actualizaciones%20arquitectura/%F0%9F%93%B2%F0%9F%93%8C%F0%9F%9A%80%F0%9F%93%B2%F0%9F%93%B2%20UI%20YAIWES%20INTERFACE%20VERSI%C3%93N%201.0%20FINAL%20%F0%9F%93%8C%F0%9F%9A%80%F0%9F%93%B2%20Con%20backend%20frontend%20y%20URL%20visible%20...a%20y%20dise%C3%B1o%20para%20backend%20y%20frontend%20todo%20%E2%9B%94no%20tocar%20%F0%9F%94%A8%F0%9F%93%8C.md
- Plan ejecutable frontend: https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/actualizaciones%20arquitectura/%F0%9F%93%B2%F0%9F%93%B2%20UI%20YAIWES.%20fromtend%20plan%20de%20ejecuci%C3%B3n%20todo%20%20no%20tocar.md

Evidencia visual:
- Fotos parte 1: https://github.com/maxbry123-commits/frontend/commit/13f4e932866284fb5ddfaaf6ada5ce4809f82f46
- Fotos parte 2: https://github.com/maxbry123-commits/frontend/commit/c50fc98d19debe1a85817cf1129b55a99c895c9f
- Fotos parte 3: https://github.com/maxbry123-commits/frontend/commit/430809bd98c614435ad7597493ed46c16d6552a3

Microflujo canónico:
`USUARIO -> PANEL A/B -> CONTRATO UI -> ACTION BUS -> BRIDGE -> BACKEND (frontera) -> EVENTO/RESULTADO -> CANVAS/WINDOW`

Plan frontend consolidado:
- Salida 1: Fundación — 11 nodos.
- Salida 2: Panel A — 10 nodos.
- Salida 3: Panel B — 12 nodos.
- Salida 4: voz/offline/sync cliente — 10 nodos.
- Salida 5: empaque/a11y/i18n/design/QA — 12 nodos.
- **Total corregido: 55 nodos.** Los archivos fuente indican 45 en el cierre, pero 11+10+12+10+12 = 55.

Regla de continuidad: los tres archivos fuente marcados `no tocar` permanecen intactos; cualquier implementación nueva debe partir de la arquitectura frontend consolidada y cerrar con wiring + test + evidencia.

## Actualización — PANEL-01 / CHAT-01 — inventario completo de controles — 2026-09-27

Se incorpora oficialmente al plan de arquitectura el inventario consolidado del chat, cruzado con `FOTOS-REF` y con las instrucciones originales de `Maxbry web/Readme arquitectura Maxbry web.md`.

Documento detallado:
https://github.com/maxbry123-commits/frontend/blob/main/UI%20YAIWES%20interface/readme%20arquitectura%20UI%20YAIWES%20interface%20beta/actualizaciones%20arquitectura/ACTUALIZACION-PANEL-01-CHAT-CONTROLES-Y-SELECTORES-2026-09-27.md

Reglas nuevas del plan:

- PANEL-01/CHAT-01 pasa a tener un **inventario de 60 acciones/capacidades de chat**, no 60 botones simultáneos.
- Mantener **10–15 controles persistentes visibles** y agrupar el resto en `+`, Modelo, Modo, Workflow, Agente y `•••`.
- Persistentes base: `+`, Thinking, Modelo, Modo, Micrófono, Enviar, Documento, Website, Imagen y Audio.
- Modelo debe soportar **9 AI + 3 AGI** desde registry/configuración; la UI no inventa nombres faltantes.
- Los seleccionables parten blanco/gris y pasan a **Little azul `#2563eb`** al quedar activos.
- Cada control requiere `actionId -> Action Bus -> bridge/plugin -> backend frontera -> evento -> StateStore`.
- Acción no registrada o bridge ausente = **fail-closed**; nunca fabricar respuesta.
- Salida obligatoria: HTML funcional de referencia + código modular + assets + dependencias + manifest + tests + versión.
- Gate: no integración hasta `OK PANEL-01-CHAT`.

Microflujo:

`REFERENCIAS -> INVENTARIO CHAT -> AGRUPACIÓN -> HTML FUNCIONAL -> FUENTE MODULAR -> ACTION BUS -> BRIDGE/PLUGIN -> QA -> OK -> INTEGRACIÓN`

## Integración canónica de Skills — 2026-09-27

Auditoría física cerrada sobre las dos raíces:

- `UI YAIWES interface/`: 10 `SKILL.md`.
- `fabrica de UI INTERFACE fromtend/`: 41 `SKILL.md`.
- Total: **51 archivos físicos / 39 familias lógicas** tras mirrors/alias.

Documentos canónicos:

- Registry máquina: `actualizaciones arquitectura/SKILL-REGISTRY-UI-YAIWES-2026-09-27.json`.
- Handoff: `actualizaciones arquitectura/HANDOFF-SKILLS-UI-YAIWES-2026-09-27.md`.
- Plan: `actualizaciones arquitectura/PLAN-ACCION-SKILLS-UI-YAIWES-2026-09-27.md`.

Regla: **presencia != activación**. Skills de donors quedan `DONOR_SCOPED`; sólo un adapter probado puede promoverlos.

Microflujo:

`TASK -> SkillResolver -> FROMTED policy -> skill de superficie -> tool/component -> browser/device -> QA -> evidence -> PASS/FAIL`
## Skills — handoff canónico 2026-09-27

Fuente única de planificación:
`actualizaciones arquitectura/HANDOFF-SKILLS-UI-YAIWES-2026-09-27.md`

Plan:
`actualizaciones arquitectura/PLAN-ACCION-SKILLS-UI-YAIWES-2026-09-27.md`

Alcance:
- 10 SKILL.md físicos verificados en `UI YAIWES interface/`;
- catálogo de fábrica incorporado desde el índice entregado por el Director, sin reescaneo de fábrica en esta actualización;
- donor skills permanecen `DONOR_SCOPED` hasta adapter+test;
- `PANEL-01-CHAT` usa la cadena: Image-to-Code → frontend-design → build → Impeccable → visual/a11y QA → Playwright → evidencia.

Regla: `skill != tool != plugin`; el skill orienta, el componente/tool ejecuta, Action Bus gobierna las acciones.

## Método ejecutable para cualquier IA — 2026-09-27

Entrada: `UI YAIWES interface/AGENTS.md`.

Gobierno: `Schema -> Contract -> Sheriff -> Validator -> Codex -> Browser -> Meta Review -> Sentinel -> Verifier -> Guardian`.

Método: `readme arquitectura UI YAIWES interface beta/METODO-DE-TRABAJO.md`.  
Workflow: `workflow/`. Skills nativos: `skills/`. QA Playwright: `qa/`.


# Actualización arquitectura — PANEL-01 / CHAT-01 — controles y selectores

Fecha: 2026-09-27  
Estado: `PLAN / SOURCE-OF-TRUTH`  
Alcance: **solo chat** de UI YAIWES. No incluye navegación general de la web, Panel A, Canvas, Inspector, proyectos, archivos ni otras ventanas.

## 1. Fuentes consolidadas

Esta actualización cruza:

1. `UI YAIWES interface/Ui Yaiwes interface beta/01-original/FOTOS-REF/`.
2. `📌p01-chat-minimax.html`.
3. `p04-sheet-agregar.html`.
4. `p05-sheet-herramientas.html`.
5. `p09-mode-dropdown.html`.
6. Más de 50 imágenes del lote `F001...` revisadas para patrones de chat.
7. `Maxbry web/Readme arquitectura Maxbry web.md` — BLOQUE A, punto 2 CHAT.
8. `Maxbry web/memoria grock.md` — lock: “CHAT: MiniMax + 9 AI + 3 AGI + todos los accesos listados por el Director”.
9. Skill de diseño UI YAIWES: Matte/Little, actionId conocido, fail-closed y cableado posterior por contrato.

## 2. Regla de composición

No mostrar todas las capacidades simultáneamente.

```text
CHAT VISIBLE
────────────────────────────────────
[ conversación ]

┌──────────────────────────────────┐
│ Escribe o usa / para skills      │
│                                  │
│ + Thinking Modelo▾ Modo▾ Mic ↑   │
└──────────────────────────────────┘

Documento · Website · Imagen · Audio

SECUNDARIO
+ → herramientas/medios/capacidades
Modelo▾ → 9 AI + 3 AGI
Modo▾ → razonamiento/especialistas/Expert/Fast/Heavy/Auto
Workflow▾ → loops/watchdogs/investigación/workflows
Agente▾ → YAIWES/CODE/NCT/roles/skills
••• → acciones de conversación
```

Objetivo: **10–15 controles persistentes visibles** y el resto bajo desplegables/sheets. La cifra “60” describe el inventario de acciones/capacidades del chat, no 60 botones simultáneos.

## 3. Inventario consolidado del chat

1. Agregar `+`.
2. Thinking / razonamiento.
3. Selector de 9 modelos AI.
4. Selector de 3 modelos AGI.
5. Selector de modo Heavy / Expert / Fast / Auto.
6. Enviar.
7. Micrófono / voz.
8. Cámara.
9. Fotos / galería.
10. Archivos.
11. Video.
12. Documento.
13. Website / web.
14. Imagen.
15. Audio.
16. Búsqueda web.
17. Investigación.
18. Investigación en profundidad.
19. Conectores.
20. Plugins.
21. Galería.
22. Automatización.
23. Construcción.
24. Agente YAIWES.
25. Selector de 5 sistemas CODE.
26. NCT CODE / Swarm.
27. App.
28. Web builder.
29. Selector de 12 módulos de habilidades.
30. Selector de 5 módulos web.
31. Memoria.
32. Proyectos.
33. Selector de 12 sistemas/niveles de intensidad de razonamiento.
34. Selector de 8 especialidades.
35. Selector de 8 sistemas de expertos.
36. Selector adicional de intensidad de 8 niveles.
37. Selector de 12 sistemas de trabajo Loop.
38. Selector de 5 sistemas Watchdog.
39. Selector de 10 sistemas de investigación avanzada.
40. Selector de 10 workflow / tareas especializadas.
41. Selector de 4 sistemas de proyectos.
42. Selector de 8 proyectos de negocios/comercialización.
43. Selector de 3 sistemas de personalización AI.
44. Selector de 3 sistemas de roles.
45. Selector de 3 sistemas de System Prompt.
46. Ciclo de trabajo AI: investigación/objetivos/planificación/tareas/revisión/ejecución/resultados.
47. Videos.
48. Películas.
49. Almacenamiento local.
50. Sistema de agente con 16 especialidades.
51. Skills/bibliotecas con 10 especialidades.
52. Agregar al proyecto.
53. Acceso a herramientas.
54. Usar estilo.
55. Habilitar todo.
56. Crear imagen.
57. Crear video.
58. Artefactos.
59. Aprende.
60. Detener / cancelar ejecución.

### Nota de fuente

El texto de `Maxbry web/Readme arquitectura Maxbry web.md` dice “6 sistemas de investigación objetivos planificación tareas revisión ejecución resultados”, pero enumera siete conceptos. Esta actualización **no corrige esa contradicción**; queda marcada para decisión del Director.

## 4. Controles persistentes propuestos

Persistentes del compositor:

- `+` Agregar.
- Thinking.
- Modelo `▾`.
- Modo `▾`.
- Micrófono.
- Enviar.
- Documento.
- Website.
- Imagen.
- Audio.

Opcionales persistentes por estado:

- Detener/cancelar cuando `queued/running`.
- indicador de estado textual.

No persistentes:

- Cámara/Fotos/Video/Archivos.
- herramientas avanzadas.
- selectors de especialistas/workflows/agentes.
- acciones de conversación.

## 5. Agrupación obligatoria

### A. `+` Agregar al chat

- Cámara.
- Fotos.
- Video.
- Archivos.
- Investigación.
- Investigación en profundidad.
- Búsqueda Web.
- Agregar al proyecto.
- Usar estilo.
- Acceso a herramientas.
- Conectores.
- Plugins.
- Galería.
- Memoria.
- Habilitar todo.
- Crear imagen.
- Crear video.
- Artefactos.
- Aprende.

### B. Modelo

- 9 modelos AI.
- 3 modelos AGI.

Los nombres finales de los 12 modelos se toman del registry/configuración del proyecto; la vista no debe inventarlos si el registry aún no los define.

### C. Modo / razonamiento

- Heavy.
- Expert.
- Fast.
- Auto.
- 12 sistemas/niveles de intensidad de razonamiento.
- 8 especialidades.
- 8 expertos.
- 8 niveles de intensidad.

### D. Workflow

- 12 Loops.
- 5 Watchdogs.
- 10 sistemas de investigación avanzada.
- 10 workflows/tareas especializadas.
- 4 sistemas de proyectos.
- 8 sistemas de negocio/comercialización.
- ciclo investigación → objetivos → planificación → tareas → revisión → ejecución → resultados.

### E. Agente / capacidades

- YAIWES.
- 5 sistemas CODE.
- NCT CODE / Swarm.
- App.
- Web builder.
- 12 módulos de habilidades.
- 5 módulos web.
- 3 personalizaciones AI.
- 3 roles.
- 3 System Prompt.
- sistema de agente con 16 especialidades.
- skills/bibliotecas con 10 especialidades.
- almacenamiento local.

## 6. Estados visuales

Tokens:

- fondo Matte: `#0a0a0d`;
- surface: `#141417`;
- panel: `#1a1a1e`;
- card: `#202025`;
- border: `#2a2a33`;
- texto: `#ffffff`;
- Little: `#2563eb`;
- naranja: `#ff5500` **solo Cargar/Descargar**.

Comportamiento:

- control no seleccionado = blanco/gris;
- seleccionado = texto/borde/fondo Little azul;
- `aria-pressed=true` o `aria-selected=true` debe coincidir con estado lógico;
- hover/focus/selected/disabled visibles;
- no depender solo del color: añadir check, texto o estado cuando aplique.

## 7. Contrato funcional

Cada control debe tener:

```text
control
→ actionId
→ payload tipado
→ Action Bus
→ bridge/plugin
→ backend (frontera)
→ evento/resultado
→ StateStore
→ rerender
```

Reglas:

- cero controles muertos;
- acción no registrada = `action_missing` y fail-closed;
- sin bridge = no fabricar respuesta de IA;
- frontend no llama directamente a proveedores;
- modelos/capacidades se leen de registry/configuración;
- estado persistente solo cuando el contrato lo requiera.

## 8. actionId mínimos

```text
chat.send
chat.cancel
chat.attach
chat.voice.start
chat.voice.stop
mode.thinking.toggle
model.select
agi.select
mode.select
tool.document.toggle
tool.website.toggle
tool.image.toggle
tool.audio.toggle
tool.camera.open
tool.gallery.open
tool.video.open
tool.file.open
tool.web.toggle
tool.research.toggle
tool.deep_research.toggle
tool.connectors.open
tool.plugins.open
tool.project.select
tool.style.select
tool.access.select
workflow.select
agent.select
skill.select
memory.toggle
storage.select
```

Los actionId adicionales deben provenir del manifest/registry y no inventarse en la vista.

## 9. Formato de entrega obligatorio

```text
Diseño/Manus
→ HTML funcional de referencia
→ proyecto fuente modular
→ assets
→ manifest
→ tests
→ versión
→ continuar edición
```

Para React/Vite:

```text
PANEL-01-CHAT/
├── index.html
├── package.json
├── vite.config.js
├── src/
│   ├── App.jsx
│   ├── main.jsx
│   ├── components/
│   │   ├── ChatPanel.jsx
│   │   ├── ChatComposer.jsx
│   │   ├── ModelSelector.jsx
│   │   ├── ToolButton.jsx
│   │   └── MessageList.jsx
│   ├── styles/
│   └── assets/
├── manifest.json
├── ACCEPTANCE.md
├── README.md
├── tests/
└── snapshot/index-reference.html
```

## 10. Gate de aceptación PANEL-01

PASS solo si:

- controles visibles corresponden a la referencia;
- capacidades secundarias están agrupadas y no saturan la UI;
- botones/toggles seleccionados cambian a Little azul;
- selectores abren/cierran/seleccionan/persisten cuando aplique;
- ningún botón está muerto;
- teclado/touch/mouse funcionan;
- 0 errores de consola;
- 0 assets faltantes;
- bridge/plugin listo por contrato;
- backend sigue fuera de la vista;
- HTML funcional + fuente modular + assets + dependencias + versión;
- no se integra al producto hasta `OK PANEL-01-CHAT`.

## 11. Microflujo canónico

`REFERENCIAS + MAXBRY WEB -> INVENTARIO CHAT -> AGRUPACIÓN -> PROTOTIPO HTML -> REACT/VITE MODULAR -> ACTION BUS -> BRIDGE/PLUGIN -> QA -> OK PANEL-01-CHAT -> INTEGRACIÓN`

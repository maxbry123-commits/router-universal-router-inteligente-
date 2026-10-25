---
name: fromted-yaiwes-perfil-visual
version: 0.1.0-review
status: PROPUESTA_PARA_APROBACION
language: es
product: FROMTED / YAIWES
primary_theme: little
---

# SKILL MAESTRO — Perfil visual FROMTED × YAIWES (borrador de aprobación)

## Resumen y objetivo

Unificar en **un solo SKILL principal** las instrucciones de diseño, componentes, interacciones y trabajo de FROMTED/YAIWES. La interfaz cambia de apariencia, pero no cambia sus funciones ni sus conexiones.

**Microflujo:** PETICIÓN → REFERENCIAS → TEMA → COMPONENTES → INTERACCIONES → VALIDACIÓN → ENTREGA.

**Principal:** `little` (carbón cálido, textos beige y terracota). Se conserva intacto su color oficial `#C65D3B`.

> IMPORTANTE: el material original protege tres paletas inmutables (`matte`, `little`, `blanco`). Por petición actual del Director, se han añadido tres **variantes de muestra** (`crystal`, `orange`, `blue`) en un archivo aparte. **No se ha modificado** la ley inmutable ni los archivos de entrada. Estas variantes no son canónicas hasta que se aprueben. Esta versión es un perfil en revisión, no un desbloqueo de los originales.

## 1. Inventario de apariencias

| ID | Nombre | Naturaleza | Fondo | Tarjeta | Texto principal | Selección / énfasis | Regla visual |
|---|---|---|---|---|---|---|---|
| `little` | **Little · PRINCIPAL** | Original, canónico | `#1C1B1A` | `#2A2927` | `#F5F4F0` | `#C65D3B` | CTA principal terracota; prohibido mezclar azul/naranja Grok. |
| `matte` | Negro mate / grises | Original, canónico | `#0a0a0d` | `#202025` | `#e4e4e7` | `#2563eb` | Azul solo selección; `#ff5500` solo texto Cargar/Descargar. |
| `crystal` | Cristal holográfico | **Propuesta** | `#0c1421` | `rgba(242,250,255,.095)` | `#e6f4ff` | `#b8f5fa` | Transparencia, desenfoque y acentos fríos suaves. |
| `orange` | Naranja y negro | **Propuesta** | `#100e0d` | `#26211d` | `#f5e9df` | `#ef823c` | Negro cálido con acento naranja. |
| `blue` | Tonos azules | **Propuesta** | `#0a1424` | `#192c45` | `#e1edfa` | `#66b7ff` | Azul oscuro con azules claros para destacar. |
| `blanco` | Blanco y negro + detalle azul | Original, canónico | `#f4f4f5` | `#ffffff` | `#3f3f46` | `#2563eb` | Texto gris, selección y enlace Descargar azules. |

La lista anterior cubre las **seis referencias visuales** nombradas por el Director. Los cuatro perfiles de exploración principales (`little`, `matte`, `crystal`, `orange`) se complementan con los perfiles `blue` y `blanco` también solicitados. No se debe interpretar esta tabla como permiso automático para reescribir los tokens originales.

**Jerarquía Little canónica adicional:** `--card-hover:#353330`, `--border:rgba(255,255,255,.1)`, `--text-secondary:#A8A29E`, `--text-tertiary:#9C9590`, `--accent-hover:#b05031`, `--accent-light:rgba(198,93,59,.15)`.

## 2. La forma no cambia al cambiar de color

- Radio de marco móvil: **24 px** (solo emulación escritorio; móvil real ocupa ancho completo).
- Radio de tarjeta: **12 px**.
- Radio de botón: **10 px**.
- Radio superior de ventana inferior: **28 px**.
- Tipografía de producto: `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`.
- Tamaños: título 16 px, nombre 14 px, metadata 12 px, descripción 11 px; iconos de línea 14/16 px según contexto.
- Roles compartidos: `title`, `name`, `meta`, `sub`, `card`, `btn-primary`, `btn-secondary`, `btn-link`, `sheet`, `tab`, `selected`.
- **Operator interno** conserva su identidad independiente (carbono + lime `#d9ff43` + IBM Plex Mono); nunca importar ese acento de marca al tema Little de producto.

**Microflujo:** UN TEMA ACTIVO → TOKENS CSS → COMPONENTES COMUNES → ESTADOS VISUALES.

## 3. Componentes que el agente puede componer

Componentes existentes en el catálogo recibido: marco móvil, status bar, cabecera, pestañas superiores, tarjeta/fila, búsqueda, botones, bottom sheet, selector de modo, cuadrícula de acciones, navegación inferior, interruptor, progreso, estado vacío y notificación toast. Los HTML entregados ilustran además panel de rutas, explorador de archivos, árbol de raíces y flujo horizontal de Crazy Wall.

**Microflujo de las pantallas de ejemplo:**

- `CHAT`: CABECERA → MODO (RÁPIDO/PENSAR/EQUILIBRADO) → COMPOSER → MENSAJE → ACCIONES.
- `ARCHIVOS`: BÚSQUEDA → LOCAL/ANCLADOS → LISTADO → ANCLAR/DESCARGAR → FEEDBACK.
- `CRAZY WALL`: INPUT → MISIÓN → KERNEL → WORDFLOW → EVIDENCIA → OUT → FICHA DETALLE.
- `CONFIGURACIÓN`: PREFERENCIAS → TOGGLES → CAMBIO VISUAL → CONFIRMAR.

La demo no implementa backend ni afirma ejecutar workflows reales del Router: las vistas Crazy Wall y Chat son estados locales etiquetados como demostración.

## 4. Instrucciones para cualquier agente que use este SKILL

1. **Recepción:** reunir HTML, capturas, MD, JSON, ZIP y el repositorio indicado. Si falta un recurso real, registrar `UNKNOWN`, no inventarlo.
2. **Forensic X-Ray:** clasificar cada archivo como interfaz producto, Operator interno, backend o referencia obsoleta. Registrar ruta y evidencia.
3. **Selección:** elegir `little` por defecto para el perfil visual nuevo. Para aplicar cualquiera de los otros temas, debe existir selección explícita. Las variantes propuestas requieren aprobación antes de declararse oficiales.
4. **Preservación:** copiar estructura y comportamiento existentes. Cambiar solo los estilos aprobados. **No** cambiar IDs, event handlers, endpoints, rutas, datos ni flujos. Si hay código ajeno, reutilizarlo en vez de inventarlo.
5. **Separación:** en producción usar **1 ventana = 1 archivo; 1 función = 1 módulo**. El HTML monolítico adjunto a este SKILL es exclusivamente una **demo autocontenida de aprobación visual**.
6. **Interactividad:** los botones de pestaña abren panel, los sheets abren y cierran, la búsqueda filtra, selección aplica estados, toggles responden, los botones muestran feedback. Distinguir demo local de puente API real.
7. **Internacionalización:** UI de producción con claves `es`, `en`, `fr`, `pt`; `es` por defecto. No dejar cadenas literales en componentes finales. El archivo HTML demostrativo está en español para revisar diseño.
8. **Backend:** si existe, separar e identificar `BACKEND`. Prohibido retocar visualmente el backend o fingir que está conectado.
9. **Entrega:** comparar contra fuentes, hacer checklist visual, interacción y rutas. Mostrar screenshot/código, archivos y resultado de pruebas. No anunciar `DONE` sin evidencia.

**Microflujo transversal:** OBJETIVO → AUDITAR FUENTES → ELEGIR TEMA → COMPONER UI → CABLEAR INTERACCIÓN → REVISAR → EVIDENCIA → APROBAR.

## 5. Política de trabajo y trazabilidad

- Mantener originales intactos y registrar diferencias por archivo. Evitar reescritura global innecesaria.
- Para entregas de producción, tomar un lote explícito, verificar todas las piezas y hacer cross-check antes de integrar. El parche de recuperación recibido describe lotes de 10 archivos; no aplicar esa regla de lote a esta demostración aislada.
- Mantener `state`, bitácora y handoff de cada fase si el trabajo se realiza dentro del repositorio. No publicar modificaciones de repositorio sin una orden explícita.
- No confundir React/HTML de ejemplo con DAG real, API real o modelos ejecutados: interfaces de demo son solo interfaz.

## 6. Fuentes de verdad y precedencia

1. Solicitudes explícitas actuales del Director, para determinar la demo a revisar.
2. `01-DESIGN-TOKENS-THEMES-IMMUTABLE.md`: los **tres** juegos de colores originales, con valores exactos y restricciones.
3. `02-UI-COMPONENT-CATALOG-SKILL.md`: geometría, patrones de presentación y componentes.
4. `03-FUNCTIONAL-INTERACTION-SKILL.md`: patrones de acciones/estado y pruebas.
5. `04-AGENT-PROTOCOL-SKILL.md`: protocolo de agentes y prohibiciones.
6. `FROMTED-ARCHITECTURE-AND-DESIGN-BASE.md` y `FROMTED-FRONTEND-IMMUTABLE-LAW.json`: módulos y reglas de trabajo.
7. HTML y capturas adjuntas: `Run.html`, `📲👨‍💻📳📱🖥️Run UI YAIWES.html`, `YAIWES-CRAZY-WALL*.html`, capturas Grok; referencias de estructura y comportamiento, no licencia para mezclar colores canónicos.
8. `DESIGN-LOCK.json`: **otra** identidad visual de Operator interno; no mezclar sus colores con el producto.
9. `PARCHE-RECUPERACION-XRAY-FROMTED-YAIWES.md`: instrucciones de preservación, arquitectura modular y evidencia.

En caso de conflicto de estilo en temas originales, gana el juego exacto de `01`; para `crystal`, `orange` y `blue`, se usa provisionalmente la demo HTML hasta que el Director apruebe los valores.

## 7. Contrato de aceptación del perfil

- [ ] Little predeterminado, fiel a los HEX originales.
- [ ] Los seis estilos se pueden alternar sin alterar diseño, contenido ni acciones.
- [ ] Matte y Blanco conservan sus restricciones de acento.
- [ ] Tarjetas, pestañas, archivos, Crazy Wall y bottom sheet utilizables.
- [ ] Android y escritorio sin cortes de contenido.
- [ ] HTML de revisión funciona localmente (sin servidor / sin API).
- [ ] Producción futura: paneles y funciones separados, i18n completo, backend identificado.
- [ ] El Director acepta o ajusta la paleta y las formas antes de emitir `DESIGN LOCK` definitivo.

**Archivo de vista previa:** `YAIWES-PERFIL-VISUAL-DEMO.html`.

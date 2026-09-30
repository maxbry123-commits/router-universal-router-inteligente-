---
name: fromted-yaiwes-frontend-factory
version: 0.2.0-review
status: PENDIENTE_APROBACION_VISUAL
language: es
primary_theme: little
supported_themes: [little, matte, crystal, orange, blue, blanco, gris]
source_status: originales_preservados
---

# SKILL MAESTRO — Arquitectura, diseño y verificación FROMTED × YAIWES

## 0. Propósito

Un único punto de entrada para cualquier IA o desarrollador que deba **recibir referencias, construir interfaces editables, conectar comportamiento, probarlas en navegador y entregar evidencia**. No es una autorización para reemplazar los componentes reales o inventar un diseño paralelo. **Little es el perfil principal**.

**Microflujo global:** PETICIÓN → REFERENCIA REAL → CONTEXTO REPO → SKILLS → IMPLEMENTAR → BROWSER → VERIFICAR → CORREGIR ↺ → ENTREGAR.

**Norma NO MOCK:** el frontend entregado debe manejar interacciones reales de su propio dominio. Está prohibido fingir mensajes de IA, API, ejecución de DAG, archivos o transferencias. Si el backend no existe, mostrar `BRIDGE_MISSING` o error real y **no fabricar una respuesta**. Los datos de ejemplo, si se usan, se identifican como *referencia editable local*, nunca como estado verificado.

## 1. Precedencia de trabajo y contexto

Leer en este orden ANTES de cambiar código:

1. **Referencia real:** Figma, capturas, frontend existente, HTML y design system. No imaginar pantallas ya representadas.
2. **Contexto del repositorio:** árbol, `AGENTS.md`, `SKILL.md`, contratos, componentes y módulos existentes.
3. **SKILLS originales:** `01-DESIGN-TOKENS-THEMES-IMMUTABLE.md`, `02-UI-COMPONENT-CATALOG-SKILL.md`, `03-FUNCTIONAL-INTERACTION-SKILL.md`, `04-AGENT-PROTOCOL-SKILL.md`.
4. **Archivos reales del proyecto:** código HTML/CSS/JS, componentes React, registros de acciones, rutas y recursos.
5. **Instrucciones actuales del usuario:** alcance, estilo, comportamiento, aprobaciones explícitas y límites.

**Política de fuentes:** referencias y repos fijan la estructura; skills fijan reglas canónicas; instrucción explícita del propietario autoriza variaciones nuevas. Reusar componentes/handlers existentes; la **invención por IA es el último recurso** y debe identificarse. Si faltan archivos, indicar `UNKNOWN` y solicitar la referencia concreta, no atribuir funciones sin evidencia.

## 2. Sistema de temas visuales

### Tres perfiles originales canónicos: no reescribir sus tokens

| Tema | Fondo | Card | Texto | Regla de acento |
|---|---|---|---|---|
| `little` **PRINCIPAL** | `#1C1B1A` | `#2A2927` | `#F5F4F0`, secundario `#A8A29E` | terracota `#C65D3B` **solo CTA primario** |
| `matte` | `#0a0a0d` | `#202025` | `#e4e4e7`, `#a1a1aa` | azul `#2563eb` selección; naranja `#ff5500` solo texto Cargar/Descargar |
| `blanco` | `#f4f4f5` | `#ffffff` | `#18181b`, `#3f3f46` | azul `#2563eb` selección/Descargar; texto del cuerpo no negro puro |

### Cuatro perfiles NUEVOS de muestra (requieren aprobación)

| Tema | Fondo | Card | Texto | Acento |
|---|---|---|---|---|
| `crystal` Cristal holográfico | `#0c1421` | `rgba(242,250,255,.095)` | `#e6f4ff` | `#b8f5fa` |
| `orange` Naranja/negro | `#100e0d` | `#26211d` | `#f5e9df` | `#ef823c` |
| `blue` Azules | `#0a1424` | `#192c45` | `#e1edfa` | `#66b7ff` |
| `gris` Grises sin superficies negras | `#969ba2` | `#d6d9de` | `#252932`, secundarios `#484f59`, botones blancos | `#303740` |

`gris` usa un gris medio para el lienzo, gris claro para tarjetas, gris oscuro para texto, gris para metas y blanco para botones/textos inversos. **No usar `#000000` como fondo en este perfil.** Puede mostrar tarjetas de otros perfiles *dentro del selector* a modo de miniaturas; eso no cambia el tema activo.

**Geometría original:** marco móvil 24px (solo preview de escritorio); tarjeta 12px (o variantes locales justificadas); botón 10px; radio superior de sheet 28px; tipografía `system-ui`; tamaños establecidos por skill 01 y catálogo 02. Para producción preservar geometría de cada componente existente; no reescribir en masa.

### Indicadores funcionales en todos los temas — ENMIENDA SOLICITADA

El propietario solicita añadir indicadores semánticos a todos los perfiles, incluso donde la norma histórica recomendaba estados neutrales. **Esta extensión NO transforma los acentos de marca de los tres temas originales**.

| Estado | Papel | Variable CSS | Uso permitido |
|---|---|---|---|
| `progress` | **VERDE encendido** | `--status-green` | Acción que esté *realmente* en curso, etiqueta y borde contextual |
| `enabled` | **AZUL encendido** | `--status-blue` | Selector/toggle/función *realmente* habilitada |
| `warning` | **ROJO visible** | `--status-red` | Error, bloqueo, falta de bridge o advertencia demostrable |
| `pending` | **GRIS** | `--sub` | Pendiente/indeterminado, sin afirmar éxito |

Los colores representan *estados reales de interfaz*. Nunca colocar verde sobre una operación cuyo backend no fue ejecutado. No pintar botones de marca con colores de estado sin una acción correspondiente. En tema Little, por ejemplo, el CTA sigue terracota y el indicador `enabled` puede ser azul **solo como indicador funcional**. En mate, el naranja permanece reservado a Cargar/Descargar. En tema blanco/gris, aumentar contraste de los estados (verde/azul/rojo más oscuros) sin cambiarlos de significado.

## 3. Composición de componentes

Conservar o recuperar antes de generar: shell/marco móvil, header, topbar, sidebar, tabs, cards, buscador, filas de archivos, popover/sheet, selector de modo, composer de chat, botones, toggles, iconos lineales, estados, toast y navegación. Interfaces de referencia añadidas: `Run.html` (CASCADE/TREN/AUDITOR/VENTANAS/ORQUESTA) y `YAIWES-CRAZY-WALL*.html` (árbol y microflujos).

**Microflujos:**

- Chat: MODELO → MODO → TOOLS → REDACTAR → ACTION BUS → BRIDGE REAL → RESPUESTA/ERROR.
- Archivos: ELEGIR ARCHIVO REAL → VALIDAR → ALMACÉN LOCAL → BUSCAR/ANCLAR → DESCARGAR ARCHIVO REAL.
- Crazy Wall: RAÍZ → ESTADO LOCAL → BITÁCORA → PERSISTIR → EXPORTAR; nunca decir que esos estados son pruebas de GitHub.
- Configuración: TEMA → TOKENS → COMPONENTES → APLICAR → PERSISTIR → REVISAR DESKTOP/MÓVIL.

## 4. Contrato de ejecución — No mock

- Eventos de interfaz: `window.dispatchEvent(new CustomEvent('yaiwes:ui-action', {detail:{actionId,payload,...}}))`.
- Acciones REMOTAS: llamar exclusivamente a `window.YAIWES_PLUGIN_BRIDGE.execute(actionId,payload)` cuando exista y sea función. La acción no se considera completada hasta obtener confirmación real del bridge.
- Acciones locales: estado de UI, tema, búsqueda, notas, archivos locales, toggles, selector, importación/exportación. Tienen efectos visibles y estado consistente.
- Acciones requeridas: `chat.close`, `chat.export`, `chat.attach`, `mode.thinking.toggle`, `model.select`, `chat.send`, `tool.document.toggle`, `tool.website.toggle`, `tool.image.toggle`.
- Prohibido: endpoint ficticio, `setTimeout` simulando IA, chat completado por texto inventado, descarga de un PDF inventado a partir del nombre, confirmación verde sin verificación.
- Falta de backend: `chat.send` mantiene el borrador y muestra `BRIDGE_MISSING`. No añade un mensaje de IA imaginario.
- Adjuntos: conservar archivos reales en UI; hasta 1 MB se pueden serializar localmente; mayores a 1 MB permanecen solo en la pestaña y requieren un bridge de subida específico para transporte remoto.
- Seguridad: no incluir PAT, API keys ni `token_ref` resuelto en el navegador. Los secretos pertenecen al runtime seguro; no confundir `localStorage` con una bóveda.

## 5. Método de trabajo transversal obligatorio

```text
REFERENCE (Figma / imágenes / frontend real / design system)
   → CONTEXT (repo / AGENTS.md / SKILL.md / existentes)
   → PLAN (tarea pequeña, rutas, preservación, criterios)
   → IMPLEMENT (HTML/CSS/JS o React, sin borrar handlers)
   → START (localhost:5173; abrir web real)
   → INSPECT (DOM + estilos + consola + capturas)
   → INTERACT (clic / select / input / scroll / touch)
   → COMPARE (referencia ↔ resultado)
   → CORRECT (únicamente divergencias verificadas)
   ↺ LOOP hasta cumplir todos los criterios verificables
   → VERSION + HANDOFF + DELIVERY (código modular + evidencias)
```

**Reglas operativas:** una tarea pequeña por ciclo. Antes de una transformación, inventario y snapshot del original. Cambiar archivos mínimos. Una ventana = un componente/archivo principal. Backend identificado, fuera de las ventanas. Cuando exista una ruta real en el repo, no inventar otra. En `README.md` anotar decisiones, gaps, fallos y cómo reanudar. Un bloqueo técnico debe quedar etiquetado `BLOCKED`, nunca `PASS`.

## 6. Contrato de entrega

La **fuente editable** nunca será un solo HTML con miles de líneas. Como mínimo:

```text
PANEL-01-CHAT/
├── index.html
├── styles.css
├── app.js
├── assets/
│   ├── icons/
│   └── images/
├── src/lib/actionBus.js
├── manifest.json
├── README.md
├── SKILL.md
├── AGENTS.md
├── VERSION.md
├── ACCEPTANCE.md
├── tests/panel-01-chat.spec.js
├── snapshot/index-standalone.html  # preview/respaldo, NO fuente canónica
└── screenshots/                  # evidencia desktop/mobile
```

Cuando la interfaz esté aprobada, llevarla a **React/Vite modular** con `src/App.jsx`, `src/main.jsx`, `src/components/{ChatPanel,ChatTopbar,ChatComposer,MessageList,ModelSelector,ToolButton,Icon}.jsx`, `src/styles`, y tests. **No afirmar que React está entregado si solo se entrega HTML/JS.** Versionar ambos estados en `VERSION.md`. No portar silenciosamente handlers del HTML; conservar contrato de acciones y verificar paridad.

**Pipeline de entrega:** REFERENCIA → HTML FUNCIONAL → PRUEBAS → REACT/VITE MODULAR → PRUEBAS DE PARIDAD → VERSIÓN → SIGUIENTE EDICIÓN.

## 7. Criterios obligatorios — 11 comprobaciones

| ID | Exigencia | Evidencia mínima |
|---|---|---|
| REF | Referencia | HEX canónicos + comparación visual contra fuente real |
| LAYOUT | Estructura | no scroll horizontal accidental y geometría consistente |
| BUTTONS | Botones | cada botón de la UI tiene acción real o bloqueo explícito |
| DROPDOWNS | Desplegables | cambian selección confirmada o borrador cancelable |
| TABS | Pestañas | panel visible correcto y `aria-selected` |
| INPUTS | Entradas | teclado/clic y datos validados |
| STATE | Estado | cambios locales observables y veraces |
| RELOAD | Recarga | persistencia comprobada en origen web real (no `about:blank`) |
| DESKTOP | Escritorio | screenshot y pruebas Chromium a tamaño escritorio |
| MOBILE | Móvil | screenshot, scroll, tap y navegación móvil |
| CONSOLE | Consola | cero errores JS inesperados; los fallos de conexión se comunican |

**PASS final = 11/11 con evidencia verificable**, y validación visual del propietario si el referente no tiene una medición automática. No escribir `PASS` en una línea no ejecutada. Las acciones backend solo pueden evaluarse `PASS` con backend conectado y prueba de integración real; sin él usar `BLOCKED_REMOTE` aunque la UI local pase.

## 8. Internacionalización y accesibilidad

- Idiomas esperados: `es`, `en`, `fr`, `pt`; predeterminado `es`. Todas las cadenas visibles de producción se extraen a diccionarios i18n.
- Foco visible, etiquetas de campos, estados no comunicados solo por color, contraste suficiente, tabulación y tap móvil.
- Reducir animaciones cuando el usuario activa modo reducido; evitar scroll horizontal.
- Identificador y contrato de acciones estables: no renombrar `actionId` sin migración.

## 9. Trazabilidad mínima

Para cada lote: `(fuente, referencia visual, archivo tocado, versión, tema, acciones, tests, screenshots, PASS/FAIL/BLOCKED, diferencia, reparación y handoff)`. Mantener original intacto hasta aceptar cambios. React/Vite de producción no hereda mock ni bridge ficticio.

## 10. Fuentes utilizadas / límites

Fuentes aportadas: `01-DESIGN-TOKENS-THEMES-IMMUTABLE.md` (paletas 3 originales), `02-UI-COMPONENT-CATALOG-SKILL.md` (formas), `03-FUNCTIONAL-INTERACTION-SKILL.md` (interacciones), `04-AGENT-PROTOCOL-SKILL.md` (protocolo), `FROMTED-ARCHITECTURE-AND-DESIGN-BASE.md`, `FROMTED-FRONTEND-IMMUTABLE-LAW.json` (ley original), `DESIGN-LOCK.json` (Operator interno, no mezclar), screenshots de Grok, `Run.html`, `YAIWES-CRAZY-WALL-1/2.html`, `YAIWES-CRAZY-WALL.html`, y `SKILL-MAESTRO-FROMTED-YAIWES-BORRADOR.md` anterior. La propuesta actual **no edita ninguno de esos originales**; la ampliación `gris`/semántica está documentada como solicitud reciente pendiente de validación visual final.

**Estado:** `REVIEW`. El propietario todavía debe aprobar el perfil visual definitivo.

# FROMTED × YAIWES — README / SKILL · PARTE 3
## Iconos 2D, emojis y colores de encendido · V12 EN REVISIÓN

**Estado:** `PROTOTIPO / NO APROBADO VISUALMENTE`  
**Fuente revisada:** `YAIWES-ICONOS-PRO-V12.html`  
**Fundamento visual aprobado:** `README-SKILL-PARTE-1-GRIS-PRINCIPAL.md`  
**Tipografía:** `SKILL-PARTE-2-TIPOGRAFIA-EN-REVISION.md`, todavía pendiente de corrección funcional.  
**Alcance:** documentar qué existe en V12, qué se debe preservar y los requisitos para rehacer la biblioteca de iconos. **Este archivo no equivale a aprobación del diseño de V12.**

---

## 1. Qué se está construyendo

Un catálogo reutilizable para representar las **acciones reales del frontend** mediante mini logos, pictogramas y, en una etapa separada, emojis/ilustraciones de mayor calidad. Cada símbolo debe corresponder claramente con su **nombre, propósito y estado** dentro de un botón.

**Objetivo visual del usuario:** resultado reconocible y con acabado profesional, superior a los iconos lineales genéricos; no sustituir una biblioteca profesional por signos básicos, emojis de sistema aleatorios o etiquetas decorativas.

**Microflujo:**

```text
REFERENCIAS VISUALES → OBJETIVO DEL BOTÓN → DIBUJO SVG REAL
→ ESTADOS Y COLORES → PREVIEW MÓVIL/ESCRITORIO
→ INTERACCIÓN COMPROBADA → APROBACIÓN DEL USUARIO
```

## 2. Regla obligatoria: conservar el gris principal aprobado

| Uso | HEX obligatorio |
|---|---|
| Fondo de pantalla | `#1B1B1B` |
| Panel/contenedor | `#202020` |
| Superficie auxiliar | `#252525` |
| Botón o tarjeta **sin marcar** | `#2A2A2A` |
| Botón o tarjeta **seleccionado** | `#3C3C3C` |
| Máscara o capa elevada | `#484848` |
| Borde normal | `#3A3A3A` |
| Borde destacado | `#525252` |

**Regla cerrada:** el hover, el glow y el color del símbolo no pueden aclarar todos los módulos. Solo el botón o módulo seleccionado cambia de base al tono `#3C3C3C`. No convertir `#353535`, degradados plateados o `#484848` en el fondo habitual de botones normales.

**Nota sobre V12:** el HTML realmente utiliza degradados para botones normales (`#303030` → `#262626`) y en el estilo elevado (`#353535` → `#242424`). Se consideran **experimentos de acabado no aprobados**, no parte de la paleta aprobada.

## 3. Inventario fiel de la prueba V12

La lista JavaScript `icons` incluye **54 entradas**, no 50; el encabezado visible decía 50 incorrectamente. Las 54 entradas tienen un objeto de trazos SVG en `paths`, sin IDs duplicados ni entradas sin trazado. Esta comprobación se refiere a la estructura de datos, **no** a su calidad visual o significado.

| Categoría V12 | Total | Elementos del catálogo |
|---|---:|---|
| `ai` | 7 | Asistente AI, Razonamiento, Agente, Idea, Lanzar, Procesador, Rápido |
| `general` | 14 | Buscar, Ajustes, Inicio, Menú, Cuadrícula, Chat, Enviar, Calendario, Filtrar, Controles, Actualizar, Usuario, Equipo, Vista |
| `status` | 14 | Favorito, Guardado, Anclar, Notificación, Seguridad, Bloquear, Acceso, Aprobar, Advertencia, Cerrar, Tiempo, Tendencia, Métricas, Distribución |
| `files` | 6 | Carpeta, Archivo, Subir, Descargar, Duplicar, Eliminar |
| `media` | 5 | Imagen, Cámara, Video, Micrófono, Altavoz |
| `connect` | 8 | Enlace, Web, Conector, Nube, Base de datos, Código, Terminal, Herramienta |
| **Total** | **54** | **Prototipos lineales, no 54 iconos aprobados** |

**Pendiente de diseño:** elegir y dibujar 50 piezas finales, o ampliar el objetivo a 54 **solo tras autorización**. El catálogo debe incluir nombres en español, acción asociada, estado posible y SVG fiel a su función; ejemplos como `brain`/`ai` o `heart`/“Guardado” requieren revisión semántica para que no confundan.

## 4. Los seis colores de encendido de V12

| Color | HEX en V12 | Significado sugerido, NO obligatorio |
|---|---|---|
| Blanco iluminado | `#F8F8F8` | acción o símbolo neutro visible |
| Azul eléctrico profundo | `#0647F4` | seleccionado / interacción activa |
| Verde intenso | `#0FD56A` | disponible / operación correcta |
| Rojo vivo | `#FF4A5F` | alerta o cancelación |
| Naranja vivo | `#FF7A1C` | espera, carga o advertencia contextual |
| Gris claro | `#DADADA` | símbolo neutro |

**No mezclar significado y estilo sin contrato.** Ejemplo: una acción destructiva no debe verse como éxito solo por recibir un icono verde. El usuario puede previsualizar otras combinaciones; las restricciones semánticas se aplicarán al integrar cada acción real.

### Comportamiento del color en el prototipo

`activeColor.hex` se propaga mediante `applyTheme()` a los tokens `--accent` y `--accent-rgb`. Los controles individuales del catálogo se reconstruyen con `renderSwatches()`, `renderGrid()` y `renderDetail()`. En otras palabras, el selector de color es un **control de previsualización local**, no un selector guardado por botón ni un sistema global de preferencias.

## 5. Tres acabados visuales existentes (solo prototipos)

- **Suave:** `linear-gradient(180deg,#303030,#262626)`; borde `#434343`.
- **Elevado:** `linear-gradient(180deg,#353535,#242424)`; borde `#505050`.
- **Cristal oscuro:** degradado semitransparente; borde claro.

**No aprobarlos por defecto:** deben rediseñarse con la jerarquía del gris aprobada. Los efectos de profundidad no autorizan un aclarado global.

## 6. Interacciones reales que existen en el HTML V12

| Control | Implementación verificable en el código | Límite |
|---|---|---|
| Elegir color de encendido | `renderSwatches()` modifica `activeColor`; `applyTheme()` cambia variables CSS | No guarda un color individual por icono |
| Elegir acabado visual | `renderStyles()` actualiza `activeStyle` | Acabados todavía no aceptados |
| Filtrar categoría | `renderCats()` actualiza `activeCat` | Se filtran entradas, no se organizan archivos de producción |
| Buscar iconos | `filteredIcons()` utiliza el valor de `#search` | Solo filtra contenido del catálogo |
| Elegir mini logo | `renderGrid()` establece `activeIcon` y `renderDetail()` pinta el detalle | El clic selecciona una muestra, no ejecuta una función del producto |
| Vista “Foco en selección” | Cambia las columnas de `#grid` a 2 | **No** es un modo de foco real en un solo icono |
| Botones Normal, Activo, Disponible, Proceso y Alerta | Son ejemplos visuales generados con `setBtn()` | **No tienen acciones funcionales vinculadas** |

**No implementado en V12:** exportar SVG desde la UI, descargarlos como biblioteca, cambiar color por icono de manera persistente, elegir emoji ilustrado independiente, click real de acciones, toggle por tarjeta persistente, guardado local, integración con pantallas originales, prueba de compatibilidad Android.

## 7. Contrato de calidad para la siguiente iteración

**Propuesta de implementación, no descripción de V12:**

1. Cada icono nuevo se diseña a partir de **su función específica**; primero silueta identificable, luego detalle, contraste y acabado.
2. Cada mini logo conserva proporciones y grosor coherentes; SVG vectorial con `viewBox` homogéneo (24×24 o 32×32), márgenes consistentes y trazos sin geometría accidental.
3. Redibujar, no simplemente ampliar o recolorear los trazos lineales de V12. Diferenciar visualmente `AI`, `pensamiento`, `agente`, `herramienta`, `web`, `archivo`, `alerta`, `procesador`, etc.
4. Diseñar **dos familias separadas**: `iconos de interfaz` (compactos y legibles) y `emojis/mini ilustraciones premium` (volumen, materiales o expresividad). Una no debe fingir ser la otra.
5. Colores de estado independientes de los colores propios de una ilustración. El activo no debe eliminar detalles necesarios para reconocer su función.
6. Contraste y legibilidad comprobables en 18, 20, 24, 32, 48 y 64 px, tanto apagado como encendido; contemplar daltonismo: el significado no depende solo del color.
7. Cada botón real necesita estado accesible (`aria-pressed` cuando proceda), control por teclado, foco visible, área táctil suficiente y acción efectiva o desactivada de forma explícita.
8. Ninguna acción de producción (descargar, compartir, conectar, eliminar, ejecutar) se considerará implementada si solo cambia un texto o icono sin realizar la operación.
9. No sustituir IDs, handlers, rutas ni estructura del HTML original; integrar mediante un registro de iconos desacoplado.
10. Las capturas de aprobación se generan de la implementación final móvil + escritorio; sin dependencia de fuentes ni scripts remotos en la demo autónoma.

## 8. Contrato técnico propuesto para módulos reutilizables

Este fragmento **es una especificación para la fase de integración, NO código actualmente implementado en V12**:

```js
const iconDefinition = {
  id: 'download',
  label: 'Descargar',
  category: 'files',
  description: 'Guardar un archivo o una salida',
  svg: '<svg viewBox="0 0 24 24">...</svg>',
  states: ['off', 'on', 'selected', 'loading', 'warning', 'disabled'],
  colorOn: '#0647F4',
  colorOff: '#DADADA',
  actionId: 'download-file' // debe resolverse a una acción REAL al integrar
};
```

```text
ICONO DEFINIDO
  → VALIDAR ID + SVG + OBJETIVO
  → VINCULAR ACCIÓN REAL
  → APLICAR COLOR DE ESTADO
  → RENDERIZAR EN BOTÓN
  → PROBAR CLICK/TACTO/TECLADO
  → VERIFICAR EFECTO Y ESTADO
```

### Reglas para el código de integración

- Tokens separados: `--bg`, `--surface`, `--module`, `--module-selected`, `--icon-on`, `--icon-off`, `--button-text`, `--status-success`, `--status-warning`, `--status-danger`.
- Registrar los iconos por ID con nombres descriptivos; no inferir la función desde el dibujo ni reutilizar un icono equivocado porque “se parece”.
- Persistir preferencias solo cuando se implemente almacenamiento real; no declarar “guardado” por mantener el color hasta el próximo render.
- Al pulsar un botón activo, debe responder según su contrato: acción, toggle o selección, sin decorar una operación ficticia.

## 9. Pruebas necesarias para declarar APROBADA esta parte

- [ ] Exactamente 50 diseños finales **o** nuevo número acordado por el usuario (la V12 contiene 54).
- [ ] Nombre ↔ silueta ↔ función coinciden en cada elemento; revisión visual individual.
- [ ] Distinción visible entre icono funcional y emoji/ilustración premium.
- [ ] Los seis tonos de encendido son seleccionables y afectan al elemento correcto.
- [ ] No cambian los colores aprobados de fondo, panel, módulo normal o seleccionado.
- [ ] Se puede combinar color del icono, texto y botón sin perder legibilidad.
- [ ] Los estados apagado, encendido, seleccionado, advertencia y deshabilitado se distinguen.
- [ ] Cada botón con función declarada hace algo verdadero o indica que no está conectado.
- [ ] Filtrar, buscar, seleccionar, restablecer y exportar funcionan y se comprueban en navegador.
- [ ] Pruebas de foco, táctiles y tamaño mínimo en pantalla Android y escritorio.
- [ ] Comparación visual con las referencias originales enviadas por el usuario.
- [ ] El usuario aprueba explícitamente el acabado antes de integrar.

## 10. Siguiente plan, paso a paso

**Prioridad de calidad:** no llamar “terminada” una parte por tener HTML que abre. El usuario ya reportó errores con los selectores de letra y falta de calidad visual de iconos.

| Paso | Entregable | Estado al redactar |
|---|---|---|
| 1 · Base visual | README/SKILL de grises aprobados | **Aprobado** |
| 2 · Letras y color de texto | HTML autónomo con controles funcionales para cada clase | **Pendiente de reparación/aceptación** |
| 3 · Iconos/emoji | Nueva familia ilustrada, acabado profesional, semántica fiel | **V12 no aprobada; requiere rediseño** |
| 4 · Botones y estados | HTML aislado que combine texto + icono + color + click real | **Pendiente** |
| 5 · Integración | Llevar los módulos aceptados al HTML original sin romper el diseño | **Pendiente** |
| 6 · Complementos | Componentes Rare UI de fuente comprobada, animaciones y microinteracciones | **Pendiente** |
| 7 · Validación | Navegador móvil/escritorio, estados, exportación y documentación final | **Pendiente** |

## 11. Archivos y responsabilidades

```text
FROMTED / YAIWES
├── README-SKILL-PARTE-1-GRIS-PRINCIPAL.md
│   └── Norma visual principal APROBADA
├── SKILL-PARTE-2-TIPOGRAFIA-EN-REVISION.md
│   └── Letras: trabajo pendiente
├── YAIWES-ICONOS-PRO-V12.html
│   └── Muestra exploratoria de iconos; NO aprobada
└── README-SKILL-PARTE-3-ICONOS-Y-EMOJIS-EN-REVISION.md
    └── Este documento: inventario, deuda y próximos criterios
```

**Prohibiciones:** no sobrescribir el HTML original; no llamar “aprobada” a la V12; no añadir ni prometer Rare UI, CSS funcional de letras, exportaciones o operaciones que no existan y se hayan probado; no sustituir emojis premium por iconos lineales simples sin acordarlo.

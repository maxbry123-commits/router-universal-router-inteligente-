# FROMTED · YAIWES — README / SKILL · PARTE 1
## Diseño general, estilo visual y colores base aprobados

**Edición:** 1.1 · Ajuste de tema principal aprobado por el usuario  
**Ámbito:** frontend FROMTED / YAIWES, escritorio y Android/móvil  
**Estado:** APROBADO en sus decisiones indicadas; **NO** es una certificación de que todos los controles estén implementados.  
**Referencia visual aceptada para el gris:** `FROMTED-YAIWES-PRUEBA-PALETA-V07.html` y sus capturas móvil/escritorio.  
**Norma:** preservar la interfaz original. La aprobación de colores **no autoriza** reconstruir el HTML anterior ni cambiar el comportamiento de los botones.

---

## 1. Objetivo y alcance de esta parte

Conservar una familia visual coherente para FROMTED / YAIWES: **superficies oscuras, módulos por capas, títulos legibles, bordes discretos, selección visible y ventanas móviles de tipo app**, siguiendo las referencias entregadas y el HTML original.

**Tema principal actualizado:** `gris` V07. `little` pasa a opción secundaria sin perder sus colores canónicos.

**Solo queda asentado en esta parte:**

- La estructura y el carácter visual general ya acordados.
- **El tema principal `gris` (V07)**, según la aprobación posterior del usuario. `little` se conserva como tema alternativo canónico.
- Los tres temas heredados y bloqueados del paquete de diseño: `little`, `matte`, `blanco`.
- El nuevo **gris oscuro aprobado de la prueba V07**: fondo, superficie, módulo normal, módulo marcado y máscara.
- Las reglas de separación entre color de marca, color de selección y estado funcional.
- La forma de comprobar que un nuevo diseño mantiene esta base.

**Fuera de esta parte, y SIN afirmar que funciona:** selectores individuales de color de letras, editor de input/salidas, selector de fuentes, emojis, 50 iconos 2D, botones multicolor, Rare UI, microanimaciones, videos, drag-and-drop, puentes de backend y todas sus pruebas. Corresponden a salidas posteriores.

---

## 2. Jerarquía visual obligatoria

```text
PANTALLA / FONDO
        ↓
PANEL / CONTENEDOR
        ↓
MÓDULO O TARJETA NORMAL
        ↓  solo si hay selección real
MÓDULO MARCADO
        ↓  solamente cuando aparece una ventana superior
MÁSCARA / SHEET
```

**Regla esencial:** no aclarar todo el sistema porque se selecciona un elemento. La selección modifica **únicamente el módulo afectado** y su indicador; el fondo y los demás módulos conservan su color.

**Distribución a preservar del diseño anterior:**

- **Escritorio:** menú lateral, vista principal/central y zona auxiliar de configuración o inspección cuando corresponda. No inventar otra plantilla para sustituirlos.
- **Móvil:** un panel principal, cabecera, tarjetas/listas, pestañas y navegación inferior cuando esa pantalla las tenga.
- **Sheets / modales:** aparecen encima de la pantalla real, mantienen el contexto detrás y pueden cerrarse. No deben reemplazar permanentemente la pantalla original.
- **Patrones reconocibles:** Chat, Archivos, Crazy Wall/Actividades y Configuración; filas de herramientas, selectores de modo y controles agrupados en tarjetas.
- **Interacciones representadas en referencias:** estado apagado/encendido, seleccionado/no seleccionado, lista de opciones, input, elementos de archivo y acciones. Su implementación y prueba se documentarán en otra parte, sin simular éxito.

---

## 3. Tema gris oscuro — base APROBADA en V07

Este es el **gris base de la nueva variante**, separado de `matte` y de `little`. **No es negro puro** ni gris claro general.

| Papel | Color exacto | Uso |
|---|---|---|
| Fondo general | `#1B1B1B` | Lienzo y pantalla. Nunca aclarar por hover/selección. |
| Panel / contenedor | `#202020` | Barras, contenedores y navegación. |
| Capa intermedia | `#252525` | Superficies auxiliares y fondo de sheet. |
| Módulo **normal**, sin seleccionar | `#2A2A2A` | Cards, botones secundarios y filas. |
| Módulo **seleccionado** | `#3C3C3C` | **Solo** card, botón o fila activados explícitamente. |
| Máscara / elemento elevado | `#484848` | Agarre de sheet, elementos destacados de capa superior; nunca fondo general. |
| Borde normal | `#3A3A3A` | Líneas suaves y separación. |
| Borde de énfasis | `#525252` | Contorno en selección o foco, cuando la pantalla lo necesite. |
| Título principal | `#FAFAFA` | Máximo contraste del texto principal. |
| Texto principal | `#EDEDED` | Nombres y contenido prioritario. |
| Texto secundario | `#BFBFBF` | Explicaciones, subtítulos y metadatos. |
| Texto terciario | `#A0A0A0` | Etiquetas y ayudas de menor jerarquía. |

**Aprobación explícita del ajuste:** el módulo normal pasó de un gris visualmente demasiado claro a `#2A2A2A` (aproximadamente un 30 % menos brillo respecto a `#3C3C3C`, según el criterio de la revisión). **El antiguo `#3C3C3C` permanece exclusivamente como color de módulo marcado.**

### CSS fuente de verdad para la variante gris

```css
html[data-theme="gris"] {
  --bg:             #1B1B1B;
  --surface:        #202020;
  --surface-alt:    #252525;
  --card:           #2A2A2A;
  --card-hover:     #2A2A2A; /* Hover no equivale a selección. */
  --module-selected:#3C3C3C;
  --mask-panel:     #484848;
  --border:         #3A3A3A;
  --border-strong:  #525252;
  --text:           #FAFAFA;
  --text-primary:   #EDEDED;
  --text-secondary: #BFBFBF;
  --text-tertiary:  #A0A0A0;
}

/* Aplicar SOLO al elemento seleccionado, NO a todos los módulos. */
html[data-theme="gris"] .module { background: var(--card); }
html[data-theme="gris"] .module:hover { background: var(--card-hover); }
html[data-theme="gris"] .module.selected,
html[data-theme="gris"] .module[aria-selected="true"],
html[data-theme="gris"] .module[aria-pressed="true"] {
  background: var(--module-selected);
}
```

**Nota importante:** `.module` es un nombre de clase de ejemplo para explicar el contrato visual, **no una afirmación sobre el selector HTML original**. Al implementarlo, enlazar los selectores reales existentes, sin sustituir IDs, HTML ni handlers.

---

## 4. Little — alternativa canónica e intacta

`little` se conserva como **tema alternativo canónico**: carbón cálido y botón principal terracota. El **predeterminado es `gris`**. No modificar los tokens de Little al trabajar sobre el gris.

```css
html[data-theme="little"] {
  --bg:             #1C1B1A;
  --surface:        #2A2927;
  --card:           #2A2927;
  --card-hover:     #353330;
  --border:         rgba(255,255,255,0.1);
  --border-strong:  rgba(255,255,255,0.18);
  --text:           #F5F4F0;
  --text-primary:   #F5F4F0;
  --text-secondary: #A8A29E;
  --text-tertiary:  #9C9590;
  --accent:         #C65D3B;
  --accent-hover:   #b05031;
  --accent-soft:    rgba(198,93,59,0.15);
}
```

Uso distintivo: **terracota para acciones principales**, no pintar todos los botones, iconos y títulos de terracota. El gris aprobado de V07 es otro tema; no lo impongas dentro de Little.

---

## 5. Otros temas del diseño previo

Los temas no se mezclan a mitad de una misma pantalla, salvo mediante un selector explícito. El HTML de revisión ya contempla siete opciones, pero **aprobar el gris V07 no significa dar por aprobados todos los tonos experimentales**.

| Identificador | Descripción | Situación |
|---|---|---|
| `little` | Carbón cálido, terracota `#C65D3B` | **Canónico / alternativo** |
| `matte` | Negro mate con grises neutros | **Canónico, no modificar** |
| `blanco` | Claro, títulos gris oscuro y selección azul | **Canónico, no modificar** |
| `gris` | **Gris profundo V07**, `#1B1B1B` → `#2A2A2A` | **PRINCIPAL / aprobado** |
| `crystal` | Cristal/holográfico/transparencias | Referencia de diseño, no aprobar detalles nuevos aquí |
| `orange` | Naranjas y carbón/negro | Referencia de diseño, no aprobar detalles nuevos aquí |
| `blue` | Gama de azules | Referencia de diseño, no aprobar detalles nuevos aquí |

### Valores de los otros dos temas canónicos

**Matte:** `--bg: #0a0a0d`, `--surface: #141417`, `--panel: #1a1a1e`, `--card: #202025`, `--card-hover: #282830`; borde `#2a2a33`, borde claro `#3f3f4e`; texto brillante `#ffffff`, principal `#e4e4e7`, secundario `#a1a1aa`. Azul `#2563eb` para selección/check; naranja `#ff5500` en el texto Cargar/Descargar, no como relleno de botón.

**Blanco:** `--bg: #f4f4f5`, `--surface: #ffffff`, `--card: #ffffff`, `--card-hover: #f8f8f9`; bordes `#e4e4e7`/`#d4d4d8`; títulos `#18181b`, texto principal `#3f3f46`, secundario `#71717a`; azul `#2563eb` para selección/enlace Descargar. No introducir texto principal negro puro `#000000`.

**Separación:** `matte` puede usar fondos casi negros; `gris` **no** debe confundirse con `matte`, porque su fondo aprobado es `#1B1B1B`.

---

## 6. Texto y estilo general — solo lo ya definido

La tipografía base es `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`. Se conserva una jerarquía visible por peso, tamaño y color: títulos destacados, nombres legibles, subtítulos secundarios y metadatos tenues.

| Papel de texto | Carácter visual base |
|---|---|
| Título | Alto contraste, tipografía limpia, peso destacado. |
| Subtítulo | Gris de menor intensidad, buen espacio respecto al título. |
| Escritura/entrada | Legible sobre superficie oscura; distinguir el texto escrito del placeholder. |
| Salida/respuesta | Legible, integrada visualmente en la tarjeta de respuesta. |
| Etiqueta auxiliar | Tamaño y contraste menores sin perder legibilidad. |
| Texto de botón | Contraste suficiente con el fondo del botón y su estado. |

**Límite de aprobación:** este documento fija la *jerarquía de base*, **NO** da por aprobados los selectores de colores de texto de V08/V09. El usuario reportó que no funcionan correctamente; no copiar sus comportamientos ni declararlos `PASS`.

### Geometría heredada del skill base

```text
Marco principal tipo teléfono: 24 px de radio
Tarjetas/filas:               12 px de radio
Botón base:                   10 px de radio
Sheet inferior (esquinas sup):28 px de radio
Iconos estándar:              14–16 px
Títulos seccionales de base:  16 px
Nombres de lista de base:     14 px
Metadatos:                   12 px
Texto de apoyo:              11 px
```

Estas medidas son **constantes del skill original** para componentes básicos; no obligan a imponer tamaños diminutos a las pantallas de ejemplo con títulos más grandes.

---

## 7. Color visual frente a estado funcional

**No confundir tres conceptos:**

1. **Tema:** el gris, Little u otra paleta que define el fondo y los módulos.
2. **Selección:** un elemento realmente elegido usa fondo marcado `#3C3C3C` en `gris`. El resto permanece normal.
3. **Estado operativo:** el verde indica *trabajo realmente en curso*, el azul *activado/seleccionado* y el rojo *alerta real*. En un prototipo, mostrarlos como **ejemplos visuales**, no fingir progreso, conexión ni errores.

Las referencias de trabajo también contemplan naranja en progreso/descarga y blanco/gris para controles neutros; no convertir los indicadores en colores de marca obligatorios. Los **valores exactos de la futura biblioteca multicolor de botones e iconos siguen en revisión** y no forman parte de esta aprobación cromática de base.

**Norma de interacción futura:** un botón que se ilumina, un check y una animación no demuestran por sí solos que se ejecutó una API o se guardó un archivo. No mostrar éxito ficticio. Cuando haya backend, verificar la respuesta real; si falta, informar del estado sin inventarlo.

---

## 8. Qué debe conservar toda siguiente salida

```text
REFERENCIA ORIGINAL
     ↓
PRESERVAR ESTRUCTURA, IDs, HANDLERS Y VENTANAS
     ↓
USAR TOKENS DEL TEMA ELEGIDO
     ↓
APLICAR COLOR NORMAL POR DEFECTO
     ↓
CAMBIAR SOLO MÓDULO SELECCIONADO
     ↓
PROBAR ESCRITORIO + MÓVIL + NAVEGADOR
     ↓
COMPARAR CON CAPTURA / HTML ANTERIOR
     ↓
CORREGIR HASTA RESPETAR REFERENCIA
```

La referencia manda más que una reconstrucción estética por gusto del agente. **Primero reutilizar componentes existentes y restaurar paridad; solo generar elementos nuevos cuando haya autorización.**

Se deben distinguir tres estados en informes posteriores:

- `APROBADO_VISUAL`: cumple la referencia de diseño acordada.
- `PROBADO_FUNCIONAL`: botones y entradas probados de verdad en el navegador.
- `PENDIENTE`: faltan implementación, integración o comprobación.

La aprobación de este README es **de diseño base** y no equivale a decir que V08/V09 tienen controles funcionales, que el backend está conectado o que Rare UI fue instalado.

---

## 9. Lista de control visual de la parte 1

- [ ] `little`, `matte` y `blanco` conservan sus colores canónicos.
- [ ] Existe la variante `gris` independiente de `matte`.
- [ ] Fondo de `gris` = `#1B1B1B`.
- [ ] Paneles = `#202020` y capa intermedia = `#252525`.
- [ ] Módulos sin marcar = `#2A2A2A`.
- [ ] **Solo** módulos marcados = `#3C3C3C`.
- [ ] Máscara o agarre de sheet usa `#484848`, nunca toda la pantalla.
- [ ] Hover no ilumina todos los módulos como si estuvieran seleccionados.
- [ ] Títulos y textos mantienen contraste y jerarquía.
- [ ] Sigue presente la interfaz original: Chat, Archivos, Actividades/Crazy Wall y Configuración.
- [ ] La pantalla móvil mantiene disposición de aplicación, sin overflow horizontal.
- [ ] Se inspecciona en navegador antes de afirmar un `PASS`.
- [ ] No se declara funcionalidad de selectores V08/V09 hasta corregirla y probarla.

**Este checklist no registra un resultado de test nuevo:** fija los criterios para la próxima fase.

---

## 10. Archivos de referencia y precedencia

1. `FROMTED-YAIWES-PRUEBA-PALETA-V07.html` — **fuente de color gris aprobado**.
2. `01-DESIGN-TOKENS-THEMES-IMMUTABLE.md` — tokens canónicos `little`, `matte` y `blanco`.
3. `YAIWES-PERFIL-VISUAL-DEMO.html` — primer diseño reconocible, referencia estructural sin autorización de reescritura.
4. `FROMTED-YAIWES-IGUAL-AL-ORIGINAL-V03/SKILL.md` — regla de preservar diseño original y no simular operaciones.
5. Las capturas proporcionadas de chat, conectores, settings y ventanas móviles — referencias de composición, no autorización para copiar marcas o fingir integraciones.

**Si un documento anterior describe un `gris` más claro**, para la variante actual prevalece la decisión posterior **V07**. Los colores Little/Matte/Blanco del skill original permanecen sin sustitución.

---

## 11. Cierre de alcance para el siguiente turno

**PARTE 1 COMPLETADA COMO DOCUMENTACIÓN, NO COMO NUEVA INTERFAZ.**

El siguiente trabajo deberá tratar individualmente los controles de títulos, subtítulos, escritura, input, salida, colores de botones, iconos y emojis. **No declararlos corregidos por el hecho de estar escritos aquí.** Ese trabajo tendrá su propia salida y pruebas; esta parte 1 solo es la **base visual aprobada**.

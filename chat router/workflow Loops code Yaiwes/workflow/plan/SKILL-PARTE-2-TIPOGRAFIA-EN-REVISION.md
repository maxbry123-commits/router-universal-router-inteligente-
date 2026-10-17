# FROMTED / YAIWES — SKILL de tipografía (PARTE 2)

**Estado:** PROTOTIPO EN REVISIÓN · No homologado hasta que el usuario apruebe la V10.  
**Dependencia:** `README-SKILL-PARTE-1-GRIS-PRINCIPAL.md`.  
**HTML autónomo:** `FROMTED-YAIWES-LETRAS-GRIS-V10.html`.

## 1. Propósito
Configurar **solo letras y tipografía**, con cambios reales, independientes y comprobables. No construir navegación, Chat con IA, iconos, botones de API, Rare UI ni animaciones en esta parte. No recrear el diseño original de la aplicación; el laboratorio V10 es un ensayo de estilos aplicables a la interfaz existente.

## 2. Base visual obligatoria
El tema predeterminado pasa a ser **GRIS**. No aclarar el fondo cuando se cambia una letra.

```css
:root {
  --bg: #1B1B1B;       /* fondo */
  --panel: #202020;    /* panel */
  --subpanel: #252525; /* superficie auxiliar */
  --module: #2A2A2A;  /* tarjeta no marcada */
  --selected: #3C3C3C;/* tarjeta seleccionada únicamente */
  --mask: #484848;    /* máscara/sheet, nunca fondo común */
  --line: #3A3A3A;
  --line-strong: #525252;
}
```

**Regla cromática:** modificar únicamente el `color` de la categoría textual elegida. La selección de texto no modifica `background-color` de otras tarjetas. Los colores vivos del editor son **alternativas del texto**, no un rediseño de fondos.

## 3. Categorías de texto independientes

| ID técnico | Explicación | Elemento de demostración |
|---|---|---|
| `title` | Título principal | `#sampleTitle` |
| `subtitle` | Subtítulo | `#sampleSubtitle` |
| `body` | Texto de escritura general | `#sampleBody` |
| `input` | Texto que escribe una persona | `#demoInput` |
| `placeholder` | Texto de ayuda antes de escribir | `#demoInput::placeholder`, `#placeholderDisplay` |
| `output` | Texto de una salida o resultado | `#demoOutput` |
| `button` | Letras dentro de botones | `#sampleButton` |
| `meta` | Etiquetas, metadatos | `#sampleMeta` |

**Importante:** `placeholder` no es `input`: tienen colores y estilos separados. `output` es editable localmente para previsualizar letras; **no** simula respuesta de IA.

## 4. Paleta de letras (10 colores)

| Nombre | HEX |
|---|---|
| Blanco brillante | `#FFFFFF` |
| Azul eléctrico profundo | `#0848F7` |
| Verde intenso | `#10D86B` |
| Rojo vivo | `#FF475F` |
| Naranja vivo | `#FF7719` |
| Gris claro | `#DADADA` |
| Cian | `#00C8F8` |
| Violeta | `#8860EA` |
| Dorado | `#FFC14A` |
| Rosa | `#FB63AD` |

Adicionalmente, existe un `<input type="color">` para seleccionar cualquier HEX válido. La interfaz muestra **contraste calculado** entre el texto y el módulo `#2A2A2A`; las combinaciones con contraste insuficiente se deben señalar, no declarar accesibles.

## 5. Propiedades que deben funcionar por categoría
- `color` y color personalizado.
- `font-family`: siete familias mediante fuentes del sistema/fallbacks; sin importar fuentes externas.
- `font-size`: 10–48 px.
- `font-weight`: 300–900.
- `letter-spacing`: −1 a +4 px.
- `line-height`: 1 a 2,3.
- `font-style`: normal/cursiva.
- `text-decoration`: normal/subrayado.
- `text-transform`: normal/mayúsculas.
- `text-align`: izquierda, centro, derecha.
- Texto de ejemplo editable; selector de clase de texto.

## 6. Contrato de estado

```js
const typographicState = {
  title: { color: '#FAFAFA', font: 'sistema', size: 28, weight: 700,
           tracking: -0.5, lineHeight: 1.18, italic: false,
           underline: false, uppercase: false, align: 'left', sample: 'Diseño inteligente' },
  // Las otras 7 clases comparten el esquema, pero conservan sus propios valores.
};
```

`applyRole(id)` actualiza **solo los nodos asociados a `id`**. `input` preserva el texto escrito mientras cambia su estilo; `placeholder` actualiza tanto el atributo como la pseudo-clase. Guardar por clase con `localStorage`; ofrecer restablecimiento individual/global; permitir exportación de un CSS independiente.

## 7. Flujo obligatorio para un agente

```text
LEER REFERENCIA BASE V07
  → CONSERVAR GRIS COMO PRINCIPAL
  → SELECCIONAR CLASE DE LETRA
  → CONFIGURAR COLOR / FUENTE / TAMAÑO / ESTILO
  → APLICAR A SELECTOR REAL
  → INSPECCIONAR CSS COMPUTADO
  → EDITAR EJEMPLO Y VERIFICAR RESULTADO
  → RECARGAR Y COMPROBAR PERSISTENCIA
  → CAPTURAR MÓVIL Y ESCRITORIO
  → PEDIR APROBACIÓN
```

## 8. Criterios de aceptación

- [ ] Gris base exacto y sin degradados más claros.
- [ ] Cada una de las 8 clases responde a 10 colores: 80 casos.
- [ ] Cambio de clase no modifica valores de otras clases.
- [ ] `input`, `placeholder` y `output` son independientes.
- [ ] Tamaño, peso, familia, cursiva, subrayado, mayúsculas, espaciado y alineación se reflejan en estilo computado.
- [ ] Texto escrito no desaparece por cambiar color.
- [ ] Guardado, reinicio individual/global y exportación CSS comprobados.
- [ ] Sin dependencias CSS/JS externas ni error de consola.
- [ ] Funciona en móvil sin desbordamiento horizontal.
- [ ] Probar en el navegador Android del usuario antes de declarar homologación definitiva.

## 9. No extender esta parte todavía
**Iconos 2D, emojis, colores de activación de botones, Rare UI, microanimaciones, videos, drag-and-drop y backend** quedan para aprobaciones separadas. La presente parte solo modifica tipografía y colores de letras.

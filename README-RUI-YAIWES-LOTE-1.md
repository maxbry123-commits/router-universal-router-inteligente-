# RUI / Rare UI → YAIWES · Lote 1

## Objetivo
Integrar Rare UI sin rediseñar sus componentes. Regla:
**instalar original → conservar estructura, interacción y animación → sustituir únicamente color/tokens → probar.**

## Fuente verificada
- Proyecto: Rare UI
- Repositorio: `swamimalode07/rare-ui`
- Registro actual inspeccionado: **22 archivos UI** en `components/ui/`.

## Diseño YAIWES bloqueado
Paleta gris principal:
- Fondo: `#1B1B1B`
- Panel: `#202020`
- Módulo normal: `#2A2A2A`
- Módulo seleccionado: `#3C3C3C`
- Máscara: `#484848`
- Borde: `#3A3A3A`
- Borde fuerte: `#525252`
- Texto principal: `#EDEDED`
- Texto secundario: `#BFBFBF`
- Texto terciario: `#A0A0A0`

Acentos funcionales:
- Azul eléctrico: `#0848F7` — provisional hasta aprobación final del tono
- Verde intenso: `#12D86A`
- Rojo vivo: `#FF475F`
- Naranja vivo: `#FF7B1A`
- Blanco iluminado: `#FFFFFF`
- Gris claro: `#DADADA`

## Lote 1
Se inicia con 5 componentes de navegación/estructura:
1. `bounce-sidebar`
2. `hook-sidebar`
3. `proximity-sidebar`
4. `gooey-nav`
5. `family-drawer`

### Regla de modificación
No cambiar:
- geometría
- tamaños
- springs
- motion
- timings
- layout
- props
- comportamiento táctil/click
- SVG original

Sí cambiar:
- fondos
- superficies
- bordes
- textos
- color activo
- estados warning/error/success

## Auditoría inicial del código
- `bounce-sidebar`: color duro `#FC4C01` en el indicador.
- `hook-sidebar`: color duro `#FC4C01`.
- `gooey-nav`: usa `#F4F4F9`, `#262626`, `#868593`, `#FC4C01` y blanco.
- `proximity-sidebar`: no mostró HEX duro en la revisión inicial; priorizar tokens del tema.
- `family-drawer`: tiene varios HEX claros y estados de acción; requiere remapeo cuidadoso sin tocar su estructura.

## Uso
1. Ejecutar `install-lote-1.sh` dentro del proyecto React/shadcn.
2. Añadir `rareui-yaiwes-theme.css` al CSS global.
3. Ejecutar `node patch-lote-1.mjs`.
4. Revisar el diff: solo deben cambiar colores/tokens.
5. Probar los 5 componentes antes de continuar al Lote 2.

## Licencia
Rare UI permite usar y modificar los componentes en proyectos, pero exige atribución visible y mantiene restricciones contra redistribuir los componentes como una biblioteca competidora. Conservar los avisos/licencia originales y acreditar Rare UI donde corresponda.

## Estado
- Base gris YAIWES: APROBADA.
- Rare UI Lote 1: INICIADO / PENDIENTE DE PRUEBA VISUAL.
- No declarar PASS hasta ejecutar los componentes reales.

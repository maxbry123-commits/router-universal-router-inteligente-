# RUI → YAIWES · Lote 1 · Test report

Resultado del demo autónomo: PASS.

Comprobado en Chromium del sistema mediante Playwright + `page.set_content()`:
- Bounce Sidebar: selección sincronizada Original/YAIWES.
- Hook Sidebar: selección sincronizada.
- Gooey Nav: selección sincronizada.
- Family Drawer: apertura sincronizada y navegación a vista secundaria.
- Proximity Sidebar: selección sincronizada.
- Consola: 0 errores JavaScript.
- Captura escritorio: generada.
- Captura móvil: generada.

Límite: esta prueba valida el port visual/interactivo autónomo. No afirma que el runtime React/Next original de Rare UI se haya ejecutado dentro de este contenedor.

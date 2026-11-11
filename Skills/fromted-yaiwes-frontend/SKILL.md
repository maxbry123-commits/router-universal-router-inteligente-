---
name: fromted-yaiwes-frontend
description: Úsalo siempre que se construya, modifique, revise o pruebe una interfaz FROMTED × YAIWES. Incluye el chat (modelo, modo, herramientas, adjuntos, borrador, exportar, enviar), la pestaña de archivos (subir, anclar, buscar, descargar, borrar), Crazy Wall (raíces, estados, notas), la configuración (temas, idioma, animación, exportar e importar, reinicio), los siete temas (Little como principal, Matte, Blanco, Cristal, Naranja, Azul y el gris sin superficies negras), los indicadores verde, azul, rojo y gris, el action bus y el evento yaiwes:ui-action, el bridge window.YAIWES_PLUGIN_BRIDGE y su fallo cerrado (BRIDGE_MISSING), los componentes Rare UI (bounce-sidebar, hook-sidebar, folder, family-drawer), el diseño FROMTED y YAIWES, y las pruebas Playwright de estas pantallas. Actívalo también si el usuario no nombra el skill pero habla de estas pantallas, de no simular respuestas, de no inventar datos, de conectar el bridge o de verificar en navegador.
---

# FROMTED × YAIWES: frontend de interfaces

## 1. Propósito

Este skill es el punto de entrada único para construir interfaces editables, conectar comportamiento real, probarlas en navegador y entregar evidencia. Little es el perfil principal. Cristal, Naranja, Azul y Gris son propuestas que requieren aprobación visual.

Una interfaz que finge una respuesta de IA es peor que una que muestra `BRIDGE_MISSING`. El usuario confía en lo que ve, así que una demo no debe parecer producto. Por eso cada regla de abajo existe.

Estado de este skill: `REVIEW`. El perfil visual definitivo no está aprobado.

## 2. Precedencia de fuentes

Antes de cambiar código, lee en este orden:

1. **Referencia real**: Figma, capturas, frontend existente, HTML de referencia y design system. No imagines pantallas que ya estén representadas.
2. **Contexto del repo**: `AGENTS.md`, `README.md`, `manifest.json`, contratos, componentes y módulos existentes.
3. **Skills originales** 01 a 04 (tokens, catálogo de componentes, interacciones, protocolo de agente).
4. **Archivos reales del proyecto**: HTML, CSS, JS, componentes React, registros de acciones.
5. **Instrucción actual del usuario**: alcance, estilo, comportamiento y aprobaciones explícitas.

Por qué este orden: la referencia dice cómo se ve, las reglas dicen qué está permitido y el código dice qué existe. El código puede estar mal. Si contradice una regla, no lo copies: repórtalo como hallazgo (ver `references/hallazgos-revision.md`).

Una instrucción explícita del propietario gana sobre una regla y debe quedar anotada en `VERSION.md`. Es la única forma legítima de variar una regla.

Si falta un archivo, escribe `UNKNOWN` y pide la referencia concreta. No atribuyas funciones sin evidencia. Las fuentes originales no están en el repo; su lista está en `docs/handoff/SKILL_FRONTEND_FROMTED_YAIWES.md`.

## 3. Contrato no-mock y fail-closed

- Las acciones remotas son solo `chat.send`. Se ejecutan llamando a `window.YAIWES_PLUGIN_BRIDGE.execute(actionId, payload)`, y solo cuando el bridge existe y es función.
- Una acción remota está completada solo con `{ok:true, reply}` real del bridge. Un evento `yaiwes:ui-action` no es prueba de nada.
- Sin bridge: el envío devuelve `BRIDGE_MISSING`, el borrador se conserva y no aparece ningún mensaje.
- Prohibido: `setTimeout` que simule IA, texto de respuesta inventado, un PDF inventado a partir de un nombre de archivo, verde sin verificación, o endpoints ficticios.
- Los datos de ejemplo se llaman **referencia editable local**, nunca estado verificado. Las seis raíces de Crazy Wall son así.
- Secretos: nunca PAT, API keys ni `token_ref` resuelto en el navegador. `localStorage` no es una bóveda.
- Archivos: hasta 1 MB se guardan localmente. Los mayores solo viven en la pestaña y necesitan un bridge de subida, que hoy no existe.

Contrato detallado de acciones y respuestas: `references/actions-contract.md`.

## 4. Temas y tokens

- Los tokens viven en `:root` y en `html[data-theme="…"]` de `styles.css`. Los HEX completos están en `references/tokens.md`.
- Canónicos, no reescribir: `little` (principal), `matte`, `blanco`. Propuestas: `crystal`, `orange`, `blue`, `gris`.
- Terracota `#C65D3B` solo para el CTA primario en Little. El CSS actual la usa también en foco, navegación, kicker, toast y selección (hallazgo 6). No repitas ese patrón.
- Gris: sin superficies negras y sin `#000` como fondo. Los estados se oscurecen. Aun así, en gris el contraste de los estados sobre el lienzo es bajo (ver `tokens.md`). No lo des por resuelto.
- Estados semánticos, solo para estados reales: `progress` verde (`--status-green`), `enabled` azul (`--status-blue`), `warning` rojo (`--status-red`), `pending` gris (`--sub`). Nunca pintes verde una operación no ejecutada. No pintes botones de marca con colores de estado.
- Ningún color fuera de tokens. Si hace falta uno nuevo, se añade como token con justificación.

## 5. Componentes

- Reutiliza lo que existe: sidebar, topbar, inspector, sheet, toast, composer, filas de archivo, tarjetas de raíz y opciones de tema. Inventario en `references/components.md`.
- Una ventana o archivo principal por componente. El HTML único de miles de líneas no es fuente canónica.
- **Rare UI**: no copies ni descargues nada. Las cuatro adaptaciones (`bounce-sidebar`, `hook-sidebar`, `folder`, `family-drawer`) están sin verificar, con licencia pendiente y dependen de `@/components/ui/*`. Antes de usarlas, revisa la licencia, reemplaza sus colores por tokens y verifica en navegador.

## 6. Flujo de trabajo por fases

Microflujo: referencia → contexto → plan → implementar → navegador → verificar → corregir (bucle) → entregar.

**Fase 0. Referencia.** Carga la captura o el Figma. Si no hay referencia, `UNKNOWN` y pídela.

**Fase 1. Contexto.** Lee `AGENTS.md`, el README, el manifest y el código del módulo que vas a tocar. Revisa la lista de acciones.

**Fase 2. Plan.** Una tarea pequeña por ciclo. Escribe rutas, qué se preserva y los criterios. Haz inventario y snapshot del original antes de transformar nada.

**Fase 3. Implementar.** Cambia archivos mínimos. No borres handlers existentes. Usa solo acciones de la allowlist. Si añades una acción, actualiza el manifest y la tabla del contrato en el mismo cambio.

**Fase 4. Navegador.** Sirve en `http://127.0.0.1:5173`. Nunca `file://` ni `about:blank` para RELOAD: sin origen HTTP real, `localStorage` no persiste y la prueba no vale.

**Fase 5. Verificar.** Ejecuta las 11 comprobaciones de `references/verification.md`. Revisa consola y `pageerror`, y guarda capturas de escritorio (1440×900) y móvil (390×844).

**Fase 6. Entregar.** Actualiza `VERSION.md`, `ACCEPTANCE.md` y el README con decisiones, gaps, fallos y `UNKNOWN`. Entrega el código modular con sus evidencias. No despliegues nada (Hugging Face, Vercel ni GitHub Pages): el propietario lo pidió.

Corrige solo divergencias verificadas y repite. Un bloqueo técnico se anota como `BLOCKED`, nunca como `PASS`.

## 7. Criterios de aceptación (11 comprobaciones)

| ID | Exigencia | Evidencia mínima |
|---|---|---|
| REF | Colores y estructura coinciden con la referencia | HEX canónicos + comparación visual |
| LAYOUT | Sin scroll horizontal accidental | Medida a 1440 y 390 px |
| BUTTONS | Cada botón tiene acción real o bloqueo explícito | Clic y resultado observado |
| DROPDOWNS | Cambian la selección confirmada o un borrador cancelable | Selección y estado tras confirmar |
| TABS | El panel visible es el correcto | `aria-selected` y panel activo |
| INPUTS | Teclado, clic y validación de datos | Entrada y error mostrado |
| STATE | Cambios locales visibles y veraces | Estado tras acción y tras exportar |
| RELOAD | Persistencia en origen HTTP real | `page.reload()` en `http://127.0.0.1` |
| DESKTOP | Escritorio correcto | Captura y prueba a 1440×900 |
| MOBILE | Móvil correcto | Captura, scroll, tap y navegación inferior a 390×844 |
| CONSOLE | Cero errores JS inesperados | `pageerror` en cero |

**PASS final = 11 de 11 con evidencia verificable.** Además, el propietario valida visualmente si la referencia no tiene medición automática. El envío remoto se marca `BLOCKED_REMOTE` hasta tener un bridge real con prueba de integración, aunque la UI local pase.

## 8. Estados de verificación

`PASS` solo con ejecución y evidencia. Los demás son `FAIL` (ejecutado y fallado), `REVIEW` (revisado sin ejecutar completo), `BLOCKED` (no ejecutable, con causa), `BLOCKED_REMOTE` (falta backend) y `BLOCKED_ENV` (entorno). No escribas `PASS` en una línea que no se ejecutó. Motivo: una casilla verde sin ejecución es el fallo que más daño hace.

## 9. Internacionalización y accesibilidad

- Idiomas `es`, `en`, `fr`, `pt`; predeterminado `es`. Todo texto visible va a un diccionario. Hoy hay textos fijos (hallazgo 9).
- Foco visible, etiquetas en campos, estados que no dependan solo del color, contraste suficiente, navegación con teclado y tap en móvil.
- Respeta `prefers-reduced-motion` y el modo de movimiento de la configuración.
- No renombres un `actionId` sin migración: el contrato depende de él.

## 10. Límites conocidos

- No hay backend en las fuentes. El envío real queda `BLOCKED_REMOTE`.
- El snapshot autocontenido es respaldo, no fuente. No lo edites a mano.
- ACCEPTANCE declara 9 de 11 PASS. Esas pruebas no se reproducen desde las fuentes: la suite no está y el hallazgo 1 no se cubre.
- Los hallazgos graves de la revisión del chat están en `references/hallazgos-revision.md`. Resuélvelos antes de declarar un lote.

## 11. Punteros

- `references/tokens.md`: HEX de los 7 temas, estados y contraste medido.
- `references/actions-contract.md`: 23 acciones, eventos, respuestas del bus y formato del bridge.
- `references/verification.md`: cómo ejecutar Playwright, entorno, matriz de 11 comprobaciones y estado actual.
- `references/components.md`: inventario de componentes con archivo y línea, y estado de las adaptaciones Rare UI.
- `references/hallazgos-revision.md`: revisión del chat con archivo, línea y tipo de evidencia.

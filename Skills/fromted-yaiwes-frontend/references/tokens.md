# Tokens de los 7 temas (fuente: `styles.css`)

Fuente: upload `dff2f49e-_styles.css`, líneas 2-11. Cada valor se copió del CSS y no de la tabla del SKILL.

- **[C]** canónico (little, matte, blanco). No reescribir sin aprobación del propietario.
- **[P]** propuesta (crystal, orange, blue, gris). Requiere validación visual.

El tema se aplica con `html[data-theme="…"]`. Todo tema hereda de `:root`, salvo lo indicado abajo.

## Superficies y texto

| Token | little [C] | matte [C] | blanco [C] | crystal [P] | orange [P] | blue [P] | gris [P] |
|---|---|---|---|---|---|---|---|
| `--bg` (lienzo) | `#1C1B1A` | `#0a0a0d` | `#f4f4f5` | `#0c1421` | `#100e0d` | `#0a1424` | `#969ba2` |
| `--surface` | `#2A2927` | `#141417` | `#fff` | `rgba(230,247,255,.065)` | `#1c1714` | `#11223a` | `#b6bac0` |
| `--card` | `#2A2927` | `#202025` | `#fff` | `rgba(242,250,255,.095)` | `#26211d` | `#192c45` | `#d6d9de` |
| `--hover` | `#353330` | `#282830` | `#f8f8f9` | `rgba(237,251,255,.13)` | `#342a23` | `#233b56` | `#e5e7ea` |
| `--border` | `rgba(255,255,255,.1)` | `#2a2a33` | `#e4e4e7` | `rgba(190,232,252,.2)` | `#3c3029` | `#30435b` | `#858a93` |
| `--border-strong` | `rgba(255,255,255,.18)` | `#3f3f4e` | `#d4d4d8` | `rgba(190,232,252,.38)` | `#554233` | `#42617f` | `#5c626d` |
| `--title` | `#F5F4F0` | `#fff` | `#18181b` | `#f2fbff` | `#fff5eb` | `#f4faff` | `#1f2228` |
| `--text` | `#F5F4F0` | `#e4e4e7` | `#3f3f46` | `#e6f4ff` | `#f5e9df` | `#e1edfa` | `#252932` |
| `--sub` (secundario, y `pending`) | `#A8A29E` | `#a1a1aa` | `#71717a` | `#a5bfce` | `#b7a49b` | `#a1bad5` | `#484f59` |
| `--dim` | `#9C9590` | `#71717a` | `#a1a1aa` | `#829ba9` | `#907c71` | `#829ab5` | `#59616b` |

## Marca, acento y botones

| Token | little [C] | matte [C] | blanco [C] | crystal [P] | orange [P] | blue [P] | gris [P] |
|---|---|---|---|---|---|---|---|
| `--brand` | `#C65D3B` | `#2563eb` | `#2563eb` | `#b8f5fa` | `#ef823c` | `#66b7ff` | `#3b444e` |
| `--brand-hover` | `#b05031` | `#1d4ed8` | `#1d4ed8` | `#d3fcff` | `#f79351` | `#8ecaff` | `#252e37` |
| `--brand-wash` | `rgba(198,93,59,.15)` | `rgba(37,99,235,.12)` | `rgba(37,99,235,.08)` | `rgba(184,245,250,.13)` | `rgba(239,130,60,.14)` | `rgba(102,183,255,.15)` | `rgba(51,58,68,.12)` |
| `--primary-bg` | `#C65D3B` | `#e4e4e7` | `#18181b` | `#b8f5fa` | `#ef823c` | `#66b7ff` | `#303740` |
| `--primary-text` | `#fff` | `#0a0a0d` | `#fff` | `#15323c` | `#26140b` | `#0c2137` | `#fff` |
| `--scene` (fondo decorativo) | radial terracota 7% | none | none | radial azul-violeta y cian | radial naranja 12% | radial azul 19% | gradiente blanco 14% |

Nota: en gris, `--brand` (`#3b444e`) no es el `#303740` que la tabla del SKILL llama "acento". El `#303740` es `--primary-bg`.

## Estados semánticos (indicadores, no acentos de marca)

Variables: `--status-green` (progress), `--status-blue` (enabled), `--status-red` (warning), y `--sub` (pending). Fondos suaves: `--status-soft-green|blue|red`. Clases: `.tag-status.progress|enabled|warning|pending`, `.signal.progress|enabled|warning`.

| Tema | green | blue | red | soft green | soft blue | soft red | Origen |
|---|---|---|---|---|---|---|---|
| base `:root` (little, matte, crystal, orange, blue) | `#50df94` | `#65a7ff` | `#ff777e` | `rgba(80,223,148,.13)` | `rgba(101,167,255,.13)` | `rgba(255,119,126,.13)` | `:root`, línea 2 |
| blanco [C] | `#157748` | `#1c59bd` | `#bd2840` | `rgba(21,119,72,.1)` | `rgba(28,89,189,.1)` | `rgba(189,40,64,.09)` | línea 11 |
| gris [P] | `#147a44` | `#1158b6` | `#b1253e` | `rgba(20,122,68,.13)` | `rgba(17,88,182,.13)` | `rgba(177,37,62,.12)` | línea 10 |

En blanco y en gris los estados se oscurecen respecto a la base. Eso es lo que pide el SKILL.

### Contraste medido (WCAG, color sólido sobre el color indicado)

| Tema | Verde sobre card / bg | Azul sobre card / bg | Rojo sobre card / bg |
|---|---|---|---|
| little | 8,53 / 10,09 | 5,90 / 6,98 | 5,67 / 6,71 |
| matte | 9,52 / 11,60 | 6,58 / 8,03 | 6,33 / 7,71 |
| blanco | 5,58 / 5,08 | 6,54 / 5,95 | 5,93 / 5,40 |
| orange | 9,35 / 11,30 | 6,47 / 7,82 | 6,22 / 7,51 |
| blue | 8,28 / 10,83 | 5,73 / 7,49 | 5,51 / 7,20 |
| gris | **3,81 / 1,93** | 4,79 / 2,43 | 4,63 / 2,34 |

Lectura: en gris, el verde sobre la tarjeta no llega a 4,5:1 para texto, y sobre el lienzo ningún estado llega a 3:1. El tinte suave de `--status-soft-*` cambia algo estos valores; la medida es orientativa. Crystal, orange y blue usan la base `:root`; sus valores de card no son sólidos, así que su medida exacta queda en UNKNOWN.

## Colores fijos fuera de tokens

| Archivo:línea | Valor | Motivo |
|---|---|---|
| `styles.css:16` | `#ff5500` (matte) | Texto Cargar/Descargar, permitido por SKILL |
| `styles.css:16` | `#2563eb` (blanco) | Texto Descargar, permitido por SKILL |
| `styles.css:19` | `rgba(0,0,0,.63)` | `::backdrop` del sheet. Es un velo, no un fondo |
| `styles.css:19` | `rgba(0,0,0,.35)` | Sombra del sheet |

## Discrepancias entre `app.js` y el CSS

| Archivo:línea | Token | app.js | styles.css |
|---|---|---|---|
| `app.js:10` | crystal `card` | `rgba(135,190,210,.36)` | `rgba(242,250,255,.095)` (línea 6) |
| `app.js:14` | gris `accent` | `#303740` | `--brand` `#3b444e` (línea 10) |

Las miniaturas del selector de temas usan `app.js:8-14` (bg, card, accent, swatch). El tema real usa el CSS.

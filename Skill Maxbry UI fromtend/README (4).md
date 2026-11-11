# Rare UI → YAIWES · 5 componentes con código real de integración

Esta salida contiene **5 componentes adaptadores TSX escritos y utilizables**, más un codemod que modifica únicamente los colores de los componentes Rare UI instalados.

## Componentes
1. Folder
2. Bounce Sidebar
3. Hook Sidebar
4. Family Drawer
5. Proximity Sidebar

## Flujo real

```text
Rare UI upstream
      ↓
shadcn instala TSX original
      ↓
recolor-rui-01-05.mjs
      ↓
snapshot original + TSX recoloreado
      ↓
5 adaptadores YAIWES
      ↓
app/rui-demo/page.tsx
```

## Ejecutar

Copia esta carpeta dentro de tu proyecto y ejecuta:

```bash
bash scripts/install-rui-01-05.sh
```

Después importa:

```css
@import "./styles/rui-yaiwes.css";
```

y abre:

```text
/rui-demo
```

## Qué hace cada archivo

- `components/yaiwes/01-folder-yaiwes.tsx` — código del adaptador Folder.
- `components/yaiwes/02-bounce-sidebar-yaiwes.tsx` — código Bounce con azul YAIWES.
- `components/yaiwes/03-hook-sidebar-yaiwes.tsx` — código Hook con azul YAIWES.
- `components/yaiwes/04-family-drawer-yaiwes.tsx` — código contenedor del Drawer real.
- `components/yaiwes/05-proximity-sidebar-yaiwes.tsx` — código funcional y secciones de prueba.
- `scripts/recolor-rui-01-05.mjs` — cambia **solo** los colores internos que Rare UI tiene hardcodeados.
- `app/rui-demo/page.tsx` — renderiza los 5 juntos.

## Originales

El script guarda el código upstream original antes de modificarlo en:

```text
components/ui/_rare-ui-original-01-05/
```

Por tanto puedes verificar exactamente:

```text
ORIGINAL → CAMBIO DE COLOR → YAIWES
```

## Paleta

- `#1B1B1B` fondo
- `#202020` panel
- `#2A2A2A` módulo
- `#3C3C3C` seleccionado
- `#484848` máscara
- `#3A3A3A` borde
- `#525252` borde fuerte
- `#EDEDED` texto
- `#BFBFBF` secundario
- `#A0A0A0` terciario
- `#0848F7` activo
- `#12D86A` success
- `#FF475F` error/destructivo
- `#FF7B1A` warning

## Estado

El código de integración y el codemod están preparados y comprobados sintácticamente.
Los TSX Rare UI originales se obtienen del registro oficial al ejecutar el instalador; no se sustituyen por una imitación.

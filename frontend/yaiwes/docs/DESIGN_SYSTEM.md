# DESIGN_SYSTEM.md — UI YAIWES

## Tokens
Matte: `#000000 #0a0a0d #141417`  
Panel/Card: `#1a1a1e #202025`  
Borders: `#2a2a33 #3f3f4e`  
Text: `#ffffff` + grises  
Little: `#2563eb` = selection/focus/active  
Orange: `#ff5500` = solo Cargar/Descargar.

No lima/neon verde/morado como marca principal.

## Estados
default, hover, focus-visible, pressed, active, selected, expanded, disabled, error.
Estado visual debe coincidir con estado lógico (`aria-pressed/aria-selected`).

## Base components
Button, IconButton, Input, Textarea, Select, Dropdown, Toggle, Tabs, Dialog/Sheet, Card, Badge, WindowFrame, Composer, Message, ToolChip.

Preferir HTML/primitives accesibles. Custom widget exige teclado, foco, accessible name, role y state attrs.

## Referencias
`Ui Yaiwes interface beta/01-original/FOTOS-REF/` es evidencia visual/layout; no modificar originales.

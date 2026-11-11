#!/usr/bin/env bash
set -euo pipefail

npx shadcn@latest add swamimalode07/rare-ui/bounce-sidebar
npx shadcn@latest add swamimalode07/rare-ui/hook-sidebar
npx shadcn@latest add swamimalode07/rare-ui/proximity-sidebar
npx shadcn@latest add swamimalode07/rare-ui/gooey-nav
npx shadcn@latest add swamimalode07/rare-ui/family-drawer

echo "Rare UI Lote 1 instalado. Ejecuta: node patch-lote-1.mjs"

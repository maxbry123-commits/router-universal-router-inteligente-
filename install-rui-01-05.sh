#!/usr/bin/env bash
set -euo pipefail

npx shadcn@latest add swamimalode07/rare-ui/folder-component
npx shadcn@latest add swamimalode07/rare-ui/bounce-sidebar
npx shadcn@latest add swamimalode07/rare-ui/hook-sidebar
npx shadcn@latest add swamimalode07/rare-ui/family-drawer
npx shadcn@latest add swamimalode07/rare-ui/proximity-sidebar

node scripts/recolor-rui-01-05.mjs

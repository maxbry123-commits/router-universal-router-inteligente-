# Handoff Router Inteligente Universal — ADN operativo

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · repo `maxbry123-commits/router-universal-router-inteligente-` · branch `main`.

## Estado consolidado
El core del Router está `VERIFIED_CLOSED` al 100%: P01/P02/P03, certificación 20/20, Connectivity Fabric 19/19, runtime, pruebas amplias 75/75, pruebas frescas de connectivity 7/7 y comportamiento fail-closed están preservados.

## Nodo vivo
`RIU-0069_CLAUDE_DIRECT_GITHUB_ROOT_ACCESS`.

## Arquitectura e integraciones verificadas
- Fabric 19/19 bridges v2.
- Frontend/Astra integra GitHub, Hugging Face `COMAND-CENTER-1`, Jobs CPU/GPU, Space `COMAND-CENTER-1/yaiwes-ui-factory`, GitHub MCP y memoria.
- Runtime y runner de conectividad ya existen; no se requiere una arquitectura nueva ni refactor general.
- La conexión GitHub disponible en esta sesión confirmó permisos admin/push sobre Router y `TAREA-1`; esa evidencia no sustituye la validación runtime de Claude/Actions.

## Hugging Face / OIDC
- Space `COMAND-CENTER-1/yaiwes-ui-factory` confirmado como `static`.
- Publicación OIDC al Hub verificada mediante runs `34675165228` attempt 2 y `34677293995`.
- Hub read-back HTTP 200 PASS.
- Hugging Face es autoridad para recursos HF; un token HF no concede permisos de escritura GitHub.

## Claude — ruta directa GitHub
- `CLAUDE.md` en raíz define `main` como fuente de verdad.
- `GitHub Backup HF` es respaldo opcional y su ausencia no bloquea lectura, edición u organización de raíces GitHub.
- `.github/workflows/claude-root-editor.yml` ejecuta `anthropics/claude-code-action@v1` con `contents: write`, `pull-requests: write` e `issues: write`.
- Para el repo actual usa `RIU_GITHUB_PAT` si está presente o `github.token` como fallback repo-local.
- Para múltiples repos se requiere `RIU_GITHUB_PAT` o GitHub App con permisos efectivos en cada destino.
- Claude Code requiere `CLAUDE_CODE_OAUTH_TOKEN` disponible en Actions; nunca se registra el valor.

## Seguridad corregida
`.github/workflows/claude-token-setup.yml` ya no imprime la sesión completa de `claude setup-token`: solo salida sanitizada, persistencia cifrada vía helper existente y destrucción del log local.

## Evidencia fresca
- commit `f3d0daa60cecc25e711886cac6b6f468feedfe05`: setup-token seguro.
- commit `946f1a0e1c976298c6c34d4e70f0a07243109aa6`: Claude Root Editor directo.
- commit `ddfeb73e4c5d80515e28ed8511c14f8f0fc1ba88`: política raíz `CLAUDE.md`.
- workflows anteriores leídos de vuelta desde `main`.

## GAP restante — sin sobreingeniería
Solo falta evidencia runtime: ejecutar `Claude Root Editor` con `CLAUDE_CODE_OAUTH_TOKEN` presente y exigir un commit/read-back real sobre un archivo de raíz. Si se pide edición transversal, validar además el PAT/App sobre el repo objetivo. Hasta esa evidencia, `CLAUDE_ROOT_WRITE_VERIFIED` permanece PENDING.

## Fuente de verdad
- `CLAUDE.md`
- `bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/STATE.json`
- `bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/BITACORA-CRAZY-WALL.md`
- `Handoff router inteligente universal.md`

## Gate final
Ruta Claude directa=`MATERIALIZED`; backup HF=`OPTIONAL_NON_BLOCKING`; runtime root-write=`PENDING_FRESH_WRITE_READBACK`.

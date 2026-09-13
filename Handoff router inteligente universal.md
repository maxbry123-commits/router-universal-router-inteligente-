# Handoff Router Inteligente Universal — ADN operativo

Contrato: `tel.workflow/v3` · `FAIL_CLOSED_LOOP` · repo `maxbry123-commits/router-universal-router-inteligente-` · branch `main`.

## Estado consolidado
El core del Router está `VERIFIED_CLOSED` al 100%: P01/P02/P03, certificación 20/20, Connectivity Fabric 19/19, runtime, pruebas amplias 75/75, pruebas frescas de connectivity 7/7 y comportamiento fail-closed están preservados.

## Nodo vivo
`RIU-0068_BOOTSTRAP_GLOBAL_AUTH`.

## Arquitectura e integraciones verificadas
- Fabric 19/19 bridges v2.
- Frontend/Astra integra GitHub, Hugging Face `COMAND-CENTER-1`, Jobs CPU/GPU, Space `COMAND-CENTER-1/yaiwes-ui-factory`, GitHub MCP y memoria.
- Runtime y runner de conectividad ya existen; no se requiere una arquitectura nueva ni refactor general.
- La conexión GitHub disponible en esta sesión confirmó permisos admin/push sobre Router y `TAREA-1`; esa evidencia no sustituye la validación runtime de automatizaciones externas.

## Hugging Face / OIDC
- Space `COMAND-CENTER-1/yaiwes-ui-factory` confirmado como `static`.
- Publicación OIDC al Hub verificada mediante runs `34675165228` attempt 2 y `34677293995`.
- commits HF `57b5a04d371bad59bab6fa7e9db791fb982daec4` y `307549f879b6a3d40493b3bb82d285cb93f76047`.
- Hub read-back HTTP 200 PASS.
- El endpoint directo `hf.space` conserva un 404 de serving separado; no invalida la escritura OIDC ya verificada.

## Automatizaciones existentes
- `.github/workflows/riu-auth-presence-probe.yml`: verifica presencia/capacidad sin imprimir valores sensibles y realiza pruebas de identidad/permisos.
- `.github/workflows/riu-propagate-auth-secrets.yml`: propagación controlada en modo fail-closed.
- Probe previo `34677207175`: la capa global de autenticación de Actions no estaba disponible en ese momento.

## Delta restante — sin sobreingeniería
1. Completar el bootstrap externo requerido por los workflows existentes.
2. Ejecutar la propagación controlada.
3. Re-ejecutar el probe de capacidad y exigir identidad/permisos PASS.
4. Completar autenticación de las dos cuentas Codex mediante el flujo seguro ya preparado.
5. Completar autenticación Claude mediante el flujo seguro ya preparado.
6. Ejecutar E2E global GitHub + Hugging Face + MCP + memoria.
7. Cerrar únicamente con evidencia fresca de runtime/read-back.

## Qué NO falta
No falta otro router, nuevos bridges, rediseño de arquitectura ni refactor masivo. El pendiente real es la autenticación externa/runtime y su certificación E2E.

## Fuente de verdad
- `bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/STATE.json`
- `bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/BITACORA-CRAZY-WALL.md`
- `bitácora stated JSON Craxy wall plan checkpoint router inteligente universal/PLAN-TAREAS.md`

## Gate final
Estado actual: `ACTIVE_BOOTSTRAP_GLOBAL_AUTH`.
Cierre: solo cuando autenticación global + Codex + Claude + MCP + memoria + E2E de conectividad tengan evidencia fresca verificable.

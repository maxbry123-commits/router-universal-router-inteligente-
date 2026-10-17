# AGENTS.md — UI YAIWES interface

Estado: ACTIVE · fecha: 2026-09-27  
Objetivo: que cualquier IA/agente pueda retomar y ejecutar el proyecto sin depender del historial del chat.

## Lectura obligatoria
1. `readme arquitectura UI YAIWES interface beta/METODO-DE-TRABAJO.md`
2. `EXECUTION-CONTRACT.md`
3. `readme arquitectura UI YAIWES interface beta/ARQUITECTURA-FRONTEND-UI-YAIWES-V1.md`
4. `readme arquitectura UI YAIWES interface beta/PLAN-DE-TRABAJO-UI-YAIWES.md`
5. `readme arquitectura UI YAIWES interface beta/actualizaciones arquitectura/HANDOFF-SKILLS-UI-YAIWES-2026-09-27.md`
6. `SKILL.md`
7. `DESIGN_SYSTEM.md`
8. `COMPONENT_INDEX.md`
9. `ACCEPTANCE.md`
10. `readme arquitectura UI YAIWES interface beta/HANDOFF-FRONTEND-UI-YAIWES.json`
11. `Ui Yaiwes interface beta/01-original/FOTOS-REF/`

## Staff
- Director: requisitos y aprobación final.
- Codex: EXECUTOR + IMPROVER; implementa, refactoriza, prueba y corrige.
- v0: VISUAL_BOOTSTRAP opcional para screenshot/diseño -> primera propuesta.
- Reference Reader: forense de referencias/assets.
- Design System Agent: aplica tokens/componentes.
- Meta Visual Reviewer: usa Meta OSS Cookbook/Muse Glimmer solo si existe adapter/runtime real; si no: `META_REVIEW_UNAVAILABLE`.
- Sheriff: policy gate.
- Validator: Schema/Contract/manifest.
- Verifier: browser/Playwright.
- Sentinel Web Auditor: investiga documentación/web oficial cuando aplique y audita el resultado.
- Guardian: cierre; exige evidencia y 100% PASS.

## Jerarquía
`Director > referencia visual > design system > componentes existentes > archivos proyecto > SKILL/AGENTS > inferencia`.

## Ejecución
`READ -> CONTRACT -> SHERIFF -> IMPLEMENT -> RUN -> BROWSER -> INTERACT -> CAPTURE -> COMPARE -> FIX -> META REVIEW -> SENTINEL -> VERIFY -> GUARDIAN`.

## Fórmula
`REFERENCE + CONTEXT + SKILLS + BROWSER + VERIFIER`.

## Salida FIFA
HTML funcional/autocontenido + fuente modular + assets + dependencias + manifest + tests + versión + evidencia desktop/móvil.

## Prohibiciones
No mock final; no controles muertos; no UI/modelos/capacidades inventadas; no tocar `01-original/`; no proveedores directos desde UI; no PASS parcial; no donor skill activo sin scope+adapter+test; no fingir revisión externa.

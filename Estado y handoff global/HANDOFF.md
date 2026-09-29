# HANDOFF GLOBAL — router-universal-router-inteligente-
Actualizado: 2026-09-29. Quien retome: lee esto, luego `CRAZY_WALL.json`, `ESTADO.json` y `BITACORA.jsonl` (misma carpeta). No inventes: si algo no está aquí, pregunta al Director.

## Tareas (una ficha por tarea; cada enlace sirve como handoff y control de trabajo)
Base: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Estado%20y%20handoff%20global/tareas/

| # | Tarea | Estado | Ficha |
|---|---|---|---|
| T-00 | Auditar Router y dejar uno solo | PASS | `T-00-auditar-router-y-unificar.md` |
| T-01 | Limpieza del repo y de Hugging Face | PASS (Vercel queda para después) | `T-01-limpieza-repo-y-hf.md` |
| T-02 | Reorganizar el repo en las raíces pedidas | PASS | `T-02-reorganizar-repo-en-raices.md` |
| T-03 | Quitar Cerebras del código del Router y poner Groq | PENDIENTE | `T-03-quitar-cerebras-poner-groq.md` |
| T-04 | Equipo de los 4 objetivos conectado al Router único + sentinela | PENDIENTE | `T-04-equipo-4-objetivos-al-router.md` |
| T-05 | 20 sitios de investigación en el motor de búsqueda | PENDIENTE | `T-05-veinte-sitios-de-investigacion.md` |
| T-06 | Cadena Rowboat → Ruflo → Claude Code → Grok → Claude Code → 4 Meta | PENDIENTE | `T-06-cadena-rowboat-a-4-meta.md` |
| T-07 | Skills (ECC, Archify, Agent Skills, Ponytail) a esquema Sheriff/DSL DAG | PENDIENTE | `T-07-skills-a-esquema-sheriff.md` |
| T-08 | Memoria de Manus + puente Hugging Face | PENDIENTE | `T-08-memoria-manus-y-puente-hf.md` |
| T-09 | Un solo deploy final en Vercel | BLOQUEADO (solo con orden del Director) | `T-09-vercel-deploy-final.md` |

## Dónde está cada cosa (main)
`router inteligente universal/` (Router, `Banco de claves/`, `Componentes del Router/`) · `chat router/` · `Motores descarga extracción búsquedas/` · `Readme router inteligente universal/` · `Readme arquitectura router inteligente universal/` · `Claude notas/` (solo en curso) · `Estado y handoff global/` (esta carpeta) · `Huggingface/` (incluye `README-HUGGINGFACE.md`) · `Vercel/` (incluye `HANDOFF-VERCEL.md`) · `Documentos del proyecto/`. Sueltos: `README.md`, `CLAUDE.md`, `vercel.json`.
Para llevarse la raíz del Router a otro repo: copiar `router inteligente universal/` completa (lanzador: `.github/workflows/riu-router-job-central.yml`).

## Reglas del Director (siempre)
- Seguir sus instrucciones textuales; sin alucinar, sin sobre-ingeniería; si hay duda, preguntar en texto plano (nada de widget de opciones: usa el móvil).
- Modelos SOLO por el Router único: NVIDIA (hasta 4 claves; Kimi K3 o el más nuevo) → Groq → DeepSeek V4 Flash al final. Cerebras y OmniRoute eliminados. Sin APIs de Anthropic.
- Nunca claves en el repo (es público): solo nombres de secretos.
- Vercel = solo pantalla. No instalar nada hasta que todo esté listo; un único deploy final, solo si él lo ordena.
- No tocar ni reiniciar el conector MCP (Space `claude-github-mcp-backup`). `keep-mcp-space-awake` sigue desactivado.
- Prohibido escribir código desde cero: podar, editar quirúrgico y cablear lo descargado.
- No borrar componentes: se reubican.
- Respuestas cortas (~10 líneas), español simple. Explicar el cómo antes de hacer.

## Abiertos / no inventar
- "Prompt Master": no verificado qué es. Buscar en `Documentos del proyecto/Notas del Director (verbatim)/`; si no aparece, decir que no se sabe.
- Rotar las 7 llaves de Groq que pegó el Director en el chat.
- Lo del conector MCP hecho por Opus está documentado, no verificado por mí.
- El loop del repo `agentes` todavía usa la ruta vieja del banco (`Chat%20Mvp/…`); se resuelve en T-04.
- Los workflows cuyas rutas se corrigieron (banco de claves, motores, `chat_orders`, `scripts`, búsqueda web) no se probaron en vivo todavía.

## Cómo se trabaja (herramientas)
- GitHub por conector: `github_api` (puede lanzar workflows), `create_or_update_file` (usa `current_sha` para actualizar). Errores 502: reintentar, comprobando antes que la acción no se haya hecho.
- Cambios grandes: workflow de una sola vez con PAT (el token por defecto no puede empujar archivos de workflow) y `[skip ci]` en el commit para no disparar otros workflows.
- Resultados de un run: leer las anotaciones del check-run (máx. 10 por paso).

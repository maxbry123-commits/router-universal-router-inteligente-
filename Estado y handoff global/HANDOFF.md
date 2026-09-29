# HANDOFF GLOBAL — router-universal-router-inteligente-
Actualizado: 2026-09-29. Quien retome: lee esto, luego `CRAZY_WALL.json`, `ESTADO.json` y `BITACORA.jsonl` (misma carpeta). No inventes: si algo no está aquí, pregunta al Director.

**Todo lo del Router** (el Router, sus conexiones, claves, Hugging Face, Vercel y sus tareas T-00, T-01, T-03, T-10) vive SOLO en `router inteligente universal/HANDOFF-PROVISIONAL-ROUTER.md` y `router inteligente universal/CONECTAR-ROUTER.md`. Aquí no se repite, para no mezclar.

## Tareas (una ficha por tarea; cada enlace sirve como handoff y control de trabajo)
Base: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Estado%20y%20handoff%20global/tareas/

| # | Tarea | Estado | Ficha |
|---|---|---|---|
| T-02 | Reorganizar el repo en las raíces pedidas | PASS | `T-02-reorganizar-repo-en-raices.md` |
| T-04 | Equipo de los 4 objetivos conectado al Router único + sentinela | PENDIENTE | `T-04-equipo-4-objetivos-al-router.md` |
| T-05 | 20 sitios de investigación en el motor de búsqueda | PENDIENTE | `T-05-veinte-sitios-de-investigacion.md` |
| T-06 | Cadena Rowboat → Ruflo → Claude Code → Grok → Claude Code → 4 Meta | PENDIENTE | `T-06-cadena-rowboat-a-4-meta.md` |
| T-07 | Skills (ECC, Archify, Agent Skills, Ponytail) a esquema Sheriff/DSL DAG | PENDIENTE | `T-07-skills-a-esquema-sheriff.md` |
| T-08 | Memoria de Manus + puente Hugging Face | PENDIENTE | `T-08-memoria-manus-y-puente-hf.md` |
| T-09 | Un solo deploy final del chat en Vercel | BLOQUEADO (solo con orden del Director) | `T-09-vercel-deploy-final.md` |

Las tareas del Router (T-00, T-01, T-03, T-10) ya no están aquí: ver el handoff provisional del Router.

## Dónde está cada cosa (main)
`router inteligente universal/` (Router, `Banco de claves/`, `Componentes del Router/`) · `chat router/` · `Motores descarga extracción búsquedas/` · `Readme router inteligente universal/` · `Readme arquitectura router inteligente universal/` · `Claude notas/` (solo en curso) · `Estado y handoff global/` (esta carpeta) · `Huggingface/` · `Vercel/` · `Documentos del proyecto/`. Sueltos: `README.md`, `CLAUDE.md`, `vercel.json`.

## Reglas del Director (siempre)
- Seguir sus instrucciones textuales; sin alucinar, sin sobre-ingeniería; si hay duda, preguntar en texto plano (nada de widget de opciones: usa el móvil).
- Los modelos se llaman SOLO por el Router único (ver su handoff). Sin APIs de Anthropic.
- Nunca claves en el repo (es público): solo nombres de secretos.
- No instalar nada hasta que todo esté listo; un único deploy final, solo si él lo ordena.
- No tocar ni reiniciar el conector MCP (Space `claude-github-mcp-backup`). `keep-mcp-space-awake` sigue desactivado.
- Prohibido escribir código desde cero: podar, editar quirúrgico y cablear lo descargado.
- No borrar componentes: se reubican.
- Respuestas cortas (~10 líneas), español simple. Explicar el cómo antes de hacer.

## Abiertos / no inventar
- "Prompt Master": no verificado qué es. Buscar en `Documentos del proyecto/Notas del Director (verbatim)/`; si no aparece, decir que no se sabe.
- El loop del repo `agentes` todavía usa la ruta vieja del banco (`Chat%20Mvp/…`); se resuelve en T-04.
- Workflows con rutas corregidas en la reorganización que no se probaron en vivo: `riu-microkernel-run`, `riu-agents-run`, `riu-chat-mvp-core-verify`, `riu-agent11-canonical-download` (además mira `hermes-agent/` en la raíz, que ahora está en `Componentes del Router/`), `riu-websearch`, `riu-websearch-run`, `riu-dag-run`, `riu-propagate-auth-secrets`.
- Link del chat de Manus: pendiente de que lo pase el Director (T-08).

## Cómo se trabaja (herramientas)
- GitHub por conector: `github_api` (puede lanzar workflows), `create_or_update_file` (usa `current_sha` para actualizar). Errores 502: reintentar, comprobando antes que la acción no se haya hecho.
- Cambios grandes: workflow de una sola vez con PAT (el token por defecto no puede empujar archivos de workflow), checkout parcial en lote (rápido) y `[skip ci]` en el commit para no disparar otros workflows. El workflow se borra a sí mismo al aplicar.
- Resultados de un run: leer las anotaciones del check-run (máx. 10 por paso).

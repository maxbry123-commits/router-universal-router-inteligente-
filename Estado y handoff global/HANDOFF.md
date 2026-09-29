# HANDOFF GLOBAL — router-universal-router-inteligente-
Actualizado: 2026-09-29 (checkpoint ~11:20 Bogotá; antes, la versión de la mañana). Quien retome: lee esto, luego `CRAZY_WALL.json`, `ESTADO.json` y `BITACORA.jsonl` (misma carpeta). No inventes: si algo no está aquí, pregunta al Director.

**Todo lo del Router** (el Router, sus conexiones, claves, Hugging Face, Vercel y sus tareas T-00, T-01, T-03, T-10) vive SOLO en `router inteligente universal/HANDOFF-PROVISIONAL-ROUTER.md` y `router inteligente universal/CONECTAR-ROUTER.md`. Aquí no se repite el detalle, para no mezclar; PERO desde el 11:07 el Director ordena checkpoints progresivos también aquí, así que la sección «Checkpoint progresivo» de abajo trae el resumen y los punteros.

## Checkpoint progresivo 2026-09-29 (~11:20 Bogotá) — Router, chat como plugin y Plugin Host
Para quien llega sin contexto: el proyecto tiene UN Router de modelos de IA (un Job de Hugging Face); todo lo demás (el chat, los agentes, las pantallas) se conecta a él como un plugin. El Director ordenó (11:07) dejar el estado anotado por partes por si Anthropic se satura. Detalle completo, una sola nota: `Claude notas/CHECKPOINT-2026-09-29-1100-router-chat-plugins.md`. Estado técnico del Router: `router inteligente universal/HANDOFF-PROVISIONAL-ROUTER.md` (secciones 10 a 19). Bitácora: `BITACORA.jsonl` (B-0022 a B-0029). Rama de trabajo: `bloque1-cadena-chat` (todavía NO unida a main).
Marcas: ✅ VERIFICADO (ejecutado + probado + 4 pasadas de revisión + 3 rondas limpias seguidas) · 🟡 HECHO SIN PROBAR / probado a medias · 🔴 PENDIENTE · ⛔ BLOQUEADO. **Nada está ✅ todavía**: las rondas 1 y 2 de auditoría independiente salieron NO LIMPIAS (sin bloqueadores, con defectos reales ya corregidos en código).

### Órdenes del Director vigentes
- 10:55 (textual según el archivo de hechos): "Ok termina el router y activalo / El chat es solo un plugins más conectado al router" → autoriza relanzar el Job del Router tras terminarlo; el chat es UN plugin más, no el centro.
- 11:07 (paráfrasis; el texto literal no está en el repo): checkpoint progresivo (bitácora, estado JSON, handoff, Claude notas, Crazy Wall); no desviarse; terminar el Router primero (prioridad 1) con un agente auditándolo en paralelo; luego chat + agentes (prioridad 2): DSL DAG con loops, agente orquestador, Hermes y OpenClaw como asistente/sheriff/sentinela/supervisor/juez/guardián/investigador de contexto/manipulación de memoria y almacenamiento, harness de DeepSeek; generar un espejo (mirror) solo de Hermes+OpenClaw o de todo el equipo, y varias UI de chat una debajo de otra, todo separado, nada monolítico.
- 11:11 (paráfrasis): delegar varias tareas a varios agentes (Claude escribe el código, ellos hacen lo demás) para terminar lo antes posible.
- 05:18 (textual): 3 bucles de revisión + 4 pasadas por tarea terminada; sin eso no es ✅. 02:06 (textual): "El chat y los agentes de Hermes y open claw prioridad con Nvidia si está ocupado las primeras 3 Salta a la 4 o a groq" (hoy solo cubre el chat y a medias; Hermes/OpenClaw sin tocar).

### Estado por bloque
- 🟡 Prioridad 1, Bloque 1 (cadena de modelos del chat dentro del Router): hecho y probado en CI (corridas 36557644179, 36561019462, 36562078042 del flujo temporal; 183 pasan en la rama contra 153 en main con el mismo conjunto de 14 fallos previos; 42 pruebas de la cadena; mutaciones 27 de 28 detectadas; en vivo, la cadena Kimi K3 → GLM 5.3 → DeepSeek V4 → Qwen 3.8 (Groq) → Nemotron último funciona escalón por escalón). No es ✅.
- 🟡 Correcciones de la ronda 2 (9 puntos): subidas a la rama entre las 11:14 y las 11:18, SIN CI.
- 🔴 El Router VIVO (Job `6abb503a6b030d633f6a2dca`) no corre nada de esto; relanzarlo requiere: CI verde, Plugin Host mínimo, unir a main; y arreglar dos huecos del lanzador (no pasa `HF_TOKEN_1` ni `RIU_CHAT_ALLOW_PROVIDER_LIVE=1` al Job).
- 🟡/🔴 Bloque 2, Plugin Host mínimo con el chat como primer plugin: EN CONSTRUCCIÓN por otro agente; sin código en la rama al 11:20, sin pruebas.
- 🔴 Bloque 3: registro de fichas, compilador ficha→flujo, agente operador, autodetección, gobernador de capacidad paralelo/cola, ZIP de subrouters montado APAGADO con interruptor, conectores plugin (HTTP, SSH, MCP, push), dataset Yaiwes y anclas del Control Plane.
- 🔴 Después del Router: chat + agentes (prioridad 2), IA local en la máquina de 32 GB, autoescalado, pantalla final (al último, con la skill de diseño que dará el Director).

### Tareas del Router que se mueven con esto (una línea cada una; detalle en el handoff del Router)
| # | Marca | Resumen |
|---|---|---|
| T-10 | 🟡 | Guía de conexión reescrita; `provider:"auto"` obligatorio; `RouterCliente` sin parche |
| T-11 | 🔴 | IA local en 32 GB, después del Router |
| T-12 | 🟡 | Cadena del chat hecha y probada en CI en la rama; no en el Router vivo |
| T-13 | 🟡/🔴 | Claves NVIDIA 1→4 hechas para el chat; sin salto directo a Groq; Hermes/OpenClaw sin tocar |
| T-14 | 🔴 | Autoescalado: no existe |
| T-15 | 🟡/🔴 | Plugin Host en construcción por otro agente |
| T-16 | 🔴 | ZIP de subrouters/thinking: montar apagado con interruptor |
| T-17 / T-18 / T-19 | 🔴 | Cruce con Opus (parcial) / prueba del Router y equipo de 4 objetivos / aceleradores HF |
| T-20 | 🟡 | Lista de modelos disponibles + Nemotron último: hecho en la rama y probado en CI |
| T-21 / T-22 / T-23 / T-24 | 🔴 | Paralelo y cola / fichas / pantalla final / dataset y Control Plane |
| T-25 | — | No definida en ninguna fuente: no se inventó |

### Lo que decide el Director (detalle en la nota de checkpoint)
DeepSeek en hora pico (hoy se salta en `default`, `g2` y `minor`); Nemotron segundo en `minor`; OK a la reescritura de `g2`; salto directo a Groq; si una respuesta vacía debe pasar al siguiente modelo; plazo TOTAL de la cadena (hoy hasta ~210–450 s); OK al «tribunal» de plugins; borrar `.omniroute_proxy` y `.github/omniroute-relaunch.trigger`; rotar las 7 llaves Groq.

### Incidente y lección de hoy
El script local de mutaciones se interrumpió a las 10:55 y dejó una mutación en `model_pool.py` del árbol de trabajo local; se detectó por las pruebas locales antes de subir y se restauró (35/35); nada mutado llegó al repo. Lección: las mutaciones se corren en una COPIA o en CI, y las pruebas locales se corren ANTES de cada push.

### Estado de subida del código (comprobado al escribir)
Estado de subida comprobado con `git fetch` a las 11:33 (Bogotá); rama `bloque1-cadena-chat` en el commit cb229a12. Un archivo cuenta como subido solo si el blob de la rama es igual a `git hash-object` del archivo local:
- `router inteligente universal/integration/chat_mvp/resilience.py` [cambio de la ronda 2]: local `c3043881` · rama `c3043881` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/model_pool.py` [cambio de la ronda 2]: local `34df8847` · rama `34df8847` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/router.py` [cambio de la ronda 2]: local `3b0445af` · rama `3b0445af` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/route_api.py`: local `83d2e677` · rama `83d2e677` → SUBIDO (blob igual)
- `router inteligente universal/integration/chat_mvp/providers.py`: local `bd96dd07` · rama `bd96dd07` → SUBIDO (blob igual)
- `router inteligente universal/tests/test_resilience.py` [cambio de la ronda 2]: local `26255aa3` · rama `26255aa3` → SUBIDO (blob igual)
- `router inteligente universal/tests/test_model_pool.py` [cambio de la ronda 2]: local `cc5b8fa1` · rama `cc5b8fa1` → SUBIDO (blob igual)
- `router inteligente universal/tests/test_chat_mvp_app.py`: local `fd64ad22` · rama `fd64ad22` → SUBIDO (blob igual)
Veredicto: las correcciones de la ronda 2 en resilience.py, model_pool.py y router.py están SUBIDAS a la rama. Siguen SIN CI (ninguna corrida las ha ejecutado).

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
`router inteligente universal/` (Router, `Banco de claves/`, `Componentes del Router/`) · `chat router/` · `Motores descarga extracción búsquedas/` · `Readme router inteligente universal/` · `Readme arquitectura router inteligente universal/` · `Claude notas/` (solo en curso; el checkpoint vigente es `CHECKPOINT-2026-09-29-1100-router-chat-plugins.md`) · `Estado y handoff global/` (esta carpeta) · `Huggingface/` · `Vercel/` · `Documentos del proyecto/`. Sueltos: `README.md`, `CLAUDE.md`, `vercel.json`.

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
- Rama `bloque1-cadena-chat`: NO está unida a main; el código de la cadena del chat solo existe allí. Los workflows temporales (`tmp-bloque1-cadena-verify.yml`, en main) hay que borrarlos al terminar.
- `T-25`: no está definida en ninguna fuente; si existe, que el Director o el coordinador la definan (no se inventó).
- Cifras de pruebas de fuentes distintas que no se han reconciliado: 168 pasan / 8 fallan / 0 errores (corrida 36526076292) frente a 153 / 8 / 6 (main, carpeta completa); ver el handoff del Router, sección 18.
- "Prompt Master": no verificado qué es. Buscar en `Documentos del proyecto/Notas del Director (verbatim)/`; si no aparece, decir que no se sabe.
- El loop del repo `agentes` todavía usa la ruta vieja del banco (`Chat%20Mvp/…`); se resuelve en T-04.
- Workflows con rutas corregidas en la reorganización que no se probaron en vivo: `riu-microkernel-run`, `riu-agents-run`, `riu-chat-mvp-core-verify`, `riu-agent11-canonical-download` (además mira `hermes-agent/` en la raíz, que ahora está en `Componentes del Router/`), `riu-websearch`, `riu-websearch-run`, `riu-dag-run`, `riu-propagate-auth-secrets`.
- Link del chat de Manus: pendiente de que lo pase el Director (T-08).

## Cómo se trabaja (herramientas)
- GitHub por conector: `github_api` (puede lanzar workflows), `create_or_update_file` (usa `current_sha` para actualizar). Errores 502: reintentar, comprobando antes que la acción no se haya hecho.
- Cambios grandes: workflow de una sola vez con PAT (el token por defecto no puede empujar archivos de workflow), checkout parcial en lote (rápido) y `[skip ci]` en el commit para no disparar otros workflows. El workflow se borra a sí mismo al aplicar.
- Resultados de un run: leer las anotaciones del check-run (máx. 10 por paso).

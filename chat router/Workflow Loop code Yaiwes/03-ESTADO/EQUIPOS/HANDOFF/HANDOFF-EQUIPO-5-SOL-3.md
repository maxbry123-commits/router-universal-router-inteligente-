# HANDOFF EQUIPO-5 — Sol 🐻 3 — Lote SKILLS-UI (28 repos descargados)

## 0. Dónde estás parado (todo en la rama del PR #6, nunca en main)
- Repo: https://github.com/maxbry123-commits/router-universal-router-inteligente-
- Rama: `devin/1790824641-chat-agent-plan`
- Carpeta de trabajo (RAIZ-WL): https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes
- TU ARCHIVO, aquí escribes tu resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/EQUIPO-5-SOL-3.json
- Reglas de todos: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/00-LEEME-EQUIPOS.md
- Esquema de cada entrada de resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/ESQUEMA-TRAZABILIDAD.json
- Carpeta de tu evidencia (créala con el primer archivo real): `chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/equipos/EQUIPO-5/`

## 1. Qué hay que cerrar
28 repos de skills y componentes de UI ya descargados con el motor. TODOS están como 'por verificar integración': descargar NO es integrar. Hay que clasificar cada uno y dar contrato solo a los que apliquen. Son capacidades, no agentes ni staff.

Lista exacta (28): npxskillui, recordly, rare-ui, shadcn-skills, firecrawl, firecrawl-cli, firecrawl-mcp-server, firecrawl-skills, emilkowalski-skills, impeccable, getdesign, open-design, headroom, ponytail, find-skills, superpowers, get-shit-done, claude-mem, context-mode, local-ultra-review, one-skill-to-rule-them-all, motionsites, caret-desktop, onlook, plasmic, webstudio, taste-skill, magic-mcp.

## 2. Dónde está cada cosa
- Veredicto del motor (cola): `chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/motor2-skills-ui/queue.json` https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/11-EVIDENCIA/motor2-skills-ui/queue.json
  Si ese archivo no existe en la rama, escribe `GAP-ACCESO` con la ruta que intentaste y para. No lo reconstruyas de memoria.
- Código descargado de cada repo (solo lectura), carpeta por nombre: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/router%20inteligente%20universal/Componente%20open%20soure%20router%20inteligente%20universal
- Dónde van los esquemas de skills (RAIZ-WL): https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema (copia el formato de un `.dag.yaml` existente; hay 24)
- Cómo se registra una capacidad: `COMPONENT_CAPABILITIES` en `wordflow_loop/wordflow_loop/orchestrator_adapters.py` (RAIZ-WL). Cableado, sin lógica nueva.

## 3. Grupos (así se reparten las tareas)
| Tarea | Grupo | Repos |
|---|---|---|
| C-03 | Firecrawl | firecrawl, firecrawl-cli, firecrawl-mcp-server, firecrawl-skills |
| C-04 | Contexto | context-mode, headroom, ponytail, claude-mem |
| C-05 | Diseño 1 | shadcn-skills, rare-ui, taste-skill, emilkowalski-skills, impeccable |
| C-06 | Diseño 2 | getdesign, open-design, npxskillui, magic-mcp |
| C-07 | Método | superpowers, get-shit-done, find-skills, local-ultra-review, one-skill-to-rule-them-all |
| C-08 | Apps | caret-desktop, onlook, plasmic, webstudio, motionsites, recordly (solo registrar capacidades si son apps de escritorio) |

## 4. RONDA 1 (haz solo estas 3, luego commit y sal)
- C-01 Leer el veredicto del motor de los 28 repos
- C-02 Clasificar cada repo en una de tres: `skill`, `herramienta` o `solo referencia`. Escribe la tabla de 28 filas en `resultado` con la razón de una frase por cada una
- C-03 Grupo Firecrawl: un `.dag.yaml` por skill y entrada de capacidad solo si la clasificación de C-02 dice `herramienta`

## 5. Cómo escribes el resultado
Una entrada por tarea en `resultado` (esquema), `estado` en `cola`, una línea en `bitacora` y `handoff` actualizado. Evidencia real con sha256 en `chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/equipos/EQUIPO-5/`.

## 6. Si falta algo o no corre
No escribas código para reemplazarlo. `gap` con el motivo exacto. Si hay que traer algo de GitHub: solo con los motores de descarga y extracción de main.

## 7. Si no puedes leer una URL o escribir en GitHub
No inventes. `GAP-ACCESO` y para; o devuelve tus entradas como arreglo JSON que cumpla el esquema y Claude las sube.

## 8. Prohibido
Tocar el router (`router inteligente universal/` es solo lectura), LFS git, GitHub Actions, Hugging Face. No editar a mano STATE.json, BITACORA.jsonl ni CRAZY_WALL.json.

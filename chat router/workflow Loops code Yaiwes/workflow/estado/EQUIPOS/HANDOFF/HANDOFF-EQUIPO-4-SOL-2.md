# HANDOFF EQUIPO-4 — Sol 🏭 2 — Crazy Wall visual (O4-17), cierre O4-20 y pre-auditoría

## 0. Dónde estás parado (todo en la rama del PR #6, nunca en main)
- Repo: https://github.com/maxbry123-commits/router-universal-router-inteligente-
- Rama: `devin/1790824641-chat-agent-plan`
- Carpeta de trabajo (RAIZ-WL): https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes
- TU ARCHIVO, aquí escribes tu resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/EQUIPO-4-SOL-2.json
- Reglas de todos: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/00-LEEME-EQUIPOS.md
- Esquema de cada entrada de resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/ESQUEMA-TRAZABILIDAD.json
- Carpeta de tu evidencia (créala con el primer archivo real): `chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/equipos/EQUIPO-4/`

## 1. Qué hay que cerrar
O4-17: dibujar el Crazy Wall (el tablero de nodos y estados) a partir del registro real de eventos (ledger), no de datos inventados. O4-20: auditoría de cierre de los nodos O4. Más: pre-auditar a los otros equipos para que Claude audite más rápido (no reemplaza la auditoría de Claude).

## 2. Piezas exactas (dentro de RAIZ-WL; léelas antes de escribir nada)
- Función a usar: `build_crazy_wall_projection` en `runtime/src/core/graph_visual_projection.py` https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/runtime/src/core/graph_visual_projection.py
- Su test existente: `runtime/tests/test_graph_visual_projection_g026.py` (úsalo como modelo)
- Evidencia anterior: `wordflow_loop/evidence/G026_CRAZY_WALL_VISUAL_PROJECTION_2026-09-12.json`
- Ledger real: `EvidenceLedger` en `wordflow_loop/wordflow_loop/orchestrator_adapters.py` y `wordflow_loop/wordflow_loop/ledger.py`
- Componente Archify (solo lectura, ya descargado): carpeta `archify` dentro de https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/router%20inteligente%20universal/Componente%20open%20soure%20router%20inteligente%20universal
- Prueba E2E que debe seguir pasando (O4-19): `runtime/tests/test_orchestrator_e2e.py`

Cómo correr tests: `cd "chat router/Workflow Loop code Yaiwes" && source ~/.venv-riu/bin/activate && pytest runtime/tests -q`. Base: 267 pass / 3 stale (no tocar los 3 stale).

## 3. Dónde dejas el resultado visual
`chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/equipos/EQUIPO-4/crazy_wall_projection.html` (o `.svg`), con su sha256 en el resultado. Debe generarse del ledger real; si el ledger está vacío, di eso en `gap`, no lo rellenes con datos de mentira.

## 4. RONDA 1 (haz solo estas 3, luego commit y sal)
- B-01 Leer `build_crazy_wall_projection` y anotar qué entrada espera y qué devuelve
- B-02 O4-17: generar la proyección desde el ledger real
- B-03 Guardar la proyección en `EQUIPO-4/` con sha256

## 5. Más adelante (no ahora)
B-09 a B-11 son pre-auditorías de los resultados de otros equipos. Solo leerás sus archivos `EQUIPO-N-*.json` en esta misma carpeta; nunca edites el JSON de otro equipo.

## 6. Cómo escribes el resultado
Una entrada por tarea en `resultado` (esquema), `estado` de la tarea en `cola`, una línea en `bitacora` y `handoff` actualizado.

## 7. Si no puedes leer una URL o escribir en GitHub
No inventes. `GAP-ACCESO` y para; o devuelve tus entradas como arreglo JSON que cumpla el esquema y Claude las sube.

## 8. Prohibido
Tocar el router (`router inteligente universal/` es solo lectura), LFS git, GitHub Actions, Hugging Face. No editar a mano STATE.json, BITACORA.jsonl ni CRAZY_WALL.json. Si falta un componente: no escribas código, bájalo con los motores de descarga y extracción de main.

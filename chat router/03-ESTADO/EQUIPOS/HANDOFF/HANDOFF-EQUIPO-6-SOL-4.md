# HANDOFF EQUIPO-6 — Sol 🧑‍💻 4 — Memoria y almacenamiento (solo local)

## 0. Dónde estás parado (todo en la rama del PR #6, nunca en main)
- Repo: https://github.com/maxbry123-commits/router-universal-router-inteligente-
- Rama: `devin/1790824641-chat-agent-plan`
- Carpeta de la memoria: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/04-MEMORIA
- TU ARCHIVO, aquí escribes tu resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/EQUIPO-6-SOL-4.json
- Reglas de todos: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/00-LEEME-EQUIPOS.md
- Esquema de cada entrada de resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/ESQUEMA-TRAZABILIDAD.json
- Carpeta de tu evidencia (créala con el primer archivo real): `chat router/11-EVIDENCIA/equipos/EQUIPO-6/`

## 1. Estado real hoy (del handoff del Devin, no lo repitas de memoria: verifícalo)
- Funciona: SQLite y grafo SQLite de respaldo. 8/8 pruebas focalizadas. Rutas `/memoria/*` montadas.
- NO demostrado: Graphiti y Graphify (solo código fuente descargado, sin servicio); FalkorDB y AgentDB (fuente extraída, sin conectar); Memanto (sin contrato runtime); PostgreSQL y Redis (sin servicio).
- Fuente: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/HANDOFF.md (sección 'Auditoría Manus y organización T-01')

## 2. Piezas exactas
- Código de memoria: `chat router/04-MEMORIA/memoria_yaiwes/__init__.py` https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/04-MEMORIA/memoria_yaiwes/__init__.py
- Inventario actual (el histórico del 27-sep NO se borra, se le agrega lo nuevo): https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/MEMORIA-INVENTARIO.json
- Script del inventario: `chat router/03-ESTADO/inventory_memory.py`
- Adaptador de Graphiti ya existente (RAIZ-WL): `runtime/src/core/graphiti_temporal_adapter.py` y su test `runtime/tests/test_graphiti_temporal_adapter_g027.py` en https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes
- Plan de memoria: `chat router/01-PLAN/DSL-DAG-MEMORIA-ALMACENAMIENTO.yaml`
- SOLO LECTURA (es del Router, no se toca): `router inteligente universal/integration/chat_mvp/memoria_loader.py`

## 3. RONDA 1 (haz solo estas 3, luego commit y sal)
- D-01 Inventario con evidencia actual: para cada componente de memoria (SQLite, grafo SQLite, Graphiti, Graphify, FalkorDB, AgentDB, Memanto, PostgreSQL, Redis) di si corre o no, con la prueba. Agrégalo a `MEMORIA-INVENTARIO.json` sin borrar lo anterior
- D-02 Graphify: contrato de herramienta de solo lectura
- D-03 Graphiti: probar si corre en local sin servicio. Si no, GAP con el motivo exacto

## 4. Cómo escribes el resultado
Una entrada por tarea en `resultado` (esquema), `estado` en `cola`, una línea en `bitacora` y `handoff` actualizado. Evidencia real con sha256 en `chat router/11-EVIDENCIA/equipos/EQUIPO-6/`.

## 5. Límites claros
- Nada de Hugging Face: el puente HF (H-1) queda fuera y se registra como GAP estructural.
- No se toca el Router. Lo que el Router necesite se lista en D-11 para el Director.
- Si un servicio (PostgreSQL, Redis) no se puede levantar en tu entorno: GAP con motivo, y se prueba el respaldo SQLite.
- Si falta un componente: no escribas código, bájalo con los motores de descarga y extracción de main.

## 6. Si no puedes leer una URL o escribir en GitHub
No inventes. `GAP-ACCESO` y para; o devuelve tus entradas como arreglo JSON que cumpla el esquema y Claude las sube.

## 7. Prohibido
Tocar el router, LFS git, GitHub Actions, Hugging Face. No editar a mano STATE.json, BITACORA.jsonl ni CRAZY_WALL.json.

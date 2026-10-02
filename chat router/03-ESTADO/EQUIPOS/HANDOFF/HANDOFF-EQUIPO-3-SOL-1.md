# HANDOFF EQUIPO-3 — Sol 🚀 1 — Conectar 4 capacidades descargadas como herramientas (P2)

## 0. Dónde estás parado (todo en la rama del PR #6, nunca en main)
- Repo: https://github.com/maxbry123-commits/router-universal-router-inteligente-
- Rama: `devin/1790824641-chat-agent-plan`
- Carpeta de trabajo (RAIZ-WL): https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes
- TU ARCHIVO, aquí escribes tu resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/EQUIPO-3-SOL-1.json
- Reglas de todos: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/00-LEEME-EQUIPOS.md
- Esquema de cada entrada de resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/ESQUEMA-TRAZABILIDAD.json
- Carpeta de tu evidencia (créala con el primer archivo real): `chat router/11-EVIDENCIA/equipos/EQUIPO-3/`

## 1. Qué hay que cerrar
Cuatro componentes ya descargados y verificados por el motor (VERIFIED_CLOSED) deben quedar como HERRAMIENTAS del orquestador. No son agentes ni staff. Descargar no es integrar.
- `anthropic-skills`
- `scrapling`
- `scrapegraph-ai`
- `agent-reach`

Dónde están sus fuentes (solo lectura): https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/router%20inteligente%20universal/Componente%20open%20soure%20router%20inteligente%20universal
Si alguno no está ahí, búscalo en el árbol del repo y anota la ruta real en `resultado`. No inventes rutas.

## 2. Piezas que debes leer antes de tocar nada (todas dentro de RAIZ-WL)
- Cómo se registra una capacidad: `wordflow_loop/wordflow_loop/orchestrator_adapters.py`, diccionario `COMPONENT_CAPABILITIES` (cada entrada: provides, forbidden, command_env). Enlace: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/wordflow_loop/orchestrator_adapters.py
- Contratos: `wordflow_loop/wordflow_loop/orchestrator_contracts.py`
- Registro de componentes: `wordflow_loop/contracts/MVP-COMPONENT-REGISTRY.json`
- Esquemas de skills (24 archivos `.dag.yaml`; copia el formato de uno existente): carpeta `skills_schema/` https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/skills_schema
- Test modelo: `runtime/tests/test_orchestrator_adapters.py` y `runtime/tests/test_skills_schema.py`

## 3. Qué significa 'conectar' (MVP, sin sobre ingeniería)
1. Una entrada nueva en `COMPONENT_CAPABILITIES` por cada capacidad (cableado; no escribas lógica nueva).
2. Un `.dag.yaml` en `skills_schema/` copiando el formato de uno existente.
3. Una prueba real: 1 entrada de ejemplo, salida guardada.
4. Un test que falla cerrado si falta la capacidad.

## 4. RONDA 1 (haz solo estas 3, luego commit y sal)
- A-01 `anthropic-skills`: contrato de herramienta (pasos 1 y 2 de arriba)
- A-02 `scrapling`: contrato de herramienta
- A-03 `scrapegraph-ai`: contrato de herramienta

## 5. Cómo escribes el resultado
Una entrada por tarea en `resultado` (esquema), `estado` de la tarea en `cola` a CERRADO o BLOQUEADO, una línea en `bitacora`, y `handoff` actualizado. Evidencia real en `chat router/11-EVIDENCIA/equipos/EQUIPO-3/<id_tarea>.txt` con sha256.

## 6. Si falta un componente o no corre
No escribas código para reemplazarlo. Anótalo en `gap` con el motivo exacto. Si hay que traer algo de GitHub: solo con los motores de descarga y extracción que están en main.

## 7. Si no puedes leer una URL o escribir en GitHub
No inventes. `GAP-ACCESO` y para; o devuelve tus entradas como arreglo JSON que cumpla el esquema y Claude las sube.

## 8. Prohibido
Tocar el router (`router inteligente universal/` es solo lectura), LFS git, GitHub Actions, Hugging Face. No editar a mano STATE.json, BITACORA.jsonl ni CRAZY_WALL.json.

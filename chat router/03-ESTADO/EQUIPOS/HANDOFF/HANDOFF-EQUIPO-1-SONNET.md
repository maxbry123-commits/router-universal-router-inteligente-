# HANDOFF EQUIPO-1 — Sonnet — Orquestador real (P1) y 3 workers (P3)

## 0. Dónde estás parado (todo en la rama del PR #6, nunca en main)
- Repo: https://github.com/maxbry123-commits/router-universal-router-inteligente-
- Rama: `devin/1790824641-chat-agent-plan`
- Carpeta de trabajo (RAIZ-WL): https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes
- TU ARCHIVO, aquí escribes tu resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/EQUIPO-1-SONNET.json
- Reglas de todos: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/00-LEEME-EQUIPOS.md
- Esquema que debe cumplir cada entrada de resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/ESQUEMA-TRAZABILIDAD.json
- Carpeta de tu evidencia (créala al guardar el primer archivo real): `chat router/11-EVIDENCIA/equipos/EQUIPO-1/`

## 1. Qué hay que cerrar
Los componentes del orquestador están registrados pero NO se invocan de verdad: falta la variable de entorno de cada uno.

Archivo clave (léelo entero): https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes/wordflow_loop/wordflow_loop/orchestrator_adapters.py
- Ruta: `chat router/📂 workflow Loops code Yaiwes/wordflow_loop/wordflow_loop/orchestrator_adapters.py`
- El diccionario `COMPONENT_CAPABILITIES` dice qué variable usa cada componente. Si la variable no está, el adapter falla cerrado con `RUNTIME_UNAVAILABLE`.

| Tarea | Componente | Variable de entorno |
|---|---|---|
| S1-01 | rowboat | `YAIWES_ROWBOAT_COMMAND` |
| S1-02 | ms_agent_framework | `YAIWES_MSAF_COMMAND` |
| S1-03 | orca | `YAIWES_ORCA_COMMAND` |
| S1-04 | omniroute | `YAIWES_OMNIROUTE_COMMAND` |
| S1-05 | deepseek_harness | `YAIWES_DEEPSEEK_HARNESS_COMMAND` |
| S1-06 | munder_difflin | `YAIWES_MUNDER_COMMAND` |
| S1-07 | dagu_dbos | `YAIWES_DAGU_DBOS_COMMAND` |
| S1-08 | mcp | `YAIWES_MCP_COMMAND` |

Cómo se invoca (ya está escrito, NO se modifica el código): `ComponentAdapter("<componente>").invoke(task, mission)` ejecuta el comando de la variable, le manda el payload por entrada estándar y devuelve la salida.

## 2. Cómo hacer cada tarea (siempre igual)
1. Encuentra el CLI o SDK real del componente dentro de su carpeta (solo lectura): https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/router%20inteligente%20universal/Componente%20open%20soure%20router%20inteligente%20universal
2. Define la variable de entorno SOLO en tu sesión. No la escribas en ningún archivo del repo ni la commitees.
3. Usa como modelo el test que ya existe: `chat router/📂 workflow Loops code Yaiwes/runtime/tests/test_orchestrator_adapters.py` y `test_orchestrator_e2e.py` (misma carpeta).
4. Corre la invocación real. Instalar dependencias en tu entorno está permitido; modificar el Router no.
5. Guarda la salida real resumida (sin claves) en `chat router/11-EVIDENCIA/equipos/EQUIPO-1/<id_tarea>.txt` y registra el sha256.
6. Si el componente no tiene CLI o no corre: NO inventes un comando. Marca BLOQUEADO con el motivo exacto en `gap`.

Cómo correr tests: `cd "chat router/📂 workflow Loops code Yaiwes" && source ~/.venv-riu/bin/activate && pytest runtime/tests -q` (el conftest ya fija PYTHONPATH). Base conocida: 267 pass / 3 stale. No toques los 3 stale.

## 3. RONDA 1 (haz solo estas 3, luego commit y sal)
- S1-01 Rowboat -> salida: `EQUIPO-1/S1-01.txt` + entrada en resultado
- S1-02 MSAF -> salida: `EQUIPO-1/S1-02.txt` + entrada en resultado
- S1-03 Orca -> salida: `EQUIPO-1/S1-03.txt` + entrada en resultado

## 4. Cómo escribes el resultado
Agrega UNA entrada por tarea al arreglo `resultado` de tu JSON, con el formato del esquema (id_tarea, equipo, ronda, estado, ejecutor, fecha_utc, accion, archivos[path+url+sha256], prueba_real, gap, siguiente). Cambia el `estado` de la tarea en `cola` a CERRADO o BLOQUEADO. Agrega una línea a `bitacora` y actualiza `handoff`.

## 5. Si no puedes leer una URL o escribir en GitHub
No inventes. Para y escribe `GAP-ACCESO` diciendo qué te faltó. Si no puedes escribir, devuelve tus entradas como un arreglo JSON que cumpla el esquema; Claude las sube por ti.

## 6. Prohibido
Tocar el router (`router inteligente universal/`, solo lectura), LFS git, GitHub Actions, Hugging Face. No editar a mano STATE.json, BITACORA.jsonl ni CRAZY_WALL.json.

## 7. Espera
Empieza después de la ronda 0, que ya está cerrada (commit 7b52b8e).

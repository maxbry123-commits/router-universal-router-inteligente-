# HANDOFF EQUIPO-2 — SOL 7 (relevo de Haiku) — Mover los archivos y ordenar

## 0. Dónde estás parado (todo en la rama del PR #6, nunca en main)
- Repo (termina con guion): https://github.com/maxbry123-commits/router-universal-router-inteligente-
- Rama: `devin/1790824641-chat-agent-plan`
- TU ARCHIVO, aquí escribes (es el mismo del equipo 2; el nombre dice Haiku pero el trabajo ahora es tuyo; en `ejecutor` pon "Sol 7"): https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/EQUIPO-2-HAIKU.json
- Reglas de todos: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/00-LEEME-EQUIPOS.md
- Esquema de cada entrada de resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/ESQUEMA-TRAZABILIDAD.json
- Evidencia ya hecha (H-01 a H-05, inventario y mapa; no la repitas): https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/11-EVIDENCIA/equipos/EQUIPO-2/H-01-H-02-H-05-inventario-mapa.md
- Tu evidencia nueva va en `chat router/Workflow Loop code Yaiwes/11-EVIDENCIA/equipos/EQUIPO-2/`

## 1. ORDEN DEL DIRECTOR (ya decidida): MOVER los 5 archivos sueltos a `chat router/Workflow Loop code Yaiwes/01-PLAN/`
Hoy están sueltos en `chat router/`. Cada uno con su hash de archivo (debe quedar idéntico después de moverlo):
| Archivo | Hash git |
|---|---|
| `INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL.md` | 383c45ac0f7afedec1a6a855dfe7835c27f6f042 |
| `INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL-PARTE-3.md` | a813e848f50d4b419eddbb7768b4d5ad8c295479 |
| `INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL-PARTE-4.md` | 0aa63de8a549d85258542041ea127f2020fa1a93 |
| `ORQUESTADOR-DE-TRABAJO.yaml` | b729f8ef440701a7d2410788d4c39c3b7be1c0c1 |
| `PLAN-DSL-DAG-CHAT-AGENTES-INFRA.yaml` | ddbfd02a3d3d9df718481ae5ae645bbb28cd413c |

## 2. RONDA 1: haz estas 3, en este orden. No escales, no pares hasta terminarlas.
- **H-06 Mover.** Usa `git mv` (mover de verdad, no copiar a mano). Destino: `chat router/Workflow Loop code Yaiwes/01-PLAN/<mismo nombre>`. Comprueba que cada archivo conserva su hash de la tabla. Anota 5 filas en tu evidencia.
- **H-09 Actualizar rutas.** En el MISMO commit que H-06 actualiza `chat router/Workflow Loop code Yaiwes/01-PLAN/ROOT-MAP-T11.yaml`: las raíces 04 y 05 citan 3 de estos archivos en `chat router/`; pásalas a `chat router/Workflow Loop code Yaiwes/01-PLAN/<nombre>`. Busca otras referencias a esos 5 nombres SOLO en archivos escritos a mano (`INDICE.md`, `memoria.md`, README) y corrígelas. En código y tests: solo reporta, no toques. `HANDOFF.md`: fuera del bloque State Hub.
- **H-07 Skills frontend.** Copia con motor_3 las 3 skills frontend de `chat router/Workflow Loop code Yaiwes/skills` (big-AGI) a `Skills agente/`. Motor: `chat router/Workflow Loop code Yaiwes/wordflow_loop/adapters/seals_motors/motor_3_copy_batches.py`. Si la fuente no está o no encuentras `Skills agente/`, anótalo como gap con la ruta exacta que buscaste; no inventes. Si hay que traer algo de GitHub: solo con el motor de descarga y extracción de main. No crees carpetas vacías.

En tu JSON: pasa H-06 y H-09 de `ESPERA_DECISION` a `EN_CURSO` (el Director ya decidió) y pon `ronda_actual` en `["H-06","H-09","H-07"]`.

## 3. Después (rondas siguientes, no ahora)
H-08 (biblioteca RAG), H-11 (segunda pasada de orden), H-12 (handoff final). H-10 (borrar duplicados) NO se hace sin permiso expreso del Director.

## 4. Cómo escribes el resultado
Una entrada por tarea en `resultado` con el esquema (archivos con path + url + sha256 + prueba real). Estado en `cola` a CERRADO o BLOQUEADO. Una línea en `bitacora`. `handoff` actualizado. Commit en la rama y sal (máx. 1 minuto de espera).

## 5. Si no puedes leer una URL o escribir en GitHub
No inventes. `GAP-ACCESO` y para; o devuelve tus entradas como arreglo JSON que cumpla el esquema.

## 6. Prohibido
Tocar el router (`router inteligente universal/`), LFS git, GitHub Actions, Hugging Face. No editar a mano STATE.json, BITACORA.jsonl ni CRAZY_WALL.json. No borrar nada fuera de lo que mueve `git mv`.

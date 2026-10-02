# HANDOFF EQUIPO-2 — Haiku — Ordenar el repo y cablear lo sencillo

## 0. Dónde estás parado (todo en la rama del PR #6, nunca en main)
- Repo (el nombre TERMINA con guion): https://github.com/maxbry123-commits/router-universal-router-inteligente-
- Rama: `devin/1790824641-chat-agent-plan`
- Carpeta donde está todo el chat: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router
- TU ARCHIVO, aquí escribes tu resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/EQUIPO-2-HAIKU.json
- Reglas de todos: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/00-LEEME-EQUIPOS.md
- Esquema de cada entrada de resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/ESQUEMA-TRAZABILIDAD.json

## 1. ACCESO (esto fue lo que bloqueó tu primer intento)
Necesitas el conector de GitHub en tu chat, el mismo que usa Claude. Vercel NO sirve: ahí no hay nada de este repo.
- Sin conector de GitHub no puedes leer ni escribir. En ese caso NO intentes otra vía: escribe `GAP-ACCESO` y para. Claude toma tu cola.
- No pidas tokens ni los pegues en ningún archivo.

## 2. Lo que ya está hecho (no lo repitas)
- H-03 CERRADA: se creó `chat router/📂 workflow Loops code Yaiwes/` como copia exacta de `chat router/wordflow loop code Yaiwes/` (mismo hash de árbol `f8aee828`). Commit `7b52b8e`.
- H-04 CERRADA: 0 diferencias, porque es el mismo árbol.
- Ejecutó: Claude, porque Haiku no tenía acceso. Anótalo tal cual.
- Carpeta nueva: https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes
- Carpeta vieja (NO se borra todavía): https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/wordflow%20loop%20code%20Yaiwes

## 3. RONDA 1 (haz solo estas 3, luego commit y sal)
- **H-01 Inventario (solo lectura, no muevas nada).** Lista lo que está suelto en `chat router/`. Ya sé que ahí están: `INPUT-BLOCK-VERBATIM-CHAT-Y-PANEL.md`, `...-PARTE-3.md`, `...-PARTE-4.md`, `ORQUESTADOR-DE-TRABAJO.yaml`, `PLAN-DSL-DAG-CHAT-AGENTES-INFRA.yaml`, y las carpetas `chat_orders`, `deepseek-harness-chat`, `space`, `ui`. Dime cuáles más y su tamaño. Escribe la lista en `resultado`.
- **H-02 Mapa de destino.** Para cada ítem de H-01: a qué subcarpeta de la carpeta nueva va, o si se queda. NO inventes subcarpetas nuevas vacías (regla del plan: no crear carpetas vacías). Escribe el mapa en `resultado`.
- **H-05 Comparar la carpeta duplicada.** Compara https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20Wordflow%20LOOP%20Yaiwes contra la carpeta nueva. Anota qué archivos están solo en uno. Copia con motor_3 SOLO los que falten en la carpeta nueva. No borres nada.

Motor_3 (copia física con hash y read-back): `chat router/📂 workflow Loops code Yaiwes/wordflow_loop/adapters/seals_motors/motor_3_copy_batches.py`
Contrato: `chat router/📂 workflow Loops code Yaiwes/wordflow_loop/contracts/seals_motors/motor_3_copy_batches.schema.json`
Regla del Director: motor_3 copia, nunca mueve. Si falta algo que no sea copiar, se baja con el motor de descarga y extracción de main; no se escribe código.

## 4. Cómo escribes el resultado
Una entrada por tarea en `resultado` con el formato del esquema (archivos con path + url + sha256, prueba_real, gap). Cambia el `estado` en `cola` a CERRADO o BLOQUEADO. Agrega una línea a `bitacora`. Evidencia en `chat router/11-EVIDENCIA/equipos/EQUIPO-2/`.

## 5. Borrar: SOLO con permiso
H-10 (borrar originales) no está en esta ronda. Nunca se borra nada hasta que la copia tenga el mismo hash que el original y el Director lo autorice.

## 6. Si no puedes leer una URL o escribir
No inventes. `GAP-ACCESO` y para. Si solo no puedes escribir, devuelve tus entradas como arreglo JSON que cumpla el esquema; Claude las sube.

## 7. Prohibido
Tocar el router (`router inteligente universal/`), LFS git, GitHub Actions, Hugging Face. No editar a mano STATE.json, BITACORA.jsonl ni CRAZY_WALL.json.

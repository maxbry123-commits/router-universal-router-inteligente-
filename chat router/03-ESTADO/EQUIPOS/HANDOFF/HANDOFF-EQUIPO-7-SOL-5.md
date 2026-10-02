# HANDOFF EQUIPO-7 — Sol 👾 5 — Tests finales, evidencia global y README (P8)

## 0. Dónde estás parado (todo en la rama del PR #6, nunca en main)
- Repo: https://github.com/maxbry123-commits/router-universal-router-inteligente-
- Rama: `devin/1790824641-chat-agent-plan`
- Carpeta de trabajo (RAIZ-WL): https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/%F0%9F%93%82%20workflow%20Loops%20code%20Yaiwes
- TU ARCHIVO, aquí escribes tu resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/EQUIPO-7-SOL-5.json
- Reglas de todos: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/00-LEEME-EQUIPOS.md
- Esquema de cada entrada de resultado: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/ESQUEMA-TRAZABILIDAD.json
- Plan de cierre (qué es 'cerrado'): https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS/PLAN-CIERRE-BACKEND.yaml
- Carpeta de tu evidencia (créala con el primer archivo real): `chat router/11-EVIDENCIA/equipos/EQUIPO-7/`

## 1. Qué hay que cerrar
Correr las suites contra la base conocida, clasificar los fallos, juntar la evidencia de todos los equipos y escribir el README final. Tú cierras al final: tus tareas E-09 a E-12 esperan a que los equipos 1 a 6 terminen.

## 2. Comandos exactos (en tu sesión, con el entorno del proyecto)
- Suite del loop: `cd "chat router/📂 workflow Loops code Yaiwes" && source ~/.venv-riu/bin/activate && pytest runtime/tests -q` -> base: 267 pass / 3 stale (g009, g021, ficha loader; son de upstream)
- Suite seals_core: carpeta `backend/Seals team YAIWES` dentro de RAIZ-WL, con `PYTHONPATH=seals_core` -> base: 44/45 (el fallo es un test inexistente que contradice el fix SIM-01; upstream)
- Ruff: el mismo que usa el proyecto
- Suite ampliada del Router/memoria (solo correr y leer; es del Router): base conocida 371 passed, 5 failed (GitHub E2E con 502 y 4 de configuración/modelos). Fuente: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/HANDOFF.md

REGLA: no modifiques tests upstream stale. Se listan con su motivo.

## 3. Piezas que lees
- Mapa de raíces: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/01-PLAN/ROOT-MAP-T11.yaml
- Plan de acción: https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/devin/1790824641-chat-agent-plan/chat%20router/01-PLAN/PLAN-ACCION-XRAY.md
- Los 8 archivos de equipo (solo lectura, nunca edites el de otro): carpeta https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/devin/1790824641-chat-agent-plan/chat%20router/03-ESTADO/EQUIPOS

## 4. Dónde dejas lo tuyo (rutas exactas)
- README final: `chat router/📂 workflow Loops code Yaiwes/README-ARQUITECTURA-BACKEND.md`
- Evidencia global: `chat router/11-EVIDENCIA/equipos/EVIDENCIA-GLOBAL.json` (path + sha256 de cada resultado de cada equipo)

## 5. RONDA 1 (haz solo estas 3, luego commit y sal)
- E-01 Suite del loop: corre y anota pass/fail/stale contra la base
- E-02 Suite seals_core: corre y anota contra la base
- E-03 Clasifica los 5 fallos de la suite ampliada: causa de cada uno en una frase

## 6. Cómo escribes el resultado
Una entrada por tarea en `resultado` (esquema), `estado` en `cola`, una línea en `bitacora` y `handoff` actualizado. La salida real de cada corrida, resumida y sin claves, va en `chat router/11-EVIDENCIA/equipos/EQUIPO-7/<id_tarea>.txt` con su sha256.

## 7. Si no puedes correr algo
No inventes un resultado. Marca BLOQUEADO con el motivo exacto (por ejemplo: falta un paquete, falta el entorno). Un número que no corriste no se escribe.

## 8. Si no puedes leer una URL o escribir en GitHub
`GAP-ACCESO` y para; o devuelve tus entradas como arreglo JSON que cumpla el esquema y Claude las sube.

## 9. Prohibido
Tocar el router (solo lectura), LFS git, GitHub Actions, Hugging Face. No editar a mano STATE.json, BITACORA.jsonl ni CRAZY_WALL.json.

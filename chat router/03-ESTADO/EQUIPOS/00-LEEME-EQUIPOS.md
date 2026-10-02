# EQUIPOS — cómo se trabaja (MVP, sin sobre ingeniería)
Creado 2026-10-02 por Claude (Sonnet) según INPUT-BLOCK-VERBATIM-2026-10-02-PLAN-7-EQUIPOS y ...-ORGANIZAR-Y-8-EQUIPOS (en main: chat router/01-PLAN/).

## Reglas (valen para los 8)
1. Cada equipo escribe SOLO en su archivo `EQUIPO-N-*.json` de esta carpeta: campos `resultado`, `bitacora` y `handoff`.
2. Máximo 3 tareas por ronda (normalmente 2 o 3). Al terminar: commit, anotar, SALIR. Nadie se queda ejecutando cómputo. El Director activa la siguiente ronda.
3. RONDA 0: solo Haiku (EQUIPO-2) organiza el repo. Los demás esperan a que EQUIPO-2 marque H-04 como CERRADO.
4. RAIZ-WL = `chat router/📂 workflow Loops code Yaiwes/`. Hasta que H-03 y H-04 cierren, la carpeta actual sigue siendo `chat router/wordflow loop code Yaiwes/`.
5. PROHIBIDO a todos: tocar el router (`router inteligente universal/`), tocar LFS git, usar GitHub Actions, usar Hugging Face.
6. Si falta un componente: NO se escribe código. Se busca en GitHub y se trae solo con los motores de descarga y extracción que están en main, al destino que haga falta.
7. NO editar a mano `STATE.json`, `BITACORA.jsonl` ni `CRAZY_WALL.json` (los genera el State Hub con hash). Para el checkpoint: `python "chat router/03-ESTADO/watchdog_checkpoint.py" --summary "..."`.
8. Rama de trabajo: `devin/1790824641-chat-agent-plan` (PR #6). No crear otro PR.
9. Estados de tarea: PENDIENTE -> EN_CURSO -> CERRADO | BLOQUEADO (con GAP). Sin prueba real y sin evidencia (path + sha256) no hay CERRADO. Lo que no se pueda resolver se anota como GAP, no se inventa.
10. El frontend sigue bloqueado hasta cerrar el backend.
11. Auditor: Claude (Sonnet) lee los 8 archivos y audita los resultados.

## Reparto (pendientes de memoria.md P1..P8)
| Equipo | Modelo | Pendiente | Archivo |
|---|---|---|---|
| 1 | Sonnet | P1 adapters reales (O4-07..14) + P3 (S-11, S-12) | EQUIPO-1-SONNET.json |
| 2 | Haiku | Organizar repo + P5 + parte de P6 | EQUIPO-2-HAIKU.json |
| 3 | Sol 🚀 1 | P2 cuatro capacidades descargadas | EQUIPO-3-SOL-1.json |
| 4 | Sol 🏭 2 | P4 Archify (O4-17) + O4-20 + auditoría cruzada | EQUIPO-4-SOL-2.json |
| 5 | Sol 🐻 3 | Lote SKILLS-UI (28 repos) | EQUIPO-5-SOL-3.json |
| 6 | Sol 🧑‍💻 4 | Memoria y almacenamiento (solo local) | EQUIPO-6-SOL-4.json |
| 7 | Sol 👾 5 | P8 tests finales + README + flags (P7) | EQUIPO-7-SOL-5.json |
| 8 | Sol ☀️ 6 | Tarea 8: extraer funciones de las imágenes (nueva auditoría) | EQUIPO-8-SOL-6.json |

## Flujo de una ronda
Director activa -> equipo lee su JSON -> hace las tareas de `ronda_actual` -> escribe resultado + evidencia -> commit -> sale -> Claude audita -> Director activa la siguiente.

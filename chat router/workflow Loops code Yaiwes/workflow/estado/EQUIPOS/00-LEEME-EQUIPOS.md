# EQUIPOS — cómo se trabaja (MVP, sin sobre ingeniería)
Creado 2026-10-02 por Claude (Sonnet) según INPUT-BLOCK-VERBATIM-2026-10-02-PLAN-7-EQUIPOS y ...-ORGANIZAR-Y-8-EQUIPOS (en main: chat router/Workflow Loop code Yaiwes/01-PLAN/).

## Qué hay en esta carpeta
- `PLAN-CIERRE-BACKEND.yaml` — qué significa 'backend cerrado', quién lo cierra, rondas y lo que NO se puede cerrar con las prohibiciones
- `ESQUEMA-TRAZABILIDAD.json` — formato obligatorio de cada resultado (archivo + url + sha256 + prueba real)
- `HANDOFF/HANDOFF-EQUIPO-N-*.md` — dónde trabaja exactamente cada equipo, con enlaces visibles (EMPIEZA POR TU HANDOFF)
- `EQUIPO-N-*.json` — la cola de 12 tareas de cada equipo y el lugar donde escribe su resultado

## Reglas (valen para los 8)
1. Cada equipo escribe SOLO en su archivo `EQUIPO-N-*.json` de esta carpeta: campos `resultado`, `bitacora` y `handoff`. Cada entrada de `resultado` cumple el esquema.
2. Máximo 3 tareas por ronda. Al terminar: commit, anotar, SALIR. Nadie se queda ejecutando cómputo. El Director activa la siguiente ronda.
3. RONDA 0 CERRADA (2026-10-02, commit 7b52b8e): la raíz nueva ya existe. Todos los equipos pueden empezar.
4. RAIZ-WL = `chat router/Workflow Loop code Yaiwes/`. La carpeta vieja `chat router/Workflow Loop code Yaiwes/_copias-anteriores/wordflow loop code Yaiwes/` sigue existiendo y NO se borra hasta que Haiku lo cierre con permiso del Director.
5. PROHIBIDO a todos: tocar el router (`router inteligente universal/`), tocar LFS git, usar GitHub Actions, usar Hugging Face.
6. Si falta un componente: NO se escribe código. Se busca en GitHub y se trae solo con los motores de descarga y extracción que están en main, al destino que haga falta.
7. NO editar a mano `STATE.json`, `BITACORA.jsonl` ni `CRAZY_WALL.json` (los genera el State Hub con hash). Para el checkpoint: `python "chat router/Workflow Loop code Yaiwes/03-ESTADO/watchdog_checkpoint.py" --summary "..."`.
8. Rama de trabajo: `devin/1790824641-chat-agent-plan` (PR #6). No crear otro PR.
9. Estados de tarea: PENDIENTE -> EN_CURSO -> CERRADO | BLOQUEADO (con GAP). Sin prueba real y sin evidencia (path + sha256) no hay CERRADO. Lo que no se pueda resolver se anota como GAP, no se inventa.
10. Si no puedes leer una URL o escribir en GitHub: no inventes. Escribe GAP-ACCESO y para; o devuelve tus entradas como arreglo JSON que cumpla el esquema y Claude las sube.
11. El frontend sigue bloqueado hasta cerrar el backend.
12. Auditor: Claude (Sonnet) lee los 8 archivos y audita los resultados después de cada ronda.

## Reparto (pendientes de memoria.md P1..P8)
| Equipo | Modelo | Pendiente | Handoff | Archivo de resultado |
|---|---|---|---|---|
| 1 | Sonnet | P1 adapters reales (O4-07..14) + P3 (S-11, S-12) | HANDOFF-EQUIPO-1-SONNET.md | EQUIPO-1-SONNET.json |
| 2 | Haiku | Organizar repo + P5 + parte de P6 | HANDOFF-EQUIPO-2-HAIKU.md | EQUIPO-2-HAIKU.json |
| 3 | Sol 🚀 1 | P2 cuatro capacidades descargadas | HANDOFF-EQUIPO-3-SOL-1.md | EQUIPO-3-SOL-1.json |
| 4 | Sol 🏭 2 | P4 Archify (O4-17) + O4-20 + pre-auditoría | HANDOFF-EQUIPO-4-SOL-2.md | EQUIPO-4-SOL-2.json |
| 5 | Sol 🐻 3 | Lote SKILLS-UI (28 repos) | HANDOFF-EQUIPO-5-SOL-3.md | EQUIPO-5-SOL-3.json |
| 6 | Sol 🧑‍💻 4 | Memoria y almacenamiento (solo local) | HANDOFF-EQUIPO-6-SOL-4.md | EQUIPO-6-SOL-4.json |
| 7 | Sol 👾 5 | P8 tests finales + README + flags (P7) | HANDOFF-EQUIPO-7-SOL-5.md | EQUIPO-7-SOL-5.json |
| 8 | Sol ☀️ 6 | Tarea 8: extraer funciones de las imágenes (nueva auditoría) | HANDOFF-EQUIPO-8-SOL-6.md | EQUIPO-8-SOL-6.json |

## Flujo de una ronda
Director activa con el prompt fijo del equipo -> el equipo lee su handoff por URL y su JSON -> hace las tareas de `ronda_actual` -> escribe resultado + evidencia -> commit -> sale -> Claude audita y actualiza `ronda_actual` -> Director activa la siguiente.

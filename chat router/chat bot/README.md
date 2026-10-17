# Chat BOTS — fuente principal (todo en un sitio)

Actualizado: 17-oct-2026 00:50, hora Bogotá (UTC-5). Dueño: **Antonio Mendoza**. Base: `main` `b17c430857`.

Esta carpeta (`chat router/chat bot/`) es la **fuente principal** de Chat BOTS (orquestador de agentes) + ROOM CONFERENCIAS. Los originales siguen en [`HANDOFF/CHATBOTS/`](../../HANDOFF/CHATBOTS/) (no se borran). Inventario de ramas, archivos y PROGRESO: [`HANDOFF.md`](HANDOFF.md).

Todo dato sale de GitHub (main y ramas citadas). Lo que no está comprobado va «por confirmar».

## Índice
- 1. Reglas (obligatorias)
- 2. Instrucciones de Antonio sobre Chat BOTS
- 3. Arquitectura completa (de README-ARQUITECTURA.md)
- 4. ROOM CONFERENCIAS — estado de ramas
- 5. Propuestas de diseño A / B
- 6. Mirror (enlaces de agentes)
- 7. Componentes open source (resumen)
- 8. Escribir sin esperar
- 9. Pendientes
- 10. BLOQUE DE ANTONIO (verbatim)

## 1. Reglas (obligatorias)

1. **Español, respuestas mínimas** a Antonio. Sin explicaciones largas.
2. **Tiempos siempre como `X s YYY ms`.**
3. **Nunca inventes.** Todo dato sale del código, de GitHub, del bucket o de una prueba tuya. Si no está: «por confirmar» y pregunta a Antonio en una lista corta.
4. **Un agente por tarea, en su propia rama.** Sin trabajo doble.
5. **Revisión ×3:** otro agente revisa 3 veces, conecta y prueba en PC y Android.
6. **Prueba en vivo en Android (412 px, 4G), E2E real (Enviar → respuesta visible), antes de merge o deploy.** Sin esa prueba no se reporta como hecho.
7. **Nunca borres nada sin el sí explícito de Antonio.**
8. **Nunca imprimas ni subas secretos** (tokens solo por nombre).
9. **No cambies la arquitectura:** COMPONENTE → HARNESS (puente_chat) → HTTP → FICHA → MODELO.
10. **La computadora del bot es solo para pruebas de frontend.**
11. **En main solo va lo probado.** Lo que está a medias va en ramas `wip/…`.
12. **Un `git worktree` por rama** (sparse si el disco está justo). No toques los worktrees de otros agentes.
13. **Al empezar y al terminar:** actualizar la tabla PROGRESO de [`HANDOFF.md`](HANDOFF.md) y `HANDOFF/TAREAS.md`.
14. Frontend: cambios milimétricos; propuestas como HTML funcional o imágenes, no maquetas.
15. Backend Chat BOTS: **esperar la descarga y reciclar componentes open source antes de escribir código** (§7).

Fuentes: `HANDOFF/CHATBOTS/HANDOFF.md` §Reglas, `HANDOFF/TAREAS/03` y `04` §Reglas, `HANDOFF/CHATBOTS/COMPONENTES-OPENSOURCE.md`.

## 2. Instrucciones de Antonio sobre Chat BOTS

### 2.1 Registro (copiado de `HANDOFF/CHATBOTS/HANDOFF.md` «INSTRUCCIONES DE ANTONIO»)

Añade una fila por instrucción nueva (fecha y hora Bogotá + texto lo más literal posible). No borres filas.

| Fecha hora (Bogotá) | Instrucción | Fuente |
|---|---|---|
| 16-oct-2026 (hora por confirmar) | Chat BOTS bajo el chat abierto; herramienta para crear agentes siempre visible | TAREAS §5 (t100) |
| 16-oct-2026 (hora por confirmar) | Sandbox con ejecución real + router de deploy (GitHub/HF/Vercel solo con token) | TAREAS §5 (t100) |
| 16-oct-2026 (hora por confirmar) | 50 agentes por sección | TAREAS §5 (t100) |
| 16-oct-2026 (hora por confirmar) | Nada se pierde: agentes, chats y proyectos persisten en la memoria existente | TAREAS §5, ARQUITECTURA |
| 16-oct-2026 (hora por confirmar) | ROOM CONFERENCIAS: los modelos debaten entre ellos | TAREAS §5 (t100) |
| 16-oct-2026 (hora por confirmar) | A−/A+ tamaño de texto | TAREAS §5 (t100) |
| 16-oct-2026 ~23:15 | Pausa total (t101 «Detente», t102 «Pon todo en pausa…») | TAREAS |
| 17-oct-2026 (hora por confirmar) | Aprueba la creación de agentes + ficha de Chat BOTS | Orden al agente de docs |
| 17-oct-2026 (hora por confirmar) | Pendiente: mirror desde los enlaces del agente | Orden al agente de docs |
| 17-oct-2026 (hora por confirmar) | Propuesta de nuevo diseño del frontend de Chat BOTS | Orden al agente de docs |
| 17-oct-2026 (hora por confirmar) | «Todos participan» en ROOM | Orden al agente de docs |
| 17-oct-2026 (hora por confirmar) | Escribir sin esperar en Chat / ROOM / Chat BOTS | Orden al agente de docs |
| 17-oct-2026 00:35 | Esta documentación (docs a main por aprobación permanente) | Orden al agente de docs |
| 17-oct-2026 00:40 | Descargar Agent Zero, OpenManus, OpenHands, Agent-S y Browser Use (solo carpetas útiles) e inventariarlos: **el agente backend debe esperar esta descarga y reciclar componentes antes de escribir código** ([`COMPONENTES-OPENSOURCE.md`](../../HANDOFF/CHATBOTS/COMPONENTES-OPENSOURCE.md)) | Orden al agente de descarga |

### 2.2 `HANDOFF/PARCHE-RECUPERACION.md` (líneas 101 y 119, literal)

- [L101](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/PARCHE-RECUPERACION.md#L101):

  | `orquestador-agentes-rebase` | **Chat BOTS v2**: sección debajo del chat abierto; cada agente es un sub-chat con semáforo, stream de 4 líneas, botón +, mirror, selector de la Ficha 4, memoria/sandbox/ID propios, máximo 50 por sección y la tool `crear_agente` siempre visible. Sandbox en HF Jobs con ejecución real; router de deploy a GitHub, HF y Vercel con el token cifrado y confirmación en cada "Desplegar". | **Pregunta abierta a Antonio:** HF Jobs tiene la red abierta. ¿Lo usamos así, esperamos a noviembre por Vercel Sandbox sin red, o paga Vercel Pro? Falta exponer `status`/`reiniciar` para el watchdog. |

- [L119](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/PARCHE-RECUPERACION.md#L119):

  - La sección "ROOM" y "Chat BOTS" viven como pestañas o secciones del chat, igual que Chat 1, 2 y 3.

### 2.3 `HANDOFF/TAREAS.md` (literal; L41–46 = §5 «Pedidos de Antonio (t100), estado»)

- [L3](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS.md#L3): **Estado: TODO EN PAUSA por orden de Antonio (t101 «Detente», t102 «Pon todo en pausa…»), 16-oct-2026 ~23:15 hora Bogotá (UTC-5).** No hay agentes corriendo. Nada se despliega ni se fusiona hasta que Antonio lo pida.
- [L21](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS.md#L21): `orquestador-agentes-rebase` (`9dc637165f`) = **Chat BOTS v2**: agentes bajo cada chat, persistidos en la memoria del chat (sobrevive reinicio), sandbox real en HF Jobs (6 s 627 ms), tope 50 por sección, tokens de deploy cifrados en el banco, «Desplegar» siempre pide confirmación. **Pendiente: decisión de Antonio sobre la red de HF Jobs.**
- [L38](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS.md#L38): Preguntas a Antonio: red de HF Jobs para Chat BOTS; PIN de secretos; elegir panel B/C si no quiere A.
- [L41](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS.md#L41): Nada se pierde: todo en la memoria/almacenamiento existentes (SQLite + bucket + grafo) → memoria-audit, historial y red caída en main; Chat BOTS persiste en la memoria del chat.
- [L42](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS.md#L42): Chat BOTS bajo el chat abierto; herramienta para crear agentes siempre visible → `orquestador-agentes-rebase`.
- [L43](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS.md#L43): Sandbox con ejecución real + router de deploy (GitHub/HF/Vercel solo con token) → `orquestador-agentes-rebase` (HF Jobs; deploy con confirmación).
- [L44](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS.md#L44): 50 agentes por sección → hecho en la rama.
- [L45](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS.md#L45): ROOM CONFERENCIAS (los modelos debaten entre ellos) → `wip/room-conferencias`.
- [L46](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS.md#L46): A−/A+ tamaño de texto → `wip/room-conferencias`.

### 2.4 `HANDOFF/TAREAS/03` y `04`

- [03 — Backend Chat BOTS / evolución](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS/03-BACKEND-CHATBOTS-EVOLUCION.md): **EN PAUSA** (orden de Antonio, no retomar sin su orden). Ramas `orquestador-agentes-rebase` (`9dc637165f`) y `wip/grokbot-evolucionado` (`5778306623`, 24 propuestas + `SINTESIS.md` + 24 imágenes). Pendiente: mirror desde los enlaces (§6), red de HF Jobs (respuesta de Antonio), reciclar componentes open source antes de escribir código.
- [04 — Frontend Chat BOTS (propuesta)](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS/04-FRONTEND-CHATBOTS-PROPUESTA.md): **ACTIVO** (aparte). Antonio aprobó crear agente + ficha y dijo: «el frontend no es así». Esperando que elija A o B (§5).

### 2.5 Notas del Director (verbatim) sobre agentes / mirror / Chat BOTS

Líneas copiadas tal cual de `Documentos del proyecto/Notas del Director (verbatim)/`:

- **[`INPUT-BLOCK-05-chat-storage-grupos-VERBATIM.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-BLOCK-05-chat-storage-grupos-VERBATIM.md)**
  - [L50](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-BLOCK-05-chat-storage-grupos-VERBATIM.md#L50): 1. Vasmos a tener más de 50 agente con el nombre de agente Seals Team YAIWES necesito que operen con las api locales que te voy a define esos modelos locales no deben estar instalado a huggueface deben llamar al modelo remoto como lo indica hugguenface para no descargar el modelo y deben trabajar como mirror y duplicarse sines necesario 50 o 100 veces
- **[`INPUT-VERBATIM-2026-09-20-e-banco-modelos-vercel-agentes-enchufe.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-20-e-banco-modelos-vercel-agentes-enchufe.md)**
  - [L30](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-20-e-banco-modelos-vercel-agentes-enchufe.md#L30): Luego vas a cableas con el plugins universal enchufe universal Fables a los agentes en el chat dese el repo de agente ➡️📂 wordflow loop code Yaiwes/
  - [L31](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-20-e-banco-modelos-vercel-agentes-enchufe.md#L31): Los buscas y haces un mirror con todos los agente para usarlos en el chat
  - [L53](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-20-e-banco-modelos-vercel-agentes-enchufe.md#L53): E6. Cablear con el plugin universal (Enchufe Universal de Fables) los agentes en el chat, desde el repo `agentes` carpeta `➡️📂 wordflow loop code Yaiwes/`: buscarlos y hacer un mirror de todos los agentes para usarlos en el chat.
- **[`INPUT-VERBATIM-2026-09-21-t-espejo-10-procesadores-mvp-delegar.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-21-t-espejo-10-procesadores-mvp-delegar.md)**
  - [L7](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-21-t-espejo-10-procesadores-mvp-delegar.md#L7): Ok espejo es que se puede usar el mismo peso del modelo ai por varias secciones al mismo tiempo sin copiar el modelo
  - [L42](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-21-t-espejo-10-procesadores-mvp-delegar.md#L42): T1. Corrección del Director: "espejo" = usar el MISMO peso de un modelo de IA en varias sesiones a la vez SIN copiar el modelo (una copia cargada + varias ranuras/agentes concurrentes).
- **[`INPUT-VERBATIM-2026-09-22-gg-orquestadores-ms-agent-framework-grok.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-22-gg-orquestadores-ms-agent-framework-grok.md)**
  - [L7](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-22-gg-orquestadores-ms-agent-framework-grok.md#L7): 1. Agente adicional para "mirror" del chat: ventana selector donde Max marca uno o varios agentes (1 a 22+), les da un system prompt, y
  - [L8](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-22-gg-orquestadores-ms-agent-framework-grok.md#L8): los ejecuta.
  - [L9](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-22-gg-orquestadores-ms-agent-framework-grok.md#L9): 2. Un orquestador (el centinela ya pedido) que controle el trabajo de todos los agentes, use el sistema de memoria para controlar tareas e
  - [L10](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-22-gg-orquestadores-ms-agent-framework-grok.md#L10): información, y el almacenamiento vinculado a lo ya aprobado sobre la memoria del chat.
  - [L14](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-22-gg-orquestadores-ms-agent-framework-grok.md#L14): 4. Grok como orquestador de los agentes DEL CHAT, mandado a descargar con un agente, con los motores.
- **[`INPUT-VERBATIM-2026-09-22-y-3-roles-delegar-watchdog-jev.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-22-y-3-roles-delegar-watchdog-jev.md)**
  - [L30](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-22-y-3-roles-delegar-watchdog-jev.md#L30): Y3. SOLO Claude (no delegar): activar todos los modelos en HF dentro del Router, con capacidad de espejo/duplicarse o crear las APIs que los agentes necesiten (es un enjambre).
- **[`INPUT-VERBATIM-2026-09-24-CHAT-VERCEL-OPENWEBUI.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-24-CHAT-VERCEL-OPENWEBUI.md)**
  - [L19](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-24-CHAT-VERCEL-OPENWEBUI.md#L19): El chat debe poder usarse con solo IA, y con IA + agentes del repo con acceso total a Hugging Face y a todos los repos de GitHub.
  - [L20](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-24-CHAT-VERCEL-OPENWEBUI.md#L20): Botón con selector para conectar workflows de otros repos, activarlos y darles órdenes como orquestador; mandar agentes o cablear procesos y chatear con un agente encargado. Orquestadores propuestos: Microsoft Agent Framework, Rowboat y Hermes.
  - [L26](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-24-CHAT-VERCEL-OPENWEBUI.md#L26): 3. Hermes es un agente que está en main, descargado.
  - [L27](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-24-CHAT-VERCEL-OPENWEBUI.md#L27): 4. Todos los agentes del repo deben quedar cableados con el chat.
  - [L28](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-24-CHAT-VERCEL-OPENWEBUI.md#L28): 5. Repo `agentes`: plan pendiente para ejecutar un workflow. Agente orquestador que controle; un agente investiga el plan y prepara el cableo; destino: repo agentes raíz ➡️📂 wordflow loop code Yaiwes/ (plan de 4 objetivos). Un agente cablea y conecta todo con el orquestador del chat (MSAF, Rowboat o Hermes); investiga, cablea e informa a Opus; Opus da las instrucciones.
- **[`INPUT-VERBATIM-2026-09-25-INPUT-7.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-25-INPUT-7.md)**
  - [L2](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-25-INPUT-7.md#L2): - Verificar que los agentes trabajen; si no, el centinela con watchdog cada 5–10 min resuelve. Darle al centinela los objetivos de cada agente.
  - [L3](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-25-INPUT-7.md#L3): - Centralizar todos los agentes en el chat como equipo; Opus revisa Crazy Wall / bitácora / state JSON / handoff y da órdenes; orquestadores ejecutan, automatizado. Objetivo final: el chat centraliza todos los proyectos; Opus es el cerebro que revisa y decide; agentes y workflows ejecutan los loops.
  - [L4](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-25-INPUT-7.md#L4): - Mirrors de agentes si hacen falta. Descargar Codex, MiMo Code y Claude Code con el agente de descargas; conectarlos al router; incorporarlos al staff.
- **[`INPUT-VERBATIM-2026-09-25-INPUT-12.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-25-INPUT-12.md)**
  - [L2](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-25-INPUT-12.md#L2): Encender y enrutar el Router con los agentes de 3 maneras con selector:
  - [L9](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-25-INPUT-12.md#L9): 7. Enrutar texto y archivos anclados; en cada agente colocar código ejecutable (GitHub + HF o sandbox), skills, archivos, indicaciones; crear Memoria.md, Claude.md, Handoff.md.
  - [L10](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-25-INPUT-12.md#L10): 8. Cablear varios agentes solo con botones selector.
  - [L11](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-25-INPUT-12.md#L11): 9. Mirror de un agente.
  - [L13](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-25-INPUT-12.md#L13): 11. Activar el destino del agente.

## 3. Arquitectura completa (de `HANDOFF/CHATBOTS/README-ARQUITECTURA.md`)

Contenido íntegro de [`README-ARQUITECTURA.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/CHATBOTS/README-ARQUITECTURA.md) en main `b17c430857` (títulos bajados un nivel; enlaces relativos apuntan a `HANDOFF/CHATBOTS/`).

Actualizado: 17-oct-2026 00:35, hora Bogotá (UTC-5). Fuente: solo el código de las ramas citadas. Lo que no sale del código va marcado **por confirmar**.

- Chat BOTS: rama `orquestador-agentes-rebase` (`9dc637165f`, 4 commits sobre main: backend, frontend, tool `crear_agente`, pruebas). **No está en main.**
- ROOM CONFERENCIAS + A−/A+: rama `wip/room-conferencias-rebase2` (`a014c943c0`, 2 commits sobre main `55d9d95fb4`). **No está en main.**
- Handoff para agentes: [`HANDOFF.md`](../../HANDOFF/CHATBOTS/HANDOFF.md). Bloque de Antonio: [`GROKBOT-FUNCIONAMIENTO-Y-MEJORAS.md`](../../HANDOFF/CHATBOTS/GROKBOT-FUNCIONAMIENTO-Y-MEJORAS.md).

### 0. Ruta (no cambiar)

```
COMPONENTE → HARNESS (puente_chat) → HTTP → FICHA → MODELO
```

Chat BOTS, tal como está construido:

```
orquestador.js (COMPONENTE, sección #chat-bots)
  → POST /plugins/orquestador/call/<acción>       (Vercel reescribe /plugins → Space)
  → plugin orquestador (plugin.py)
  → HTTP POST <puente>/chat_async  y  <puente>/resultado   (HARNESS puente_chat)
  → FICHA (modelo de la lista MODELOS, ids "qw-…")
  → MODELO
```

- `<puente>` = `RIU_PUENTE_URL` o `RIU_ROUTER_URL` (o `http://127.0.0.1:$PORT`, por defecto 7860) + `/plugins/puente_chat/call` (`plugin.py`, `_puente`). Timeout HTTP 30 s.
- El plugin **no toca fichas** (docstring de `plugin.py`): siempre pasa por el harness.
- Al revés (chat → agentes): la tool `crear_agente` vive en `puente_chat/herramientas.py` y llama `plugins.orquestador.plugin.crear(...)` en el mismo proceso.

ROOM CONFERENCIAS: `room-conferencias.js` → `window.RIU_HARNESS` (la misma función del chat) → plugin `puente_chat` por HTTP (`chat_async` + `/resultado`) → `fichas_qwen` (fichas 1/2/3) o NVIDIA → modelo. Sin backend propio.

### 1. Archivos de Chat BOTS (rama `orquestador-agentes-rebase`)

| Archivo | Qué hace |
|---|---|
| `router inteligente universal/plugins/orquestador/plugin.py` (397 líneas) | Plugin: acciones, persistencia, llamada al harness, mirror, sandbox, deploy |
| `router inteligente universal/plugins/orquestador/sandbox.py` (154) | Ejecución de código: HF Jobs > Vercel Sandbox > local (bwrap / unshare / rlimits) |
| `router inteligente universal/plugins/orquestador/deploy.py` (124) | Enrutador de deploy GitHub / Hugging Face / Vercel y tokens cifrados |
| `router inteligente universal/plugins/orquestador/ficha.json` | Contrato `plugin_host/v1`: id `orquestador`, versión `0.2.0`, estado `testing`, `entry_point plugins.orquestador.plugin:handle`, `timeout_ms 90000`, acciones permitidas |
| `router inteligente universal/plugins/orquestador/__init__.py` | Paquete |
| `router inteligente universal/plugins/puente_chat/herramientas.py` (+16) | Tool `crear_agente(nombre, sistema, modelo)` para la LLM del chat |
| `router inteligente universal/plugins/puente_chat/capacidad.py` (+5) | Regex `_AGENTE` (`agentes?|bots?|chat bots|mirror|crear_agente`): sin intención externa devuelve `CAP_READ` en vez de `CAP_NONE`, así `crear_agente` queda visible cuando se habla de agentes |
| `chat router/chat frontend/orquestador.js` (137) | Frontend de la sección Chat BOTS |
| `chat router/chat frontend/orquestador.css` (34) | Estilos (incluye los de la ventana v1 `#ventana-orq`/`.orq-grid` y los de v2 `.chat-bots`/`.bots-tira`) |
| `chat router/chat frontend/shell.html` (+1) | `<link>` a `orquestador.css` |
| `chat router/chat frontend/shell.js` (+1) | `import "./orquestador.js"` |
| `tests_fix/orq_srv.py`, `orq_srv2.py` | Servidor local de prueba (puerto 8899) que sirve el frontend y el plugin; usa el puente real del Space |
| `tests_fix/orq_test.py` | Prueba Playwright 412 px de la **v1** (botón `#btn-orq`, ya no existe en v2: por confirmar si sigue sirviendo) |
| `tests_fix/orq_test2.py` | Prueba Playwright 412 px de la **v2** (tira `#bots-tira`, crear, hablar, ejecutar en sandbox, archivo, token falso) |

### 2. Endpoints (plugin `orquestador`)

Todas: `POST /plugins/orquestador/call/<acción>` con JSON; respuesta `{status:"ok", result:{…}}`. El frontend manda siempre `seccion` (la sesión del chat abierto).

| Acción | Entrada principal | Qué hace |
|---|---|---|
| `status` | — | Salud de la memoria (`sqlite.health()`), `max_por_seccion`, proveedor de sandbox, destinos de deploy con token (solo `true/false`) |
| `modelos` | — | `ficha: "ficha4-workflow-yaiwes"`, lista MODELOS y estados |
| `listar` | `seccion` | Agentes de la sección (vista corta) |
| `crear` | `nombre, sistema, modelo, icono` | Crea agente; error `MAX_AGENTES` si ya hay 50; `MODELO_NO_FICHA4` si el modelo no está en la lista |
| `chat_crear` | `pedido` | La LLM (`qw-qwen-3-8-flash`, sesión `orq-chat`, `max_tokens 600`) devuelve un JSON `{nombre, sistema, modelo}` y se crea el agente con `creado_por: llm-chat`. Espera hasta 80 s. Error `LLM_SIN_JSON` |
| `mirror` | `de` (`"chat"` o id de agente), `mensajes`, `modelo` | Crea una copia que trabaja en paralelo (ver §5) |
| `enviar` | `id, mensaje, max_tokens` (1200 por defecto) | Manda el hilo al harness (`chat_async`); error `AGENTE_OCUPADO` si ya tiene proceso |
| `estado` | `id, espera` (≤4 s) | Consulta `/resultado` y, al terminar, guarda la respuesta y la latencia |
| `aprobar` | `id` | Pasa el agente de `aprobacion` a `activo` |
| `configurar` | `id, modelo, sistema` | Cambia modelo y/o system |
| `subir` | `id, instruccion` o `nombre + datos_b64` (≤4 000 000 caracteres b64) | Añade instrucción o archivo (memoria + sandbox) |
| `archivos` | `id` | Lista nombre y bytes |
| `ejecutar` | `id, codigo` (si falta, el último bloque ```python del agente), `timeout_s` (30; tope 300) | Corre en el sandbox (§6) |
| `borrar` | `id` | Quita del índice, deja lápida `borrado:true` (el historial sigue en SQLite) y borra la carpeta sandbox |
| `token_guardar` | `destino, token` | Guarda el token cifrado (§7) |
| `deploy` | `id, destino, repo, rama, dry_run, confirmado` | Plan o despliegue de los archivos del agente (§7) |

### 3. Frontend (`orquestador.js`)

- **Montaje:** un `MutationObserver` crea `<div id="chat-bots" class="chat-bots">` **antes** de `#histories` (cambio quirúrgico, sin tocar `panel-chat.js`). Expone `window.RIU_ORQ = { orq, refrescar }`.
- **Base URL:** `localStorage.riu_orq_base` o `RIU_CONFIG.harnessUrl` sin `/plugins/puente_chat/call`. Cabecera `X-API-Key` si hay `sessionStorage.riu_clave`. Timeout 20 s (300 s para `chat_crear`, `ejecutar`, `deploy`).
- **Sección:** `seccionActiva()` lee la sesión del chip activo de `#chat-tabs` («sesión X» en el `title`) o `sessionStorage.riu_sesion` o `web-general`. Al pulsar otra pestaña de chat se recarga su propia sección de bots.
- **Tira** `#bots-tira`: «🤖 Chat BOTS N/50», un chip por agente (icono + semáforo + nombre) y `＋` (`#bots-nuevo`).
- **Formulario nuevo** `#orq-form-nuevo`: nombre, system, selector de modelo; «🧠 Crear con LLM» (`chat_crear`); «🪞 Añadir mirror» del chat abierto o de un agente.
- **Sub-chat abierto** `#orq-sec`: cabecera (icono, nombre, semáforo `#orq-sem`, estado, selector de modelo, ✕), info (system, memoria, archivos, creador, mirror de, última latencia «X s YYY ms»), **stream de 4 líneas** `#orq-stream`, hilo `#orq-hilo`, `+` (archivo o instrucción), 🎙 (SpeechRecognition `es-CO`), Enviar, ✅ Aprobar (solo en `aprobacion`), ▶ Ejecutar, 🪞 Mirror, 🗑 (con `confirm`), y `<details>` 🚀 Deploy.
- Con un panel abierto se **ocultan** `#histories` y `#composer` (el chat sigue debajo, oculto).
- **Repintado:** `pintar()` reemplaza todo el contenido de `#chat-bots` (`replaceChildren`) y solo restaura el valor de `#orq-input`, `+` abierto, deploy abierto y el foco. Si algún agente está `trabajando`, se repite cada 1 200 ms. (Por eso el campo repo `#orq-dep-repo` se borra al repintar: fallo visto en capturas.)
- Semáforo (`orquestador.css`): activo verde, trabajando azul con pulso, bloqueado naranja, aprobación amarillo con pulso, terminado gris, error rojo.

### 4. Agentes y FICHA

- Agente = dict con `id` (`ag-` + 8 hex), `seccion`, `nombre` (≤40), `icono`, `modelo`, `modelo_nombre`, `sistema` (≤4000), `estado`, `memoria_id` (`mem-<id>`), `archivos`, `instrucciones`, `mensajes`, `ejecuciones`, `stream` (últimas 40 líneas; la vista manda 4), `origen`, `creado_por` (`director` o `llm-chat`).
- **Tope: `MAX_AGENTES = 50` por sección** (`plugin.py`).
- Estados: `activo, trabajando, bloqueado, aprobacion, terminado, error`. Tras la respuesta: empieza con `[APROBACION]` → `aprobacion`; `[BLOQUEADO]` → `bloqueado`; si no → `terminado`. `CHAT_OCUPADO_REINTENTA` del harness → `bloqueado`.
- **Modelos (lista `MODELOS`, «ficha 4»):** `ficha-qwen38max`→`qw-qwen-3-8-max`, `ficha-qwen38flash`→`qw-qwen-3-8-flash` (por defecto), `ficha-qwen37max`, `ficha-qwen37plus`, `ficha-qwen36flash`, `ficha-dsv4pro`→`qw-deepseek-v4-pro`, `ficha-dsv4flash`, `ficha-glm52`→`qw-glm-5-2`. Qué ficha real del Router atiende cada id `qw-…`: **por confirmar** (lo decide puente_chat).
- **Mensaje al modelo** (`_mensajes_llm`): system del agente (o uno por defecto en español) + nombre, memoria y ruta del sandbox + reglas `[EJECUTAR]`, `[APROBACION]`, `[BLOQUEADO]` + instrucciones (≤2000 c/u) + archivos adjuntos (≤6000 c/u) + últimos 12 mensajes (≤6000 c/u).
- `enviar` llama `chat_async` con `sesion: agente-<id>`, `tools_habilitadas: false`, `request_id: orq-<id>-<n>` (idempotente). `estado` hace polling de `/resultado`; la latencia se mide en el plugin desde `t0`.

### 5. Mirror

- `mirror(de="chat")`: el frontend manda los últimos 12 elementos visibles de `#histories .chat-history:not([hidden])` (rol por clase CSS, ≤3000 caracteres); el agente nuevo recibe system «mirror del chat principal».
- `mirror(de=<id>)`: copia system, modelo, mensajes, instrucciones y archivos (re-subidos) del agente origen.
- Nombre `Mirror <origen>`, icono 🪞, `origen` = de dónde salió. Cuenta para el tope de 50.
- «Mirror desde los enlaces del agente»: **no existe en el código** (pendiente, ver HANDOFF §PROGRESO).

### 6. Sandbox (`sandbox.py`)

- Proveedor (`proveedor()`): `ORQ_SANDBOX=vercel` con `VERCEL_TOKEN` + `VERCEL_SANDBOX_PROJECT` → `vercel`; si hay token HF y `ORQ_SANDBOX≠local` → `hf-jobs` (**por defecto**); si no → `local`.
- **HF Jobs:** `POST /api/jobs/<RIU_HF_NS o COMAND-CENTER-1>`, imagen `python:3.12-slim`, `cpu-basic`, archivos <200 KB en base64, código en `ORQ_CODE`. Intenta `unshare -rn`; si no puede, la red queda **abierta** con bloqueo solo a nivel Python. Polling cada 3 s. Docstring: «5050 en 6 s 456 ms»; TAREAS: 6 s 627 ms.
- **Vercel Sandbox:** microVM, `networkPolicy deny-all`; docstring: la cuenta Hobby devuelve 402 hasta 2026-11-01.
- **Local:** bubblewrap (sin red, `/` solo lectura) > `unshare -rn` > solo rlimits (CPU 20 s, 768 MB, archivos 20 MB, 64 procesos). Entorno vacío: el código nunca recibe secretos.
- Carpeta: `RIU_ORQ_DIR` o `/tmp/riu-data/orquestador` + `/sandbox/<id>/archivos`; se rematerializa desde la memoria si se perdió.
- Decisión abierta de Antonio sobre la red de HF Jobs (TAREAS §2).

### 7. Deploy (`deploy.py`)

- Destinos: `github`, `hf`, `vercel`. Token: RAM → cifrado en memoria (scope `chat-ui:orq:gov:tokens`, scrypt + AES-256-GCM con `RIU_VAULT_PASSPHRASE` o `FICHA_CLAVE_BANCO`) → `providers.env_keys` → entorno (`GITHUB_TOKEN`/`GH_TOKEN`, `HF_WRITE_TOKEN`/`HF_TOKEN`, `VERCEL_TOKEN`). Nunca se devuelve ni entra al sandbox; los errores HTTP reemplazan el token por `***`.
- Sube los archivos de `sandbox/<id>/archivos`. `dry_run` → `estado: plan`. Sin `confirmado: true` → `FALTA_CONFIRMACION` (el botón «Desplegar» pide `confirm()` cada vez).
- GitHub: `PUT /repos/<repo>/contents/<archivo>` por archivo en `rama` (por defecto `main`). HF: commit NDJSON a `models|spaces|datasets/<repo>`. Vercel: `POST /v13/deployments` con `target: preview`.

### 8. Almacenamiento / memoria

- Sin SQLite propio: todo va a la fachada `memoria_yaiwes` (`integration.chat_mvp.memoria_loader._memory()`), la misma del chat: SQLite `riu_chat.sqlite3` → réplicas (grafo fallback, state-hub) → sync al bucket `yaiwes-memoria-storage` → restauración en frío (docstring de `plugin.py`). La RAM (`_CACHE`) es solo caché.
- Scopes: `chat-ui:orq:<seccion>` (claves `indice`, `agente:<id>`, `archivo:orq:<id>:<nombre>`), `chat-ui:orq:secciones` (`lista`), `chat-ui:orq:gov:tokens`.
- `_guardar(replicas=True)` usa `facade.save`; los latidos del stream usan solo `sqlite.save`. Las claves `archivo:` y los scopes `:gov:` quedan solo en SQLite (comentarios del código).

### 9. Límites (del código)

| Límite | Valor | Dónde |
|---|---|---|
| Agentes por sección | 50 | `plugin.py MAX_AGENTES` |
| Stream visible | 4 líneas (se guardan 40) | `STREAM_N`, `_linea` |
| Historial al modelo | 12 mensajes, 6000 caracteres c/u | `_mensajes_llm` |
| Archivo subido | ≤4 000 000 caracteres base64 | `subir` |
| Timeout ejecución | 30 s por defecto, tope 300 s | `ejecutar` |
| Timeout plugin | 90 000 ms | `ficha.json` |
| MAX_INFLIGHT por plugin | 8 | `HANDOFF/ARQUITECTURA.md` (`host.py`) |

### 10. ROOM CONFERENCIAS (rama `wip/room-conferencias-rebase2`)

Archivos (solo frontend, `chat router/chat frontend/`):

| Archivo | Qué hace |
|---|---|
| `room-conferencias.js` (192) | Pestaña, vista, participantes, rondas y debate |
| `room-conferencias.css` (26) | Estilos de la sala y de A−/A+ (`html.riu-fs`) |
| `texto-tamano.js` (20) | Control A−/A+ |
| `panel-chat.js` (+5) | Importa y llama `montarRoom` y `montarTamano`; `pintarTabs` llama `window.RIU_ROOM.pintar()` |
| `shell.html` (+1) | `<link>` a `room-conferencias.css` |

Cómo funciona:
- **Pestaña** «ROOM CONFERENCIAS» al final de `#chat-tabs`, junto a Chat 1/2/3. Activa: oculta los otros historiales y `#composer` (clase `room-oculto`). Cualquier otra pestaña sale de la sala.
- **Participantes** (`participantes()`): los modelos de `window.RIU_SELECTOR_QWEN` de grupo Qwen/DeepSeek/GLM (ficha 1 de `fichas_qwen`, model `qw-<slug>`), «Ask cónsil code» (ficha 2), «Ask consil frontend» (ficha 3) y «NVIDIA Glimmer» (`RIU_CONFIG.defecto`, `nv-muse-glimmer` por defecto, sin `qwen`). Máximo 6 (`MAX_PART`). Por defecto: Qwen 3.8 Flash + DeepSeek V4 Flash. El chip muestra el orden.
- **Rondas:** 1 a 5 (`MAX_RONDAS`), botones −/+. «Nueva sala» abre otra sesión (la anterior queda guardada).
- **Estado guardado:** `localStorage.riu_room_v1` (`activo, sesion, part, rondas`). Sesión `room-<aleatorio>`.
- **Historial:** `chat-ancla.js` (`restaurar`, `registrar`, `cargarHistorial`): IndexedDB + caché localStorage + respaldo en `/memoria` del Router. Cada respuesta se guarda como `[[Nombre]]\ntexto`.

Flujo del debate:
1. El Usuario escribe el tema y pulsa «Debatir» (Enter en PC). Se guarda como `user`.
2. Para cada ronda r de R, cada participante **en orden** hace un turno (`turno`). Si R>1 se pinta «Ronda r de R».
3. El prompt (`orden`): «SALA DE CONFERENCIAS… Eres «Nombre»… coincide o rebate a los demás citando su nombre… máximo 120 palabras, en español». Contexto: últimos 24 turnos, hasta ~9000 caracteres.
4. Fichas Qwen: la conversación va en `contexto_previo` y el `message` es solo la orden + el tema del Usuario (así la puerta de capacidades mira lo que pidió el Usuario). NVIDIA: la conversación va dentro del mensaje.
5. Llamada: `window.RIU_HARNESS({ model, message, contexto_previo, max_tokens: 700, sesion, qwen, avisar })`. Burbuja «pensando…» con el parcial (evento `riu-progreso`).
6. Respuesta: quita la cabecera «ASK CONSIL / modelo» (pasa a la etiqueta) y el «**Nombre**:» inicial; pinta la burbuja con botón ⧉ copiar y una línea «Nombre · X s YYY ms».
7. **Detener:** `Promise.race` corta el turno al instante y llama `window.RIU_CANCELAR(sesion)`; queda «proceso detenido por el usuario». Error → burbuja «GAP Nombre: …».

**A−/A+** (`texto-tamano.js`): botones `#fs-menos`/`#fs-mas` en `#ctl-panel .row.fields`. Paso 1 px, rango 11–28 px, guardado en `localStorage.riu_chat_fs`. Sin valor guardado no cambia nada; con valor, `html.riu-fs` aplica `--riu-chat-fs` a mensajes, `#message` y `#room-msg`.

Evidencia (mensaje del commit `a014c943c0`, 17-oct 00:13 Bogotá): «Probado 412 px + 4G E2E real: 2x1 y 3x2 rondas, recarga conserva historial, A-/A+, Chat 1 sigue OK». Tiempos de la prueba headless: 2×1 = 9 s 249 ms, 3×2 = 72 s 703 ms. Prueba en Android real: **por confirmar**.

### 11. Por confirmar
- Qué ficha real del Router resuelve cada id `qw-…` de Chat BOTS.
- Si `tests_fix/orq_test.py` (v1) se mantiene o se retira.
- `status`/`reiniciar` para el watchdog (PARCHE §4.1: falta).
- Red de HF Jobs (decisión de Antonio).
- Integración de Chat BOTS y ROOM en main: ninguna de las dos ramas está fusionada.

## 4. ROOM CONFERENCIAS — estado de ramas

Arquitectura y flujo: §3 (sección «10. ROOM CONFERENCIAS»). Ninguna rama está en main.

| Rama | SHA | Qué añade | Evidencia (commit / TAREAS/02) | Falta |
|---|---|---|---|---|
| [`wip/room-conferencias-rebase2`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/wip/room-conferencias-rebase2) | `a014c943c0` | ROOM + A−/A+; Detener corta el turno al instante | 2×1 = 9 s 249 ms; 3×2 = 72 s 703 ms (412 px headless) | Android real |
| [`wip/room-todos`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/wip/room-todos) | `604b2866f2` | Chip «Todos» (todos los selectores, sin tope), botón Intervenir durante el debate | «Todos x1 (12 modelos) sin errores, 2x2 con intervención»; Todos = 92 s 872 ms | Preguntas a Antonio: tope 6 y fila de 6 líneas; revisión ×3 |
| [`wip/room-escribir-sin-esperar`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/wip/room-escribir-sin-esperar) | `c086120187` | Escribir sin esperar en ROOM (cola `cola-envio.js`) | en curso | Revisión ×3, Android |

Bug abierto (TAREAS/01): en ROOM, la palabra «cambia» manda Ask consil al flujo largo: **189 s 720 ms**.

## 5. Propuestas de diseño A / B

- **A**: lista de agentes bajo el chat.
- **B**: pestañas como Chat 1/2/3.
- Estado: **esperando que Antonio elija A o B.** Rama de la propuesta: por confirmar (no hay rama en origin).
- Capturas (computadora del bot, no en el repo): `/workspace/shots/chatbots-propuesta/` — A1, A2, A4, A5, B1, B2, B4, B7.
- Base: `orquestador-agentes-rebase` (`9dc637165f`: `orquestador.js`, `orquestador.css`).
- Fallos actuales en la base (TAREAS/04): 1) la tira queda encima del chat (`hist.before`); 2) `.orq-plus` con `display:flex` anula `hidden`; 3) `pintar()` no restaura `#orq-dep-repo`; 4) solapes entre Selectores y «¿Qué hacemos hoy?»; 5) Controles tapa la tira.
- Tras la elección: implementar con cambios milimétricos, corregir los 5 fallos, capturas 412 px.

## 6. Mirror (enlaces de agentes)

Lo que hay en código (rama `orquestador-agentes-rebase`): `mirror(de="chat")` y `mirror(de=<id>)` (ver §3, «5. Mirror»). **«Mirror desde los enlaces del agente» no existe en el código.**

Enlaces recopilados en [`HANDOFF/TAREAS/03` §ENLACES DE AGENTES PARA MIRROR](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS/03-BACKEND-CHATBOTS-EVOLUCION.md#enlaces-de-agentes-para-mirror) (PR #17, merge `b17c430857`). Copia:

Recopilado el 17-oct-2026 00:55, hora Bogotá (UTC-5), solo leyendo GitHub por API (nada descargado). Sin inventar: si un agente no tiene URL, se dice.

| Agente | URL | Dónde se encontró |
|---|---|---|
| OpenClaw | Repo propio (única ubicación): https://github.com/maxbry123-commits/openclaw — hoy `main` = `038b10b48d` (v2026.9.6, 27-sep-2026), **más viejo** que v2026.10.4 (`383c124c`) | Orden de Antonio 17-oct-2026: «No quedan en main trabaja organizado no cambias mi arquitectura» |
| Hermes | Repo propio (única ubicación): https://github.com/maxbry123-commits/hermes-agent — hoy `main` = `ca16be564d` (27-sep-2026), **más viejo** que v0.22.2 (`d923a5eb`) | Orden de Antonio 17-oct-2026 |
| OpenCode | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/OpenCode/OpenCode | [`agent_fleet_registry.json:24`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L24) |
| OpenHands | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/OpenHands/OpenHands | [`agent_fleet_registry.json:44`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L44) |
| Claude Code CLI | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/Claude-Code/Claude-Code | [`agent_fleet_registry.json:63`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L63) |
| MiMo Code | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/MiMo | [`agent_fleet_registry.json:84`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L84) |
| Codex | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/Codex/Codex | [`agent_fleet_registry.json:106`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L106) |
| SmolAgents | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/SmolAgents | [`agent_fleet_registry.json:125`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L125) |
| Aider | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/Aider/Aider | [`agent_fleet_registry.json:183`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L183) |
| Kimi K Code | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/Kimi-K2.5/Kimi-K2.5 | [`agent_fleet_registry.json:221`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L221) |
| Qwen Code | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/Qwen-Agent/Qwen-Agent | [`agent_fleet_registry.json:240`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L240) |
| Cline | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Core%20kernel%20razonamiento%20repo%20para%20Yaiwes/Cline/Cline | [`agent_fleet_registry.json:259`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L259) |
| Agent Zero | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Agent-Zero | [`agent_fleet_registry.json:299`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L299) |
| OpenDev | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/OpenDev | [`agent_fleet_registry.json:316`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L316) |
| Research Agent Lab | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/Research%20Agent%20Lab | [`agent_fleet_registry.json:333`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L333) |
| MiroThinker | https://github.com/maxbry123-commits/Agentes-motores-Wordflow-YAIWES/tree/main/MiroThinker | [`agent_fleet_registry.json:351`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L351) |
| Muse/Glimmer Code | **Sin URL de código** en el registro (`source_repo: operator_runtime`, `EXTERNAL_NOT_VENDORED`). Solo hay URL del modelo: https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF y del cookbook https://github.com/meta-models/meta-oss-cookbook/tree/main/agentic-fundamentals | [`agent_fleet_registry.json:203`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L203) · [`INPUT-VERBATIM-2026-09-21-r-auditor-meta-agents-watchdog.md:44`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-21-r-auditor-meta-agents-watchdog.md#L44) · [`INPUT-VERBATIM-2026-09-21-r-auditor-meta-agents-watchdog.md:82`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/INPUT-VERBATIM-2026-09-21-r-auditor-meta-agents-watchdog.md#L82) |
| Goose | **Sin URL** (`source_repo: operator_runtime`, `source_path: null`) | [`agent_fleet_registry.json:282`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/code/wordflow_loop/wordflow_loop/agent_fleet/agent_fleet_registry.json#L282) |
| Agent Zero (upstream) | https://github.com/agent0ai/agent-zero | [`05-MOTORES-DESCARGA.md:15`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS/05-MOTORES-DESCARGA.md#L15) |
| OpenManus | https://github.com/FoundationAgents/OpenManus | [`05-MOTORES-DESCARGA.md:16`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS/05-MOTORES-DESCARGA.md#L16) |
| OpenHands (upstream) | https://github.com/OpenHands/OpenHands · https://github.com/OpenHands/software-agent-sdk · https://github.com/OpenHands/automation | [`05-MOTORES-DESCARGA.md:17`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS/05-MOTORES-DESCARGA.md#L17) |
| Agent-S | https://github.com/simular-ai/Agent-S | [`05-MOTORES-DESCARGA.md:18`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS/05-MOTORES-DESCARGA.md#L18) |
| Browser Use | https://github.com/browser-use/browser-use | [`05-MOTORES-DESCARGA.md:19`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/TAREAS/05-MOTORES-DESCARGA.md#L19) |

Notas:
- OpenClaw y Hermes viven solo en sus repos propios (`maxbry123-commits/openclaw`, `maxbry123-commits/hermes-agent`). Las demás copias se borraron el 17-oct-2026 (rama `limpieza/openclaw-hermes-duplicados`): Yaiwes PR #1, osquestador-auditor PR #1, Agentes-motores-Wordflow-YAIWES PR #12, agentes PR #25 (`wordflow_loop/agent_sources`). **Pendiente** en `agentes/Core kernel Yaiwes/` (OpenClaw, Hermes-Agent, agents/Hermes, Componentes recuperados A/B: OpenClaw, Hermes-Agent y sus zips): la API de GitHub da timeout en esa carpeta. También quedan en la raíz de Agentes-motores-Wordflow-YAIWES archivos sueltos de OpenClaw 2026.7.1 (`openclaw.mjs`, `package.json`, README, etc.) mezclados con archivos del repo: por confirmar con Antonio.
- La copia de descarga en `router inteligente universal/Componente open soure router inteligente universal/` (`openclaw-v2026.10.4`, `hermes-agent-v0.22.2`) **sigue en main de forma temporal**: los repos propios están en versiones más viejas (27-sep-2026). Se borra cuando los repos propios lleguen a v2026.10.4 / v0.22.2 o más nuevo.
- En Yaiwes no hay carpeta de agentes ni de workflow loop: solo `namespace.json` que apunta a `maxbry123-commits/Agentes-motores-Wordflow-YAIWES` y `maxbry123-commits/agentes` (`memoria/osquestador auditor memoria core/…/almacenamiento huggueface/`).
- Wordflow loop completo (no se copia por tamaño): https://github.com/maxbry123-commits/agentes/tree/main/%E2%9E%A1%EF%B8%8F%F0%9F%93%82%20wordflow%20loop%20code%20Yaiwes ([`README-ARQUITECTURA.md:41`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/chat%20router/workflow%20Loops%20code%20Yaiwes/README-ARQUITECTURA.md#L41)).
- No se encontró ninguna URL de HF Space para los agentes.

Por confirmar: de qué enlaces exactos debe salir el mirror (TAREAS/03 decía: «Antonio debe decir de dónde vienen los enlaces»).

## 7. Componentes open source (resumen)

Fuente completa: [`HANDOFF/CHATBOTS/COMPONENTES-OPENSOURCE.md`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/blob/main/HANDOFF/CHATBOTS/COMPONENTES-OPENSOURCE.md). Código descargado solo en el box: `/workspace/componentes-os/` (32 MB, no va al repo). **Regla:** el backend espera esta descarga y recicla antes de escribir código.

### 2. Agrupación de Antonio (4 + 1)

| Grupo | Componente | Qué aporta (según el código) |
|---|---|---|
| 1 | **Agent Zero** → memoria + plugins + skills + proyectos + multiagente | `plugins/_memory` (FAISS por subdirectorio, áreas `main/fragments/solutions`), sistema de plugins `plugin.yaml` con `per_project_config`/`per_agent_config`, `skills/*/SKILL.md`, `plugins/_orchestrator` (adaptadores a CLIs de agentes), `plugins/_tool_access` (política de tools por proyecto/agente) |
| 2 | **OpenManus** → agente general + MCP + Flow + A2A + sandbox | `app/agent/manus.py`, `app/flow/planning.py` (`PlanningFlow`), `app/mcp/server.py` (FastMCP), `run_mcp.py`, `protocol/a2a/app/main.py` (servidor A2A), `app/sandbox/core/sandbox.py` (`DockerSandbox`), `sandbox_main.py` (Daytona) |
| 3 | **OpenHands** → runtime + estado + herramientas + aislamiento + automatización | `openhands-agent-server` (REST/WebSocket, conversaciones, eventos, bash, MCP, skills, sub-agentes, `docker_runtime/`, lease), `openhands-tools/.../browser_use`, `automation` (cron, webhooks, dispatcher, watchdog) |
| 4 | **Agent-S** → Computer Use + GUI + percepción → acción | `gui_agents/s3/agents/grounding.py` (captura → OCR → acciones `pyautogui`), `agent_s.py`, `worker.py`, `bbon/` (juez comparativo), `memory/procedural_memory.py` |
| +1 | **Browser Use** (transversal) | `browser_use/` agente de navegador por CDP (`browser/session.py` usa `cdp_use`), `tools/registry`, `browser/watchdogs/*`, `mcp/server.py`, `llm/*` (muchos proveedores, `openai/chat.py` con `base_url`) |

#### Top que SIRVEN para el backend Chat BOTS
1. **OpenHands Automation** `watchdog.py` + `dispatcher.py` + estados → watchdog/cola/rutinas.
2. **OpenManus** `app/flow/planning.py` + `app/agent/base.py` (`is_stuck`) + `app/mcp/server.py` → plan, loop detector, MCP.
3. **Browser Use** `browser_use/` (+ tools de `openhands-tools/.../browser_use`) → navegador y mirror desde enlaces.
4. **Agent Zero** `_memory` (consolidación/calidad), `_goal`, `_tool_access`, `_time_travel`, `skills/` → memoria por niveles, GOAL LOCK, permisos, checkpoints.
5. **OpenHands agent-server** `conversation_lease.py`, `event_service.py`, `_secret_redaction.py` → estado, recuperación, redacción de secretos.
6. **Agent-S** `gui_agents/s3` + `integrations/openclaw` → Computer Use (necesita worker con escritorio).

### 4. Qué reciclar por pieza del backend Chat BOTS

| Pieza RIU | Hoy (rama `orquestador-agentes-rebase`) | Reciclar de |
|---|---|---|
| Agentes | dicts en `plugin.py`, estados `activo/trabajando/…` | OpenManus `app/agent/base.py` (bucle, `max_steps`, `is_stuck`), `app/flow/planning.py`; OpenHands `sub_agents_router.py` |
| Mirror | `mirror(de=chat o id)`; «desde enlaces»: no existe | Browser Use `browser_use/` + `openhands-tools/.../browser_use/definition.py` para abrir los enlaces y volcar contenido |
| Sandbox | `sandbox.py` HF Jobs > Vercel > bwrap | Mantener. Ideas: OpenHands `conversation_lease.py`; OpenManus `app/tool/sandbox/sb_*` (interfaz de tools) |
| Memoria | `memoria_yaiwes` (SQLite → grafo → bucket) | Agent Zero `_memory/helpers/memory_consolidation.py`, `memory_quality.py`, áreas `main/fragments/solutions`, `per_project/per_agent` |
| Browser | no hay | Browser Use (core) |
| Computer use | no hay | Agent-S `gui_agents/s3` + `integrations/openclaw/agent_s_wrapper.py` |
| Rutinas / watchdog | no hay | OpenHands Automation `scheduler.py`, `dispatcher.py`, `watchdog.py` |
| MCP | MCP de RIU | OpenManus `app/mcp/server.py`; Browser Use `mcp/server.py`; OpenHands `mcp_router.py` |

### 5. Pendiente / por confirmar
- Dónde correr Computer Use (Agent-S) y Browser Use: el Space actual (sin pantalla/Chromium confirmados) — por confirmar.
- Qué modelos de FICHA tienen visión (Agent-S lo necesita) — por confirmar.
- A2A (OpenManus `protocol/a2a`): ¿lo quiere Antonio?
- Nada de esto está integrado ni probado en Android; es inventario.

## 8. Escribir sin esperar

La caja sigue libre mientras el modelo/agente trabaja; lo enviado queda «en cola» y sale en orden (helper `cola-envio.js`). Las 3 ramas ya están en origin:

- Chat 1: [`feat/escribir-sin-esperar`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/feat/escribir-sin-esperar) (`c99902c444`).
- ROOM: [`wip/room-escribir-sin-esperar`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/wip/room-escribir-sin-esperar) (`c086120187`).
- Chat BOTS: [`orquestador-escribir-sin-esperar`](https://github.com/maxbry123-commits/router-universal-router-inteligente-/tree/orquestador-escribir-sin-esperar) (`626eb65024`): cola por agente; `AGENTE_OCUPADO` vuelve al frente; botón «✕ cola (N)» devuelve la cola a la caja.
- Estado: en curso; falta revisión ×3 y prueba Android.

## 9. Pendientes

- `HF_TOKEN` para deploy y medición real en el Space (bloqueo; TAREAS/01).
- Antonio elige diseño **A o B** del frontend Chat BOTS (§5).
- Mirror desde los enlaces de agentes: no existe en el código; enlaces en §6; confirmar con Antonio cuáles usar.
- Pruebas reales en **Android** (412 px, 4G, E2E) de Chat BOTS, ROOM, «Todos», escribir sin esperar.
- **7 proyectos de prueba** en la memoria real (rama `feat/nuevo-proyecto`): borrar **solo con el sí de Antonio**.
- Red de HF Jobs para el sandbox (abierta): decisión de Antonio.
- `status`/`reiniciar` del orquestador para el watchdog (PARCHE §4.1: falta).
- Qué ficha real del Router resuelve cada id `qw-…` de Chat BOTS: por confirmar.
- Integrar Chat BOTS y ROOM en main: ninguna rama está fusionada.

## BLOQUE DE ANTONIO (verbatim)

# GROK BOT — FUNCIONAMIENTO + PROPUESTAS DE MEJORA

## 1. CÓMO FUNCIONA GROK BOT

Grok Bot funciona como un agente persistente que combina un modelo de IA con una computadora propia en la nube, memoria, herramientas y capacidad de ejecutar tareas durante periodos largos.

### MICROFLUJO GENERAL

USUARIO → OBJETIVO → GROK BOT → PLAN → TOOLS / NAVEGADOR / TERMINAL / APPS → EJECUCIÓN → RESULTADO → MEMORIA

### COMPONENTES PRINCIPALES

1. **Bot persistente**
   - No funciona solamente como un chat.
   - Mantiene identidad y contexto.
   - Puede continuar trabajando sobre un objetivo.
   - Puede conservar memoria entre tareas.

2. **Computadora en la nube**
   - Cada Bot puede trabajar dentro de un entorno de cómputo.
   - Puede utilizar navegador.
   - Puede utilizar terminal.
   - Puede trabajar con archivos.
   - Puede interactuar con software y servicios.

3. **Chat**
   - El usuario entrega instrucciones.
   - El Bot pregunta cuando necesita información.
   - El usuario puede supervisar el trabajo.
   - Puede recibir nuevas instrucciones mientras ejecuta.

4. **Memoria**
   - Conserva información útil del trabajo.
   - Puede reutilizar contexto anterior.
   - Puede aprender preferencias y formas recurrentes de ejecutar tareas.

5. **Tools**
   - Navegador.
   - Terminal.
   - Archivos.
   - APIs.
   - Aplicaciones.
   - Integraciones.
   - Herramientas de programación.

6. **Skills**
   - Una forma de definir capacidades o procedimientos reutilizables.
   - Permiten repetir una forma determinada de ejecutar una tarea.

7. **Routines**
   - Automatizan tareas repetitivas.
   - Una rutina puede ejecutarse nuevamente sin reconstruir todo el proceso.

8. **Computer Use**
   - El Bot puede interactuar con interfaces visuales.
   - Puede abrir páginas.
   - Pulsar controles.
   - Introducir información.
   - Navegar aplicaciones.

9. **Ejecución de código**
   - Puede inspeccionar repositorios.
   - Leer código.
   - Modificar archivos.
   - Ejecutar comandos.
   - Ejecutar pruebas.
   - Investigar errores.

10. **Varios Bots**
    - Puede haber varios Bots trabajando al mismo tiempo.
    - Cada uno puede encargarse de una tarea diferente.
    - Pueden colaborar dentro del mismo trabajo.

11. **Permisos**
    - Determinadas acciones pueden permitirse.
    - Otras pueden necesitar aprobación.
    - Otras pueden bloquearse.

12. **Artefactos**
    - El trabajo puede producir:
      - código;
      - archivos;
      - documentos;
      - análisis;
      - resultados de herramientas;
      - modificaciones sobre proyectos.

### ARQUITECTURA SIMPLIFICADA

USUARIO → BOT → MODELO → PLAN → TOOL → COMPUTADORA → ARCHIVOS/APPS → RESULTADO

### PROBLEMA PRINCIPAL

Una parte importante del control todavía depende del comportamiento del agente y del modelo.

Eso puede provocar:

PLAN DEMASIADO GRANDE → CAMBIOS INNECESARIOS → MÁS TOKENS → MÁS LATENCIA → MAYOR RIESGO DE ERROR

También pueden aparecer:

TAREA → EJECUCIÓN → PROCESO BLOQUEADO → ESTADO RUNNING → SIN RECUPERACIÓN AUTOMÁTICA

O:

MODELO DICE "HECHO" → NO EXISTE EVIDENCIA SUFICIENTE → RESULTADO NO VERIFICADO


# 2. MEJORAS PROPUESTAS PARA GROK BOT

1. **GOAL LOCK**
   - Congelar el objetivo original.
   - Ningún agente puede modificar silenciosamente la misión.

2. **PLAN LOCK**
   - Crear el plan antes de ejecutar.
   - Validarlo.
   - Congelarlo.
   - Modificaciones importantes requieren una nueva revisión.

   OBJETIVO → PLAN → VALIDATE → LOCK → EXECUTE

3. **TASK COMPILER**
   - Convertir una tarea grande en microtareas pequeñas.
   - Cada tarea debe tener entrada, salida y condición de PASS.

4. **DAG DETERMINISTA**
   - Definir dependencias antes de ejecutar.

   T01 → T02 → T03
          ↘ T04
   T03 + T04 → T05

5. **1 TAREA = 1 WORKER**
   - Cada agente recibe únicamente una tarea.
   - Contexto mínimo.
   - Tools mínimos.
   - Permisos mínimos.

6. **SCOPE FIREWALL**
   - Definir exactamente qué archivos, aplicaciones o recursos puede modificar cada tarea.
   - Evitar cambios fuera del objetivo.

7. **EVIDENCE GATE**
   - Ninguna tarea puede declarar DONE solamente porque el modelo lo afirma.
   - Debe presentar evidencia real.

   RESULTADO → ARCHIVO/DIFF/TEST/LOG → VERIFY → PASS

8. **RECEIPTS**
   - Registrar cada acción importante.

   WHO → WHAT → TOOL → INPUT → OUTPUT → TIME → HASH

9. **WATCHDOG**
   - Detectar automáticamente:
     - procesos congelados;
     - workers muertos;
     - loops;
     - sesiones huérfanas;
     - estados RUNNING falsos;
     - locks abandonados.

10. **RECOVERY OS**
    - Sistema específico para recuperar tareas interrumpidas.

    RUNNING → FAIL → FREEZE → RECOVERY → RETRY/ROLLBACK → VERIFY → CONTINUE

11. **CHECKPOINTS**
    - Guardar el estado después de cada tarea correcta.

    T01 PASS → CHECKPOINT
    T02 PASS → CHECKPOINT
    T03 FAIL → RECUPERAR CHECKPOINT T02

12. **ROLLBACK AUTOMÁTICO**
    - Si una modificación rompe el sistema:
      - cancelar;
      - restaurar;
      - diagnosticar;
      - intentar nuevamente.

13. **DIFF BUDGET**
    - Limitar cuánto código puede modificar un agente.
    - Si un error necesita cambiar 5 líneas, impedir una reescritura de cientos de líneas sin autorización.

14. **TOKEN GOVERNOR**
    - Presupuesto independiente por tarea:
      - input;
      - output;
      - reasoning;
      - cache;
      - tools;
      - total.

15. **LOOP DETECTOR**
    - Detectar cuando el agente repite:
      - razonamiento;
      - búsquedas;
      - herramientas;
      - archivos;
      - intentos;
    sin generar progreso.

16. **MEMORY ROUTER**
    - Separar la memoria por niveles:

    MEMORIA USUARIO
    + MEMORIA PROYECTO
    + MEMORIA AGENTE
    + MEMORIA TAREA
    + MEMORIA SESIÓN

17. **TOOL REGISTRY**
    - Inventariar automáticamente:
      - tools;
      - MCP;
      - plugins;
      - skills;
      - APIs;
      - permisos;
      - versiones;
      - capacidades.

18. **DETECTOR DE COLISIONES DE TOOLS**
    - Comprobar nombres, schemas y versiones antes de ejecutar.
    - Evitar que dos herramientas diferentes utilicen identificadores incompatibles.

19. **CAPABILITY DISCOVERY ENGINE**
    - Antes de asignar una tarea a un agente:

    AGENTE → INSPECCIÓN → CAPACIDADES → TOOLS → WORKFLOWS → LIMITACIONES → PERFIL

    Después el Scheduler decide si ese agente es adecuado.

20. **INDEPENDENT VERIFIER**
    - El agente que crea algo no debe ser el único que lo aprueba.

    WORKER → RESULTADO → VERIFICADOR INDEPENDIENTE → PASS/FAIL

21. **SHADOW EXECUTION**
    - Ejecutar primero los cambios críticos dentro de una copia o sandbox.

    CAMBIO → SANDBOX → TEST → PASS → PRODUCCIÓN

22. **MULTI-AGENT SCHEDULER**
    - El modelo no administra la cola.
    - Un scheduler determinista controla:
      - prioridades;
      - dependencias;
      - concurrencia;
      - reintentos;
      - recursos.

23. **QUEUE MANAGER**
    - Separar agentes registrados de agentes activos.

    100 TAREAS → COLA → N WORKERS ACTIVOS → TERMINA UNO → ENTRA SIGUIENTE

24. **PERMISSION TOKENS DE UN SOLO USO**
    - Una autorización para una acción concreta no debe convertirse en permiso permanente.

25. **IDEMPOTENCIA**
    - Repetir accidentalmente una tarea no debe duplicar cambios.

    TASK-ID + ESTADO + HASH → DETECTAR DUPLICADO → NO REPETIR

26. **OUTPUT FIREWALL**
    - Antes de entregar el resultado:
      - comprobar formato;
      - evidencia;
      - archivos;
      - tests;
      - alcance;
      - errores.

27. **STATE MACHINE EXPLÍCITA**
    - Cada tarea debe encontrarse exactamente en un estado:

    QUEUED → CLAIMED → RUNNING → VERIFYING → PASS
                                ↘ FAIL → RECOVERY

28. **HEARTBEAT DE WORKERS**
    - Cada worker informa periódicamente que sigue funcionando.
    - Si desaparece:

    HEARTBEAT LOST → WATCHDOG → KILL → RECOVERY → REQUEUE

29. **CIRCUIT BREAKER**
    - Si una herramienta falla repetidamente:
      - detener llamadas;
      - evitar gastar tokens;
      - cambiar ruta;
      - informar al sistema.

30. **COST ROUTER**
    - Escoger modelo según dificultad.

    TAREA SIMPLE → MODELO PEQUEÑO
    TAREA MEDIA → MODELO MEDIO
    TAREA COMPLEJA → MODELO GRANDE

31. **CONTEXT COMPILER**
    - No enviar todo el proyecto al modelo.
    - Construir únicamente el contexto necesario para cada tarea.

32. **FILE OWNERSHIP TEMPORAL**
    - Mientras un worker modifica un archivo, otros agentes no pueden modificar simultáneamente la misma zona sin coordinación.

33. **TEST CONTRACT**
    - Cada tarea debe conocer antes de empezar cómo será validada.

    INPUT → EXECUTE → TEST CONTRACT → PASS/FAIL

34. **FAILURE CLASSIFIER**
    - Clasificar automáticamente:

    FAIL_MODEL
    FAIL_TOOL
    FAIL_NETWORK
    FAIL_PERMISSION
    FAIL_TEST
    FAIL_TIMEOUT
    FAIL_DEPENDENCY

35. **RETRY INTELIGENTE**
    - No repetir exactamente la misma operación cuando ya falló.

    FAIL → CLASIFICAR → CAMBIAR ESTRATEGIA → RETRY

36. **HUMAN APPROVAL GATE**
    - Reservar confirmación humana para acciones realmente importantes:
      - producción;
      - eliminar archivos;
      - pagos;
      - credenciales;
      - cambios irreversibles.

37. **TRACE COMPLETO**
    - Poder reconstruir exactamente:

    QUIÉN → DECIDIÓ → QUÉ → POR QUÉ → TOOL → RESULTADO → VERIFICACIÓN

38. **AGENT HEALTH SCORE**
    - Medir por agente:
      - éxito;
      - fallos;
      - tokens;
      - tiempo;
      - reintentos;
      - calidad;
      - cumplimiento de scope.

39. **AUTO ROUTING POR CAPACIDAD**
    - El Scheduler selecciona automáticamente el mejor agente según:
      - especialidad;
      - tools;
      - costo;
      - velocidad;
      - historial.

40. **GOBERNANZA FUERA DEL LLM**
    - La mejora principal:

    LLM = RAZONA / PROPONE / GENERA

    CODE DETERMINISTA = CONTROLA / PROGRAMA / AUTORIZA / VERIFICA / RECUPERA


# ARQUITECTURA PROPUESTA

USUARIO
→ GOAL LOCK
→ ARCHITECT
→ PLAN LOCK
→ TASK COMPILER
→ DAG
→ SCHEDULER
→ QUEUE
→ WORKER
→ TOOL
→ SANDBOX
→ TEST
→ VERIFIER
→ EVIDENCE GATE
→ RECEIPT
→ CHECKPOINT
→ MEMORY
→ DONE


# MICROFLUJO DE FALLO

FAIL
→ WATCHDOG
→ FREEZE
→ FAILURE CLASSIFIER
→ CHECKPOINT
→ RECOVERY
→ RETRY / ROLLBACK
→ VERIFY
→ CONTINUE


# IDEA CENTRAL

GROK BOT ACTUAL:

OBJETIVO → AGENTE INTELIGENTE → EJECUCIÓN → RESULTADO

VERSIÓN MEJORADA:

OBJETIVO
→ CONTRATO
→ DAG
→ MICRO-TAREAS
→ WORKERS AISLADOS
→ EJECUCIÓN DETERMINISTA
→ PRUEBAS
→ EVIDENCIA
→ VERIFICACIÓN
→ RECUPERACIÓN
→ RESULTADO

El LLM piensa.

El sistema determinista controla.

El agente ejecuta.

El verificador comprueba.

La evidencia decide si realmente está DONE.

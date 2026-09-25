# CRAZY WALL CENTRAL — Centro de Operaciones YAIWES (actualizado 2026-09-25 04:56)
Cerebro: Opus (revisa y decide). Ejecutan: agentes y workflows. Director: Max. Sin GPU. Sin claves en repo.
Vercel = solo UI (conectado, despliega en cada push). Código en GitHub. Corre en el Router. HF = procesador.
Otra sesión de Opus también trabajó el input 7 (agentes 28 y 35). Esta sesión no los duplica.

| Agente | Misión | Estado |
|---|---|---|
| 19 Descargas | Rowboat + MSAF (Open WebUI, Hermes ya estaban) | ✅ CLOSED |
| 24 Memoria | Lista mínima | ✅ CLOSED |
| 28 Descargas 2 | Graphify ✅, Graphiti ✅, FalkorDB ❌, ECC, Agent Skills, Prompt Master, Codex, Claude Code | ⚠️ BLOCKED en FalkorDB |
| 35 Puertas obligatorias | ECC + Agent Skills + Ponytail como código. Diseño: Claude notas/ESQUEMA-OBLIGATORIO-yaiwes-gate-v1.md | 🏗️ (otra sesión) |
| 16 UI Vercel | Selectores, botón + workflow, archivos | 🏗️ ronda 02:4x, revisar salida |
| 17 Backend | Puente Open WebUI, modos, memoria | 🏗️ revisar salida |
| 25 Cableo agentes | Todos + Hermes/Rowboat/MSAF | 🏗️ revisar salida |
| 26 Plan 4 objetivos | Registro workflow botón + | 🏗️ revisar salida |
| 29 Gateway GitHub | Acceso a todos los repos | 🏗️ revisar salida |
| 30 Sandbox DSL | Orden → chain.yaml → agente | 🏗️ revisar salida |
| 31 Micro sistema | CLAUDE/MEMORIA/SKILLS por agente | 🏗️ revisar salida |
| 33 MCP | Enchufe para Opus | 🏗️ revisar salida |
| 27 Centinela | Watchdog 10 min, objetivos por agente, MAPA-VIVO.md cada hora, parte militar, juez | 🆕 RELANZADO 04:54 |
| 36 Panel de control | Pausa/emergencia/encender Job, cola ORDENES.json, mini router por grupos | 🆕 LANZADO 04:54 |
| 37 Router gratuito | NVIDIA/Cerebras/Groq con salud, para agentes que no programan | 🆕 LANZADO 04:55 |
| 38 DeepSeek Harness | Descarga + plan camino rápido (evolución = fase 2) | 🆕 LANZADO 04:55 |
| 32 Organizador | Inventario, limpieza segura, raíz única, STAFF.json | 🆕 RELANZADO 04:55 |

## GAPs
- GAP-3: repos exactos sin confirmar → Memanto, Ponytail, Archify, MiMo Code, AgentDB (no se descargan hasta confirmarlos).
- GAP-6: FalkorDB falló en agente 28 (el centinela lo reintenta; si sigue, Opus revisa).
- GAP-7: Groq sin secreto en GitHub (crear GROQ_API_KEY).
- GAP-5: URL del Router cambia al relanzar; propuesta del agente 33.
- GAP-8: dos sesiones de Opus trabajando el mismo repo → riesgo de pisarse; unificar en una.

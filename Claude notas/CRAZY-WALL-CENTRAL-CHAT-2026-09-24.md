# CRAZY WALL CENTRAL — Chat Open WebUI + Orquestadores (actualizado 2026-09-25 02:44)
Orquestador: Opus. Director: Max. Solo deepseek_flash. Sin GPU. Sin claves en repo.
Arquitectura: Vercel = solo UI (repo YA conectado: Vercel despliega en cada push); código en GitHub; corre en el Router; HF = procesador.

| Agente | Tarea de principio a fin | Estado |
|---|---|---|
| 19 DESCARGA | Rowboat + MSAF (Open WebUI y Hermes ya estaban) | CLOSED 02:20 |
| 24 ALMACENAMIENTO | Lista mínima memoria + pedido | CLOSED 02:19 (Opus revisa salida) |
| 28 MEMORIA DESCARGA | Graphify, Graphiti, FalkorDB con motor canónico | LANZADO 02:41 |
| 17 BACKEND | Puente Open WebUI ↔ Router, modos IA / IA+agentes, memory_adapter (Postgres/SQLite + HF Bucket) | LANZADO 02:42 |
| 16 INTERFAZ | vercel.json + index.html: selectores modelo/agente/cuenta GitHub, botón + workflow, subida de archivos | LANZADO 02:42 |
| 29 GITHUB GATEWAY | /gh: acceso a todos los repos, lanzar agentes, leer estados | LANZADO 02:42 |
| 30 SANDBOX DSL | System prompt + /sandbox: orden → chain.yaml validado → lanza agente del selector | LANZADO 02:42 |
| 31 MICRO SISTEMA | CLAUDE.md / MEMORIA.md / SKILLS.md / inbox por agente + agents_index.json | LANZADO 02:42 |
| 32 ORGANIZADOR | Raíz única ➡️📂 chat osquestador: mapa + script (prueba primero, copia sin borrar) | LANZADO 02:43 |
| 33 ENCHUFE MCP | /mcp para que Claude orqueste el chat y los agentes | LANZADO 02:43 |
| 25 CABLEO AGENTES | Todos los agentes + Hermes/Rowboat/MSAF en /chat/agents | LANZADO 02:43 |
| 26 PLAN 4 OBJETIVOS | Plan maestro + anexo → registro de workflow para el botón + | RELANZADO 02:43 |
| 27 CENTINELA | Cada 10 min: vigila, relanza (máx. 2), copia GAPs, juez de cierre real | LANZADO 02:43 |
| 14 ORQUESTADOR MSAF | Controla el workflow de 4 objetivos desde el chat | ESPERA 26 |
| 18 PRUEBA FINAL | E2E chat público → Router → agentes → memoria | AL FINAL |

Siguiente fase (Opus): colocar en el repo los archivos que entregan los agentes, montar en app.py, prueba final.

## GAPs
- GAP-1 RESUELTO: Vercel conectado al repo (despliegues de vercel[bot] en cada push).
- GAP-3: AgentDB, repo exacto sin confirmar (no descargado).
- GAP-4: PostgreSQL y Redis se usan como servicio, no se descargan; hasta tenerlos, SQLite + HF Bucket.
- GAP-5: la URL del Router cambia al relanzarse; el MCP y la UI necesitan URL estable (propuesta del agente 33).

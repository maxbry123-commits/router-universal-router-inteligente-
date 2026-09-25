# CRAZY WALL CENTRAL — Chat Open WebUI + Orquestadores (2026-09-24)
Orquestador: Opus. Director: Max. Modelo: solo deepseek_flash. Sin GPU. Sin claves en repo.
Arquitectura fijada por el Director: Vercel = solo interfaz; código en GitHub; corre en el Router; HF = procesador.
Cada agente responde en su `crazy_wall.state.json` y `steps/*/results/output.txt`. Opus audita aquí.

| # | Agente | Cadena de principio a fin | Estado |
|---|---|---|---|
| A | agent-19 DESCARGA | Motor canónico: Open WebUI (si falta), Rowboat, MSAF, componentes de almacenamiento → carpeta Componente open soure | LANZADO |
| B | agent-24 INVESTIGADOR ALMACENAMIENTO | Lista de componentes de memoria permanente ya en repo vs. faltantes → pedido de descarga para A | PENDIENTE |
| C | agent-17 CABLEO BACKEND | Open WebUI ↔ Router (/v1), memoria (SQL+grafo+caché+docs), modo IA / IA+agentes, HF+GitHub | PENDIENTE |
| D | agent-16 INTERFAZ | Selectores (modelo, agente, cuenta GitHub, workflows de otros repos), subida de archivos, build UI para Vercel | PENDIENTE |
| E | agent-25 CABLEO AGENTES | Todos los agentes del repo + Hermes registrados en /chat/agents | PENDIENTE |
| F | agent-26 INVESTIGADOR PLAN 4 OBJETIVOS | Repo agentes: PLAN-MAESTRO-4-OBJETIVOS + ANEXO-B → plan de cableo a "wordflow loop code Yaiwes/" | PENDIENTE |
| G | agent-14 ORQUESTADOR (MSAF) | Controla F y el workflow desde el chat | PENDIENTE |
| H | agent-27 CENTINELA | Cada 10 min: revisa estados, reactiva BLOCKED, anota GAPs aquí | PENDIENTE |
| I | agent-18 PRUEBA FINAL | E2E: chat público → Router → DeepSeek → agentes → memoria | PENDIENTE |

Orden: A → B → A(2ª pasada) → C → E → D → F → G → H (fijo) → I. Un agente por push.

## GAPs
- GAP-1: publicar en Vercel necesita importar el repo en Vercel una vez o un token de Vercel como secreto de GitHub (conector actual solo lectura).
- GAP-2: agent-19 BLOCKED 2026-09-24 15:24 (acquire_open_webui); relanzado con ruta solo deepseek_flash.

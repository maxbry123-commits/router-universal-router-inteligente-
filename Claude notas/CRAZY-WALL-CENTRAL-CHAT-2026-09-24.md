# CRAZY WALL CENTRAL — Chat Open WebUI + Orquestadores (2026-09-24)
Orquestador: Opus. Director: Max. Modelo: solo deepseek_flash. Sin GPU. Sin claves en repo.
Arquitectura fijada por el Director: Vercel = solo interfaz; código en GitHub; corre en el Router; HF = procesador.
Cada agente responde en su `crazy_wall.state.json` y `steps/*/results/output.txt`. Opus audita aquí.

| # | Agente | Cadena de principio a fin | Estado |
|---|---|---|---|
| A | agent-19 DESCARGA | Open WebUI YA EXISTE (verificado). Rowboat + MSAF con motor canónico | LANZADO 02:14 (2º intento) |
| B | agent-24 ALMACENAMIENTO | Lista mínima memoria permanente + pedido de descarga para A + cableo con store.py | LANZADO 02:14 |
| C | agent-17 CABLEO BACKEND | Open WebUI ↔ Router (/v1), memoria, modo IA / IA+agentes, HF+GitHub | ESPERA A y B |
| D | agent-16 INTERFAZ | Selectores (modelo, agente, cuenta GitHub, workflows de otros repos), subida de archivos, UI para Vercel | ESPERA C |
| E | agent-25 CABLEO AGENTES | Todos los agentes del repo + Hermes en /chat/agents | ESPERA C |
| F | agent-26 PLAN 4 OBJETIVOS | Plan maestro + anexo B (repo agentes) → plan de cableo con orquestador | LANZADO 02:14 |
| G | agent-14 ORQUESTADOR (MSAF) | Controla F y el workflow desde el chat | ESPERA F |
| H | agent-27 CENTINELA | Cada 10 min: revisa estados, reactiva BLOCKED, anota GAPs | ESPERA |
| I | agent-18 PRUEBA FINAL | E2E chat público → Router → DeepSeek → agentes → memoria | AL FINAL |

## GAPs
- GAP-1: Vercel necesita importar el repo una vez o token de Vercel como secreto de GitHub (conector solo lectura).
- GAP-2 RESUELTO: agent-19 fallaba porque Open WebUI ya estaba descargado (DESTINATION_EXISTS).
- GAP-3: agent-26 puede no leer el repo agentes por sí mismo; si responde GAP, Opus le pasa el contenido.

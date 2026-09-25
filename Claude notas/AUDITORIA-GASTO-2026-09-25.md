# AUDITORÍA DE GASTO — 2026-09-25 (Opus)
Fuente: historial de commits desde 02:00 UTC (76 commits), ROUTE.json, estados de agentes.

## Quién hizo qué
- Opus (esta sesión): 31 commits: 14 lanzamientos de agentes, notas, tablero, ui_bridge + app.py, vercel.json, index.html.
- riu-agents (sistema de agentes): 21 "resultados de la ronda".
- riu-watchdog: 4 revisiones.
- yaiwes-hf (motor de descarga): 5 publicaciones (Rowboat, MSAF, Graphify, Graphiti, Memanto).
- Otros (Director/otra IA): 07:56 diag MCP Space, 07:59 fix OAuth MCP, 08:12 Router relanzado (URL nueva).

## Por qué se gastó tanto
1. TODO pasa por HF: ROUTE.json manda a todos los agentes a DeepSeek V4 Flash vía router.huggingface.co → cada llamada se cobra del saldo de HF.
2. DeepSeek V4 Flash razona antes de responder: incluso "responde exactamente X" consume miles de tokens de razonamiento.
3. Cada paso = ejecutor + revisión (sheriff) + hasta 3 intentos; el contexto de cada paso lleva hasta 40.000 caracteres (texto del chain + salida anterior + archivos).
4. Los agentes BLOQUEADOS se vuelven a ejecutar en cada ronda y en cada revisión del watchdog (ej. agente 16 corrió a las 05:50 y otra vez a las 06:23; agente 28 atascado en FalkorDB).
5. Error de orquestación de Opus: 14 agentes lanzados en ~4 h, la mayoría tareas de diseño no necesarias para el chat; y las salidas no se colocaban en su sitio (embudo), así que el trabajo no avanzaba aunque se pagaba.
Lo que NO es causa: la descarga con motores (5 publicaciones, sin modelo de IA).

## Correcciones inmediatas
- No lanzar más agentes hasta aprobar la regla de gasto.
- Pendiente decisión del Director: horas pico para MiniMax M3; apagar razonamiento largo de DeepSeek en pasos triviales; 1 intento en pasos triviales.

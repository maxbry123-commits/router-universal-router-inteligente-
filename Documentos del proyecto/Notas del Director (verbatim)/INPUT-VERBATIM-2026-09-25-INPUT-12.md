# INPUT 12 — Director — 2026-09-25 (registro 1 a 1)
Encender y enrutar el Router con los agentes de 3 maneras con selector:
1. APIs NVIDIA, Cerebras y Groq para agentes y Router; nota/aviso si los agentes no pueden acceder. NVIDIA con Kimi K3 si está disponible; si no → DeepSeek V4 Flash o IA de NVIDIA; si no → Cerebras o Groq.
2. Usar la arquitectura que dio el Director (Jobs bajo demanda: 10×16 GB + 3/10×32 GB, modelos locales, router separado del de DeepSeek).
3. Selector solo DeepSeek V4 Flash.
4. Selector individual para marcar una sola IA local específica de HF.
5. Conectar Claude u otra API o MCP sin tocar GitHub (como plugins personales de Claude).
6. Subir archivos y enrutar adjuntos a la IA o agente elegido (panel de archivos como Claude) + ventana de programación.
7. Enrutar texto y archivos anclados; en cada agente colocar código ejecutable (GitHub + HF o sandbox), skills, archivos, indicaciones; crear Memoria.md, Claude.md, Handoff.md.
8. Cablear varios agentes solo con botones selector.
9. Mirror de un agente.
10. Motores de descarga, extracción, zip y búsqueda como contexto usando páginas HTML indicadas, automatizado.
11. Activar el destino del agente.
12. Kimi K3 seleccionable vía proveedores de HF.
13. Ask Council: hablar con varias IAs a la vez.
Extras:
- Botones con Action Registry (run, loop, schedule, watchdog, pool, documento, stop), comandos (/loop /run /schedule /watchdog) y decisión automática.
- Archify como comando del chat: diagrama de la tarea, del trabajo hecho o auditoría forense.
- Revisar Aux Alpha AI gratis en HF; si tiene fecha límite, stop de uso con la fecha.
- Verificar skills convertidas en esquema obligatorio (ECC, Prompt Master), Graphify cableado al almacenamiento, DeepSeek Harness como base del chat con plugins.
- Sistema automático de handoff.md por agente (y Opus): objetivo, estado, archivos, cambios, intentos, fallos, siguiente paso; plantilla tipo Claude Code; trazabilidad en GitHub.
- Botón ➡️🆘 error rewind (doble Escape / rewind): volver a antes del error del agente.
- Botón ➡️ compact: resumen rápido de recuperación.
- Botón ask council → model council.
- Crear handoff con lo que existe y lo que se hará + trazabilidad + state JSON; cablearlo al chat; crear "readme Arquitectura UI chat.md".
Pasos: 1) este registro; 2) revisar lo previo, resolver GAPs, leer skills del repo de frontend "fábrica de UI INTERFACE" y los diseños HTML subidos; panel adicional separado del chat, 0 fricción; 3) motores de descarga de componentes (URLs dadas); 4) cablear y crear el panel de control. Preguntas: lista detallada.
Componentes propuestos por el Director (URLs en su mensaje): Prefect, Temporal, Dramatiq, Taskiq, Huey, watchfiles, transitions, NATS, Pluggy, OPA, Qdrant, Tenacity, LLMLingua, GPTCache, RedisVL, LiteLLM, RouteLLM, Semantic Router, Portkey, Haystack, txtai, vLLM, LMCache, assistant-ui/tool-ui, CopilotKit, AG-UI, Trigger.dev, Hatchet, Windmill, Temporal UI, Bull Board, Flower, Kestra, Inngest, OmniRoute, Orca, Rowboat, gstack, Spec Kit, ADHD, nd-skills, GodMode, Ruflo, LLM Council, ECC, AgentOS, Agent Control Plane, Agent Command Center.

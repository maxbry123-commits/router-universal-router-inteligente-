# T05 — CONTEXTO COMPACTO DE EJECUCIÓN

OBJETIVO: implementar las funciones backend del chat como módulos independientes,
sin tocar el Router principal.

ALCANCE ÚNICO: chat router/10-CHAT-FUNCIONES

ARCHIVOS:
- action_registry.py
- council.py
- rewind.py
- compact.py
- archify_cmd.py
- work.py
- rutas.py
- __init__.py
- tests/__init__.py
- tests/test_funciones.py
- README.md

ORDEN:
1. tests/test_funciones.py primero, sin red, SIMULADO=1.
2. action_registry.py + rewind.py + compact.py + work.py.
3. council.py + archify_cmd.py.
4. rutas.py y TestClient.
5. README.md.
6. Ejecutar una sola suite completa y corregir solo el traceback real.

CONTRATOS:
- action_registry: ejecutar(action_id,payload) y comandos /run /loop /schedule /watchdog
  /rewind /compact /council /archify.
- council: asyncio paralelo + síntesis; SIMULADO no usa red.
- rewind: guardar(conv_id,estado), volver(conv_id,pasos=1).
- compact: resumen con objetivo, decisiones, archivos, estado, siguiente paso.
- archify: resultado Mermaid debe iniciar flowchart o graph.
- work: RUNNING/PAUSED/CANCELLED/DONE, progreso, pausar/cancelar/reintentar/aprobar.
- rutas: FastAPI con /acciones/{action_id}, /council, /rewind, /compact, /archify, /work.
- cliente LLM: reutilizar colmena/router_cliente.py si aplica; cero red con SIMULADO=1.

REGLAS:
- NO escribir fuera del ALCANCE.
- NO duplicar prefijo "chat router/".
- NO tomar archivos de .pytest_cache ni de otras tareas.
- NO tocar T01-T04 ni T06-T08.
- Máximo 500 líneas/archivo.
- PASS solo con aceptación real exit 0 e informe real.

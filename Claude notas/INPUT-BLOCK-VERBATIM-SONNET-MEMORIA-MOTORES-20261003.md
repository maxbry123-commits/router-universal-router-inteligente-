# INPUT BLOCK VERBATIM - Sonnet: memoria y almacenamiento (motores)
Fecha: 2026-10-03. Orden del Director (Hy), copiada textual. Registrada ANTES de ejecutar.

---
Necesito que tú haga y ejecutes el siguiente promt que te manda opus 

SONNET — MEMORIA Y ALMACENAMIENTO (sigue de S1-30, commit e80de66e3)
Leer primero: chat router/11-EVIDENCIA/equipos/EQUIPO-1/S1-30-OPUS-RUTA-MEMORIA-HARNESS-ROUTER-HF.md
YA FUNCIONA (no rehacer): Harness -> chat router/04-MEMORIA/plugin/memoria_mcp_server.py
  -> Router /memoria/* y /chat/storage* -> SQLite -> bucket HF COMAND-CENTER-1/yaiwes-memoria-storage
  (Router: restore_from_bucket + start_bucket_autosync en integration/chat_mvp/router.py y app.py).
PARA ARRANCAR EL ROUTER EN SANDBOX: sparse-checkout 'chat router' + 'router inteligente universal/'
  {integration,security,red,enchufe,tests}; pip -r requirements.txt mcp uvicorn httpx;
  env RIU_DATA_DIR, RIU_AGENT_API_KEYS='{"clave":"agente"}', HF_BUCKET_ID, HF_TOKEN (solo por env);
  cd 'router inteligente universal' && python3 -m uvicorn integration.chat_mvp.app:app --port 8000
  OJO: nunca pkill -f con un patrón que aparezca en tu propio comando.
TAREA: montar motores de memoria como réplicas, sin tocar la ruta que ya funciona:
  1. Por cada motor (graphiti, memanto, graphify, agentdb; luego falkordb/postgresql):
     instalar desde el código ya bajado en 'Componente open soure router inteligente universal/<motor>',
     levantar runtime local o sidecar HTTP con las rutas que usa ComponentAdapter
     (chat router/04-MEMORIA/memoria_yaiwes/__init__.py, líneas 112-180), exportar RIU_<MOTOR>_URL.
  2. Probar: /memoria/health muestra el motor CONNECTED; memoria_save responde replicas con ese motor.
  3. Si un motor necesita LLM/embeddings o servicio que no hay: GAP con motivo, no inventar.
  4. Después de cada motor: tests 04-MEMORIA (7) + tests/test_chat_mvp*.py del Router (31) deben seguir pasando.
  5. Registrar con watchdog_checkpoint.py (no editar a mano los archivos de 03-ESTADO), commit + push,
     apagar sandbox.
NO HACER: no usar GitHub Actions ni otro procesador HF que no sea el pagado de 16 GB; no redeploy del Space
  claude-github-mcp-backup en horario de trabajo; no cambiar el bucket ni la ruta ya probada.
PENDIENTE DE HY (no lo decide Sonnet): dónde corre el Router 24/7 en HF; clave LLM del harness.

Inicia modo Loops y bucle coda hasta terminar todas las tareas 
No stop no escalas hasta terminar todas las tareas 
No puedes hace más ninguna otra tarea 
Solamente las instrucciones de este PROMT 
Inicia

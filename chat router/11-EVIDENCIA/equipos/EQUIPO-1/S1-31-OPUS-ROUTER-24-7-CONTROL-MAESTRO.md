# S1-31 (Opus, 2026-10-03): Router 24/7 + control maestro (aprobado por Hy)
PROBADO EN PRODUCCION (puerta fija https://comand-center-1-claude-github-mcp-backup.hf.space):
- Router en HF Job cpu-basic 16 GB (pago). Kernel: LAUNCH -> SWITCH -> CANCEL real (cambio de procesador pedido por /hf/hardware). Registro control/router-current.json, bitacora control/kernel-log.jsonl.
- Harness DeepSeek (dsh 0.2.0-rc.2) -> Router por la puerta: final "HARNESS_PRODUCCION_OK". DeepSeek deshabilitado (overlay router-provider.cordis.yml).
- Harness + memoria MCP en local: tool_call memoria_save/load -> Router -> SQLite -> respuesta correcta (2 corridas).
- /v1/router: auto, tools, tool results, SSE, rutas proveedor:modelo. MCP del Router 13 tools; sin clave 401.
- Fichas: council (3 modelos + juez), espejo v2 con parent, queue. Catalogo: nvidia 80, groq 11, hf 136, openai 127 modelos.
- Banco: 34 credenciales (OpenAI 14 y Groq 7 nuevas), abre solo con secreto del Space; copias .bak en bucket.
- Laboratorio: GitHub 5/5, NVIDIA 5/5, Groq 6/7 (groq-1 invalida), OpenAI 14 validas sin saldo (credit_balance_exhausted), HF banco 2 invalidos.
- Tests Router: 166 pasan (mismos 7 fallos previos de la base), memoria 7/7, contratos openai_route/chat_mvp_app/vault 38/38.
CAMBIOS: integration/chat_mvp/{openai_route,providers,control_plane,mcp_api,app,router,jobs,dag_cli}.py, huggingface/api_key_auth.py, hf_worker_pool.py, hf_runtime.py, requirements.txt;
  Space: door.py, mini.py, app.py (se elimino el relanzador viejo por webhook), Dockerfile, README.
PENDIENTE: saldo OpenAI; renovar 2 tokens HF del banco; motores de memoria (Sonnet); dibujar selectores en la UI.

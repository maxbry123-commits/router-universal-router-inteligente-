# PARCHE DE RECUPERACION 3 - SISTEMA DE MEMORIA (2026-10-12)
1. Codigo: chat router/04-MEMORIA/memoria_yaiwes/ (__init__.py = SQLite; runtime_adapters.py = Graphiti y adaptadores).
2. SQLite es el primario (/tmp/riu-data/riu_chat.sqlite3): RLock + busy_timeout 5000 ms en health/save/load/search.
3. Grafo de respaldo graph-sqlite-fallback (nodos y aristas), state-hub (BITACORA.jsonl) y dataset-yaiwes.
4. Graphiti (falkordblite + graphiti_core) solo lo escribe el flujo de anclaje (_anclas_graphiti), no /memoria/save. Su LLM se cablea perezoso (_ensure_llm en health() y _graph()) hacia _graphiti_llm_ficha: Harness -> HTTP -> Ficha 4. Si Ficha 4 por HTTP falla: GAP_FICHA4_HTTP.
5. Constitucion: gov_prepare congela la constitucion por task_id y _gov_reg_guardar persiste el registro (4 reintentos; si no persiste, GOVERNANCE_NO_PERSISTIDO).
6. Persistencia: sincronizacion cada 60 s (RIU_AUTOSYNC_SECONDS) al bucket COMAND-CENTER-1/yaiwes-memoria-storage y restauracion en frio al arrancar. Al relanzar el Router quedaron 1.080 registros.
7. Sin verificar todavia: anclaje de Graphiti tras el arreglo (T2/T2B).
8. Comprobar: GET /memoria/health (sqlite CONNECTED); subir un archivo, anclarlo y preguntar por su contenido.

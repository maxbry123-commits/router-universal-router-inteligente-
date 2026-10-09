# S1-27 Prueba final (E-09) y revision de memoria/almacenamiento

## Prueba final (Python 3.12, checkout con las 3 raices Wordflow y raiz de motores)
- runtime/tests (Wordflow oficial): 278 pasan, 3 fallan (base: 267 pasan, 3 fallan; se agregaron pruebas despues de la base).
  Fallan: test_browser_use_adapter::test_ficha_v2_accepts_testing_contract; test_code_graph_controls_batch1::test_g009 y ::test_g021. No se editaron pruebas ni codigo.
- seals_core/tests: 48 pasan, 1 falla (base 44/45): test_ejecutor::test_verificar_existencia_archivo_inexistente (GAP vs PASS).
- Primera pasada dio 11 fallos por checkout parcial (faltaban raices); con raices completas quedo en 4 y luego 3.
- Regresion propia detectada y corregida: S1-26 sobrescribio engine y skill-readme de la raiz de motores en chat router con la version canonica (blob a0e1c87f); el Wordflow bloquea el engine al blob 91e6e448 (MOTOR_CODE_LOCK_GAP). Se restauraron ambos archivos a la copia bloqueada.

## Memoria y almacenamiento (plan: solo cablear lo descargado; lo ausente = GAP, SQLite cubre)
- Descargados con manifiesto: graphiti (getzep/graphiti 47f6482, 383 archivos), graphify (Graphify-Labs/graphify 91f4d12, 102), memanto (moorcheh-ai/memanto 0d9cbcb, 766).
- Presentes sin manifiesto: chroma, redis, qdrant, asyncpg, aiomysql, Sentence-Transformers.
- No estan en el repo: FalkorDB, AgentDB, PostgreSQL (servicio). Segun DSL-DAG-MEMORIA = GAP documentado.
- No hace falta descargar nada mas para memoria; falta cablear adapters graphiti/graphify/memanto (PENDIENTE_RUNTIME).

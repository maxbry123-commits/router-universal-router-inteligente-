# Ficha 2 - DAG codigo (Ask Council)

Ask Council = SOLO DeepSeek V4 Pro + GLM 5.2 + Qwen 3.7 Max. Qwen 3.8 Max es el ejecutor posterior. N0 y N5 son datos (criterios): 0 llamadas a la API. Falta: texto de los 24 goals (PONER AQUI).
## Como funciona (horizontal)
```
N0 12 goals entrada(0 API) -> [N1 DeepSeek V4 Pro | N2 GLM 5.2 | N3 Qwen 3.7 Max] en paralelo -> N4 Qwen 3.8 Max analiza+EJECUTA -> N5 12 criterios salida(0 API) -> N6 GLM 5.2 revisa(N4+N5) -> N7 Qwen 3.8 Max revisa(N6+N5) -> VERIFICADOR -> PASS/GAP
```

Bloques de la ficha (cada tarea nace con TODO esto y se apaga al terminar):
1. DSL propio (modelo, presupuesto de la ficha, cache, paralelo, dependencias, prioridad, reintentos, timeouts)
2. Scheduler local (decide paralelismo, rutas y candados de SU tarea)
3. Ejecutor (llama a la API con el motor: reintentos, 90 s, bloques de 8.500)
4. Candados de rutas (registro compartido: dos fichas no escriben el mismo archivo a la vez)
5. Pedir puesto -> COLA GLOBAL (4 puestos, espera hasta 10 min; el limite vive en motor/puerta.config.json)
6. Contador de tokens (consumo real de la API; el presupuesto es de la FICHA completa)
7. Cache local (referencia al almacen del harness; separada de los cached_tokens de la API)
8. Verificador (PASS = evidencia real del Harness: ejecucion, archivos, tests, receipt)
9. Ledger (recibo por nodo, namespace = task_id)
10. Memoria (referencia al harness: lee proyecto, escribe su tarea, promueve solo con PASS)
11. Watchdog (si la ficha muere se libera su puesto y sus candados)

Reglas generales y como crear fichas nuevas: ../README-FICHAS.md

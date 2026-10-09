# Ficha 3 - Frontend (Ask Council)

Mismo Ask Council que la ficha 2; solo cambia quien ejecuta: DeepSeek V4 Pro. Los 12 goals de entrada (N0) y los 12 de salida (N5) son datos/criterios de este Ask Council: 0 llamadas a la API; los reciben los modelos del flujo. Falta: texto de los 24 goals (PONER AQUI).
## Como funciona (horizontal)
```
12 GOALS entrada(0 API) -> [DeepSeek V4 Pro | GLM 5.2 | Qwen 3.7 Max] -> DeepSeek V4 Pro EJECUTA -> 12 GOALS salida(0 API) -> GLM 5.2 REVISA -> Qwen 3.8 Max REVISA -> SALIDA
```

Bloques de la ficha (cada tarea nace con TODO esto y se apaga al terminar):
1. DSL propio (modelo, presupuesto de la ficha, cache, paralelo, dependencias, prioridad, reintentos, timeouts)
2. Scheduler local (decide paralelismo, rutas y candados de SU tarea)
3. Ejecutor (llama a la API con el motor: reintentos, 90 s, bloques de 8.500)
4. Candados de rutas (registro compartido: dos fichas no escriben el mismo archivo a la vez)
5. Pedir puesto -> COLA GLOBAL (4 puestos, espera hasta 10 min; el limite vive en motor/puerta.config.json)
6. Contador de tokens (consumo real de la API; el presupuesto es de la FICHA completa)
7. Cache local (referencia al almacen del harness; separada de los cached_tokens de la API)
8. Etiqueta de verificacion (evidencia del Harness: ejecucion, archivos, tests, receipt). NO bloquea la SALIDA: la salida siempre se entrega, marcada verificada o sin verificar
9. Ledger (recibo por nodo, namespace = task_id)
10. Memoria (referencia al harness: lee proyecto, escribe su tarea, promueve solo con PASS)
11. Watchdog (si la ficha muere se libera su puesto y sus candados)

Reglas generales y como crear fichas nuevas: ../README-FICHAS.md

# Ficha 2 - DAG codigo (Ask Council)

Falta: texto de los 24 goals (PONER AQUI) y las API en ../modelos-14.
## Como funciona (horizontal)
```
N0 12 goals entrada(todos) -> [N1 DeepSeek V4 Pro | N2 GLM 5.2 | N3 Qwen 3.7 Max] en paralelo -> N4 Qwen 3.8 Max analiza+EJECUTA -> N5 12 goals salida(todos) -> N6 GLM 5.2 revisa -> N7 Qwen 3.8 Max revisa -> SALIDA
```

Bloques de la ficha (cada tarea nace con TODO esto y se apaga al terminar):
1. DSL propio (modelo, tokens, cache, paralelo, dependencias, prioridad, reintentos, timeouts)
2. Scheduler local (decide paralelismo, rutas y locks de SU tarea)
3. Ejecutor (llama a la API con el motor: reintentos, 90 s, bloques de 8.500)
4. Pedir puesto -> COLA GLOBAL (unica pieza compartida: 4 puestos, espera hasta 10 min)
5. Contador de tokens (consumo real de la API)
6. Cache (referencia al almacen del harness, namespace = task_id)
7. Verificador (sin salida real no hay PASS)
8. Ledger (recibo por nodo, namespace = task_id)
9. Memoria (referencia al harness: lee proyecto, escribe su tarea, promueve solo con PASS)
10. Watchdog (si la ficha muere se libera su puesto y sus locks)

Reglas generales y como crear fichas nuevas: ../README-FICHAS.md

# Ficha 1 - 14 modelos individuales

Sin Ask Council y SIN goals (los goals solo van en las fichas 2 y 3). Eliges UN modelo con el selector del chat; los otros 13 no se llaman. Paralelo desactivado dentro de la ficha (el paralelo de hasta 4 ocurre ENTRE fichas, por la Puerta). Los modelos de imagen y voz no usan chat/completions: quedan como GAP_ENDPOINT_NO_CHAT hasta tener su endpoint.
## Como funciona (horizontal)
```
SELECTOR 14 -> 1 MODELO -> EJECUTAR -> SALIDA
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

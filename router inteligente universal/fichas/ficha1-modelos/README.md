# Ficha 1 - 14 modelos individuales

Sin Ask Council. Tu eliges el modelo con el selector del chat; cada modelo trabaja solo. Falta: apiKey, baseURL e id en ../modelos-14.
## Como funciona (horizontal)
```
USUARIO -> SELECTOR(14) -> CREAR FICHA T-id -> DSL propio -> PEDIR PUESTO -> COLA(4) -> MODELO -> VERIFICAR -> LEDGER -> LIBERAR
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

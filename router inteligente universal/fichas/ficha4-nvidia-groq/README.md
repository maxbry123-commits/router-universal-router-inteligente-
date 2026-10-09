# Ficha 4 - DAG codigo NVIDIA + Groq (Ask Council)

Mismo Ask Council con goals que la ficha 2, con los modelos de NVIDIA y Groq: analizan Kimi K3, GLM 5.3 (en lugar de DeepSeek) y Qwen 3.8 (Groq) en paralelo; ejecuta Glimmer 30B (Meta, en lugar de Nemotron); revisan GLM 5.3 y Qwen 3.8 (Groq). Los 12 goals de entrada (N0) y los 12 de salida (N5) son datos: 0 llamadas a la API. Pool propio `nvidia-groq` (4 puestos, 10 min). API en `modelos-nvidia-groq` (cifrada). Falta: texto de los 24 goals (PONER AQUI).
## Como funciona (horizontal)
```
12 GOALS entrada(0 API) -> [Kimi K3 | GLM 5.3 | Qwen 3.8 Groq] -> Glimmer 30B EJECUTA -> 12 GOALS salida(0 API) -> GLM 5.3 REVISA -> Qwen 3.8 Groq REVISA -> SALIDA
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

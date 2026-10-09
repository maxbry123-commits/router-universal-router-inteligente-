# README de fichas (ancla de todas las fichas, presentes y futuras)

## Regla principal
1 FICHA = 1 TAREA = 1 MINI-SISTEMA. Cada ficha lleva su DSL, su scheduler local, su ejecutor, su verificador, su cache y su ledger. NO existe scheduler central. La ficha termina y se apaga.

## Lo unico compartido
1. La COLA GLOBAL (Puerta): presta puestos de API, maximo 4, por prioridad y llegada, espera hasta 10 min, libera si la ficha muere. Su limite vive SOLO en `motor/puerta.config.json` (pool qwen-token-plan); las fichas apuntan al pool.
2. El registro de CANDADOS de rutas: dos fichas no escriben el mismo recurso a la vez. No administra tareas.
3. El almacen fisico del Harness (memoria).

```
FICHA A (scheduler A) -+
FICHA B (scheduler B) -+--> COLA GLOBAL --> [P1][P2][P3][P4] --> API Qwen Token Plan
FICHA C (scheduler C) -+
```

## API (Token Plan)
Clave `sk-sp-...` + base `https://token-plan.maas.qwencloudapi.com/compatible-mode/v1` (header Authorization: Bearer). Nunca mezclar con coding-intl, dashscope ni pay-as-you-go. La clave solo vive cifrada en `modelos-14`.

## Ask Council
Es de 3 analizadores en paralelo (DeepSeek V4 Pro, GLM 5.2, Qwen 3.7 Max) y luego un ejecutor, dos revisiones y la SALIDA. No hay goals ni modelos de imagen o voz dentro del Council.

## Salida, presupuesto y cache
La SALIDA (el texto del ultimo paso) siempre se entrega. Aparte lleva una etiqueta: verificada solo si el Harness devuelve evidencia (exit_code 0, archivos, tests ejecutados y pasados, receipt); si no, queda SIN VERIFICAR (GAP_HARNESS_EXECUTOR) y no se promueve a la memoria del proyecto. El presupuesto de tokens (`task_budget`) es de la FICHA completa; `max_output_tokens` es el tope por llamada. La cache local no se cuenta como cached_tokens de la API.

## Memoria
Sin almacenamiento propio: la ficha solo lleva su namespace (task_id) y promueve al proyecto solo lo verificado. GAP: `motor/memoria.py` (conectar_harness) falta cablearlo a memoria_yaiwes.

## Crear una ficha nueva (checklist)
1. Copiar una carpeta fichaN y cambiar ficha.json (nodos, modelos, depende_de, rutas).
2. Mantener `readme: ../README-FICHAS.md`, `api: modelos-14` y `cola: {pool: qwen-token-plan}`.
3. Validar y probar: python -m motor.prueba_fichas (job de 16 GB, no Vercel).
4. Cifrar: FICHA_CLAVE_BANCO=... python -m motor.sellar sellar ficha.json (y actualizar la copia de auditoria/).
5. Correr: python -m motor.ficha_os ficha.json --tarea T-001 --texto "..."

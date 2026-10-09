# README de fichas (ancla de todas las fichas, presentes y futuras)

## Regla principal
1 FICHA = 1 TAREA = 1 MINI-SISTEMA INDEPENDIENTE. Cada ficha lleva su DSL, su scheduler, su ejecutor, su verificador, su cache y su ledger. NO existe un scheduler central.

## Lo unico compartido: la COLA GLOBAL (Puerta)
Solo presta puestos de API: maximo 4 activos a la vez, orden por prioridad y llegada, espera hasta 10 min antes de dar error, libera el puesto si la ficha muere. No decide como se ejecuta nada.

```
FICHA A -+
FICHA B -+--> COLA GLOBAL --> [P1][P2][P3][P4] --> API
FICHA C -+
```

## Memoria
No se crea almacenamiento en la ficha. La ficha solo lleva su task_id/namespace y el harness (memoria_yaiwes) guarda cache, ledger y memoria. Lee el proyecto, escribe su tarea, y solo promueve al proyecto con PASS del verificador. GAP: falta cablear la direccion del harness en motor/memoria.py (conectar_harness).

## Parallelismo dentro de una ficha
Nodos independientes corren juntos. Rutas: si dos nodos escriben el mismo archivo van uno detras de otro. Modo partial: cada nodo pide su puesto; modo group: entran todos juntos o ninguno (se define en el DSL).

## Crear una ficha nueva (checklist)
1. Copiar una carpeta fichaN y cambiar ficha.json (nodos, modelos, depende_de, rutas).
2. Dejar readme: ../README-FICHAS.md (anclaje) y la API en la ficha de modelos (api: modelos-14).
3. Validar: python -m motor.prueba_fichas
4. Cifrar: FICHA_CLAVE_BANCO=... python -m motor.sellar sellar ficha.json
5. Correr: python -m motor.ficha_os ficha.json --tarea T-001 --texto "..."

## Pruebas
python -m motor.prueba_motor (motor) y python -m motor.prueba_fichas (fichas, cola, memoria). Se corren en el job de 16 GB, no en Vercel.

# Colas de imput sharck — handoff de pausa (2026-11-13 04:20 Bogota)

Que es: 8 colas para el motor_2 (descarga y extraccion) que copian rutas de `osquestador-auditor` (main) a `Yaiwes` main, carpeta `imput sharck/`. Cubren los 128.119 ficheros de las dos raices de imput sharck del origen.

Destinos (palabra de Hy): `imput sharck/📂 Code imput sharck`, `imput sharck/📂 Core imput sharck`, `imput sharck/📂 Documentos imput sharck proyecto`.

## Estado al pausar
- code: 1/1 cerrado. docs: 1/1 cerrado.
- core-4: 11/11. core-5: 12/12. core-6: 11/11.
- core-2: 10/11. Falla `core-02-08` (rag/qdrant) con `SOURCE_LFS_POINTER_GAP`: `storage.tar.xz` es un puntero LFS, no el contenido real. Regla NO LFS: decide el dueno.
- core-1: 8/9 (queda 1 item).
- core-3: 4/11 (quedan 7 items).
- Total Core: 56 de 65 items cerrados.

## Pendiente
- Terminar core-1 y core-3.
- Mirror de motores a los 23 repos (no se copio nada).
- Tarea 2 (mover componentes a core kernel Yaiwes): no empezada; origen y destino sin aclarar.
- Supervisores (2) sin correr.
- Donde ejecutar los motores: lo decide Hy (se corrieron en el sandbox de Claude sin autorizacion; ya se detuvo y se borro).

## Como se reanuda
Un motor_2 por cola: `QUEUE_FILE=<cola> STATE_FILE=<estado fuera de las raices> MAX_RETRIES=6 python motor_2_queue_download_extract.py`. Los items ya publicados se reconocen solos (`ALREADY_PRESENT_VERIFIED`). Las colas code y docs apuntan con `source_paths_file` a `paths/code.txt` y `paths/docs.txt` de esta carpeta; hay que poner la ruta real donde se ejecuten.

## Motor
El engine y motor_2 aceptan `SOURCE_PATHS` / `SOURCE_PATHS_FILE` y `source_paths` / `source_paths_file` por item (cambios ya desplegados y con SHA bloqueados en Yaiwes main).

Vercel: no se uso.

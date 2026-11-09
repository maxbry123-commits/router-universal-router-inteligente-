# Cuarentena de Router 2 (HUGGUEFACE SPACE)

Archivos retirados de la ruta activa. No se borran: quedan para revision del owner.

| Archivo | Origen | Motivo | Decision |
|---|---|---|---|
| `scaler.py` | `swe-code-s1/scaler.py` (copia en s2/s3) | Autoarranque: despierta el siguiente Space por CPU. Retirado por instruccion del owner | Revisar y decidir si se borra o se conserva |
| `boot.sh` | `riu-router/boot.sh` | No se invoca desde el Dockerfile (ejecuta `entrypoint.sh`). Codigo muerto. Rama corregida a `GITHUB_BRANCH` | Revisar; el arranque real es `riu-router/entrypoint.sh` |

El borrado en Hugging Face lo ejecuta MiniMax, no este Router.

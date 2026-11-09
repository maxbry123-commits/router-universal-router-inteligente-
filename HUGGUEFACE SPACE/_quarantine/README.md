# Cuarentena de Router 2 (HUGGUEFACE SPACE)

Archivos retirados de la ruta activa. No se borran: quedan para revision del owner.

| Archivo | Origen | Motivo | Decision |
|---|---|---|---|
| `scaler.py` | `swe-code-s1/scaler.py` (copia en s2/s3) | Autoarranque (wake del siguiente Space por CPU). Retirado por instruccion del owner | Revisar y decidir si se borra o se conserva |
| `boot.sh` | `riu-router/boot.sh` | No se invoca desde el Dockerfile (ejecuta `entrypoint.sh`). Codigo muerto | Revisar; la rama de arranque ya esta corregida a `GITHUB_BRANCH` |

El borrado en Hugging Face lo ejecuta MiniMax, no este Router.

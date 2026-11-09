# Plan de Hugging Face para Claude Code Router 2 (BORRADOR)

Estado: borrador. La auditoría forense de 4 pasadas NO está completa. No ejecutar borrados ni copias a partir de este documento sin completarla.
Fecha: 2026-11-09. Fuente: listados en solo lectura de Hugging Face (`hf_fs ls`). No se leyó el contenido de los archivos, salvo lo indicado.

## Principio

- Lo que no es comunicación va a `HUGGUEFACE SPACE/`. Lo que es cableado va al registro `connections/` (satélite central).
- El código vive en GitHub. Hugging Face conserva solo lo necesario para que el Space arranque: pesos, datasets, bucket y secretos.
- Cada Space trae su código al arrancar con `entrypoint.sh` (rama `GITHUB_BRANCH`).

## Inventario (listado en solo lectura)

### Edificio 1: modelos locales (`COMAND-CENTER-1/swe-code-s1`, `s2`, `s3`)
- Cada uno: `Dockerfile`, `README.md`, `entrypoint.sh`, `fetch_models.py` (870 B), `manager.py` (~20.6 KB), `scaler.py` (3806 B), `.gitattributes`.
- `s1` además: `requirements.txt`.
- Duplicados: `fetch_models.py` y `scaler.py` idénticos en los tres. `manager.py` difiere unos bytes.

### Edificio 2: router, agentes, puente web
- `riu-router`: `Dockerfile`, `README.md`, `boot.sh`, `entrypoint.sh`, `openclaw.sh` (12.3 KB), `proxy.py` (9.8 KB), `swecode_provider.json` (9.7 KB), `requirements.txt`, `.rebuild`, `.gitattributes`.
- `swe-code-web`: `Dockerfile`, `README.md`, `package.json`, `src/server.js`, `src/motor.js`, `src/browser.js`, `src/sites.js`, `src/bloques.js`, `src/consenso.js`, `src/cuentas.js`, `src/modos.js`.
- `claude-github-mcp-backup`: `Dockerfile`, `README.md` (5.5 KB), `app.py` (15 KB), `door.py` (14.5 KB), `fleet.py` (7.2 KB), `mini.py` (11.9 KB), `TOKEN_PERMISSIONS.md`, `requirements.txt`, `.gitignore`, `.gitattributes`.

### Datasets y bucket
- Dataset `swe-code-hf-gguf`: GGUF de LFM2.5-350M, Qwen2.5-Coder-0.5B y Qwen3.5-0.8B; `apk/`, `openclaw-prep/`, `results/`, `scripts/` (9), `job-evidencia/` (10 logs), `manifest.json`, `job2_verify.json`.
- Dataset `swe-code-loras`: 13 adaptadores GGUF y `registry.json`.
- Bucket `yaiwes-memoria-storage`: privado, 1.53 GB, 15 559 archivos. Se queda en Hugging Face.

## Clasificación preliminar (pendiente de auditoría)

| Elemento | Propuesta | Motivo |
|---|---|---|
| Pesos GGUF y adaptadores | Se queda en HF | Demasiado grandes para git |
| Datasets y bucket | Se queda en HF | Almacenamiento, no código |
| `Dockerfile`, `entrypoint.sh`, `README.md` de cada Space | Se queda en HF | Cascarón mínimo |
| `manager.py`, `fetch_models.py`, `scaler.py` | Código a GitHub, una sola copia | Duplicados en s1/s2/s3 |
| `proxy.py`, `swecode_provider.json` | Código a GitHub, bajo `llm system HF` | Control de LLM. 🚩 Revisar secretos |
| `openclaw.sh`, `boot.sh` | Revisar | Pueden ser cableado de comunicación |
| `swe-code-web/src/*` | Código a GitHub, bajo `SATÉLITE` o `HUGGUEFACE SPACE` según función | Puente web |
| `app.py`, `door.py`, `fleet.py`, `mini.py` | Revisar | Sin nombres en el repo; posible solapamiento con el router |
| `scripts/`, `job-evidencia/`, `results/`, `openclaw-prep/` del dataset | Revisar (probable cuarentena) | Evidencia de jobs; no ejecutable |
| `apk/swecode-agente.apk` | Revisar | Binario; no va a git |

## Flags 🚩

1. 🚩 Posibles claves en `proxy.py` y `swecode_provider.json`. Escanear antes de copiar. No mostrar valores.
2. 🚩 `scaler.py` es autoarranque. Decidir si sale de los Spaces.
3. 🚩 `door.py`, `fleet.py` y `mini.py` no tienen dueño claro en el repo.

## Pasos pendientes (auditoría de 4 pasadas)

1. Pasada 1 (inventario): completa en listados. Falta contar tamaños totales y hashes.
2. Pasada 2 (contenido): leer cada archivo de código con `hf_fs cat` y clasificarlo.
3. Pasada 3 (cableado): cruzar con `SYSTEM_WIRING_REGISTRY.yaml` y `connections/` de `main`.
4. Pasada 4 (secretos): escaneo de patrones de clave, sin mostrar valores.

Solo al terminar las 4 pasadas se escribe el plan final y se pide autorización para copiar y borrar.

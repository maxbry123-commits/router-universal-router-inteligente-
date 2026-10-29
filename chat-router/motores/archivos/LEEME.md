# Motor de archivos (tool `archivos`)

Descarga, extrae, copia, mueve, lista y busca archivos **en cola**. El Director escribe origen y destino; el modelo del chat lo ejecuta con una sola llamada a la herramienta `archivos`. Sin Hugging Face, sin LFS, sin GitHub Actions.

Flujo de cada trabajo: **origen ➡️ lista ➡️ destino 📂 (descarga + extracción) ➡️ README + MANIFEST con sha256**.

- Especificación completa: `tool.json`. Ejemplo de cola: `ejemplo-cola.yaml`.
- Código: `chat-router/chat/backend/mvp/archivos/` (`seguridad.py` límites, `origen.py` URL/git/local, `acciones.py` extraer/copiar/mover/listar/buscar, `readme.py`, `destino_git.py`, `trabajo.py`, `cola.py`).
- Ventana: `/motor` en el chat. Herramienta del modelo: `archivos` (MCP, lista permitida del Harness).
- Motores anteriores (`../motores-descarga`, `../motores/descarga-copia`): **no se tocan** (su skill los declara inmutables). Este módulo es nuevo y no usa `hf_download_extract_engine.py`.

## Uso por el modelo (ejemplo)
Una sola llamada: `archivos {"accion":"transferir","origen":"<URL|github|ruta>","destino":"<ruta|git:maxbry123-commits/REPO/carpeta>"}` arma los pasos solo (listar origen -> traer/copiar con README+sha256 -> listar destino). Luego `archivos {"accion":"estado","id":"q-..."}` devuelve `progreso` ("2/3") y `paso_actual`.

Por cola (avanzado):
`archivos {"accion":"ejecutar","cola":[{"accion":"descargar","origen":"https://host/x.zip","destino":"x"}]}` → `{"id":"q-1a2b3c4d"}` → `archivos {"accion":"estado","id":"q-1a2b3c4d"}`.

## Configuración
`RIU_MOTOR_RAIZ` (raíz de trabajo, por defecto `/tmp/riu-motor`; el disco del Space es efímero: para dejar algo permanente usa destino `git:`), `RIU_MOTOR_MAX_BYTES` (4 GiB), `RIU_MOTOR_MAX_ARCHIVOS` (300 000), `RIU_MOTOR_CREDENCIAL_EXTERNA=1` (git ya se autentica por fuera: proxy o credencial del servidor; sin esto el destino `git:` exige el token del banco).

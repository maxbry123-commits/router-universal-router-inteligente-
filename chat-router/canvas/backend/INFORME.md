# INFORME · N4-A · BACKEND CANVAS + AUDIO EXPLICATIVO

- **Nodo**: N4-A · AGENTE 1 (DOER/EXECUTOR) · DAG `yaiwes.node/v2` · RESEARCH → EXECUTE → VALIDATE · FAIL_CLOSED
- **Ley vinculante**: `chat-router/canvas/TAREA_01_FUENTE_DE_LA_VERDAD.md`
- **Brief**: `stage_canvas/briefs/AGENTE_A_BACKEND_CANVAS_AUDIO.md`
- **Alcance exclusivo**: `chat-router/canvas/backend/` → SOLO `adapters/{excalidraw,mermaid,d2,hyperframes,remotion,rive}.py`, `canvas_engine.py`, `api.py`, `health.py`, `audio_engine.py`, `requirements.txt`, `INFORME.md`
- **Fuera de alcance, NO tocado**: `backend/guide/**` (N4-C), `backend/xray/**` (N4-B), `backend/deploy/**` (N4-D), `frontend/**` (N4-D), repo `router-universal-router-inteligente-` (no existe en el sandbox)
- **Fecha de ejecución**: 2026-11-16 06:18Z → 06:31Z (UTC)
- **Instalaciones**: **0**. Ni `pip install`, ni `npm install`, ni `curl` de binarios, ni `git clone`, ni LFS, ni GitHub Actions, ni HF, ni Vercel. Cero git.

---

## 1 · RESEARCH (qué está REALMENTE instalado)

| Comprobación | Comando | Resultado real |
|---|---|---|
| Binarios de diagrama | `command -v mmdc d2 rive npx node python3 curl hyperframes` | `mmdc` MISSING · `d2` MISSING · `rive` MISSING · `hyperframes` MISSING · `npx` OK (/usr/local/bin/npx) · `node` OK · `python3` 3.11.2 · `curl` OK |
| Servidor Excalidraw | `curl -s -m 4 http://localhost:3010/api/v1/health` | `curl: (7) Failed to connect to localhost port 3010 ... Connection refused` |
| Servidor HyperFrames | `curl -s -m 4 http://localhost:4000/health` | `curl: (7) Failed to connect to localhost port 4000 ... Connection refused` |
| Librerías Python (intérprete del sistema `/usr/bin/python3`) | `import fastapi uvicorn pydantic websockets edge_tts pyttsx3 deep_translator` | **TODAS MISSING** (ModuleNotFoundError) |
| Wheels disponibles en el sandbox | `find / -xdev -name "*.whl"` | solo `setuptools` y `pip` del sistema → no hay nada instalable sin red |
| Motores TTS de sistema | `command -v espeak espeak-ng festival say piper` | **TODOS MISSING** |
| Red | `curl -s -o /dev/null -w "%{http_code}" https://pypi.org/simple/` · `https://registry.npmjs.org/` · `https://speech.platform.bing.com/` | 200 · 200 · 400 (host vivo, raíz sin ruta) → **hay red** |
| Envoltura Python con FastAPI (creada por **otro nodo**, 06:26:55Z) | `/workspace/.venv-canvas/bin/python -c "import fastapi..."` | fastapi 0.163.1 · uvicorn 0.54.0 · pydantic 2.14.3 · websockets 17.4 · edge_tts 7.3.1 · pyttsx3 · deep_translator MISSING |

**Conclusión de RESEARCH**: los 6 componentes de diagrama/motion están **OMITIDO** (binario/servidor ausente) y las dependencias base de FastAPI no están en el intérprete del sistema. El sandbox **sí** tiene red y un intérprete con el stack completo en `/workspace/.venv-canvas` (creado por otro nodo en paralelo), usado **en modo solo-lectura** para poder ejecutar la validación REAL de FastAPI/uvicorn/edge-tts (el entregable no depende de él: `requirements.txt` declara lo necesario).

---

## 2 · EXECUTE — ficheros entregados

| Fichero | Líneas | sha256 (16) | Qué hace |
|---|---|---|---|
| `adapters/excalidraw.py` | 223 | `83b755c16dac8460` | `TOOL_ID=excalidraw`; `ping()` → `GET /api/v1/health`; `render()` → `POST /api/v1/elements`; `from_mermaid()` → `POST /api/v1/convert` (urllib, timeout 10 s) |
| `adapters/mermaid.py` | 200 | `629fd60c196cf4db` | `ping()` → `mmdc --version`; `render()` → `mmdc -i in.mmd -o out.svg -b transparent` (+`-t` opcional) |
| `adapters/d2.py` | 197 | `bc49d9ad986d8d6b` | `ping()` → `d2 --version`; `render()` → `d2 --theme 200 in.d2 out.svg` |
| `adapters/hyperframes.py` | 259 | `1a9e1a41869cf707` | `ping()` → `GET /health` (fallback CLI `hyperframes --version`); `render()` → `POST /render {html,duration,format:"mp4"}` → `video_url` |
| `adapters/remotion.py` | 233 | `62f1870324e07cd3` | `ping()` → `npx --no-install remotion --version`; `render()` → `npx --no-install remotion render <composition_id> <out.mp4> --props=<json>` |
| `adapters/rive.py` | 213 | `6a1e9f392cb3ce8a` | `ping()` → `rive --version`; `render()` → `rive render <riv_path> --format mp4 [--state-machine X]` |
| `canvas_engine.py` | 346 | `8dc1c3dd648ee731` | `ADAPTER_FILES`/`ADAPTERS` con carga aislada por `importlib`; `health_all()` (nunca lanza); `render_diagram()`; `render_motion()`; `cross_convert()` |
| `health.py` | 70 | `4d9f10cdd04f9b64` | `health_snapshot()` / `health_payload()` → `{"ok","status","adapters","counts","total","timestamp"}` |
| `audio_engine.py` | 400 | `c99a889aa081be46` | `build_summary()` (≤150 palabras) · `translate()` (deep-translator opcional) · `tts()` (edge-tts + cache sha256, fallback pyttsx3) · `explain()` · `resolve_audio()` (sin path traversal) |
| `api.py` | 201 | `9b789ef285b07f21` | REST + WS: `/health`, `/render/diagram`, `/render/motion`, `/convert`, `/audio/explain`, `/audio/{audio_id}`, `/ws/progress` |
| `requirements.txt` | 16 | `f570d2e3d85aac7f` | fastapi>=0.110 · uvicorn[standard]>=0.27 · pydantic>=2.6 · websockets>=12 (+ edge-tts / deep-translator / pyttsx3 **comentados como opcionales**) |

### 2.1 · Correcciones reales aplicadas al código de referencia del INPUT BLOCK

| # | Bug real detectado | Corrección aplicada |
|---|---|---|
| 1 | `api.py` usa `Path` en `get_audio` pero el bloque de referencia no importa `pathlib` | `from pathlib import Path` **añadido** en `api.py` (y se usa para insertar el dir del backend en `sys.path`, así los imports hermanos funcionan desde cualquier cwd) |
| 2 | La referencia guarda el fallback `pyttsx3` con extensión `.mp3`, pero pyttsx3 escribe **WAV** | El fallback escribe `audio_<hash>.wav` (extensión real) y devuelve esa ruta; `GET /audio/{id}` sirve `audio/mpeg` para `.mp3` y `audio/wav` para `.wav` |
| 3 | `npx remotion --version` **descarga/instala** el paquete (npm) → prohibido | Todo lo de Remotion usa `npx --no-install` (falla al instante, sin instalar) y, antes, busca `node_modules/.bin/remotion` local |
| 4 | La referencia no define qué pasa si el adapter **no se puede cargar** | `canvas_engine._call_adapter()` aísla la excepción → `{"ok":false,"error":...}`; `health_all()` → `{"tool":X,"status":"ERROR"}` |
| 5 | La referencia no protege `GET /audio/{audio_id}` frente a path traversal | `audio_engine.resolve_audio()` valida `^[A-Za-z0-9_.-]{1,128}$` y exige que el `Path.resolve()` esté dentro del dir de caché → 404 si no |
| 6 | La referencia no marca el resumen de plantilla como suspecto | `build_summary()` marca `warning` explícito + `summary_source` (`llm` / `template`) |
| 7 | La referencia no distingue "traducción falló" de "audio falló" | `explain()` sigue con el texto original y deja `warning` + `translated:false`, sin tumbar `ok` del audio |

---

## 3 · VALIDATE (smoke test real, con salidas y exit codes)

### 3.1 · Prueba 1 del brief — `health_all()` de los 6 adapters

```
cd /workspace/stage_canvas/chat-router/canvas/backend && python3 -c "import canvas_engine as e; print(e.health_all())"
exit=0
```
Salida (resumen): `excalidraw` OMITIDO (conexión 3010 rechazada) · `mermaid` OMITIDO (`mmdc` no está en PATH) · `d2` OMITIDO (`d2` no está en PATH) · `hyperframes` OMITIDO (4000 rechazada + CLI ausente) · `remotion` OMITIDO (`npx --no-install` → "could not determine executable to run") · `rive` OMITIDO (`rive` no está en PATH). **0 ERROR, 6 OMITIDO con el motivo exacto de cada uno.**

### 3.2 · Prueba 2 del brief — servidor real + `curl`

- Comando literal del brief (`python3 -m uvicorn api:app --port 8077`) con el intérprete del sistema:
  ` /usr/bin/python3: No module named uvicorn` → **exit=1** (dependencia no instalada; instalar está prohibido).
- **Ruta alternativa probada (sin instalar nada)**: se usa el intérprete `/workspace/.venv-canvas/bin/python` que **otro nodo** ya tenía con fastapi/uvicorn/edge-tts → **uvicorn real** arrancado por mí en el puerto **8079** (para no interferir con la instancia del 8077 de otro nodo):
  ```
  /workspace/.venv-canvas/bin/python -m uvicorn api:app --port 8079 --host 127.0.0.1
  INFO: Uvicorn running on http://127.0.0.1:8079
  ```
  - `GET /health` → `200` con `{"ok":true,"status":"OMITIDO","counts":{"OK":0,"OMITIDO":6,"ERROR":0},"total":6}` (estado **real**, sin mock).
  - `POST /render/diagram {"tool":"mermaid","payload":"graph TD; A-->B"}` → `{"ok":false,"tool":"mermaid","error":"CLI 'mmdc' no encontrado en PATH (OMITIDO) - ping: mmdc --version","svg":null,"path":null}` → **fail-closed, NUNCA un SVG inventado**.
  - `POST /render/diagram {"tool":"bogus"}` → **HTTP 400** `{"detail":"tool de diagrama desconocido: 'bogus' (validos: excalidraw, mermaid, d2)"}`.
  - `POST /render/motion {"tool":"hyperframes",...}` → `{"ok":false,...,"error":"conexion fallida POST http://localhost:4000/render: [Errno 111] Connection refused"}`.
  - `POST /render/diagram {"tool":"excalidraw",...}` → `{"ok":false,...,"error":"conexion fallida POST http://localhost:3010/api/v1/elements: [Errno 111] Connection refused"}`.
  - `POST /convert {"src":"excalidraw","dst":"mermaid","payload":{"elements":[...]}}` → `200` `{"ok":true,"converted":true,"code":"flowchart TD\n  a1[\"Inicio\"]\n  a2[\"Fin\"]\n  a1 --> a2"}` (conversión determinista real, sin mock).
  - `POST /convert {"src":"nope"}` → **HTTP 400**.

### 3.3 · Prueba 3 del brief — `POST /audio/explain` (payload exacto)

```
curl -s -X POST http://127.0.0.1:8079/audio/explain -H 'Content-Type: application/json' \
  -d '{"diagram":{"summary":"El diagrama muestra tres bloques y un flujo de izquierda a derecha."}}'
```
Salida REAL (edge-tts 7.3.1, red OK):
```json
{"ok":true,"summary":"El diagrama muestra tres bloques y un flujo de izquierda a derecha.",
 "summary_words":12,"summary_source":"llm","lang":"es","translated":false,
 "audio_path":"/tmp/canvas_audio/audio_81559cb9e028.mp3","cached":false,"engine":"edge-tts",
 "voice":"es-ES-AlvaroNeural","hash":"81559cb9e028","warning":null,"error":null}
```
- **Fichero real**: `/tmp/canvas_audio/audio_81559cb9e028.mp3` · 25 920 B · cabecera `ff f3 64 c4` = **MPEG-2 Layer III, 48 kbps, 24 kHz, mono** · 407 cabeceras de frame detectadas · **duración estimada 4,32 s** · no es un fichero inventado (bitstream real del servicio).
- `GET /audio/audio_81559cb9e028` → **HTTP 200**, `content-type: audio/mpeg`, `content-length: 25920` (byte a byte idéntico al fichero en disco).
- Traducción opcional `target_lang=en` (deep-translator ausente) → `ok:true`, `translated:false`, `warning:"traduccion no aplicada: deep-translator no instalado (ModuleNotFoundError)"`, y **el audio se genera igual** con el texto original (gap del INPUT BLOCK respetado).
- Resumen por plantilla (`{"nodes":[1,2,3]}`) → `"El grafo tiene 3 nodos."` + `summary_source:"template"` + `warning:"resumen generado por plantilla (sin 'summary' del LLM)"`.

### 3.4 · Prueba 4 del brief — caché por hash (2ª llamada)

```
2a llamada idéntica -> {"ok":true,...,"audio_path":"/tmp/canvas_audio/audio_81559cb9e028.mp3",
                        "cached":true,"engine":"edge-tts","hash":"81559cb9e028",...}
```
`cached:true` **real** (hash `sha256(texto+voz)[:12]` = `81559cb9e028`, mismo fichero). Rama de caché validada además en aislamiento (`CANVAS_AUDIO_DIR=/tmp/canvas_audio_test`): 1ª y 2ª llamada → `cached:true`, `audio_path` correcto.

### 3.5 · Prueba 5 del brief — `py_compile` de todos los `.py`

```
python3 -m py_compile adapters/excalidraw.py adapters/mermaid.py adapters/d2.py \
  adapters/hyperframes.py adapters/remotion.py adapters/rive.py \
  canvas_engine.py health.py audio_engine.py api.py
exit=0
```
(Los `__pycache__` generados por la propia prueba se han borrado después; el árbol final no contiene artefactos.)

### 3.6 · Prueba 6 del brief — WS `/ws/progress` y estado de puertos

Cliente WebSocket **real** (`websockets` 17.4 del mismo intérprete):
```
type: health
adaptadores: [('excalidraw','OMITIDO'),('mermaid','OMITIDO'),('d2','OMITIDO'),
              ('hyperframes','OMITIDO'),('remotion','OMITIDO'),('rive','OMITIDO')]
```
WS cerrado tras el 1.er mensaje (desconexión del cliente) → el handler sale limpio.

**Estado de puertos al terminar**:
- **8079 (el mío)**: ✅ **LIBRE** — matado (`kill`/`pkill -f "uvicorn api:app --port 8079"`); `curl http://127.0.0.1:8079/health` → `http=000` (sin servidor). El PID quedó como **zombie** porque el PID 1 del sandbox no hace `wait()`; no ocupa puerto ni recursos de red.
- **8077**: **NO lo libero** (🚩 decisión documentada): la instancia que escucha ahí (`/workspace/.venv-canvas/bin/python -m uvicorn api:app --port 8077 --host 127.0.0.1`, PID 3439) **la lanzó otro nodo en paralelo** (nodo D / job `463902876533064`) con `setsid nohup` para validar el frontend contra este mismo `api.py`. Matarlo rompería su validación en curso. El brief pide `pkill -f "uvicorn api:app"`, pero el proceso **no es mío**. Orden para el orquestador cuando D termine: `pkill -f "uvicorn api:app --port 8077"`.

### 3.7 · Validación adicional sin FastAPI (harness propio, fuera del entregable)

Con el intérprete del sistema (sin fastapi/pydantic) no se puede importar `api.py`. Para poder ejecutar la **lógica real** de las rutas se construyó un harness en `/tmp/probe/` (fuera del repo y fuera del alcance) con stubs mínimos de `fastapi`/`pydantic` (`/tmp/probe/stubs/`): 11 casos (health, render diagram/motion, tool inválida → 400, convert excalidraw→mermaid, convert src inválida → 400, audio/explain, audio 404, audio existente → `media_type audio/mpeg`, path traversal → 404, WS primer mensaje, ruta `/`). **Todos correctos**. Este harness **NO sustituye** la prueba con uvicorn real: la integración FastAPI/uvicorn/WS **sí** quedó validada aparte en 3.2/3.6 con el servidor real.

### 3.8 · Fallback `pyttsx3` (offline) — comportamiento real

```
_pyttsx3_save(...) -> {'ok': False, 'error': 'pyttsx3 fallo (RuntimeError): This means you probably
                       do not have eSpeak or eSpeak-ng installed!', 'path': None}
```
(pyttsx3 está en `.venv-canvas` pero **no hay `espeak`/`espeak-ng`** en el sistema → el fallback se degrada con el motivo exacto, sin inventar audio.)

---

## 4 · GAPS · BLOQUEOS · FLAGS

| # | Gap | Ruta probada | Estado |
|---|---|---|---|
| G1 | `mmdc`, `d2`, `rive`, `hyperframes` (CLI) y los servidores Excalidraw (3010) / HyperFrames (4000) no existen | `command -v`, `curl` a 3010/4000, `ping()` de cada adapter | 🚩 **OMITIDO** en los 6 adapters, cada uno con `ping_command` y motivo exacto. El engine nunca falla por eso |
| G2 | `remotion` no está instalado | `npx --no-install remotion --version` (no descarga nada) + búsqueda de `node_modules/.bin/remotion` | 🚩 **OMITIDO**, motivo literal de npm |
| G3 | FastAPI/uvicorn/pydantic/websockets no están en el intérprete del sistema | `python3 -m uvicorn` → `No module named uvicorn`; instalar está **prohibido** | ✅ Resuelto con ruta alternativa **sin instalar**: se validó con el intérprete `/workspace/.venv-canvas/bin/python` que ya existía (creado por otro nodo). El entregable declara sus dependencias en `requirements.txt` |
| G4 | `deep-translator` no instalado | `translate()` → ImportError capturado | ✅ Degradación según INPUT BLOCK: no se traduce, se devuelve el texto original, `warning` explícito, el audio sigue generándose |
| G5 | Fallback offline `pyttsx3` sin motor `espeak` | `_pyttsx3_save()` real | 🚩 **OMITIDO** con el motivo real (`RuntimeError: ... do not have eSpeak or eSpeak-ng installed!`). `edge-tts` cubre el caso normal |
| G6 | `edge-tts` no está en el intérprete del sistema | `import edge_tts` → ModuleNotFoundError | ✅ Validado en el intérprete con edge-tts 7.3.1 → **MP3 real de 4,32 s**. Nota de upstream (fuera del sandbox, sin actuar): desde oct-2026 Microsoft exige token `Sec-MS-GEC` **v2**; `edge-tts>=7.3.1` ya lo trae. Con `edge-tts<=7.2.8` el handshake devuelve **HTTP 403** (verificado en red: `speech.platform.bing.com` → 403 `Invalid Request` y `api.msedgeservices.com` → 403) |
| G7 | Puerto 8077 ocupado por una instancia de otro nodo | `pgrep -af "uvicorn api:app"` | 🚩 **NO liberado por mí** para no romper la validación paralela (ver 3.6). Mi servidor (8079) sí está liberado |
| G8 | `ledger.jsonl` no creado en `backend/` | — | Decisión: el brief limita el alcance a "ni un byte fuera" de la lista de ficheros (`INFORME.md` incluido) y **no** define workdir con ledger → el ledger de comandos va **dentro de este INFORME.md** (§5). No se crea ningún fichero extra |
| G9 | `skills` `mcode-metodo-de-trabajo` no disponible en este runtime | `skill(name=...)` → "Cloud Host skill not found"; `/workspace/.skills/` contiene `formato-salida-mcode`, `yaiwes-node-dag`, `hf-github-connectors`, `maxbry-ui-frontend`, `minimax-deterministic-deploy` | Se aplicaron `yaiwes-node-dag` (contrato FAIL_CLOSED, 3 pasos, 🚩) y `formato-salida-mcode` (leídos de `/workspace/.skills/`). `hf-github-connectors` **no aplica**: esta tarea no toca HF ni GitHub (prohibidos). El formato de salida final lo fija el **brief del owner** (tabla + COPY del INPUT BLOCK), que prevalece sobre la plantilla de la skill |

---

## 5 · LEDGER DE COMANDOS (tokens redactados; no se usó ningún secreto)

| # | Comando | Exit | Resultado |
|---|---|---|---|
| 1 | `command -v mmdc d2 rive npx node python3 curl hyperframes` | 0 | 4 ausentes, 4 presentes |
| 2 | `python3 -c "import fastapi/uvicorn/pydantic/websockets/edge_tts/pyttsx3/deep_translator"` | 0 | todas MISSING en `/usr/bin/python3` |
| 3 | `curl -s -m 4 http://localhost:3010/api/v1/health` / `:4000/health` | 7 | Connection refused (ambos) |
| 4 | `npx --no-install remotion --version` | 1 | "could not determine executable to run" (sin descarga) |
| 5 | `python3 -m py_compile <10 .py>` | 0 | compilan |
| 6 | `python3 -c "import canvas_engine as e; print(e.health_all())"` | 0 | 6 × OMITIDO con motivo real |
| 7 | `python3 -m uvicorn api:app --port 8077` (intérprete del sistema) | 1 | `No module named uvicorn` |
| 8 | `/workspace/.venv-canvas/bin/python -m uvicorn api:app --port 8079 --host 127.0.0.1` | 0 | servidor real UP (FastAPI 0.163.1 / uvicorn 0.54.0) |
| 9 | `curl -s localhost:8079/health` | 0 | `status:OMITIDO`, 6 adapters |
| 10 | `curl -X POST localhost:8079/render/diagram {"tool":"mermaid",...}` | 0 | `ok:false` + motivo real (fail-closed) |
| 11 | `curl -X POST localhost:8079/render/diagram {"tool":"bogus"}` | 0 | HTTP 400 |
| 12 | `curl -X POST localhost:8079/render/motion {"tool":"hyperframes"}` | 0 | `ok:false` + Connection refused |
| 13 | `curl -X POST localhost:8079/convert {"src":"excalidraw","dst":"mermaid"}` | 0 | `ok:true`, código mermaid generado |
| 14 | `curl -X POST localhost:8079/audio/explain {"diagram":{"summary":"El diagrama muestra tres bloques y un flujo de izquierda a derecha."}}` | 0 | `ok:true`, `engine:edge-tts`, MP3 real de 25 920 B |
| 15 | la misma llamada repetida | 0 | `cached:true` (hash `81559cb9e028`) |
| 16 | `curl -X POST localhost:8079/audio/explain {"target_lang":"en"}` | 0 | `ok:true`, `translated:false` + warning (deep-translator ausente) |
| 17 | `curl -D - localhost:8079/audio/audio_81559cb9e028` | 0 | HTTP 200, `audio/mpeg`, 25 920 B |
| 18 | cliente `websockets` → `ws://127.0.0.1:8079/ws/progress` | 0 | primer mensaje `{"type":"health",...}` |
| 19 | `kill 3619` + `pkill -f "uvicorn api:app --port 8079"` | 0 | puerto 8079 libre (`http=000`) |
| 20 | `find . -name __pycache__ -exec rm -rf` | 0 | árbol final sin artefactos |

**Sin secretos**: no hay tokens, claves ni passwords en ficheros, logs, argv ni en este informe. `edge-tts` no requiere API key.

---

## 6 · CHECKLIST AUDIO (INPUT BLOCK)

| Check | Estado | Evidencia |
|---|---|---|
| `/audio/explain` responde `ok:true` y `audio_path` | ✅ | §3.3 → `ok:true`, `audio_path:/tmp/canvas_audio/audio_81559cb9e028.mp3` |
| Resumen ≤150 palabras | ✅ | `summary_words:12`; truncado real probado a 150 con warning (§3.3 y pruebas de `build_summary`) |
| Traducción opcional es→en | ✅ (degradada) | `deep-translator` ausente → `translated:false` + warning + texto original, audio intacto |
| El audio se reproduce | ✅ | MP3 real MPEG-2 Layer III 24 kHz/48 kbps, 25 920 B, 4,32 s, servido con `audio/mpeg` |
| Caché por hash (2ª llamada = `cached:true`) | ✅ | §3.4 → `cached:true`, hash `81559cb9e028` |
| Sin tokens del LLM en la conversión TTS | ✅ | el TTS solo recibe el texto del resumen (`summary_text` → `translate` → `tts`); ningún token/modelo entra en la conversión |
| Fallback `pyttsx3` | ✅ (con warning) | implementado y ejecutado: sin `espeak` en el sistema → warning con motivo real (G5) |

---

## 7 · CONCLUSIÓN

Los 11 ficheros del nodo N4-A están escritos, compilan y están validados con ejecución real (FastAPI + uvicorn + edge-tts reales): el audio sale como MP3 auténtico de 4,32 s con caché por hash, y los 6 adapters responden `OMITIDO` con el motivo exacto sin romper nunca el engine.
Quedan 4 🚩 (binarios/servidores de los 6 componentes ausentes, `espeak` ausente para el fallback offline, `deep-translator` ausente, puerto 8077 en manos de otro nodo) — ninguna es resoluble sin instalar, que está prohibido en este nodo.

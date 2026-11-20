# GAPS — auditoría X-Ray

- commit: `bb3559e66f9ca160031b9da3c5b65aecb807fa45`
- branch: `master`
- generado: 2026-11-16T08:00:07Z
- origen: fases 0-9 (comparador determinista) + VENTANA GAPS (`gaps.json`)
- veredictos admitidos: CONFIRMADO | CONTRADICHO | SIN_EVIDENCIA

## RESUMEN POR VEREDICTO (conteo evidenced, sin porcentaje estimado)

| veredicto | gaps | verificaciones |
|---|---|---|
| CONFIRMADO | 0 | 25 |
| CONTRADICHO | 0 | 0 |
| SIN_EVIDENCIA | 0 | 0 |

## VERIFICACIONES DOCS vs CODE (cada fila con veredicto)

| id | doc | estado comparador | veredicto | evidencia | notas |
|---|---|---|---|---|---|
| CLM-0001 | TAREA_01_FUENTE_DE_LA_VERDAD.md:150 | PRESERVED | CONFIRMADO | `backend/api.py:1 sha256:ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` | \| 1 FUNC = 1 FICHERO \| Sin monolitos. `api.py` solo enruta; la lógica va en su módulo. \| |
| CLM-0002 | backend/INFORME.md:157 | PRESERVED | CONFIRMADO | `backend/requirements.txt:1 sha256:f570d2e3d85aac7f37f68e1c95582d555ef8085ab7d51d6bb9349804d06b52e9` | \| G3 \| FastAPI/uvicorn/pydantic/websockets no están en el intérprete del sistema \| `python3 -m uvicorn` → `No module named uvicorn`; instalar está **prohibido** \| ✅ Resuelto con ruta alternativa **sin instalar**: se validó con el intérprete `/workspace/.venv-canvas/bin/python` que ya existía (creado por otro nodo). El entregable declara sus dependencias en `requirements.txt` \| |
| CLM-0003 | backend/README.md:23 | PRESERVED | CONFIRMADO | `backend/api.py:1 sha256:ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` | \| **backend/api.py** \| módulo de entrada: enruta REST, WebSocket, MCP y frontend. No contiene lógica de negocio. \| |
| CLM-0004 | backend/README.md:24 | PRESERVED | CONFIRMADO | `backend/health.py:1 sha256:4d9f10cdd04f9b64f9a95e9a052cdcfdee5228e4537da00cf0eb9763d213b976` | \| **backend/health.py** \| módulo agregador: estado real de los 6 adapters con contadores OK / OMITIDO / ERROR. \| |
| CLM-0005 | backend/README.md:25 | PRESERVED | CONFIRMADO | `backend/canvas_engine.py:1 sha256:8dc1c3dd648ee7310d553064d1a3fa7bdbc3e6eafaf234c396c4414f052cc373` | \| **backend/canvas_engine.py** \| módulo orquestador: carga aislada de adapters, render de diagramas y motions, conversión entre herramientas. \| |
| CLM-0006 | backend/README.md:26 | PRESERVED | CONFIRMADO | `backend/audio_engine.py:1 sha256:c99a889aa081be463093146bece6fc4a14f64e8a52b882241f8768d5940cdf76` | \| **backend/audio_engine.py** \| módulo de voz: resumen de ≤150 palabras, traducción opcional, TTS con edge‑tts y respaldo en pyttsx3, caché por hash. \| |
| CLM-0007 | backend/README.md:27 | PRESERVED | CONFIRMADO | `backend/mcp_router.py:1 sha256:8acf93638d20f532825dc31986e06bfc81a973b9a9cbddd97efbf727511d4052` | \| **backend/mcp_router.py** \| módulo MCP: protocolo JSON‑RPC sobre FastAPI, allowlist por ventana, rechazo de credenciales, límite de payload. Sustituye al servidor http.server retirado. \| |
| CLM-0008 | backend/README.md:49 | PRESERVED | CONFIRMADO | `backend/adapters/excalidraw.py:1 sha256:83b755c16dac84601af573b645d280818527f69620fd703c39ef1f8d28583d0f` | \| **backend/adapters/excalidraw.py** \| módulo adaptador: convierte elementos Excalidraw en un diagrama contra la API de Excalidraw. \| |
| CLM-0009 | backend/README.md:50 | PRESERVED | CONFIRMADO | `backend/adapters/mermaid.py:1 sha256:629fd60c196cf4db078095d4bf9666eab199227a6aa758c51cb209bb55812b75` | \| **backend/adapters/mermaid.py** \| módulo adaptador: renderiza código Mermaid a SVG con el comando mmdc. \| |
| CLM-0010 | backend/README.md:51 | PRESERVED | CONFIRMADO | `backend/adapters/d2.py:1 sha256:bc49d9ad986d8d6bde979db5cb7b06dc62e3bb45a99aae6927fd3c2f24a3227e` | \| **backend/adapters/d2.py** \| módulo adaptador: renderiza código D2 a SVG con el comando d2. \| |
| CLM-0011 | backend/README.md:52 | PRESERVED | CONFIRMADO | `backend/adapters/hyperframes.py:1 sha256:1a9e1a41869cf707b0bcfc5ced316ce8bc29d8ef6e2226b063532193e2acec8b` | \| **backend/adapters/hyperframes.py** \| módulo adaptador: genera motion HTML a partir de una especificación. \| |
| CLM-0012 | backend/README.md:53 | PRESERVED | CONFIRMADO | `backend/adapters/remotion.py:1 sha256:62f1870324e07cd35061692317b3efa73ee50d7b69b6464b78a3f928e1aa3ba1` | \| **backend/adapters/remotion.py** \| módulo adaptador: genera una composición Remotion desde props. \| |
| CLM-0013 | backend/README.md:54 | PRESERVED | CONFIRMADO | `backend/adapters/rive.py:1 sha256:6a1e9f392cb3ce8a3270cff92371be456dbae03a15edc952a351cc9fe539cdc0` | \| **backend/adapters/rive.py** \| módulo adaptador: genera una animación Rive desde un fichero y una máquina de estados. \| |
| CLM-0014 | backend/README.md:62 | PRESERVED | CONFIRMADO | `backend/deploy/deploy_engine.py:1 sha256:bb739bee729f4ce0f1b4ded0df7d8faf768667d84b22ee4deb784f5fd283f501` | \| **backend/deploy/deploy_engine.py** \| módulo motor de deploy: 10 checks fail‑closed, dry‑run por defecto, expected HEAD, push transaccional de un solo commit, read‑back y manifiesto. \| |
| CLM-0015 | backend/README.md:63 | PRESERVED | CONFIRMADO | `backend/deploy/mcp_server.py:1 sha256:5bda096cc8ca90dfa7ff613dc3ef45c3e266558234fff04376320de33106b3b3` | \| **backend/deploy/mcp_server.py** \| módulo shim: reexporta la API del router MCP y avisa si alguien intenta arrancarlo como servidor standalone ya retirado. \| |
| CLM-0016 | backend/README.md:114 | PRESERVED | CONFIRMADO | `backend/guide/grammar.py:1 sha256:e67c187845e9fb21f402b26e1e84dcbdb37c8a5af6892bc3efbf5a125e0c52cb` | \| **backend/guide/grammar.py** \| módulo gramatical: descompone una frase de acción en verbo, sujeto, adjetivo y estado. \| |
| CLM-0017 | backend/README.md:115 | PRESERVED | CONFIRMADO | `backend/guide/match.py:1 sha256:f11620fb43a928c71a54f7b918cc4b1ce5f2016cc1f13a854773e5525144723d` | \| **backend/guide/match.py** \| módulo de emparejamiento: cruza la acción con el catálogo, devuelve veredicto y parche quirúrgico por líneas. \| |
| CLM-0018 | backend/README.md:116 | PRESERVED | CONFIRMADO | `backend/guide/trigger.py:1 sha256:15feb60b94b4b0e1619d4923eac6ec0774d48f9f3a04b4b0aa9ca2860327b7f3` | \| **backend/guide/trigger.py** \| módulo disparador: construye y valida el contrato de ejecución por pasos. \| |
| CLM-0019 | backend/README.md:117 | PRESERVED | CONFIRMADO | `backend/guide/discovery.py:1 sha256:143e94a8993c8b13295f999b4789da0631d737e9fec2c3d25ee7b8ab97d603d4` | \| **backend/guide/discovery.py** \| módulo de descubrimiento: busca candidatos en las fuentes configuradas con caché y presupuesto. \| |
| CLM-0020 | backend/README.md:127 | PRESERVED | CONFIRMADO | `frontend/shared/api.js:1 sha256:ba45c7b5f24cb647fac24db69861f14223554ebc6c2003c225debcef68767de2` | \| **frontend/shared/api.js** \| módulo de cliente: base de API same‑origin, fetch real, tema de 7 apariencias, utilidades de estado. \| |
| CLM-0021 | backend/README.md:128 | PRESERVED | CONFIRMADO | `frontend/shared/ws.js:1 sha256:2594083ce695130cf01ec0776def6209ad869c904d48a5be124da7d4370823d7` | \| **frontend/shared/ws.js** \| módulo de WebSocket: suscripción al progreso con reconexión y origen validado. \| |
| CLM-0022 | backend/README.md:129 | PRESERVED | CONFIRMADO | `frontend/shared/theme.css:1 sha256:dcd4b1ebaa68333082e7b6069c584a8a5087d22edcc598dc8162b34f718f628f` | \| **frontend/shared/theme.css** \| módulo de estilos: los 7 temas de la ley de diseño. \| |
| CLM-0023 | backend/README.md:130 | PRESERVED | CONFIRMADO | `frontend/shared/app.css:1 sha256:daa8c5e3e944cd48910632750caf57ba1649457c7129f25bb697f55912bd222a` | \| **frontend/shared/app.css** \| módulo de estilos: geometría, tarjetas y estados demostrables. \| |
| CLM-0024 | backend/README.md:131 | PRESERVED | CONFIRMADO | `frontend/w_mcp.js:1 sha256:73313a547445eb1393b89ae033d60792e78456b8b59471e967224c36fd2de041` | \| **frontend/w_mcp.js** \| módulo cliente MCP del navegador: initialize, listado de herramientas y llamada, con allowlist por ventana. \| |
| CLM-0025 | backend/guide/README.md:144 | PRESERVED | CONFIRMADO | `backend/guide/discovery.py:1 sha256:143e94a8993c8b13295f999b4789da0631d737e9fec2c3d25ee7b8ab97d603d4` | \| variable GUIDE_REPO_ROOT \| auto (ancestros del módulo) \| Raíz del repo; el motor de búsqueda y su catálogo de fuentes se resuelven desde backend/guide/discovery.py \| |

## GAPS

| id | tipo | sev | estado | veredicto | componente | evidencia | notas |
|---|---|---|---|---|---|---|---|
| — | — | — | — | SIN_EVIDENCIA | — | SIN_EVIDENCIA | sin gaps detectados |

## FIJAR (fixes) por estado

| id | estado | componente |
|---|---|---|

# CONTRACTS — endpoints y variables de entorno

- commit: `bb3559e66f9ca160031b9da3c5b65aecb807fa45`
- branch: `master`
- generado: 2026-11-16T08:00:06Z
- evidencia: cada fila apunta a `ruta:línea` + `sha256` del fichero.

## ENDPOINTS (17)

| método | ruta | evidencia | sha256 |
|---|---|---|---|
| GET | `/health` | backend/api.py:162 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| POST | `/render/diagram` | backend/api.py:171 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| POST | `/render/motion` | backend/api.py:180 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| POST | `/convert` | backend/api.py:189 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| POST | `/audio/explain` | backend/api.py:198 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| GET | `/audio/{audio_id}` | backend/api.py:211 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| POST | `/gaps` | backend/api.py:241 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| GET | `/gaps` | backend/api.py:260 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| GET | `/xray/{artifact}` | backend/api.py:273 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| POST | `/xray/audit` | backend/api.py:299 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| GET | `/` | backend/api.py:340 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| GET | `/ui` | backend/api.py:384 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| POST | `/mcp` | backend/mcp_router.py:543 | `8acf93638d20f532825dc31986e06bfc81a973b9a9cbddd97efbf727511d4052` |
| DELETE | `/mcp` | backend/mcp_router.py:583 | `8acf93638d20f532825dc31986e06bfc81a973b9a9cbddd97efbf727511d4052` |
| GET | `/mcp/health` | backend/mcp_router.py:593 | `8acf93638d20f532825dc31986e06bfc81a973b9a9cbddd97efbf727511d4052` |
| GET | `/guide/status` | backend/mcp_router.py:621 | `8acf93638d20f532825dc31986e06bfc81a973b9a9cbddd97efbf727511d4052` |
| POST | `/guide/match` | backend/mcp_router.py:632 | `8acf93638d20f532825dc31986e06bfc81a973b9a9cbddd97efbf727511d4052` |

## ENV VARS (20)

| variable | evidencia | sha256 |
|---|---|---|
| `EXCALIDRAW_URL` | backend/adapters/excalidraw.py:30 | `83b755c16dac84601af573b645d280818527f69620fd703c39ef1f8d28583d0f` |
| `HYPERFRAMES_URL` | backend/adapters/hyperframes.py:34 | `1a9e1a41869cf707b0bcfc5ced316ce8bc29d8ef6e2226b063532193e2acec8b` |
| `XRAY_OUT_DIR` | backend/api.py:72 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| `CANVAS_ALLOWED_ORIGINS` | backend/api.py:97 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| `XRAY_STORE` | backend/api.py:234 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| `XRAY_INVENTORY` | backend/api.py:238 | `ed45a581a500ec854fc6956a629f78cc7e8822fd57c1920631ebd9b88f3a74a8` |
| `CANVAS_AUDIO_DIR` | backend/audio_engine.py:35 | `c99a889aa081be463093146bece6fc4a14f64e8a52b882241f8768d5940cdf76` |
| `DEPLOY_MAX_FILE_BYTES` | backend/deploy/deploy_engine.py:50 | `bb739bee729f4ce0f1b4ded0df7d8faf768667d84b22ee4deb784f5fd283f501` |
| `DEPLOY_MAX_TOTAL_BYTES` | backend/deploy/deploy_engine.py:51 | `bb739bee729f4ce0f1b4ded0df7d8faf768667d84b22ee4deb784f5fd283f501` |
| `GUIDE_SEARCH_PROVIDERS` | backend/guide/discovery.py:42 | `143e94a8993c8b13295f999b4789da0631d737e9fec2c3d25ee7b8ab97d603d4` |
| `GUIDE_SEARCH_TIMEOUT_SECONDS` | backend/guide/discovery.py:43 | `143e94a8993c8b13295f999b4789da0631d737e9fec2c3d25ee7b8ab97d603d4` |
| `GUIDE_DISCOVERY_BUDGET_TOKENS` | backend/guide/discovery.py:44 | `143e94a8993c8b13295f999b4789da0631d737e9fec2c3d25ee7b8ab97d603d4` |
| `GUIDE_DISCOVERY_CACHE_TTL_SECONDS` | backend/guide/discovery.py:45 | `143e94a8993c8b13295f999b4789da0631d737e9fec2c3d25ee7b8ab97d603d4` |
| `GUIDE_REPO_ROOT` | backend/guide/discovery.py:125 | `143e94a8993c8b13295f999b4789da0631d737e9fec2c3d25ee7b8ab97d603d4` |
| `GUIDE_DISCOVERY_CACHE_DIR` | backend/guide/discovery.py:400 | `143e94a8993c8b13295f999b4789da0631d737e9fec2c3d25ee7b8ab97d603d4` |
| `GUIDE_ACTIONS_CATALOG` | backend/guide/match.py:60 | `f11620fb43a928c71a54f7b918cc4b1ce5f2016cc1f13a854773e5525144723d` |
| `MCP_MAX_PAYLOAD_BYTES` | backend/mcp_router.py:76 | `8acf93638d20f532825dc31986e06bfc81a973b9a9cbddd97efbf727511d4052` |
| `MCP_MAX_SESSIONS` | backend/mcp_router.py:77 | `8acf93638d20f532825dc31986e06bfc81a973b9a9cbddd97efbf727511d4052` |
| `MCP_ALLOWED_ORIGINS` | backend/mcp_router.py:208 | `8acf93638d20f532825dc31986e06bfc81a973b9a9cbddd97efbf727511d4052` |
| `DEPLOY_WORKDIR` | backend/mcp_router.py:418 | `8acf93638d20f532825dc31986e06bfc81a973b9a9cbddd97efbf727511d4052` |

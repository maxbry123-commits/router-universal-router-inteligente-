# Raíz BACKEND del chat — índice de archivos

Carpeta real: `mvp/` (Router FastAPI) + `plugins/deepseek_harness/server.py` (Harness) + `plugins/router_api_cliente.py`. No se movió: el Space y el autopull arrancan `mvp.run`.
Generado por `chat/e2e/indice.py`. Base: `1b916a587c`.

## Archivos

### Servidor y rutas (6)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `mvp/app.py` | 478 | `8ffec72cd7` | Claude | 35 | 22 |
| `mvp/config.json` | 26 | `9825c3402a` | Maxbry | 1 | 0 |
| `mvp/escalado.py` | 101 | `63c588b3cf` | Claude | 1 | 1 |
| `mvp/prompt.py` | 28 | `748db5a6e5` | Claude | 1 | 1 |
| `mvp/run.py` | 90 | `e960e04110` | Claude | 5 | 4 |
| `mvp/trabajos.py` | 29 | `63c588b3cf` | Claude | 1 | 1 |

### Permisos y seguridad (2)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `mvp/bank.py` | 95 | `7b2430c8e8` | Claude | 6 | 2 |
| `mvp/control.py` | 453 | `cbd1647056` | Claude | 7 | 6 |

### Modelos y proveedores (6)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `mvp/compute.py` | 70 | `6b48272e65` | Claude | 9 | 4 |
| `mvp/externos.py` | 77 | `7b2430c8e8` | Claude | 2 | 2 |
| `mvp/modelos.json` | 226 | `17f382f6a9` | Claude | 5 | 4 |
| `mvp/modelos.py` | 108 | `6d79e78b25` | Claude | 8 | 7 |
| `mvp/multimedia.py` | 110 | `17f382f6a9` | Claude | 3 | 3 |
| `mvp/sdk_qwen.py` | 90 | `17f382f6a9` | Claude | 1 | 1 |

### MCP y herramientas (4)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `mvp/harness_client.py` | 64 | `e0cc451b2b` | Claude | 4 | 1 |
| `mvp/mcp_cliente.py` | 58 | `1b916a587c` | Claude | 1 | 0 |
| `mvp/mcp_route.py` | 235 | `7b2430c8e8` | Claude | 15 | 9 |
| `mvp/sala_turno.py` | 40 | `5be2929688` | Claude | 1 | 1 |

### Persistencia y memoria (2)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `mvp/hf_store.py` | 58 | `b91fe2b572` | Claude | 3 | 1 |
| `mvp/memoria.py` | 64 | `b91fe2b572` | Claude | 2 | 2 |

### Harness y cliente (2)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `plugins/deepseek_harness/server.py` | 160 | `893b45736c` | Claude | 12 | 5 |
| `plugins/router_api_cliente.py` | 117 | `893b45736c` | Claude | 10 | 1 |

## Pruebas del backend

| Archivo | Líneas | Último commit | Autor |
|---|--:|---|---|
| `mvp/test_alias.py` | 25 | `b91fe2b572` | Claude |
| `mvp/test_app.py` | 149 | `8d485acab8` | Claude |
| `mvp/test_bank.py` | 60 | `8d485acab8` | Claude |
| `mvp/test_compute.py` | 125 | `dd833d5160` | Claude |
| `mvp/test_control.py` | 605 | `8ffec72cd7` | Claude |
| `mvp/test_escalado.py` | 109 | `63c588b3cf` | Claude |
| `mvp/test_externos.py` | 63 | `7b2430c8e8` | Claude |
| `mvp/test_harness.py` | 189 | `6d79e78b25` | Claude |
| `mvp/test_hf.py` | 112 | `b91fe2b572` | Claude |
| `mvp/test_hf_store.py` | 39 | `b91fe2b572` | Claude |
| `mvp/test_mcp.py` | 148 | `b91fe2b572` | Claude |
| `mvp/test_mcp_sesion.py` | 80 | `893b45736c` | Claude |
| `mvp/test_memoria.py` | 53 | `b91fe2b572` | Claude |
| `mvp/test_modelos.py` | 32 | `0963d2622c` | Claude |
| `mvp/test_multimedia.py` | 82 | `dd833d5160` | Claude |
| `mvp/test_pruebas_vivo.py` | 115 | `893b45736c` | Claude |
| `mvp/test_run.py` | 119 | `8d485acab8` | Claude |
| `mvp/test_sdk_qwen.py` | 87 | `6b48272e65` | Claude |
| `mvp/test_tools_chat.py` | 62 | `893b45736c` | Claude |

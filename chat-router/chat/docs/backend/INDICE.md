# Raíz BACKEND del chat — índice de archivos

Carpeta real: `mvp/` (Router FastAPI) + `plugins/deepseek_harness/server.py` (Harness) + `plugins/router_api_cliente.py`. No se movió: el Space y el autopull arrancan `mvp.run`.
Generado por `chat/e2e/indice.py`. Base: `1b916a587c`.

## Archivos

### Servidor y rutas (6)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `chat/backend/mvp/app.py` | 478 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/config.json` | 26 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/escalado.py` | 101 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/prompt.py` | 28 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/run.py` | 102 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/trabajos.py` | 29 | `9c4e58e1a3` | Claude | 1 | 1 |

### Permisos y seguridad (2)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `chat/backend/mvp/bank.py` | 95 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/control.py` | 453 | `9c4e58e1a3` | Claude | 1 | 1 |

### Modelos y proveedores (6)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `chat/backend/mvp/compute.py` | 70 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/externos.py` | 77 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/modelos.json` | 226 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/modelos.py` | 108 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/multimedia.py` | 110 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/sdk_qwen.py` | 90 | `9c4e58e1a3` | Claude | 1 | 1 |

### MCP y herramientas (4)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `chat/backend/mvp/harness_client.py` | 64 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/mcp_cliente.py` | 58 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/mcp_route.py` | 235 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/sala_turno.py` | 40 | `9c4e58e1a3` | Claude | 1 | 1 |

### Persistencia y memoria (2)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `chat/backend/mvp/hf_store.py` | 58 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/mvp/memoria.py` | 64 | `9c4e58e1a3` | Claude | 1 | 1 |

### Harness y cliente (2)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `chat/backend/deepseek_harness/server.py` | 160 | `9c4e58e1a3` | Claude | 1 | 1 |
| `chat/backend/router_api_cliente.py` | 117 | `9c4e58e1a3` | Claude | 1 | 1 |

## Pruebas del backend

| Archivo | Líneas | Último commit | Autor |
|---|--:|---|---|
| `mvp/test_alias.py` | 25 | `9c4e58e1a3` | Claude |
| `mvp/test_app.py` | 149 | `9c4e58e1a3` | Claude |
| `mvp/test_bank.py` | 60 | `9c4e58e1a3` | Claude |
| `mvp/test_compute.py` | 125 | `9c4e58e1a3` | Claude |
| `mvp/test_control.py` | 605 | `9c4e58e1a3` | Claude |
| `mvp/test_escalado.py` | 109 | `9c4e58e1a3` | Claude |
| `mvp/test_externos.py` | 63 | `9c4e58e1a3` | Claude |
| `mvp/test_harness.py` | 189 | `9c4e58e1a3` | Claude |
| `mvp/test_hf.py` | 112 | `9c4e58e1a3` | Claude |
| `mvp/test_hf_store.py` | 39 | `9c4e58e1a3` | Claude |
| `mvp/test_mcp.py` | 148 | `9c4e58e1a3` | Claude |
| `mvp/test_mcp_sesion.py` | 80 | `9c4e58e1a3` | Claude |
| `mvp/test_memoria.py` | 53 | `9c4e58e1a3` | Claude |
| `mvp/test_modelos.py` | 32 | `9c4e58e1a3` | Claude |
| `mvp/test_multimedia.py` | 82 | `9c4e58e1a3` | Claude |
| `mvp/test_pruebas_vivo.py` | 115 | `9c4e58e1a3` | Claude |
| `mvp/test_run.py` | 119 | `9c4e58e1a3` | Claude |
| `mvp/test_sdk_qwen.py` | 87 | `9c4e58e1a3` | Claude |
| `mvp/test_tools_chat.py` | 62 | `9c4e58e1a3` | Claude |

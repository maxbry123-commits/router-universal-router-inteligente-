# Raíz BACKEND del chat — índice de archivos

Carpeta real: `chat-router/chat/backend/mvp/` (Router FastAPI; enlace `router-mvp/mvp`) + `chat-router/chat/backend/deepseek_harness/server.py` (Harness) + `chat-router/chat/backend/router_api_cliente.py`. El Space y el autopull arrancan `mvp.run`.
Generado por `chat-router/chat/auditoria/indice.py`. Base: `1b916a587c`.

## Archivos

### Servidor y rutas (6)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `chat-router/chat/backend/mvp/app.py` | 611 | `e2a20fcc96` | Claude | 2 | 2 |
| `chat-router/chat/backend/mvp/config.json` | 26 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/escalado.py` | 101 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/prompt.py` | 29 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/run.py` | 133 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/trabajos.py` | 29 | `ebb21c88cd` | Claude | 1 | 1 |

### Permisos y seguridad (2)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `chat-router/chat/backend/mvp/bank.py` | 95 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/control.py` | 484 | `ebb21c88cd` | Claude | 1 | 1 |

### Modelos y proveedores (6)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `chat-router/chat/backend/mvp/compute.py` | 75 | `e2a20fcc96` | Claude | 2 | 2 |
| `chat-router/chat/backend/mvp/externos.py` | 77 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/modelos.json` | 226 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/modelos.py` | 108 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/multimedia.py` | 116 | `e2a20fcc96` | Claude | 2 | 2 |
| `chat-router/chat/backend/mvp/sdk_qwen.py` | 90 | `ebb21c88cd` | Claude | 1 | 1 |

### MCP y herramientas (4)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `chat-router/chat/backend/mvp/harness_client.py` | 64 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/mcp_cliente.py` | 58 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/mcp_route.py` | 252 | `e2a20fcc96` | Claude | 2 | 2 |
| `chat-router/chat/backend/mvp/sala_turno.py` | 40 | `ebb21c88cd` | Claude | 1 | 1 |

### Persistencia y memoria (2)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `chat-router/chat/backend/mvp/hf_store.py` | 58 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/memoria.py` | 80 | `ebb21c88cd` | Claude | 1 | 1 |

### Harness y cliente (2)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `chat-router/chat/backend/deepseek_harness/server.py` | 230 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/router_api_cliente.py` | 120 | `ebb21c88cd` | Claude | 1 | 1 |

### Otros (5)

| Archivo | Líneas | Último commit | Autor | Commits totales | Desde la base |
|---|--:|---|---|--:|--:|
| `chat-router/chat/backend/mvp/estado_tarea.py` | 64 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/frontend_estatico.py` | 23 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/loop_puente.py` | 36 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/loop_reanudar.py` | 66 | `ebb21c88cd` | Claude | 1 | 1 |
| `chat-router/chat/backend/mvp/mantener_vivo.py` | 79 | `ebb21c88cd` | Claude | 1 | 1 |

## Pruebas del backend

| Archivo | Líneas | Último commit | Autor |
|---|--:|---|---|
| `chat-router/chat/backend/mvp/test_alias.py` | 25 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_app.py` | 149 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_asr.py` | 32 | `e2a20fcc96` | Claude |
| `chat-router/chat/backend/mvp/test_bank.py` | 60 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_compute.py` | 125 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_control.py` | 605 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_escalado.py` | 111 | `e2a20fcc96` | Claude |
| `chat-router/chat/backend/mvp/test_externos.py` | 63 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_harness.py` | 230 | `e2a20fcc96` | Claude |
| `chat-router/chat/backend/mvp/test_hf.py` | 112 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_hf_store.py` | 39 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_loop_puente.py` | 70 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_loop_reanudar.py` | 73 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_mantener_vivo.py` | 161 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_mcp.py` | 148 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_mcp_sesion.py` | 95 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_memoria.py` | 53 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_modelos.py` | 32 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_multimedia.py` | 82 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_no_se_corta.py` | 100 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_prompt_ficha.py` | 22 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_pruebas_vivo.py` | 115 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_reanudar.py` | 144 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_run.py` | 145 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_sdk_qwen.py` | 87 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_tools_chat.py` | 62 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_trabajo_largo.py` | 175 | `ebb21c88cd` | Claude |
| `chat-router/chat/backend/mvp/test_trabajo_sin_vence.py` | 23 | `e2a20fcc96` | Claude |

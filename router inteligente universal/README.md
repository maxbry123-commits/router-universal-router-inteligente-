# Router Inteligente Universal - README (arquitectura simple + mapa)

Actualizado 2026-09-30 (agente organizador). Marcas: [HECHO] codigo en main; [SIN PROBAR] no probado en vivo; [PENDIENTE] no existe o no esta cableado; [BLOQUEADO] espera al Director. Nada aqui lleva claves.
Para el indice completo de documentos y el orden de lectura: [HANDOFF-CABLEADO.md](HANDOFF-CABLEADO.md).

**REGLA: usar primero el plugin harness DeepSeek (plugins/deepseek_harness) para todo. El enchufe de Fables (plugins/fables_enchufe, carpeta enchufe/) solo si es necesario, porque NO cumple la funcion del harness: lo unico cableado de Fables es el validador de fichas (validator_v2.py); el resto del bus (universal_plugin_bus_v2, ficha_contract_v2) no esta cableado ni hace de harness.**

## La arquitectura en palabras simples
1. El Router es solo la conexion viva: recibe pedidos (chat, agentes), elige un modelo segun una cadena (policies.json), toma la clave del banco secreto y devuelve la respuesta. Nada mas vive dentro.
2. Todo lo demas es plugin: una carpeta plugins/<id>/ con ficha.json (la tarjeta) y plugin.py (funcion handle(action, payload)). El Plugin Host las lee, las valida y las llama con una envoltura (call) con limite de tiempo; si un plugin falla, solo ese queda marcado y el Router sigue.
3. Computo: el Router corre como Job de Hugging Face; el plugin hf_compute escribe la politica de encender otro HF cuando el actual llega al 80% (12 GB -> 16 GB -> 32 GB). Meta del Director: Job 24/7 de 16 GB de pago, sin vencimiento.
4. Almacenamiento: un puente (plugin hf_storage) al dataset privado de HF; datasets y biblioteca de skills de HF se consultan por llamada (plugins hf_datasets, hf_skills), no viven en el Router.
5. Cada SDK/API nuevo = una carpeta nueva que se conecta al ultimo plugin, sin tocar el codigo del Router (regla por escribir, ver HANDOFF-CABLEADO.md). Como entra una clave nueva: [CONECTAR-SDK-NUEVO.md](CONECTAR-SDK-NUEVO.md).

## MAPA: que hay y donde esta
| Pieza | Donde | Estado real |
|---|---|---|
| Router (app FastAPI del chat) | integration/chat_mvp/app.py, gateway/fastapi_app.py, engine/resilience.py | [HECHO] en main. No se audito si ya es "minimo": hoy monta chat MVP, banco y Plugin Host |
| Plugin Host | integration/plugin_host/host.py y api.py. Rutas: GET /plugins, POST /plugins/{id}/enable, /disable, /call/{action} | [HECHO] probado en maquina temporal (97 pasados, 13 omitidos, 0 fallados segun Claude notas/agentes/union.md), sin CI. [PENDIENTE] failover declarativo, presupuesto por nivel, evidencia L1-L4, hot-swap, sandbox, firma (ver plugins/README-ROJO.md) |
| Plugin chat | plugins/chat | [HECHO] encendido por defecto, estado testing |
| Plugin deepseek_harness | plugins/deepseek_harness | [HECHO] apagado; acciones status/invoke; sin la variable RIU_DEEPSEEK_HARNESS_URL responde degraded. [SIN PROBAR] si la URL esta puesta no lo verifique |
| Plugin fables_enchufe | plugins/fables_enchufe + enchufe/ | [HECHO] solo envuelve validator_v2.py. [PENDIENTE] bus completo de Fables sin cablear |
| Plugin parallel | plugins/parallel | [HECHO] apagado; hasta 8 llamadas en paralelo via host.call. [SIN PROBAR] en vivo |
| Plugin connectivity | plugins/connectivity | [HECHO] reporta ok/degraded/off de transportes (FastAPI, HTTP saliente, MCP segun su ficha). SSH: [PENDIENTE] no existe |
| Plugin remote_router | plugins/remote_router | [HECHO] puente HTTP/FastAPI al Router remoto; requiere la URL por entorno. [SIN PROBAR] |
| Plugin hf_compute | plugins/hf_compute (envuelve integration/hf_worker_*) | [HECHO] politica de computo escalonado. [SIN PROBAR] en vivo |
| Plugin hf_storage | plugins/hf_storage | [HECHO] status/list/read/write/backup_sqlite sobre el dataset COMAND-CENTER-1/yaiwes-hf-memoria. [PENDIENTE] Storage Bucket real; enlace del chat de Manus (T-08) |
| Plugins hf_datasets, hf_skills | plugins/hf_datasets, plugins/hf_skills | [HECHO] por llamada, solo lectura. [SIN PROBAR] |
| Plugin thinking-modes | plugins/thinking-modes | [PENDIENTE] placeholder (draft) |
| Cadena de modelos | integration/chat_mvp/policies.json (grupos default, code, minor, g2, assistants); si falta o es invalido, cae a CODE_POLICY en resilience.py | [HECHO]. default: nvidia kimi-k3 -> nvidia glm-5.3 -> hf DeepSeek-V4-Flash (se salta en pico DeepSeek) -> groq qwen3.8-27b -> ... (ver el archivo). Campo "sdk" esta esperando la lista del Director |
| Banco de claves | Banco de claves/secret_bank/vault.py (SQLite + AES-256-GCM, clave por scrypt, nunca guardada); integration/chat_mvp/vault_bridge.py, vault_api.py, vault_hook.py | [HECHO] implementado (ADENDA-RIU-0110). [SIN PROBAR] en vivo por mi. Se abre en memoria con contrasena maestra y se cierra solo (TTL 1 h por defecto) |
| Autoescalado / Job | integration/hf_*.py y /control/hf/* (GPT); workflow riu-router-job-central.yml (Actions, PROHIBIDO por el Director) | Hoy: Job cpu-basic con timeout 48 h y cron de relanzado (Claude notas/agentes/secretos.md). [PENDIENTE] Job 24/7 16 GB sin vencimiento y salvavidas |
| Harness DeepSeek (fuente) | deepseek-harness-router/ | [HECHO] carpeta de codigo; ver regla en negrita |
| Crazy Wall | ../Estado y handoff global/CRAZY_WALL.json | [HECHO] mapa de nodos y enlaces |
| Bitacora | ../Estado y handoff global/BITACORA.jsonl | [HECHO] una linea por evento |
| Estado JSON | ../Estado y handoff global/ESTADO.json | [HECHO] estado por checkpoint |
| Handoffs | HANDOFF-PROVISIONAL-ROUTER.md, CONECTAR-ROUTER.md, ../Estado y handoff global/HANDOFF.md | [HECHO] ver indice en HANDOFF-CABLEADO.md |

## Limite de esta version del README
Se escribio leyendo el codigo del Plugin Host, los plugins, el banco de claves y los handoffs/estado; los documentos largos (ARQUITECTURA-ROUTER-FICHAS-FABLES, ARQUITECTURA-ROUTER-Y-CONEXIONES, ADENDAS, INPUT-BLOCKs, los 3 archivos Python de enchufe/) se enlazan pero NO se releyeron completos. Quien retome debe leerlos antes de decidir sobre Fables.

# HANDOFF CABLEADO - indice de todo, orden de lectura y pendientes reales

> **2026-10-03 (Opus) — LEER PRIMERO:** Router 24/7 en HF Job 16 GB detras de la puerta fija `https://comand-center-1-claude-github-mcp-backup.hf.space` (micro-kernel renueva 20 min antes), Harness DeepSeek por el Router, banco auto-abierto, laboratorio, fichas vivas, MCP `/mcp/`, puente HF y mini router L4/T4. Guia completa: [ADENDA-RIU-0111](../Readme%20arquitectura%20router%20inteligente%20universal/ADENDA-RIU-0111-ROUTER-24-7-HARNESS-BANCO-LAB-FICHAS-MCP.md). Para conectar algo NO hace falta tocar el Router.

Actualizado 2026-09-30 (agente organizador). Resumen y mapa: [README.md](README.md). Como entran SDK y claves nuevas: [CONECTAR-SDK-NUEVO.md](CONECTAR-SDK-NUEVO.md). Marcas: [HECHO] [SIN PROBAR] [PENDIENTE] [BLOQUEADO]. Sin claves en este archivo.

## Orden de lectura para una IA nueva (Fables u Opus)
1. [README.md](README.md) (mapa) y este archivo.
2. [HANDOFF global](../Estado%20y%20handoff%20global/HANDOFF.md): manda el checkpoint mas reciente si se contradicen.
3. [ESTADO.json](../Estado%20y%20handoff%20global/ESTADO.json), [CRAZY_WALL.json](../Estado%20y%20handoff%20global/CRAZY_WALL.json), [BITACORA.jsonl](../Estado%20y%20handoff%20global/BITACORA.jsonl).
4. [HANDOFF-PROVISIONAL-ROUTER.md](HANDOFF-PROVISIONAL-ROUTER.md) y [CONECTAR-ROUTER.md](CONECTAR-ROUTER.md).
5. [plugins/README-ROJO.md](plugins/README-ROJO.md): lo que NO esta cableado del Plugin Host.
6. Arquitectura: [ARQUITECTURA-ROUTER-Y-CONEXIONES.md](../Readme%20arquitectura%20router%20inteligente%20universal/ARQUITECTURA-ROUTER-Y-CONEXIONES.md) y [ARQUITECTURA-ROUTER-FICHAS-FABLES.md](../Readme%20arquitectura%20router%20inteligente%20universal/ARQUITECTURA-ROUTER-FICHAS-FABLES.md).
7. Ordenes textuales del Director: INPUT-BLOCKs (abajo) y [Notas del Director](../Documentos%20del%20proyecto/Notas%20del%20Director%20%28verbatim%29/).
8. Notas de agentes (abajo). 9. Fables ([enchufe/](enchufe/)) solo si es necesario (ver regla).

**REGLA: harness DeepSeek primero (plugins/deepseek_harness); Fables solo si es necesario, porque su enchufe no cumple la funcion del harness y solo su validador esta cableado.**

## Indice cableado
- Estado: [HANDOFF.md](../Estado%20y%20handoff%20global/HANDOFF.md), [ESTADO.json](../Estado%20y%20handoff%20global/ESTADO.json), [CRAZY_WALL.json](../Estado%20y%20handoff%20global/CRAZY_WALL.json), [BITACORA.jsonl](../Estado%20y%20handoff%20global/BITACORA.jsonl); tareas: [T-02](../Estado%20y%20handoff%20global/tareas/T-02-reorganizar-repo-en-raices.md), [T-04](../Estado%20y%20handoff%20global/tareas/T-04-equipo-4-objetivos-al-router.md), [T-05](../Estado%20y%20handoff%20global/tareas/T-05-veinte-sitios-de-investigacion.md), [T-06](../Estado%20y%20handoff%20global/tareas/T-06-cadena-rowboat-a-4-meta.md), [T-07](../Estado%20y%20handoff%20global/tareas/T-07-skills-a-esquema-sheriff.md), [T-08](../Estado%20y%20handoff%20global/tareas/T-08-memoria-manus-y-puente-hf.md), [T-09](../Estado%20y%20handoff%20global/tareas/T-09-vercel-deploy-final.md).
- Checkpoints: [2026-09-29 11:00](../Claude%20notas/CHECKPOINT-2026-09-29-1100-router-chat-plugins.md), [2026-09-30 01:00](../Claude%20notas/CHECKPOINT-2026-09-30-0100-auditoria-12h-y-3-objetivos.md). Otros handoffs: [GPT control plane HF](../Claude%20notas/HANDOFF-GPT-HF-CONTROL-PLANE-2026-09-30.md), [parche recuperacion](../Claude%20notas/HANDOFF-PARCHE-RECUPERACION-2026-09-21.md), [nota ordenes del Router](../Claude%20notas/NOTA-2026-09-29-ordenes-del-Router.md).
- Agentes: [cadena](../Claude%20notas/agentes/cadena.md), [plugins](../Claude%20notas/agentes/plugins.md), [puentes](../Claude%20notas/agentes/puentes.md), [secretos](../Claude%20notas/agentes/secretos.md), [union](../Claude%20notas/agentes/union.md), [reglas bloque 3](../Claude%20notas/agentes/REGLAS-BLOQUE3-2026-09-30.md), [reglas y contexto](../Claude%20notas/agentes/REGLAS-Y-CONTEXTO-AGENTES.md).
- Arquitectura y ADENDAS: [README de arquitectura](../Readme%20arquitectura%20router%20inteligente%20universal/README.md), [ADENDA 0107](../Readme%20arquitectura%20router%20inteligente%20universal/ADENDA-RIU-0107-INPUT-BLOCK-05-chat-storage-grupos.md), [0108](../Readme%20arquitectura%20router%20inteligente%20universal/ADENDA-RIU-0108-CHAT-MVP-SECRET-BANK-STORAGE.md), [0109](../Readme%20arquitectura%20router%20inteligente%20universal/ADENDA-RIU-0109-HF-JOBS-FALLBACK-y-decisiones.md), [0110](../Readme%20arquitectura%20router%20inteligente%20universal/ADENDA-RIU-0110-secret-bank-implementado.md), [research prepass](../Readme%20arquitectura%20router%20inteligente%20universal/ADENDA-RIU-RESEARCH-PREPASS-NATIVO.md), [CHAT-MVP](../Readme%20arquitectura%20router%20inteligente%20universal/CHAT-MVP.md), [evidencia NVIDIA](../Readme%20arquitectura%20router%20inteligente%20universal/EVIDENCIA-2026-09-29-NVIDIA-Y-COMPONENTES.md), [guia maestra](../Readme%20arquitectura%20router%20inteligente%20universal/GUIA-MAESTRA-EJECUCION-LOOP-SOL-ROUTER-INTELIGENTE-UNIVERSAL.md), [huella digital](../Readme%20arquitectura%20router%20inteligente%20universal/HUELLA-DIGITAL-ROUTER.md).
- INPUT-BLOCKs verbatim: [director](../Readme%20arquitectura%20router%20inteligente%20universal/INPUT-BLOCK-VERBATIM-2026-09-29-director.md), [parte 2](../Readme%20arquitectura%20router%20inteligente%20universal/INPUT-BLOCK-VERBATIM-2026-09-29-director-parte-2.md), [3](../Readme%20arquitectura%20router%20inteligente%20universal/INPUT-BLOCK-VERBATIM-2026-09-29-director-parte-3.md), [4](../Readme%20arquitectura%20router%20inteligente%20universal/INPUT-BLOCK-VERBATIM-2026-09-29-director-parte-4.md), [5](../Readme%20arquitectura%20router%20inteligente%20universal/INPUT-BLOCK-VERBATIM-2026-09-29-director-parte-5.md), [6 (09-30)](../Readme%20arquitectura%20router%20inteligente%20universal/INPUT-BLOCK-VERBATIM-2026-09-30-director-parte-6.md).
- Codigo clave: [plugins/](plugins/), [plugin_host](integration/plugin_host/), [policies.json](integration/chat_mvp/policies.json), [vault_api.py](integration/chat_mvp/vault_api.py), [vault_bridge.py](integration/chat_mvp/vault_bridge.py), [vault_hook.py](integration/chat_mvp/vault_hook.py), [Banco de claves](Banco%20de%20claves/README.md), [enchufe (Fables)](enchufe/), [harness DeepSeek](deepseek-harness-router/).

## Que esta hecho / sin probar / pendiente / bloqueado
- [HECHO] Plugin Host + 11 plugins (chat encendido; el resto apagado), cadena en policies.json, banco de claves implementado, puentes HF (storage, datasets, skills, compute), remote_router, plantilla de SDK nuevo (plugins/_plantilla_sdk, ignorada por el host).
- [SIN PROBAR] todos los plugins apagados en vivo, hf_compute/autoescalado, harness DeepSeek con su URL, cableado del banco con claves reales, recarga de plugins nuevos sin reiniciar. Hay cifras de pruebas sin reconciliar (168/8/0 frente a 153/8/6; ver HANDOFF global).
- [PENDIENTE] ver lista corta abajo.
- [BLOQUEADO] las 15 claves de SDK (las entrega el Director); CI de GitHub Actions (prohibido por el Director).

## Decisiones vigentes del Director
Router minimo = solo conexion viva; todo lo demas plugins (nada monolitico, lego). Job HF 24/7 de 16 GB de pago, sin vencimiento ni caidas; enciende otros HF de 16/32 GB al llegar al 80%; conexion por MCP/HTTP/SSH/token. Datasets y skills de HF: por llamada, no viven en el Router; almacenamiento solo por puente al almacenamiento permanente de HF. Conectados al harness DeepSeek: chat de Vercel, Router, Hermes, OpenClaw, Osquestador. Cadena de IA: Kimi K3, GLM 5, DeepSeek. Auditoria: 3 bucles + 4 pasadas (instrucciones, codigo, archivos/docs, ejecucion); nada es OK sin ellas. Harness DeepSeek para todo; Fables solo si es necesario.

## Prohibiciones
Sin GitHub Actions. Sin Router nuevo: edicion quirurgica del vivo. No lanzar ni cancelar Jobs (lo hace el coordinador). No tocar el Space claude-github-mcp-backup. No ejecutar codigo de terceros. Ninguna clave en archivos del repo. Nada "verde" sin evidencia.

## Pendientes reales (lista corta)
1. Salvavidas / sin vencimiento: NO existe. Hoy el Job (cpu-basic) vence (timeout 48 h) y el relanzado depende de un cron en Actions, que esta prohibido. [PENDIENTE][BLOQUEADO por decision]
2. Reinicio unico para cargar codigo nuevo, o boton de recarga de plugins: decision del Director. [BLOQUEADO]
3. SSH: no existe. [PENDIENTE]
4. Bus completo de Fables (universal_plugin_bus_v2, ficha_contract_v2) sin cablear; hoy solo validator_v2. [PENDIENTE]
5. Regla de cadena "cada archivo se conecta al ultimo": no escrita. Propuesta en una linea: cada SDK nuevo es plugins/<id>/ con conecta_con.plugin_anterior = id del ultimo plugin agregado, sin tocar el codigo del Router. [PENDIENTE: aprobar]
6. Lista de 10+ SDK "sol gpt": no la encontre en lo que lei; el campo sdk de policies.json espera la lista del Director. [PENDIENTE]
7. 15 claves de SDK por recibir: entran por /vault/credentials con el Router vivo y el banco abierto; el banco NO admite escritura desde fuera (ver CONECTAR-SDK-NUEVO.md). Ademas PROVIDER_MAP solo conoce 6 proveedores y el banco se cierra solo tras 1 h. [BLOQUEADO]
8. hf_storage: Storage Bucket real y enlace del chat de Manus (T-08). Watchdog espera el secreto de control de Jobs. [PENDIENTE]

## Bloque 4 (union2, 2026-09-30)
- Hecho y probado: banco configurable (providers.json + RIU_VAULT_AUTOLOCK_S), POST /plugins/sync y /control/reload-policies, guardian + plugin lifeguard, plugin ssh_bridge + transporte ssh.
- Las fichas de lifeguard y hf_* se corrigieron (runtime_type compute, sandbox egress-allowlist): antes el host las marcaba invalid.
- Pendiente: arrancar el guardian en HF con tokens reales (no probado en vivo), paramiko en requirements del Space, prueba real ssh contra un host.

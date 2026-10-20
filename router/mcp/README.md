# router/mcp: MCP "riu-router-github" (Edificio 1)

Que es: la puerta MCP del Router (`POST /mcp`). Claude y Sol la usan para leer/escribir GitHub y manejar el Router y el chat.
Ya existia una puerta `/mcp` (integration/chat_mvp/mcp_route.py + mcp_puente_github.py) con solo 3 herramientas GitHub (sin rama restringida ni readback, llave en `?key=`). Esta carpeta la amplia; `server.build_mcp_router()` tiene el mismo nombre para sustituirla con un cambio de una linea en app.py (no aplicado aqui).

Reglas: solo HTTP (GitHub REST y `/plugins/<id>/call/<accion>`); no importa plugins. Sin Actions/Vercel/LFS/Jobs.

Herramientas (permiso): entrada -> salida `{ok, ...}`; `ok:false` = fallo real, el MCP responde `isError:true`.
- github_leer (lectura): repo, ruta, rama, lineas -> contenido + sha.
- github_escribir (escritura): repo, ruta, contenido, rama, mensaje. Solo ramas de `RIU_MCP_RAMAS` (def. feat/modos-router,reorganizacion; `main` rechazada). Exito = commit sha + readback identico; si no, error.
- router_estado (lectura): GET /health + puente_chat/status.
- plugin_llamar (ejecucion): plugin, accion, payload -> POST /plugins/<plugin>/call/<accion>. `banco` bloqueado.
- chat_enviar (ejecucion): model, mensaje|messages, sesion -> proceso_id.
- probar_modelo (ejecucion): model, prompt. PASS solo con respuesta real; sin respuesta = PENDIENTE; error = FALLO.
- ver_proceso (lectura): proceso_id -> terminado + contenido.
Errores: RAMA_NO_PERMITIDA, READBACK_NO_COINCIDE, GITHUB_<codigo>, ROUTER_<codigo>, PLUGIN_NO_OK, RED, FALTA_GITHUB_PAT, BLOQUEADO, ARGUMENTOS.

Secretos (solo entorno; el Router los carga desde su banco): `RIU_MCP_KEY` (llave del MCP), `RIU_CHAT_KEY` (ref banco router/chat-ui-director), `RIU_GITHUB_PAT`. Auth del cliente: cabecera `X-API-Key`/`Bearer`; `?key=` solo por compatibilidad con conectores. Sin llave configurada el servidor queda cerrado. Salidas pasan por redaccion de secretos.

Pruebas offline: `python3 -I router/mcp/test_mcp.py` (desde la carpeta que contiene `router/`).

Pendiente (no cableado a proposito): leer secretos del banco por HTTP (hoy `banco/get_keys` es solo interno), acciones HTTP de reinicio/despliegue del Router, ver_proceso de procesos que no sean de puente_chat. Nota: llamar a la carpeta `mcp` puede chocar con el SDK `mcp` de Python si `router/` esta en sys.path; importar como `router.mcp`.

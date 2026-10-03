# harness plugins - el harness de DeepSeek y sus plugins YAIWES (carpeta aislada)
Objetivo: si todo lo demas se desconecta, el harness y sus plugins quedan intactos y se enchufan de nuevo.
- deepseek-harness-chat/ : harness de DeepSeek (codigo bajado y plugins oficiales). No se edita.
- memoria/ : plugin YAIWES de memoria (harness-memoria.cordis.yml + memoria_mcp_server.py).

Flujo (unica ruta): Harness -> plugin memoria (MCP) -> Router /memoria/* -> chat router/memoria (motores)
Frontera: se llega hasta este plugin. Lo que esta detras es el orquestador de memoria.
Uso: RIU_ROUTER_URL=... RIU_API_KEY=... dsh headless --patch 'chat router/harness plugins/memoria/harness-memoria.cordis.yml' "tarea"

# T-00 — Auditar el Router y dejar uno solo
**Estado:** PASS · **Depende de:** nada · **Nodo:** N-00 en `CRAZY_WALL.json`

## Qué es, en palabras simples
Comprobar cuál Router está vivo de verdad y que sea el único al que se conecta todo. Nada de suponer: solo lo que se probó.

## Resultado verificado (2026-09-29)
- Hay un solo Router: un Job de Hugging Face (máquina cpu-basic de 16 GB), lanzado por `.github/workflows/riu-router-job-central.yml`. Su dirección está en `router inteligente universal/agents-yaiwes/ROUTER_JOB_PAUSE.flag` (línea `LIVE_URL`).
- Rutas probadas (run 36513612455): `/health` 200, `/chat/models` 200, `/chat/router/status` 200. `/v1/models` solo lista 2 modelos chicos (no sirve para agentes). `/chat/send` y `/chat/jev` con provider=hf fallan (400 y 503): no usarlos.
- Incidente: un vigilante de 32 GB canceló el Router a las 02:15Z (run 36511703509). Ya está borrado.

## Cómo se llama al Router
Cabeceras: `Authorization: Bearer <HF_TOKEN_1>` + `X-API-Key: <RIU_ROUTER_API_KEY>` (solo los nombres; las claves están en tu banco).

## Listo cuando (ya cumplido)
Un solo Router vivo, probado, y todo lo demás apuntando a él.

## Evidencia
`BITACORA.jsonl` B-0001, B-0002, B-0003, B-0007.

## No hacer
Crear otro router. Reiniciar o tocar el conector MCP.

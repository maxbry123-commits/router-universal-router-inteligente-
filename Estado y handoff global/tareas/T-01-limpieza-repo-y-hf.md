# T-01 — Limpieza general del repo y de Hugging Face
**Estado:** PASS (repo y HF). Falta solo la parte de Vercel, que quedó "para después" por tu orden · **Depende de:** T-00 · **Nodo:** N-01

## Qué es, en palabras simples
Borrar lo que hace ruido (notas viejas, estados, sentinelas que generaban commits sin parar, workflows de un solo uso, Spaces sin uso) y dejar solo tus archivos y los componentes.

## Hecho (con evidencia)
- Repo: copia de seguridad en la rama `backup-antes-limpieza-20260929`; limpieza en los commits a53825c y 99e3104. Workflows: de 88 a unos 27.
- Sentinelas y mini-router: pausados/borrados (hacían ~180 commits en 3 días).
- Hugging Face: borrados `omniroute-1..5` (run 36518718390). Queda el Space del conector MCP (protegido), el Job del Router y el dataset de memoria.
- `replicar-motores.yml` borrado (copiaba los motores a todos tus repos en cada cambio).

## Pendiente (solo Vercel)
Las variables del proyecto `riu-jev-bridge` (`RIU_CHAT_PASSWORD`, `RIU_ROUTER_API_KEY`, `RIU_ROUTER_URL`, `HF_JOB_FLAVOR`, `HF_TOKEN_1`) NO se borraron: son secretas y no se pueden recuperar, y el deploy final las necesita. Tú dijiste "después borramos lo de Vercel". Decisión tuya cuando llegue el momento.

## No hacer
Tocar el Space `claude-github-mcp-backup`. Borrar componentes.

## Evidencia
`BITACORA.jsonl` B-0003, B-0004, B-0005, B-0006, B-0007, B-0008, B-0011.

# HANDOFF GPT -> HF CONTROL PLANE (2026-09-30)
Autor de la nota: agente `notas`. Fuente: resumen del coordinador. Estado: HECHO_SIN_VERIFICAR (codigo en main, sin prueba de humo).

## Que dejo GPT en main
- `remote_router`: plugin HTTP para hablar con un Router remoto.
- `hf_worker_pool.py`: autoescala al 85% de uso. CPU alta -> maquina 16 GB (cpu-basic). RAM alta -> 32 GB (cpu-upgrade). Sin uso 5 min -> cancela la maquina. Maximo 4 workers. Los workers hijos NO escalan.
- `hf_control_api.py`: rutas `/control/hf/status`, `/control/hf/workers`, `/control/hf/workers/ensure`, `/control/hf/invoke`.
- `POST /plugins/{id}/call/{action}`: llamada generica a cualquier plugin.
- Watchdog dentro de `riu-router-job-central.yml`: espera el secreto `HF_CONTROL_JOBS_TOKEN`.
- Commits: f0bca25, 3734566, ac2b4f8, b0eb32a, c5e7845, 898cec4, 7cd4f30, 2297a64, 79a5548.

## Pendiente (en este orden)
1. Crear el secreto `HF_CONTROL_JOBS_TOKEN`.
2. UN solo relanzamiento del Router con el token valido.
3. Definir `RIU_REMOTE_ROUTER_URL` y `RIU_REMOTE_ROUTER_API_KEY` (valores solo como secretos, nunca en archivos).
4. Habilitar el plugin `remote_router`.
5. Prueba de humo (status -> workers/ensure -> invoke).

## Regla
Un solo Router maestro + plugins + workers elasticos. NO cancelar el Job vivo `6abc32754c46ef1987032c93` mientras no exista un token valido.

## Huecos relacionados
Ver la seccion "Huecos detectados" de `Estado y handoff global/HANDOFF.md` (2026-09-30).

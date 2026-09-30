# secretos (bloque3)
Secretos del repo creados por API: HF_CONTROL_JOBS_TOKEN (HF, job.write), HF_TOKEN_1 (HF2), GH_AGENT_TOKEN (GH). Valores no guardados aqui.
Workflow riu-router-job-central.yml: HF_CONTROL_JOBS_TOKEN y HF_TOKEN_1 ya iban al Job; ahora HF_TOKEN_1 sale de secrets.HF_TOKEN_1 (antes copiaba el de control) y se agrega GH_AGENT_TOKEN. Se pasan por secrets= de run_job (no salen en logs).
Confirmado: flavor cpu-basic, vida 7d con fallback 48h y 24h, cron cada 30 min; no relanza si hay controlador RUNNING con menos de 46 h.
Ojo: el Job 6abc3275... corre con timeout 48h (creado 2026-09-29 21:49Z, vence ~2026-10-01 21:49Z); no tiene GH_AGENT_TOKEN ni HF_CONTROL_JOBS_TOKEN: requiere relanzamiento unico (coordinador).
Ojo: el watchdog juzga salud solo por edad (<46h), no por /health; una caida antes de 46h no se relanza. GitHub Actions bloqueado por facturacion: el watchdog no corre hasta resolverlo.
HF_TOKEN no lo usa el script del Job (solo RIU_* por defecto).

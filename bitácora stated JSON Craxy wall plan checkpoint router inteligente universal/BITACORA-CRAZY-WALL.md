# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3`
**Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0050
Trazabilidad previa preservada. HF-M01/M02/M03 mantienen PASS internos con boundaries externos; HF-M04 FLAG; HF-M05 integrado PASS; HF-M06/M07/M10/M11/M12 batch `6aa398fe5527934177ec4cd0` PASS con verifier individual, dataset RO y SHA/read-back.

## RIU-0051 — FAST-CLOSE M08-M20
Fuentes de verdad releídas antes del delta. Metadata HF revalidada: M08=31273.1M; M09=20914.8M MXFP4; M13=116829.2M MXFP4; M14=32762.1M; M15=34388.9M; M16=304180.4M FP8; M17/M18=GGUF; M19=72287.9M; M20=7615.6M AWQ 4-bit.
M08/M13/M14/M15/M16/M19 reciben FLAG específico contra `a10g-small` y el formato observado, o provider no autorizado; esto NO significa imposibilidad global.
M17/M18: Job inicial `6aa3a1875527934177ec4e06` ERROR exit127. StrategyDelta: probe `6aa3a24221047bf1b0374f88` encontró `/app/llama-cli`; retry real `6aa3a24f5527934177ec4e3c` lanzado en `a10g-small` con Q4_K_M y timeout 600s.
M09/M20: candidatos locales. vLLM smoke `6aa3a15c5527934177ec4e04` ERROR por `python` ausente de PATH en imagen; probe `6aa3a2cb5527934177ec4e50` lanzado para resolver entrypoint/runtime sin declarar fallo de modelo.
3 refutaciones PASS: metadata no equivale inferencia PASS; un fallo de ruta binaria no equivale fallo de modelo; un FLAG de flavor local no equivale imposibilidad global.
Council12 PASS; cross-check PASS; CODA `WAIT_M17_M18_THEN_M09_M20`; verify_final=`PARTIAL_PASS_CLASSIFICATION_EXECUTION_RUNNING`.

## NEXT
Cerrar M17/M18 individualmente si el retry completa; validar M09/M20 con runtime corregido; después entrar P02 sólo GAPs bloqueantes y P03 API Key Manager+E2E.
# BITÁCORA CRAZY WALL — ROUTER INTELIGENTE UNIVERSAL

**Contrato:** `tel.workflow/v3` · **Modo:** `FAIL_CLOSED_LOOP`

## RIU-0001..0051
Trazabilidad previa preservada: M01-M03 PASS internos; M04 FLAG; M05 integrado; M06/M07/M10/M11/M12 batch integrado; M08/M13/M14/M15/M16/M19 FLAGS exactos locales/provider; M17/M18 StrategyDelta en ejecución.

## RIU-0052 — HF-M20 REAL INFERENCE PASS
Fuentes de verdad releídas antes del delta. Job `6aa3a3cd5527934177ec4e7e` COMPLETED en `a10g-small` usando `/usr/local/bin/vllm serve Qwen/Qwen2.5-7B-Instruct-AWQ` con contexto 512. Endpoint OpenAI-compatible respondió para model_id exacto `Qwen/Qwen2.5-7B-Instruct-AWQ` con contenido `OK`; fingerprint `vllm-0.29.0-7d06a941`; SHA256 `/tmp/m20.json`=`5c45711905d5c34282a4711527ced24ede31e3390bf318285a01e8d78acf5302`; `HF_M20_OK=True`.
No se confundió `COMPLETED` con PASS: se exigieron model_id exacto, respuesta generada y SHA. M09 `6aa3a3dd5527934177ec4e80` y M17/M18 `6aa3a24f5527934177ec4e3c` siguen en curso.
3 refutaciones PASS; cross-check PASS; CODA `FINALIZE_M09_M17_M18_THEN_P02`; verify_final=`PASS_HF_M20_REAL_INFERENCE`.

## NEXT
Cerrar resultados terminales M09/M17/M18; si fallan, FLAG exacto sin otra ventana larga; luego P02 sólo bloqueantes y P03 API Key Manager+E2E.
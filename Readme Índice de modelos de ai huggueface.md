# Readme Índice de modelos de AI Hugging Face

## Regla de verdad
`CATALOG_OBSERVED` no significa `READY`; FAST-CLOSE cierra core con PASS ejecutable + FLAGS externos demostrados.

## Estado resumido
- M01-M03 PASS internos preservados; auth/provider/RW externos GAP/FLAG.
- M04 FLAG; M05 integrado PASS; M06/M07/M10/M11/M12 batch integrado PASS.
- M08/M13/M14/M15/M16/M19: FLAGS exactos para flavor/formato/provider actual.
- M17/M18: StrategyDelta GGUF Job `6aa3a24f5527934177ec4e3c` en curso.
- M09: vLLM Job `6aa3a3dd5527934177ec4e80` en curso.
- M20 `Qwen/Qwen2.5-7B-Instruct-AWQ`: **REAL_INFERENCE_VERIFIED** — Job `6aa3a3cd5527934177ec4e7e` COMPLETED en `a10g-small`; `/usr/local/bin/vllm serve`; exact model response `OK`; fingerprint `vllm-0.29.0-7d06a941`; SHA256 `/tmp/m20.json`=`5c45711905d5c34282a4711527ced24ede31e3390bf318285a01e8d78acf5302`; `HF_M20_OK=True`.

## Slots pendientes de cierre ejecutable
HF-M09, HF-M17, HF-M18. Los restantes no ejecutables en la ruta local actual conservan FLAG preciso y no bloquean P02/P03.

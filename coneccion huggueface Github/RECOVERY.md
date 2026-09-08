# RECOVERY

Objetivo cerrado: centralizar cómputo Hugging Face y puente GitHub sin rehacer trabajo verificado.

Último estado válido:
- 19 repositorios GitHub accesibles y registrados.
- Router central `HF1→HF2→HF3→cola` con umbral 95% verificado.
- Tres workers lógicos `cpu-upgrade` verificados con límite cgroup `32000000000` bytes.
- Storage real read/write verificado sobre bucket existente montado `/data`.
- E2E final: job `6a9f9c6f259f8e97255ee0b3` terminó `COMPLETED`, escribió `E2E_STORAGE_PASS` y creó commit GitHub `16b0ecc3b530e16b9469ef3ec3ac83ba597f7186`.

GAP resuelto por StrategyDelta: el OAuth conectado no crea buckets nuevos (403), por lo que se reutiliza el bucket existente ya probado.

Estado: VERIFIED_CLOSED. No reabrir salvo cambio de requisitos o regresión con evidencia.

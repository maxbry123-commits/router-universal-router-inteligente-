# BITACORA

## 2026-09-08 — LOOP 1
- Verificado MCP público Hugging Face sin OAuth repetitivo.
- Verificada identidad GitHub `maxbry123-commits` y 19 repositorios accesibles con el PAT clásico.
- Auditados 3 Spaces de COMAND-CENTER-1: solo `claude-github-mcp-backup` solicita `cpu-upgrade`; `COMAND-CENTER-MAXBRY` solicita `cpu-basic`; `prueba-1` es static.
- StrategyDelta: usar 3 workers lógicos Hugging Face Jobs `cpu-upgrade` bajo demanda para cumplir 32 GB sin mantener tres Spaces encendidos.
- Creada raíz central de cómputo y scheduler HF1→HF2→HF3→cola con umbral 95%.
- Creado puente lógico de almacenamiento en `osquestador-auditor/main` para 19 namespaces.
- El OAuth conectado de HF no puede crear un bucket nuevo (403); se reutiliza el bucket existente montado en `/data`.
- Desplegadas tools `storage_write/storage_read/storage_list`; roundtrip real `HF_STORAGE_ROUNDTRIP_PASS` verificado.
- Lanzados workers `cpu-upgrade`; cgroup reporta límite `32000000000` bytes en HF2/HF3.

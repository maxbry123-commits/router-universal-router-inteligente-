# RECOVERY

Objetivo: centralizar cómputo Hugging Face y puente GitHub sin rehacer trabajo verificado.

Último estado válido:
- PAT clásico del MCP enumera 19 repositorios.
- MCP público sin OAuth HF operativo.
- `COMAND-CENTER-1/claude-github-mcp-backup` solicita `cpu-upgrade` y duerme tras 300 s.
- Centro de cómputo creado en esta raíz.
- Puente lógico de almacenamiento creado en `maxbry123-commits/osquestador-auditor/main`.

GAP activo: el OAuth conectado de Hugging Face permite lectura pero no crear nuevos Buckets; se reutiliza el bucket ya montado hasta resolver sin detener el proyecto.

Siguiente delta: verificar tools de storage desplegadas y ejecutar write/read real sobre el bucket existente.

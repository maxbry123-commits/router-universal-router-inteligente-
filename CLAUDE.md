# CLAUDE.md — Router Inteligente Universal

Contrato operativo: `tel.workflow/v3` · modo `FAIL_CLOSED_LOOP`.

## Ruta canónica de trabajo
- GitHub `maxbry123-commits/router-universal-router-inteligente-`, branch `main`, es la fuente de verdad del proyecto.
- Para leer, editar y organizar archivos/raíces del repositorio usa GitHub directo mediante el workflow `Claude Root Editor` / GitHub token autorizado.
- `GitHub Backup HF` es un respaldo opcional. Si no está disponible, NO bloquea lectura, edición, organización de raíces, Handoff, Bitácora ni STATE en GitHub.
- Hugging Face y sus tokens autorizan recursos de Hugging Face; nunca se consideran autoridad para escribir en GitHub.

## Permisos y fail-closed
- Escritura en este repo: requiere capacidad GitHub con `contents: write`.
- Acceso transversal a otros repos: requiere `RIU_GITHUB_PAT` o una GitHub App con permisos efectivos sobre esos repos.
- Claude requiere `CLAUDE_CODE_OAUTH_TOKEN` disponible en GitHub Actions para ejecutar Claude Code.
- Nunca imprimir, copiar ni persistir valores de secretos en Git, logs, Handoff, Bitácora o chat.
- Si falla un permiso real de GitHub, marcar GAP con evidencia; no confundir la ausencia de un backup opcional con un fallo del repositorio primario.

## Cierre de cada cambio
1. aplicar solo el delta solicitado;
2. commit en `main` cuando esté autorizado;
3. hacer read-back del archivo/commit;
4. actualizar `STATE.json`, Crazy Wall/Handoff únicamente cuando cambie el estado operativo;
5. no declarar PASS sin evidencia real.